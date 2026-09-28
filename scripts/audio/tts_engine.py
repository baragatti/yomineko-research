"""Batched Chatterbox Multilingual V3 inference for the audio pipeline (runs in the TTS venv only).

Same maths as `ChatterboxMultilingualTTS.generate` (chatterbox@5de7a54a), with three changes for speed
and reproducibility:
  * T3 decodes a batch of utterances at once (left-padded prefix, attention mask, per-row positions);
    the stock loop decodes one utterance with a CPU sync on every token.
  * Sampling is Gumbel-max with a per-row torch.Generator seeded from the clip key (design §3.3), so a
    clip's tokens do not depend on which other clips share its batch.
  * S3Gen's flow decoder runs the batch together (it supports `speech_token_lens`); HiFiGAN runs per
    clip, seeded per clip.
The equivalence with the stock path is checked by `selfcheck()` (first-step logits match).
"""
from __future__ import annotations

import os
import types
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

os.environ.setdefault("HF_HUB_OFFLINE", "1")

from chatterbox.mtl_tts import Conditionals, punc_norm  # noqa: E402
from chatterbox.models.s3gen import S3GEN_SR, S3Gen  # noqa: E402
from chatterbox.models.s3tokenizer import S3_SR, S3_TOKEN_RATE, SPEECH_VOCAB_SIZE  # noqa: E402
from chatterbox.models.t3 import T3  # noqa: E402
from chatterbox.models.t3.modules.cond_enc import T3Cond  # noqa: E402
from chatterbox.models.t3.modules.t3_config import T3Config  # noqa: E402
from chatterbox.models.tokenizers import MTLTokenizer  # noqa: E402
from chatterbox.models.voice_encoder import VoiceEncoder  # noqa: E402
from safetensors.torch import load_file as load_safetensors  # noqa: E402
import librosa  # noqa: E402
import perth  # noqa: E402

SR = S3GEN_SR  # 24 kHz
SAMPLES_PER_TOKEN = S3GEN_SR // S3_TOKEN_RATE  # 960
DTYPES = {"fp32": torch.float32, "bf16": torch.bfloat16, "fp16": torch.float16}


@dataclass(frozen=True)
class SynthParams:
    exaggeration: float = 0.5
    cfg_weight: float = 0.5
    temperature: float = 0.8
    repetition_penalty: float = 1.2
    min_p: float = 0.05
    top_p: float = 1.0


@dataclass
class Clip:
    wav: np.ndarray | None  # float32 mono 24 kHz, watermarked; None when T3 hit its cap
    n_tokens: int
    overlong: bool


def load_s3gen(path) -> S3Gen:
    """s3gen_v3.pt ships without the tokenizer's mel buffers (they are rebuilt at init): allow only those."""
    m = S3Gen()
    r = m.load_state_dict(torch.load(path, weights_only=True), strict=False)
    bad = set(r.missing_keys) - set(S3Gen.ignore_state_dict_missing)
    if bad or r.unexpected_keys:
        raise RuntimeError(f"S3Gen checkpoint mismatch: missing {sorted(bad)[:5]} unexpected {r.unexpected_keys[:5]}")
    return m


def _seeded_cfm_forward(self, mu, mask, n_timesteps, temperature=1.0, spks=None, cond=None,
                        noised_mels=None, meanflow=False):
    """CausalConditionalCFM.forward with per-row noise from `self._row_seeds` (else global RNG)."""
    seeds = getattr(self, "_row_seeds", None)
    if seeds is None:
        z = torch.randn_like(mu)
    else:
        z = torch.stack([torch.randn(mu.shape[1:], generator=torch.Generator(device=mu.device).manual_seed(s),
                                     device=mu.device, dtype=mu.dtype) for s in seeds])
    t_span = torch.linspace(0, 1, n_timesteps + 1, device=mu.device, dtype=mu.dtype)
    if self.t_scheduler == "cosine":
        t_span = 1 - torch.cos(t_span * 0.5 * torch.pi)
    return self.solve_euler(z, t_span=t_span, mu=mu, mask=mask, spks=spks, cond=cond), None


