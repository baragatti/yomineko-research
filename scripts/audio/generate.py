"""Content-addressed TTS generator (design/audio_pipeline.md §3-§4, §7). Runs in the TTS venv.

  python generate.py --tier n5              plan, then synthesise + QA every missing unit up to tier n5
  python generate.py --tier n5 --pilot 200  stratified pilot (design §9), results in <store>/pilot.json
  python generate.py --prune                delete store files whose key is not in the manifest
  python generate.py --status               print the counts and exit

Stop: create <store>/STOP (the control app's Stop button does this), or Ctrl+C / Ctrl+Break. The batch
in flight is finished, QA'd and written; then the process exits. Resume = run again (keys already in
the manifest with their files present are skipped, so nothing is generated twice).

Store layout: masters/<k[:2]>/<k>.flac, opus/<k[:2]>/<k>.opus, manifest.json (key -> entry),
results.jsonl (append-only log, replayed on start), failures.json (needs_human), status.json (for the
app), config.json + voices.json (pins), review/ (last take of each needs_human unit).
"""
from __future__ import annotations

import argparse
import base64
import collections
import datetime as dt
import hashlib
import json
import os
import random
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("YOMINEKO_REPO", HERE.parents[1]))
AUDIO_ROOT = Path(os.environ.get("YOMINEKO_AUDIO_ROOT", Path.home() / "yomineko-audio"))
STORE = Path(os.environ.get("YOMINEKO_AUDIO_STORE", AUDIO_ROOT / "store"))
os.environ.setdefault("HF_HOME", str(AUDIO_ROOT / "hf"))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("MIOPEN_LOG_LEVEL", "1")
FFMPEG = os.environ.get("FFMPEG", r"C:\Binaries\ffmpeg.exe")
sys.path.insert(0, str(HERE))

from plan import TIERS, Unit, plan_units  # noqa: E402

BASE_REPO, BASE_REV = "ResembleAI/chatterbox", "5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18"
CONFIG_DEFAULTS = {
    "models": {
        "ja": {"name": "chatterbox-mtl-v3", "language_id": "ja", "t3_repo": BASE_REPO, "t3_revision": BASE_REV,
               "t3_file": "t3_mtl23ls_v3.safetensors",
               "t3_sha256": "5abca8321ede76f8e61f1cc0d19aea6c946b28871017ce8726f8a69203f05953",
               "s3gen_file": "s3gen.pt",
               "s3gen_sha256": "9b9ff07e60b20c136e2b1b3d7563a24604e8d2c4c267888d1ee929dd0151d2a3"},
        "pt-BR": {"name": "chatterbox-mtl-v3-pt-br", "language_id": "pt",
                  "t3_repo": "ResembleAI/Chatterbox-Multilingual-pt-br",
                  "t3_revision": "b3952f18bc2eaa72b9bd7c17d2c4653bcad4770d", "t3_file": "t3_pt_br.safetensors",
                  "t3_sha256": "074aaf65255eb9cb960288f7cc72e09d3b5008f6e0b14868c0d4e5b0bd7cbb6c",
                  "s3gen_file": "s3gen_v3.pt",
                  "s3gen_sha256": "f7abce4b196dae2d08d9296cbebc6521b046079577643b42a19a03499d08721e"},
    },
    "params": {"exaggeration": 0.5, "cfg_weight": 0.5, "temperature": 0.8, "repetition_penalty": 1.2,
               "min_p": 0.05, "top_p": 1.0},
    "precision": {"t3": "bf16", "flow": "fp16", "hift": "fp16", "miopen": False, "static_kv": True},
    "batch": 30,
    "batch_kv_budget": 25000,
    "norm": {"ja": "ja-1", "pt-BR": "pt-1"},
    "post": "p1",
    "voices": {"ja-word": "ja-pilot-f1@1", "ja-sentence": ["ja-pilot-f1@1"], "ja-M1": "ja-pilot-f1@1",
               "ja-M2": "ja-pilot-f1@1", "ja-F1": "ja-pilot-f1@1", "ja-F2": "ja-pilot-f1@1",
               "ja-N": "ja-pilot-f1@1", "pt-narrator": "pt-pilot-f1@1"},
    "asr_model": "openai/whisper-large-v3",
    "max_takes": 3,
    "opus_bitrate": "32k",
}
VOICES_DEFAULTS = {
    "ja-pilot-f1@1": {
        "lang": "ja", "role": "pilot (all ja classes until consented voices exist)", "gender": "female",
        "file": "voices/res_ja_f.flac",
        "reference_clip_sha256": "62b1b53f8b185a1df9e0086a3eee7f6447f3bbcba5154466e993458270f66e8a",
        "source": "Resemble AI's default ja prompt of the official Chatterbox Multilingual demo "
                  "(HF Space ResembleAI/Chatterbox-Multilingual-TTS@c612a942 -> "
                  "storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/ja/ja_prompts1.flac, identical to ja_f.flac)",
        "consent_ref": None, "licence": "model-bundled demo voice; no consent record; PILOT ONLY, replace before shipping",
        "created": "2026-09-27", "status": "pilot"},
    "pt-pilot-f1@1": {
        "lang": "pt-BR", "role": "pilot pt-narrator", "gender": "female", "file": "voices/res_pt_br_f2.wav",
        "reference_clip_sha256": "b74124fa87356241316d2d55b8f9dfea1da57f08325f63e9198e33f755659482",
        "source": "Resemble AI's default prompt of the official pt-BR Language Pack demo "
                  "(HF Space ResembleAI/Chatterbox-Multilingual-TTS-pt-br@9e515821 -> "
                  "storage.googleapis.com/chatterbox-demo-samples/mtl-v3-single-language-prompts/pt-br/pt_br_f2.wav)",
        "consent_ref": None, "licence": "model-bundled demo voice; no consent record; PILOT ONLY, replace before shipping",
        "created": "2026-09-27", "status": "pilot"},
}


