"""Speed/quality benchmark on 30 fixed lines (15 ja from verified tokens, 15 pt-BR narration).

Writes <audio root>/BENCHMARK.md and bench.json. Every setting synthesises the same lines with the same
seeds; RTF = synthesis wall seconds / audio seconds (after warm-up); the ASR check (qa.py) decides
whether the setting keeps quality. Run in the TTS venv:  python bench.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import generate as G  # noqa: E402  (paths, config, engine factory)
import qa  # noqa: E402
import tts_engine as te  # noqa: E402
from plan import plan_units  # noqa: E402


def pick_lines(pl) -> list:
    ja = sorted((u for u in pl.units.values() if u.tier == "n5" and u.kind == "sentence"),
                key=lambda u: (qa.morae(u.expected), u.text))
    pt = sorted((u for u in pl.units.values() if u.tier == "n5" and u.kind == "narration" and 20 <= len(u.text) <= 240),
                key=lambda u: (len(u.text), u.text))
    digits = [u for u in ja if any(c.isdigit() for c in u.display)][:2]
    rest = [u for u in ja if u not in digits]
    ja_sel = digits + [rest[int(i * (len(rest) - 1) / 12)] for i in range(13)]
    pt_sel = [pt[int(i * (len(pt) - 1) / 14)] for i in range(15)]
    return ja_sel + pt_sel


BASE = dict(cudnn=False, t3="bf16", flow="fp16", hift16=True, static=True, batch=30, over={}, sdpa=None, s3gen_ja=None)
SETTINGS = [
    dict(BASE, name="stock fp32 (ChatterboxMultilingualTTS.generate), one clip at a time", cudnn=True, t3="stock",
         static=False, batch=1),
    dict(BASE, name="engine fp32, B=1, MIOpen on, dynamic KV cache", cudnn=True, t3="fp32", flow="fp32", hift16=False,
         static=False, batch=1),
    dict(BASE, name="+ bf16 T3 + fp16 flow decoder", cudnn=True, hift16=False, static=False, batch=1),
    dict(BASE, name="+ MIOpen off (PyTorch native conv)", hift16=False, static=False, batch=1),
    dict(BASE, name="+ HiFiGAN autocast fp16", static=False, batch=1),
    dict(BASE, name="+ static KV cache", batch=1),
    dict(BASE, name="+ batch 8", batch=8),
    dict(BASE, name="+ batch 16", batch=16),
    dict(BASE, name="+ batch 30 (all 15 lines of a language in one batch)"),
    dict(BASE, name="variant: fp16 T3 (instead of bf16)", t3="fp16"),
    dict(BASE, name="variant: fp32 T3", t3="fp32"),
    dict(BASE, name="variant: SDPA math backend only (batch 8)", sdpa="math", batch=8),
    dict(BASE, name="variant: cfg_weight 0, CFG rows dropped (batch 8)", over={"cfg_weight": 0.0}, batch=8),
    dict(BASE, name="variant: temperature 0.5 (batch 8)", over={"temperature": 0.5}, batch=8),
    dict(BASE, name="variant: exaggeration 0.3 (batch 8)", over={"exaggeration": 0.3}, batch=8),
    dict(BASE, name="variant: ja decoder s3gen_v3.pt, the pt pack's decoder (batch 8)", s3gen_ja="s3gen_v3.pt", batch=8),
]
torch_compile_note = "torch.compile: not available (no Triton for ROCm on Windows: TritonMissing)"


def seed_of(u) -> int:
    return int.from_bytes(hashlib.sha256(u.text.encode()).digest()[:8], "big")


def run_setting(engines, asr, lines, st) -> dict:
    name, t3d, batch, over, sdpa = st["name"], st["t3"], st["batch"], st["over"], st["sdpa"]
    torch.backends.cudnn.enabled = st["cudnn"]
    p = te.SynthParams(**{**G.CONFIG_DEFAULTS["params"], **over})
    res = {"name": name, "clips": []}
    by_lang = {"ja": [u for u in lines if u.lang == "ja"], "pt-BR": [u for u in lines if u.lang == "pt-BR"]}
    synth_s = audio_s = 0.0
    for lang, us in by_lang.items():
        eng = engines[lang]
        mlang = "ja" if lang == "ja" else "pt"
        ctx = torch.nn.attention.sdpa_kernel(torch.nn.attention.SDPBackend.MATH) if sdpa == "math" else _null()
        with ctx:
            for warm in (True, False):
                outs = []
                t0 = te._now()
                for k in range(0, len(us), batch):
                    chunk = us[k:k + batch]
                    caps = [G.token_cap(u) for u in chunk]
                    if t3d == "stock":
                        for u in chunk:
                            torch.manual_seed(seed_of(u) % 2**63)
                            w = eng.generate(u.text, mlang, exaggeration=p.exaggeration, cfg_weight=p.cfg_weight,
                                             temperature=p.temperature).squeeze(0).numpy()
                            outs.append((u, w))
                    else:
                        clips = eng.synth([u.text for u in chunk], mlang, [seed_of(u) for u in chunk], caps, p)
                        outs.extend((u, c.wav) for u, c in zip(chunk, clips))
                    if warm:
                        break
                dt = te._now() - t0
            synth_s += dt
            audio_s += sum(len(w) / te.SR for _, w in outs)
        t0 = time.perf_counter()
        posts = [qa.post_p1(w) for _, w in outs]
        texts = asr.transcribe([pw for pw, _ in posts], "ja" if lang == "ja" else "pt")
        res.setdefault("asr_s", 0.0)
        res["asr_s"] += time.perf_counter() - t0
        for (u, w), (pw, info), tx in zip(outs, posts, texts):
            score, got = qa.ja_score(tx, u.expected) if lang == "ja" else qa.pt_score(tx, u.expected)
            sig = qa.signal_check(w, pw, info, qa.expected_seconds("ja" if lang == "ja" else "pt", u.text, u.expected))
            ok = qa.passes(u.kind, "ja" if lang == "ja" else "pt", score) and not sig
            res["clips"].append({"lang": lang, "text": u.text, "asr": tx, "score": round(score, 3), "signal": sig, "pass": ok,
                                 "audio_s": round(len(w) / te.SR, 2)})
    res["synth_s"], res["audio_s"] = synth_s, audio_s
    res["rtf"] = synth_s / audio_s
    res["pass"] = sum(c["pass"] for c in res["clips"])
    res["vram_gib"] = round(torch.cuda.max_memory_allocated() / 2**30, 2)
    return res


class _null:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def main():
    pl = plan_units(G.REPO)
    lines = pick_lines(pl)
    asr = qa.Asr(G.whisper_dir(G.CONFIG_DEFAULTS["asr_model"]))
    out = G.AUDIO_ROOT / "bench.json"
    results = json.loads(out.read_text(encoding="utf-8")) if "--only" in sys.argv and out.exists() else []
    engines, cur = None, None
    only = [int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")] if "--only" in sys.argv else None
    for i, st in enumerate(SETTINGS, 1):
        if only and i not in only:
            continue
        key = (st["t3"], st["flow"], st["hift16"], st["static"], st["s3gen_ja"], st["over"].get("exaggeration"))
        if key != cur:
            engines = None
            torch.cuda.empty_cache()
            if st["t3"] == "stock":
                engines = G.stock_engines()
            else:
                ex = st["over"].get("exaggeration", 0.5)
                engines = {lang: G.make_engine(lang, t3_dtype=st["t3"], flow_dtype=st["flow"], hift_fp16=st["hift16"],
                                               static_cache=st["static"], exaggeration=ex,
                                               **({"s3gen_file": st["s3gen_ja"]} if lang == "ja" and st["s3gen_ja"] else {}))
                           for lang in ("ja", "pt-BR")}
            cur = key
        torch.cuda.reset_peak_memory_stats()
        r = run_setting(engines, asr, lines, st)
        print(f"{r['name']}: RTF {r['rtf']:.3f}  pass {r['pass']}/30  asr {r['asr_s']:.1f}s", flush=True)
        results = [x for x in results if x["name"] != r["name"]] + [r]
        out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", out, flush=True)


def throughput(n: int = 96) -> None:
    """Batch-size sweep on a realistic mix: n random N5 ja units + n random N5 pt units, length-sorted
    like the generator does. Synthesis only; then the ASR cost per clip. Appends to bench_throughput.json."""
    import random
    torch.backends.cudnn.enabled = False
    pl = plan_units(G.REPO)
    rnd = random.Random(7)
    ja = [u for u in pl.units.values() if u.tier == "n5" and u.lang == "ja"]
    pt = [u for u in pl.units.values() if u.tier == "n5" and u.lang == "pt-BR"]
    rnd.shuffle(ja)
    rnd.shuffle(pt)
    sets = {"ja": sorted(ja[:n], key=lambda u: len(u.text)), "pt-BR": sorted(pt[:n], key=lambda u: len(u.text))}
    p = te.SynthParams(**G.CONFIG_DEFAULTS["params"])
    rows = []
    wavs_keep = {}
    for lang, us in sets.items():
        eng = G.make_engine(lang)
        mlang = "ja" if lang == "ja" else "pt"
        for bs, budget in ((1, 10**9), (8, 10**9), (16, 12000), (32, 12000), (32, 25000), (48, 12000)):
            eng.synth([us[0].text], mlang, [1], [G.token_cap(us[0])], p)  # warm
            t0, audio, k, outs = te._now(), 0.0, 0, []
            while k < len(us):
                B = min(bs, len(us) - k)
                while B > 1 and B * G.kv_cost(us[k + B - 1]) > budget:
                    B -= 1
                chunk = us[k:k + B]
                clips = eng.synth([u.text for u in chunk], mlang, [seed_of(u) for u in chunk], [G.token_cap(u) for u in chunk], p)
                audio += sum(len(c.wav) for c in clips) / te.SR
                outs += [c.wav for c in clips]
                k += B
            wall = te._now() - t0
            rows.append({"lang": lang, "batch": bs, "kv_budget": budget, "units": len(us), "wall_s": round(wall, 1),
                         "audio_s": round(audio, 1), "rtf": round(wall / audio, 3), "units_per_min": round(len(us) / wall * 60, 1)})
            print(rows[-1], flush=True)
            wavs_keep[lang] = outs
        del eng
        torch.cuda.empty_cache()
    for repo in ("openai/whisper-large-v3", "openai/whisper-large-v3-turbo"):
        asr = qa.Asr(G.whisper_dir(repo))
        for lang, outs in wavs_keep.items():
            posts = [qa.post_p1(w)[0] for w in outs]
            for bs in (8, 32):
                asr.transcribe(posts[:bs], "ja" if lang == "ja" else "pt")
                t0 = time.perf_counter()
                for k in range(0, len(posts), bs):
                    asr.transcribe(posts[k:k + bs], "ja" if lang == "ja" else "pt")
                wall = time.perf_counter() - t0
                rows.append({"asr": repo, "lang": lang, "batch": bs, "clips": len(posts), "wall_s": round(wall, 1),
                             "s_per_clip": round(wall / len(posts), 3)})
                print(rows[-1], flush=True)
        del asr
        torch.cuda.empty_cache()
    (G.AUDIO_ROOT / "bench_throughput.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")


def write_md(results: list, notes: str = "") -> Path:
    rows = ["| # | Setting | RTF (synth s / audio s) | vs stock | ASR+signal pass (of 30) | ja pass | pt pass | VRAM peak GiB |",
            "|---|---|---|---|---|---|---|---|"]
    base = results[0]["rtf"]
    for i, r in enumerate(results, 1):
        ja = sum(c["pass"] for c in r["clips"] if c["lang"] == "ja")
        pt = sum(c["pass"] for c in r["clips"] if c["lang"] != "ja")
        rows.append(f"| {i} | {r['name']} | {r['rtf']:.3f} | {base / r['rtf']:.1f}x | {r['pass']} | {ja}/15 | {pt}/15 | {r['vram_gib']} |")
    md = ["# Chatterbox V3 benchmark on the RX 9070 XT", "",
          f"Generated {time.strftime('%Y-%m-%d %H:%M')} by `scripts/audio/bench.py` (raw data: `bench.json`).", "",
          "30 fixed lines, same seeds for every setting: 15 Japanese N5 bank sentences synthesised from the verified "
          "token readings (kana), 15 pt-BR N5 lesson-narration sentences. RTF = wall seconds of synthesis "
          "(T3 + S3Gen + watermark, after one warm-up batch) / seconds of audio produced; lower is faster. "
          "Pass = ASR check (whisper-large-v3; ja mora_cer <= 0.05, pt WER <= 0.05) and signal checks.", "",
          *rows, "", notes]
    out = G.AUDIO_ROOT / "BENCHMARK.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    if "--throughput" in sys.argv:
        throughput()
    elif "--md" in sys.argv:
        notes = Path(sys.argv[sys.argv.index("--md") + 1]).read_text(encoding="utf-8") if len(sys.argv) > 2 else ""
        print(write_md(json.loads((G.AUDIO_ROOT / "bench.json").read_text(encoding="utf-8")), notes))
    else:
        main()
    os._exit(0)