class Engine:
    """One loaded model (T3 checkpoint + S3Gen) with one voice."""

    def __init__(self, *, ckpt_dir: Path, t3_file: str, s3gen_file: str, voice_path: Path,
                 t3_dtype: str = "bf16", flow_dtype: str = "fp16", hift_fp16: bool = True, static_cache: bool = False,
                 exaggeration: float = 0.5, device: str = "cuda"):
        self.device = device
        self.hift_fp16 = hift_fp16
        self.static_cache = static_cache
        self.t3_dtype = DTYPES[t3_dtype]
        self.ve = VoiceEncoder()
        self.ve.load_state_dict(torch.load(ckpt_dir / "ve.pt", weights_only=True))
        self.ve.to(device).eval()
        self.t3 = T3(T3Config.multilingual())
        state = load_safetensors(t3_file if Path(t3_file).is_absolute() else ckpt_dir / t3_file)
        if "model" in state:
            state = state["model"][0]
        self.t3.load_state_dict(state)
        self.t3.to(device).eval()
        self.s3gen = load_s3gen(s3gen_file if Path(s3gen_file).is_absolute() else ckpt_dir / s3gen_file)
        self.s3gen.to(device).eval()
        self.tokenizer = MTLTokenizer(str(ckpt_dir / "grapheme_mtl_merged_expanded_v1.json"))
        self.watermarker = perth.PerthImplicitWatermarker()
        self._prepare_voice(voice_path, exaggeration)
        self.t3.to(self.t3_dtype)
        self.cond = self.cond.to(dtype=self.t3_dtype)
        self.s3gen.flow.decoder.estimator.to(DTYPES[flow_dtype])
        dec = self.s3gen.flow.decoder
        dec.forward = types.MethodType(_seeded_cfm_forward, dec)
        hp = self.t3.hp
        self.sot, self.eot = hp.start_text_token, hp.stop_text_token
        self.sos, self.eos = hp.start_speech_token, hp.stop_speech_token
        self.max_speech_pos = hp.max_speech_tokens

    # --- voice ---------------------------------------------------------------------------------
    def _prepare_voice(self, wav_fpath: Path, exaggeration: float):
        """Mirror of ChatterboxMultilingualTTS.prepare_conditionals (fp32, before any casting)."""
        ref24, _ = librosa.load(str(wav_fpath), sr=S3GEN_SR)
        ref16 = librosa.resample(ref24, orig_sr=S3GEN_SR, target_sr=S3_SR)
        gen_ref = self.s3gen.embed_ref(ref24[: 10 * S3GEN_SR], S3GEN_SR, device=self.device)
        plen = self.t3.hp.speech_cond_prompt_len
        prompt_tokens, _ = self.s3gen.tokenizer.forward([ref16[: 6 * S3_SR]], max_len=plen)
        prompt_tokens = torch.atleast_2d(prompt_tokens).to(self.device)
        ve_embed = torch.from_numpy(self.ve.embeds_from_wavs([ref16], sample_rate=S3_SR))
        ve_embed = ve_embed.mean(axis=0, keepdim=True).to(self.device)
        self.cond = T3Cond(speaker_emb=ve_embed, cond_prompt_speech_tokens=prompt_tokens,
                           emotion_adv=exaggeration * torch.ones(1, 1, 1)).to(device=self.device)
        self.gen_ref = gen_ref
        self.exaggeration = exaggeration

    # --- T3 ------------------------------------------------------------------------------------
    def _prefix(self, text: str, lang: str, cfg_weight: float) -> torch.Tensor:
        """(2, L, D) prefix embeds exactly as T3.inference builds them (cond, text, BOS, BOS)."""
        tt = self.tokenizer.text_to_tokens(punc_norm(text), language_id=lang).to(self.device)
        tt = torch.cat([tt, tt], dim=0)
        tt = F.pad(tt, (1, 0), value=self.sot)
        tt = F.pad(tt, (0, 1), value=self.eot).long()
        bos = torch.full((2, 1), self.sos, dtype=torch.long, device=self.device)
        embeds, _ = self.t3.prepare_input_embeds(t3_cond=self.cond, text_tokens=tt, speech_tokens=bos,
                                                 cfg_weight=cfg_weight)
        bos_e = self.t3.speech_emb(bos[:1]) + self.t3.speech_pos_emb.get_fixed_embedding(0)
        return torch.cat([embeds, torch.cat([bos_e, bos_e])], dim=1)

    @torch.inference_mode()
    def t3_batch(self, texts: list[str], lang: str, seeds: list[int], caps: list[int], p: SynthParams,
                 check_every: int = 8) -> tuple[list[torch.Tensor], list[bool]]:
        """Decode B utterances together. Returns per-row speech tokens (no EOS) and overlong flags."""
        B = len(texts)
        prefixes = [self._prefix(t, lang, p.cfg_weight) for t in texts]
        L = max(x.shape[1] for x in prefixes)
        D = prefixes[0].shape[2]
        R = 2 if p.cfg_weight > 0 else 1  # cfg_weight 0 makes the uncond rows dead weight: drop them
        emb = torch.zeros(R * B, L, D, device=self.device, dtype=prefixes[0].dtype)
        mask = torch.zeros(R * B, L, dtype=torch.long, device=self.device)
        pos = torch.zeros(R * B, L, dtype=torch.long, device=self.device)
        plen = torch.zeros(R * B, dtype=torch.long, device=self.device)
        for i, x in enumerate(prefixes):
            n = x.shape[1]
            for r, row in ((i, 0), (B + i, 1))[:R]:  # rows [cond_1..cond_B, uncond_1..uncond_B]
                emb[r, L - n:] = x[row]
                mask[r, L - n:] = 1
                pos[r, L - n:] = torch.arange(n, device=self.device)
                plen[r] = n
        tfmr = self.t3.tfmr
        max_steps = min(max(caps), self.max_speech_pos)
        kw = {}
        if self.static_cache:  # preallocated KV: no per-step concatenation of the whole cache
            from transformers import StaticCache
            kw["past_key_values"] = StaticCache(config=self.t3.cfg, max_cache_len=L + max_steps + 1)
            kw["cache_position"] = torch.arange(L, device=self.device)
        out = tfmr(inputs_embeds=emb, attention_mask=mask, position_ids=pos, use_cache=True, return_dict=True, **kw)
        past = out.past_key_values
        h = out.last_hidden_state[:, -1]
        V = self.t3.speech_head.out_features
        seen = torch.zeros(B, V, dtype=torch.bool, device=self.device)
        seen[:, self.sos] = True
        gens = [torch.Generator(device=self.device).manual_seed(s) for s in seeds]
        caps_t = torch.tensor(caps, device=self.device)
        out_tok = torch.full((B, max_steps), self.eos, dtype=torch.long, device=self.device)
        done = torch.zeros(B, dtype=torch.bool, device=self.device)
        lengths = torch.full((B,), max_steps, dtype=torch.long, device=self.device)
        noise = None
        cfg = p.cfg_weight
        step_pos = plen.clone()
        for i in range(max_steps):
            if i % 64 == 0:  # per-row uniform noise for the next 64 steps (Gumbel-max sampling)
                noise = torch.stack([torch.rand(64, V, generator=g, device=self.device) for g in gens])
            logits = self.t3.speech_head(h).float()
            c = logits[:B]
            lg = c + cfg * (c - logits[B:]) if R == 2 else c
            pen = torch.where(lg < 0, lg * p.repetition_penalty, lg / p.repetition_penalty)
            lg = torch.where(seen, pen, lg)
            if p.temperature != 1.0:
                lg = lg / p.temperature
            probs = torch.softmax(lg, dim=-1)
            lg = lg.masked_fill(probs < p.min_p * probs.max(dim=-1, keepdim=True).values, float("-inf"))
            if p.top_p < 1.0:
                sl, si = torch.sort(lg, descending=False)
                cum = sl.softmax(dim=-1).cumsum(dim=-1)
                rm = cum <= (1 - p.top_p)
                rm[:, -1] = False
                lg = lg.masked_fill(rm.scatter(1, si, rm), float("-inf"))
            gumbel = -torch.log(-torch.log(noise[:, i % 64].clamp_min(1e-20)))
            nxt = torch.argmax(lg + gumbel, dim=-1)
            nxt = torch.where(done, torch.full_like(nxt, self.eos), nxt)
            out_tok[:, i] = nxt
            newly = (~done) & (nxt == self.eos)
            lengths = torch.where(newly, torch.full_like(lengths, i), lengths)
            done = done | newly | (i + 1 >= caps_t)
            seen.scatter_(1, nxt[:, None], True)
            if i % check_every == check_every - 1 and bool(done.all()):
                break
            e = self.t3.speech_emb(nxt)[:, None] + self.t3.speech_pos_emb.get_fixed_embedding(i + 1)
            if R == 2:
                e = torch.cat([e, e])
            mask = torch.cat([mask, torch.ones(R * B, 1, dtype=mask.dtype, device=self.device)], dim=1)
            if self.static_cache:
                kw["cache_position"] = torch.tensor([L + i], device=self.device)
            out = tfmr(inputs_embeds=e, attention_mask=mask, position_ids=step_pos[:, None],
                       past_key_values=past, use_cache=True, return_dict=True,
                       **({"cache_position": kw["cache_position"]} if self.static_cache else {}))
            step_pos = step_pos + 1
            past = out.past_key_values
            h = out.last_hidden_state[:, -1]
        lengths = lengths.tolist()
        toks, overlong = [], []
        for b in range(B):
            n = lengths[b]
            ov = n >= caps[b]
            t = out_tok[b, :n]
            toks.append(t[t < SPEECH_VOCAB_SIZE])
            overlong.append(ov)
        return toks, overlong

    # --- S3Gen ---------------------------------------------------------------------------------
    @torch.inference_mode()
    def s3gen_batch(self, toks: list[torch.Tensor], seeds: list[int]) -> list[np.ndarray]:
        B = len(toks)
        n = [int(t.numel()) for t in toks]
        T = max(max(n), 1)
        tok = torch.zeros(B, T, dtype=torch.long, device=self.device)
        for i, t in enumerate(toks):
            tok[i, : n[i]] = t
        lens = torch.tensor(n, device=self.device)
        dec = self.s3gen.flow.decoder
        dec._row_seeds = seeds
        try:
            mels = self.s3gen.flow_inference(tok, ref_dict=self.gen_ref, finalize=True, speech_token_lens=lens)
        finally:
            dec._row_seeds = None
        mels = mels.float()
        wavs = []
        for i in range(B):
            if n[i] == 0:
                wavs.append(np.zeros(0, dtype=np.float32))
                continue
            torch.manual_seed(seeds[i])
            with torch.autocast("cuda", dtype=torch.float16, enabled=self.hift_fp16):
                wav, _ = self.s3gen.hift_inference(mels[i : i + 1, :, : 2 * n[i]])
            wav[:, : len(self.s3gen.trim_fade)] *= self.s3gen.trim_fade
            w = wav.squeeze(0).float().cpu().numpy()
            w = w[: max(1, n[i] - 1) * SAMPLES_PER_TOKEN]  # drop the degraded last token (stock does this)
            wavs.append(w)
        return wavs

    def synth(self, texts: list[str], lang: str, seeds: list[int], caps: list[int], p: SynthParams) -> list[Clip]:
        if p.exaggeration != self.exaggeration:
            self.cond = T3Cond(speaker_emb=self.cond.speaker_emb,
                               cond_prompt_speech_tokens=self.cond.cond_prompt_speech_tokens,
                               emotion_adv=p.exaggeration * torch.ones(1, 1, 1)).to(device=self.device,
                                                                                    dtype=self.t3_dtype)
            self.exaggeration = p.exaggeration
        t0 = _now()
        toks, overlong = self.t3_batch(texts, lang, seeds, caps, p)
        t1 = _now()
        wavs = self.s3gen_batch(toks, seeds)
        self.last_timing = {"t3_s": t1 - t0, "s3gen_s": _now() - t1, "steps": max((int(t.numel()) for t in toks), default=0)}
        clips = []
        for w, t, ov in zip(wavs, toks, overlong):
            wm = self.watermarker.apply_watermark(w, sample_rate=SR) if w.size else w
            clips.append(Clip(wav=np.asarray(wm, dtype=np.float32), n_tokens=int(t.numel()), overlong=ov))
        return clips