# --- config / paths --------------------------------------------------------------------------------
def _write_json(path: Path, obj, indent=1) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=indent, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def load_config() -> tuple[dict, dict]:
    STORE.mkdir(parents=True, exist_ok=True)
    cp, vp = STORE / "config.json", STORE / "voices.json"
    if not cp.exists():
        _write_json(cp, CONFIG_DEFAULTS)
    if not vp.exists():
        _write_json(vp, VOICES_DEFAULTS)
    return json.loads(cp.read_text(encoding="utf-8")), json.loads(vp.read_text(encoding="utf-8"))


def hf_file(repo: str, rev: str, name: str) -> Path:
    from huggingface_hub import hf_hub_download
    return Path(hf_hub_download(repo, name, revision=rev))


ASR_REVISIONS = {"openai/whisper-large-v3": "06f233fe06e710322aca913c1bc4249a0d71fce1",
                 "openai/whisper-large-v3-turbo": "41f01f3fe87f28c78e2fbf8b568835947dd65ed9"}


def whisper_dir(repo: str) -> str:
    return str(hf_file(repo, ASR_REVISIONS[repo], "config.json").parent)


def make_engine(lang: str, cfg: dict | None = None, voices: dict | None = None, **over):
    import tts_engine as te
    cfg = cfg or CONFIG_DEFAULTS
    voices = voices or VOICES_DEFAULTS
    m = cfg["models"][lang]
    prec = cfg["precision"]
    base_dir = hf_file(BASE_REPO, BASE_REV, "ve.pt").parent
    hf_file(BASE_REPO, BASE_REV, "grapheme_mtl_merged_expanded_v1.json")
    t3 = hf_file(m["t3_repo"], m["t3_revision"], m["t3_file"])
    s3 = hf_file(BASE_REPO, BASE_REV, over.pop("s3gen_file", m["s3gen_file"]))
    vid = cfg["voices"]["pt-narrator"] if lang == "pt-BR" else cfg["voices"]["ja-word"]
    kw = dict(t3_dtype=prec["t3"], flow_dtype=prec["flow"], hift_fp16=prec["hift"] == "fp16",
              static_cache=prec.get("static_kv", True), exaggeration=cfg["params"]["exaggeration"])
    kw.update(over)
    return te.Engine(ckpt_dir=base_dir, t3_file=str(t3), s3gen_file=str(s3), voice_path=AUDIO_ROOT / voices[vid]["file"], **kw)


