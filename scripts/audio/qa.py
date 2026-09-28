"""Post-processing recipe p1 and the per-clip QA of design/audio_pipeline.md §3.3 and §7 (TTS venv)."""
from __future__ import annotations

import re
import unicodedata

import numpy as np
import pyloudnorm
from scipy.signal import resample_poly

from plan import canon, morae, sudachi

SR = 24000
PAD_S = 0.150
TARGET_LUFS = -16.0
PEAK_DBTP = -1.0
# duration window (design §7) plus an absolute slack so 1-2 mora units are not failed for being
# spoken at a natural isolated-word length. Calibration knobs, not facts.
DUR_LO, DUR_HI, DUR_SLACK_LO, DUR_SLACK_HI = 0.5, 2.5, 0.3, 0.6
MAX_GAP_S = 1.2


def _speech_bounds(w: np.ndarray, top_db: float = 40.0) -> tuple[int, int]:
    import librosa
    if w.size < 512:
        return 0, w.size
    _, (s, e) = librosa.effects.trim(w, top_db=top_db, frame_length=1024, hop_length=256)
    return int(s), int(e)


def _true_peak(x: np.ndarray) -> np.ndarray:
    """Per-sample true-peak estimate (4x oversampling)."""
    up = np.abs(resample_poly(x, 4, 1))[: 4 * x.size]
    return np.pad(up, (0, 4 * x.size - up.size)).reshape(-1, 4).max(axis=1)