def _now() -> float:
    torch.cuda.synchronize()
    import time
    return time.perf_counter()


def selfcheck(engine: Engine, text: str = "きょうはいいてんきですね", lang: str = "ja") -> float:
    """Max abs diff between our batched first-step logits (B=2, padded) and the stock T3 backend."""
    with torch.inference_mode():
        x = engine._prefix(text, lang, 0.5)
        stock = engine.t3.tfmr(inputs_embeds=x, use_cache=False, return_dict=True).last_hidden_state[:, -1]
        stock = engine.t3.speech_head(stock).float()
        other = engine._prefix(text + "わたしはがくせいです", lang, 0.5)
        L = other.shape[1]
        emb = torch.zeros(4, L, x.shape[2], device=engine.device, dtype=x.dtype)
        mask = torch.zeros(4, L, dtype=torch.long, device=engine.device)
        pos = torch.zeros(4, L, dtype=torch.long, device=engine.device)
        for r, (src, row) in enumerate(((x, 0), (other, 0), (x, 1), (other, 1))):
            n = src.shape[1]
            emb[r, L - n:] = src[row]
            mask[r, L - n:] = 1
            pos[r, L - n:] = torch.arange(n, device=engine.device)
        h = engine.t3.tfmr(inputs_embeds=emb, attention_mask=mask, position_ids=pos, use_cache=False,
                           return_dict=True).last_hidden_state[:, -1]
        ours = engine.t3.speech_head(h).float()[[0, 2]]
        return float((ours - stock).abs().max())