def stock_engines() -> dict:
    """The unmodified library path (fp32, one clip at a time) for the benchmark baseline."""
    import torch
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    from chatterbox.models.t3 import T3
    from chatterbox.models.t3.modules.t3_config import T3Config
    from chatterbox.models.tokenizers import MTLTokenizer
    from chatterbox.models.voice_encoder import VoiceEncoder
    from safetensors.torch import load_file
    out = {}
    base_dir = hf_file(BASE_REPO, BASE_REV, "ve.pt").parent
    for lang, m in CONFIG_DEFAULTS["models"].items():
        ve = VoiceEncoder()
        ve.load_state_dict(torch.load(base_dir / "ve.pt", weights_only=True))
        t3 = T3(T3Config.multilingual())
        t3.load_state_dict(load_file(hf_file(m["t3_repo"], m["t3_revision"], m["t3_file"])))
        from tts_engine import load_s3gen
        s3 = load_s3gen(hf_file(BASE_REPO, BASE_REV, m["s3gen_file"]))
        tts = ChatterboxMultilingualTTS(t3.to("cuda").eval(), s3.to("cuda").eval(), ve.to("cuda").eval(),
                                        MTLTokenizer(str(base_dir / "grapheme_mtl_merged_expanded_v1.json")), "cuda")
        vid = CONFIG_DEFAULTS["voices"]["pt-narrator" if lang == "pt-BR" else "ja-word"]
        tts.prepare_conditionals(str(AUDIO_ROOT / VOICES_DEFAULTS[vid]["file"]))
        out[lang] = tts
    import chatterbox.models.t3.t3 as t3mod
    t3mod.tqdm = lambda x, **k: x
    return out