def _limit(x: np.ndarray, ceiling_db: float) -> np.ndarray:
    """Transparent peak limiter: gain <= ceiling/true_peak everywhere, smoothed over +/-2.5 ms.
    min-filter then box-average keeps g(t) <= need(t) at every sample, so no peak can pass."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    need = np.minimum(1.0, 10 ** (ceiling_db / 20) / np.maximum(_true_peak(x), 1e-9))
    w = 2 * int(0.0025 * SR) + 1
    return x * uniform_filter1d(minimum_filter1d(need, size=w), size=w)


def post_p1(raw: np.ndarray) -> tuple[np.ndarray, dict]:
    """p1: trim edge silence to 150 ms, loudness-normalise to -16 LUFS, true peak <= -1 dBTP, mono 24 kHz."""
    s, e = _speech_bounds(raw)
    pad = int(PAD_S * SR)
    seg = raw[max(0, s - pad): min(raw.size, e + pad)].astype(np.float64)
    lead, tail = pad - (s - max(0, s - pad)), pad - (min(raw.size, e + pad) - e)
    seg = np.concatenate([np.zeros(lead), seg, np.zeros(tail)])
    fade = int(0.005 * SR)
    if seg.size > 2 * fade:
        ramp = np.linspace(0, 1, fade)
        seg[:fade] *= ramp
        seg[-fade:] *= ramp[::-1]
    dur = seg.size / SR
    meter = pyloudnorm.Meter(SR, block_size=min(0.400, dur * 0.9))
    out = seg
    lufs = meter.integrated_loudness(out)
    for _ in range(3):  # normalise, limit the peaks the gain pushed over -1 dBTP, re-normalise
        if not np.isfinite(lufs):
            break
        out = _limit(out * 10 ** ((TARGET_LUFS - lufs) / 20), PEAK_DBTP - 0.1)
        lufs = meter.integrated_loudness(out)
        if abs(lufs - TARGET_LUFS) < 0.2:
            break
    tp = 20 * np.log10(max(_true_peak(out).max(), 1e-9))
    if tp > PEAK_DBTP:  # resampling-estimate residue: never ship above the ceiling
        out = out * 10 ** ((PEAK_DBTP - tp) / 20)
        tp = PEAK_DBTP
    final_lufs = lufs
    return out.astype(np.float32), {"speech_s": (e - s) / SR, "lufs": round(float(final_lufs), 2),
                                    "true_peak_dbtp": round(float(tp), 2), "duration_ms": int(round(dur * 1000))}


def signal_check(raw: np.ndarray, post: np.ndarray, info: dict, expected_s: float) -> list[str]:
    import librosa
    bad = []
    if raw.size == 0 or not np.isfinite(raw).all():
        return ["empty-or-nan"]
    if np.mean(np.abs(raw) >= 0.999) > 0.001:
        bad.append("clipping")
    sp = info["speech_s"]
    if not (DUR_LO * expected_s - DUR_SLACK_LO <= sp <= DUR_HI * expected_s + DUR_SLACK_HI):
        bad.append(f"duration {sp:.2f}s vs expected {expected_s:.2f}s")
    iv = librosa.effects.split(post, top_db=40, frame_length=1024, hop_length=256)
    gaps = [(b[0] - a[1]) / SR for a, b in zip(iv[:-1], iv[1:])]
    if gaps and max(gaps) > MAX_GAP_S:
        bad.append(f"internal silence {max(gaps):.2f}s")
    if np.isfinite(info["lufs"]) and abs(info["lufs"] - TARGET_LUFS) > 1.0:
        bad.append(f"loudness {info['lufs']} LUFS")
    return bad


def expected_seconds(lang: str, text: str, expected: str) -> float:
    return morae(expected) / 6.0 if lang == "ja" else len(text) / 14.0


# --- text comparison ---------------------------------------------------------------------------
def _lev(a, b) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def ja_score(asr_text: str, expected: str) -> tuple[float, str]:
    """mora_cer = edit distance / morae over canonical phonetic hiragana (design §7).
    Arabic numerals in the transcript become kanji numerals first (plan.sudachi does that), so
    Sudachi reads 100円 as ひゃくえん and 5階 as ごかい."""
    got = canon(sudachi(asr_text)[1]) if asr_text.strip() else ""
    exp = canon(expected)
    return _lev(got, exp) / max(1, morae(expected)), got


def pt_words(t: str) -> list[str]:
    t = unicodedata.normalize("NFKC", t).lower()
    t = re.sub(r"[^\w\s]", " ", t)
    return t.split()


def pt_score(asr_text: str, expected: str) -> tuple[float, str]:
    got, exp = pt_words(asr_text), pt_words(expected)
    return _lev(got, exp) / max(1, len(exp)), " ".join(got)


def passes(kind: str, lang: str, score: float) -> bool:
    if lang == "ja" and kind in ("word", "kana"):
        return score == 0.0
    return score <= 0.05


class Asr:
    """Whisper on the same ROCm torch, fp16, batched, language forced."""

    def __init__(self, model_dir: str, device: str = "cuda"):
        import torch
        from transformers import WhisperForConditionalGeneration, WhisperProcessor
        self.torch = torch
        self.proc = WhisperProcessor.from_pretrained(model_dir)
        self.model = WhisperForConditionalGeneration.from_pretrained(model_dir, torch_dtype=torch.float16).to(device).eval()
        self.device = device

    def transcribe(self, wavs: list[np.ndarray], lang: str, sr: int = SR) -> list[str]:
        torch = self.torch
        audio16 = [resample_poly(w.astype(np.float64), 2, 3).astype(np.float32) for w in wavs]
        feats = self.proc.feature_extractor(audio16, sampling_rate=16000, return_tensors="pt").input_features
        max_tok = int(max(len(w) for w in audio16) / 16000 * 12) + 24
        with torch.inference_mode():
            ids = self.model.generate(feats.to(self.device, torch.float16), language=lang, task="transcribe",
                                      max_new_tokens=min(max_tok, 440), num_beams=1, do_sample=False)
        return [t.strip() for t in self.proc.batch_decode(ids, skip_special_tokens=True)]


if __name__ == "__main__":
    assert pt_score("Olá, tudo bem?", "olá tudo bem")[0] == 0.0
    assert ja_score("今日はいい天気ですね", "きょうわいいてんきですね")[0] == 0.0
    assert ja_score("100円しかないよ", "ひゃくえんしかないよ")[0] == 0.0, ja_score("100円しかないよ", "ひゃくえんしかないよ")
    assert ja_score("5階へはエレベーターで行きなさい", "ごかいえわえれべーたーでいきなさい")[0] == 0.0
    assert passes("word", "ja", 0.0) and not passes("word", "ja", 0.1)
    t = np.sin(np.linspace(0, 2000, SR)).astype(np.float32) * 0.3
    t = np.concatenate([np.zeros(SR), t, np.zeros(SR)])
    out, info = post_p1(t)
    assert abs(info["lufs"] - TARGET_LUFS) < 0.5 and info["true_peak_dbtp"] <= PEAK_DBTP + 1e-6, info
    rng = np.random.default_rng(0)  # peaky speech-like signal: must reach -16 LUFS without passing -1 dBTP
    spiky = (rng.standard_normal(SR * 2) * 0.02 + (rng.random(SR * 2) > 0.999) * 0.9).astype(np.float32)
    _, info2 = post_p1(spiky)
    assert abs(info2["lufs"] - TARGET_LUFS) < 0.5 and info2["true_peak_dbtp"] <= PEAK_DBTP + 1e-6, info2
    assert abs(out.size / SR - (1.0 + 2 * PAD_S)) < 0.1, out.size / SR
    print("qa selfcheck ok")