# --- keys ------------------------------------------------------------------------------------------
def canonical(spec: dict) -> bytes:
    return json.dumps(spec, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def key_of(spec: dict) -> str:
    return base64.b32encode(hashlib.sha256(canonical(spec)).digest()).decode("ascii").lower().rstrip("=")[:26]


def seed_of(spec: dict) -> int:
    return int.from_bytes(hashlib.sha256(canonical(spec)).digest()[:8], "big")


def base_of(spec: dict) -> str:
    """Identity of the utterance across takes: the key of the spec without `take`."""
    s = json.loads(json.dumps(spec))
    s["params"].pop("take", None)
    return key_of(s)


def model_id(m: dict) -> str:
    return f"{m['name']}@{m['t3_sha256'][:12]}.{m['s3gen_sha256'][:12]}"


def voice_for(u: Unit, cfg: dict) -> str:
    v = cfg["voices"][u.vclass]
    if isinstance(v, list):  # sentence pool: the choice depends on the text only (design §5)
        v = v[int.from_bytes(hashlib.sha256(u.text.encode("utf-8")).digest()[:8], "big") % len(v)]
    return v


def build_spec(u: Unit, cfg: dict, take: int = 1) -> dict:
    p = cfg["precision"]
    params = {**cfg["params"], "precision": f"t3{p['t3']}.flow{p['flow']}.hift{p['hift']}", "take": take}
    return {"v": 1, "kind": "tts", "lang": u.lang, "norm": cfg["norm"][u.lang], "text": u.text,
            "voice": voice_for(u, cfg), "model": model_id(cfg["models"][u.lang]), "params": params,
            "post": cfg["post"]}


def token_cap(u: Unit) -> int:
    import qa
    exp = qa.expected_seconds("ja" if u.lang == "ja" else "pt", u.text, u.expected)
    # 25 speech tokens/s. Measured raw/expected duration: ja 0.8-1.4, pt 1.0-1.8 (bench.json); 2x + 1.5 s
    # leaves room, and a clip that runs past it is a runaway (no EOS) that fails anyway. It also sizes the
    # static KV cache, so a loose cap costs bandwidth on every step.
    return min(1000, int(25 * (2.0 * exp + 1.5)) + 10)


def kv_cost(u: Unit) -> int:
    """KV positions one item occupies (cond + text prefix + speech cap); x2 rows for CFG, ~0.12 MB each."""
    return token_cap(u) + len(u.text) + 64


def shard(kind: str, key: str) -> Path:
    ext = "flac" if kind == "masters" else "opus"
    return STORE / kind / key[:2] / f"{key}.{ext}"


# --- store -----------------------------------------------------------------------------------------
class Store:
    def __init__(self):
        self.manifest: dict[str, dict] = {}
        self.failures: dict[str, dict] = {}
        mp, fp = STORE / "manifest.json", STORE / "failures.json"
        if mp.exists():
            self.manifest = json.loads(mp.read_text(encoding="utf-8"))
        if fp.exists():
            self.failures = json.loads(fp.read_text(encoding="utf-8"))
        rp = STORE / "results.jsonl"
        if rp.exists():  # replay the append-only log (idempotent)
            for line in rp.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue  # a torn last line after a hard kill
                if r["type"] == "pass":
                    self.manifest[r["key"]] = r["entry"]
                    self.failures.pop(r["base"], None)
                elif r["type"] == "needs_human":
                    self.failures[r["base"]] = r["record"]
        for k, e in self.manifest.items():
            if key_of(e["spec"]) != k:
                raise SystemExit(f"manifest corrupt: {k} != hash(spec)")
        self.by_base = {base_of(e["spec"]): k for k, e in self.manifest.items()}
        self._log = open(rp, "a", encoding="utf-8")

    def append(self, rec: dict) -> None:
        self._log.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._log.flush()
        os.fsync(self._log.fileno())

    def add_pass(self, key: str, entry: dict) -> None:
        old = self.manifest.get(key)
        if old is not None and canonical(old["spec"]) != canonical(entry["spec"]):
            raise SystemExit(f"KEY COLLISION {key}: two different specs")
        base = base_of(entry["spec"])
        self.manifest[key] = entry
        self.by_base[base] = key
        self.failures.pop(base, None)
        self.append({"type": "pass", "key": key, "base": base, "entry": entry})

    def add_failure(self, base: str, record: dict) -> None:
        self.failures[base] = record
        self.append({"type": "needs_human", "base": base, "record": record})

    def files_ok(self, key: str) -> bool:
        e = self.manifest.get(key)
        if not e:
            return False
        m, o = shard("masters", key), shard("opus", key)
        return m.exists() and o.exists() and m.stat().st_size == e["bytes_master"] and o.stat().st_size == e["bytes_opus"]

    def save(self) -> None:
        _write_json(STORE / "manifest.json", dict(sorted(self.manifest.items())))
        _write_json(STORE / "failures.json", dict(sorted(self.failures.items())))


# --- logging / status / stop -----------------------------------------------------------------------
LOG_LINES: collections.deque = collections.deque(maxlen=40)
STOP = {"flag": False}


def log(msg: str) -> None:
    line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    LOG_LINES.append(line)
    print(line, flush=True)
    (AUDIO_ROOT / "logs").mkdir(exist_ok=True)
    with open(AUDIO_ROOT / "logs" / "generate.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def stop_requested() -> bool:
    return STOP["flag"] or (STORE / "STOP").exists()


def _on_signal(*_):
    STOP["flag"] = True


def write_status(**kw) -> None:
    kw.update(updated=dt.datetime.now().isoformat(timespec="seconds"), pid=os.getpid(), last=list(LOG_LINES)[-15:])
    _write_json(STORE / "status.json", kw, indent=1)


# --- synthesis -------------------------------------------------------------------------------------
def encode_files(key: str, wav) -> tuple[int, int, str, str]:
    """Atomic write of <key>.flac (24-bit master) and <key>.opus (Ogg Opus 32 kbps mono)."""
    import soundfile as sf
    m, o = shard("masters", key), shard("opus", key)
    m.parent.mkdir(parents=True, exist_ok=True)
    o.parent.mkdir(parents=True, exist_ok=True)
    mt, ot = m.with_suffix(".flac.tmp"), o.with_suffix(".opus.tmp")
    sf.write(mt, wav, 24000, format="FLAC", subtype="PCM_24")
    cfgb = CONFIG_DEFAULTS["opus_bitrate"]
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", str(mt), "-c:a", "libopus",
                    "-b:a", cfgb, "-ac", "1", "-map_metadata", "-1", "-f", "ogg", str(ot)], check=True)
    os.replace(mt, m)
    os.replace(ot, o)
    mb, ob = m.read_bytes(), o.read_bytes()
    return len(mb), len(ob), hashlib.sha256(mb).hexdigest(), hashlib.sha256(ob).hexdigest()


def run_jobs(jobs: list[dict], cfg: dict, voices: dict, store: Store, status: dict, asr, pilot_log: list | None) -> None:
    """jobs: {'unit': Unit, 'spec': dict, 'attempts': []}. Groups by language, batches by length."""
    import numpy as np
    import torch
    import qa
    import tts_engine as te
    torch.backends.cudnn.enabled = bool(cfg["precision"].get("miopen", False))
    p = te.SynthParams(**cfg["params"])
    today = dt.date.today().isoformat()
    for lang in ("ja", "pt-BR"):
        queue = [j for j in jobs if j["unit"].lang == lang]
        if not queue:
            continue
        log(f"loading {lang} engine ({len(queue)} jobs)")
        eng = make_engine(lang, cfg, voices)
        mlang = cfg["models"][lang]["language_id"]
        qlang = "ja" if lang == "ja" else "pt"
        while queue:
            if stop_requested():
                log("stop requested: exiting after the last finished batch")
                return
            queue.sort(key=lambda j: len(j["unit"].text))  # similar lengths share a batch; retakes join in
            B = min(cfg["batch"], len(queue))  # the static KV cache is items x (prefix + cap): bound it
            while B > 1 and B * kv_cost(queue[B - 1]["unit"]) > cfg["batch_kv_budget"]:
                B -= 1
            batch, queue = queue[:B], queue[B:]
            t0 = time.perf_counter()
            units = [j["unit"] for j in batch]
            clips = eng.synth([u.text for u in units], mlang, [seed_of(j["spec"]) for j in batch],
                              [token_cap(u) for u in units], p)
            t_synth = time.perf_counter() - t0
            posts = [qa.post_p1(c.wav) if c.wav.size else (np.zeros(1, np.float32), {"speech_s": 0, "lufs": float("nan"),
                                                                                      "true_peak_dbtp": 0, "duration_ms": 0})
                     for c in clips]
            texts = asr.transcribe([pw for pw, _ in posts], qlang)
            audio_s = 0.0
            for j, c, (pw, info), tx in zip(batch, clips, posts, texts):
                u, spec = j["unit"], j["spec"]
                key = key_of(spec)
                score, got = qa.ja_score(tx, u.expected) if qlang == "ja" else qa.pt_score(tx, u.expected)
                sig = ["no end-of-speech within cap"] if c.overlong else qa.signal_check(
                    c.wav, pw, info, qa.expected_seconds(qlang, u.text, u.expected))
                ok = qa.passes(u.kind, qlang, score) and not sig
                att = {"take": spec["params"]["take"], "key": key, "asr": tx, "asr_norm": got, "score": round(score, 4),
                       "signal": sig, "pass": ok}
                j["attempts"].append(att)
                audio_s += info["duration_ms"] / 1000
                if ok:
                    bm, bo, hm, ho = encode_files(key, pw)
                    store.add_pass(key, {
                        "spec": spec, "display": u.display, "kind": u.kind, "reading_source": u.reading_source,
                        "duration_ms": info["duration_ms"], "bytes_master": bm, "bytes_opus": bo,
                        "sha256_master": hm, "sha256_opus": ho,
                        "qa": {"status": "pass", "asr_model": cfg["asr_model"].split("/")[-1],
                               ("mora_cer" if qlang == "ja" else "wer"): round(score, 4), "asr_text": tx,
                               "lufs": info["lufs"], "true_peak_dbtp": info["true_peak_dbtp"], "checked": today},
                        "consumers": sorted(u.consumers), "created": today})
                    status["done"] += 1
                    status["passed_run"] += 1
                elif spec["params"]["take"] < cfg["max_takes"]:
                    nxt = json.loads(json.dumps(spec))
                    nxt["params"]["take"] += 1
                    queue.append({"unit": u, "spec": nxt, "attempts": j["attempts"]})
                else:
                    base = base_of(spec)
                    rev = STORE / "review" / f"{base}.flac"
                    rev.parent.mkdir(exist_ok=True)
                    import soundfile as sf
                    if pw.size > 1:
                        sf.write(rev, pw, 24000, format="FLAC", subtype="PCM_16")
                    store.add_failure(base, {"status": "needs_human", "text": u.text, "display": u.display,
                                             "lang": u.lang, "kind": u.kind, "expected": u.expected,
                                             "consumers": sorted(u.consumers), "attempts": j["attempts"],
                                             "review_clip": str(rev.relative_to(STORE)), "date": today})
                    status["failed"] += 1
                if pilot_log is not None and (ok or spec["params"]["take"] >= cfg["max_takes"]):
                    pilot_log.append({"kind": u.kind, "lang": u.lang, "display": u.display, "text": u.text,
                                      "expected": u.expected, "pass": ok, "takes": len(j["attempts"]),
                                      "attempts": j["attempts"], "reading_source": u.reading_source})
            wall = time.perf_counter() - t0
            status["wall_s"] += wall
            status["audio_s"] += audio_s
            status["units_run"] += len(batch)
            rate = status["units_run"] / max(status["wall_s"], 1e-6)
            pending = status["total"] - status["done"] - status["failed"]
            status["pending"] = pending
            status["rate_units_per_min"] = round(rate * 60, 1)
            status["rtf_pipeline"] = round(status["wall_s"] / max(status["audio_s"], 1e-6), 3)
            status["eta_s"] = int(pending / rate) if rate > 0 else None
            log(f"{lang} batch {len(batch)}: synth {t_synth:.1f}s total {wall:.1f}s audio {audio_s:.1f}s | "
                f"done {status['done']}/{status['total']} failed {status['failed']} eta {status['eta_s']}s")
            write_status(**status)
            if status["units_run"] % 300 < len(batch):
                store.save()
        del eng
        torch.cuda.empty_cache()


# --- pilot selection (design §9) -------------------------------------------------------------------
def pick_pilot(units: list[Unit], n: int) -> list[Unit]:
    import qa
    rnd = random.Random(20260927)
    by = collections.defaultdict(list)
    for u in units:
        by[u.kind].append(u)
    for v in by.values():
        v.sort(key=lambda u: u.text)
        rnd.shuffle(v)
    homo = [u for u in by["word"] if len(u.consumers) > 1 and len({c.split("#")[0] for c in u.consumers if c.startswith("vocab:")}) > 1]
    sent = by["sentence"] + by["passage"]
    short = [u for u in sent if qa.morae(u.expected) <= 14]
    long_ = [u for u in sent if qa.morae(u.expected) > 14]
    digit = [u for u in long_ if any(ch.isdigit() for ch in u.display)]
    pick: list[Unit] = []

    def take(pool, k):
        got = [u for u in pool if u not in pick][:k]
        pick.extend(got)

    take(homo, 10)
    take(by["word"], 40)
    take(by["kana"], 20)
    take(short, 50)
    take(digit, 20)
    take(long_, 20)
    take(by["listen"], 20)
    take(by["narration"], 20)
    take(by["inline"] + by["narration"], max(0, n - len(pick)))
    return pick[:n]


# --- main ------------------------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="n5", choices=TIERS)
    ap.add_argument("--pilot", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--prune", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--retry-failed", action="store_true")
    a = ap.parse_args()
    signal.signal(signal.SIGINT, _on_signal)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, _on_signal)
    cfg, voices = load_config()
    store = Store()
    if a.prune:
        return prune(store)
    (STORE / "STOP").unlink(missing_ok=True)
    log(f"plan: reading export at {REPO}")
    pl = plan_units(REPO)
    specs: dict[str, tuple[Unit, dict]] = {}
    for u in pl.units.values():
        s = build_spec(u, cfg)
        k = key_of(s)
        if k in specs and canonical(specs[k][1]) != canonical(s):
            raise SystemExit(f"KEY COLLISION in plan: {k}")
        if k in specs:  # same spec from two voice classes (one pilot voice): merge the consumers
            specs[k][0].consumers |= u.consumers
            specs[k][0].tiers |= u.tiers
            continue
        specs[k] = (u, s)
    base_units = {base_of(s): (u, s) for u, s in specs.values()}
    # consumers are recomputed from the export on every run; orphans leave the manifest (files stay until --prune)
    retain = set(json.loads((STORE / "retain.json").read_text()) if (STORE / "retain.json").exists() else [])
    orphans = [k for k, e in store.manifest.items() if base_of(e["spec"]) not in base_units and k not in retain]
    if len(specs) < len(store.manifest) // 2 or len(pl.errors) > len(specs) // 20:
        raise SystemExit(f"plan has {len(specs)} keys / {len(pl.errors)} errors vs {len(store.manifest)} in the "
                         "manifest: the export looks broken, aborting before dropping anything")
    for k in orphans:
        del store.manifest[k]
    for k, e in store.manifest.items():
        e["consumers"] = sorted(base_units[base_of(e["spec"])][0].consumers)
    store.by_base = {base_of(e["spec"]): k for k, e in store.manifest.items()}
    upto = TIERS[: TIERS.index(a.tier) + 1]
    in_tier = {b: (u, s) for b, (u, s) in base_units.items() if u.tier in upto}
    done = {b for b in in_tier if b in store.by_base and store.files_ok(store.by_base[b])}
    failed = {b for b in in_tier if b in store.failures and b not in done}
    log(f"plan: {len(specs)} keys in export, {len(in_tier)} up to tier {a.tier}; done {len(done)}, "
        f"needs_human {len(failed)}, orphans dropped {len(orphans)}, plan errors {len(pl.errors)}")
    status = {"state": "running", "tier": a.tier, "total": len(in_tier), "done": len(done), "failed": len(failed),
              "pending": 0, "passed_run": 0, "units_run": 0, "wall_s": 0.0, "audio_s": 0.0,
              "started": dt.datetime.now().isoformat(timespec="seconds"), "pilot": a.pilot}
    if a.status:
        status["pending"] = len(in_tier) - len(done) - len(failed)
        print(json.dumps(status, indent=1))
        store.save()
        return 0
    todo_bases = [b for b in in_tier if b not in done and (a.retry_failed or b not in failed)]
    todo_units = [in_tier[b][0] for b in todo_bases]
    if a.pilot:
        todo_units = pick_pilot(todo_units, a.pilot)
        status["total"] = len(todo_units)
        status["done"] = status["failed"] = 0
    elif a.limit:
        todo_units = todo_units[: a.limit]
    jobs = []
    for u in todo_units:
        b = base_of(build_spec(u, cfg))
        spec = store.manifest[store.by_base[b]]["spec"] if b in store.by_base else build_spec(u, cfg)
        jobs.append({"unit": u, "spec": spec, "attempts": []})
    status["pending"] = len(jobs)
    write_status(**status)
    log(f"todo: {len(jobs)} units ({collections.Counter(j['unit'].kind for j in jobs)})")
    pilot_log: list | None = [] if a.pilot else None
    state = "done"
    try:
        if jobs:
            import qa
            log(f"loading ASR {cfg['asr_model']}")
            asr = qa.Asr(whisper_dir(cfg["asr_model"]))
            run_jobs(jobs, cfg, voices, store, status, asr, pilot_log)
        if stop_requested():
            state = "stopped"
    except BaseException as e:  # keep what finished; report the error to the app
        state = "error"
        log(f"ERROR {type(e).__name__}: {e}")
        raise
    finally:
        store.save()
        status["state"] = state
        write_status(**status)
        if pilot_log is not None:
            _write_json(STORE / "pilot.json", pilot_log)
        log(f"exit: {state}; done {status['done']}/{status['total']} failed {status['failed']}")
    return 0


def prune(store: Store) -> int:
    keep = set(store.manifest)
    n = 0
    for kind in ("masters", "opus"):
        for f in (STORE / kind).glob("*/*"):
            k = f.name.split(".")[0]
            if k not in keep or f.name.endswith(".tmp"):
                f.unlink()
                n += 1
    log(f"prune: deleted {n} files not in the manifest ({len(keep)} keys kept)")
    return 0


if __name__ == "__main__":
    rc = main()
    sys.stdout.flush()
    os._exit(rc)  # ROCm on Windows can hang at interpreter shutdown; everything is flushed by now
