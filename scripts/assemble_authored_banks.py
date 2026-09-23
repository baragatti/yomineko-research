#!/usr/bin/env python3
"""W18b assembly of the authored paraphrase / usage items. Deterministic, files only (never db/, corpus/, course/, git state).
Per (take, id) the verdict bound to that take (meta sha256 > `file` field > id cover): a reject or no verdict excludes, else the
strongest `corrected` wins. Level re-check on the COMMITTED tree (W17 patch applied to a scratch copy). Per vid the pp/us takes
sharing one sentence win (one journal row emits both), primary first; then per (family, level) up to the work file's deficit."""
import hashlib, io, json, os, re, subprocess, sys, tarfile, tempfile; sys.stdout.reconfigure(encoding="utf-8")  # noqa: E401,E702
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC, PATCH = ROOT / "research/derived/pending/authored_banks", ROOT / "research/derived/patches/w17_builder.patch"
OUT, REPORT = SRC.parent / "authored_banks_final.json", ROOT / "research/reports/w18b_authored_assembly.md"
TAKES = ("primary", "alt_batchC")  # _MANIFEST: an alternate row only replaces a primary that did not survive
FAM, TAIL = {"pp": "paraphrase", "us": "usage"}, ("vocab", "vocab_id", "sentence", "layer", "needs_review", "ai_generated")
SHAPE = {"paraphrase": ("id", "level", "stem", "target", "correct", "distractors", *TAIL, "source"),  # the builder's order
         "usage": ("id", "level", "target", "correct", "wrong", *TAIL, "source")}
SOURCE = {"paraphrase": "authored+verified", "usage": "authored+verified(real-correct)"}
fk = lambda i: f"{FAM[i[:2]]}:{i.split(':')[1]}"  # noqa: E731   "pp:n4:852" -> "paraphrase:n4"
sh = lambda *cmd, cwd=ROOT, **kw: subprocess.run(cmd, cwd=cwd, capture_output=True, check=True, **kw).stdout  # noqa: E731
fingerprint = lambda r: hashlib.sha256(json.dumps({k: r[k] for k in ("correct", "id", "target", "wrong")},  # noqa: E731
                                                  ensure_ascii=False).encode()).hexdigest()[:16]  # authored-4 meta's scheme
rank = lambda c: (not c["twin_ok"], c["row"]["ai_generated"], -sum(o.get("generated") is False  # noqa: E731
                  for o in c["row"]["provenance"]["options"]), c["status"] != "ok", c["take"] != TAKES[0], c["row"]["id"])

def judge(rows: dict, verdicts: list) -> tuple[dict, list]:  # verdicts [(name, take, {id: entry})], strongest first
    surv, excl = {}, []
    for (take, iid), row in sorted(rows.items(), key=lambda kv: (TAKES.index(kv[0][0]), kv[0][1])):
        vs = [(n, v[iid]) for n, t, v in verdicts if t == take and iid in v]
        bad = [f"rejected by {n}: {(e.get('problem') or e.get('reason') or '')[:220]}" for n, e in vs
               if not (e.get("ok") is True or e.get("verdict") == "pass" or e.get("corrected"))]
        fix = [(n, e["corrected"]) for n, e in vs if e.get("corrected")] or [("", row)]
        assert all(c["id"] == iid for _, c in fix), iid
        if not vs or bad:
            excl.append({"id": iid, "take": take, "reason": bad[0] if bad else "no verdict for this take"})
        else:
            surv.setdefault(iid, []).append({"take": take, "row": fix[0][1], "status": fix[0][0] and f"corrected by {fix[0][0]}" or "ok"})
    return surv, excl

def pair(surv: dict) -> dict:
    chosen = {}
    for lvl, vid in sorted({(i.split(":")[1], int(i.split(":")[2])) for i in surv}):
        P, U = surv.get(f"pp:{lvl}:{vid}", []), surv.get(f"us:{lvl}:{vid}", [])
        both = [(p, u) for p in P for u in U if p["row"]["sentence"] == u["row"]["sentence"]]
        for c, twin in ([(both[0][0], True), (both[0][1], True)] if both else [(x[0], False) for x in (P, U) if x]):
            chosen[c["row"]["id"]] = {**c, "twin_ok": twin}
    return chosen

def selfcheck() -> None:
    r = lambda i, s: {"id": i, "sentence": s, "correct": s}  # noqa: E731
    surv, excl = judge({("primary", "pp:n5:1"): r("pp:n5:1", "a"), ("alt_batchC", "pp:n5:1"): r("pp:n5:1", "b"),
                        ("primary", "us:n5:1"): r("us:n5:1", "b"), ("primary", "pp:n5:2"): r("pp:n5:2", "c")},
                       [("v1", "primary", {"pp:n5:1": {"ok": True}, "us:n5:1": {"corrected": r("us:n5:1", "b")}}),
                        ("v2", "alt_batchC", {"pp:n5:1": {"ok": True}, "pp:n5:2": {"ok": True}})])
    assert (ch := pair(surv))["pp:n5:1"]["take"] == "alt_batchC" and ch["pp:n5:1"]["twin_ok"], "pair follows the shared sentence"
    assert ch["us:n5:1"]["status"] == "corrected by v1" and "pp:n5:2" not in ch, "corrected applies; no verdict, no row"
    assert [e["reason"] for e in excl] == ["no verdict for this take"], "a missing verdict must exclude, never pass"

def why_not(r: dict, lvl: str, er, ts, bank: dict) -> str:  # validate_exam_level_gate's rule, via the patch's TaughtSets
    s, key = bank.get(r["sentence"]), r.get("stem", r["correct"])
    if s is None or s["jp"] != key:
        return f"{r['sentence']} is missing from the committed bank or not byte-equal to the stem"
    shown = [key, r["target"], r["correct"], *r.get("distractors", []), *r.get("wrong", [])]
    why = [f"kanji {c}" for c in sorted(set().union(*map(er.kanji_of, shown)) - ts.kanji_chars[lvl])]
    why += [f"vocab {x}" for x in sorted({r["vocab"], *(t["vocab"] for t in s["tokens"] if t.get("vocab"))})
            if not ts.vocab_ok(x, lvl)]
    return "; ".join(why + [f"grammar {g}" for g in s.get("grammar") or [] if not ts.grammar_ok(g, lvl)])

def main() -> None:
    selfcheck()
    need = {f"{j['family']}:{j['level']}": j["need"]["deficit_to_floor"] for j in map(json.loads, map(Path.read_bytes, SRC.glob("work*")))}
    rows, files, file_of, bound = {}, {}, {}, []
    for p in sorted(x for x in SRC.rglob("authored-*.json") if ".verdict" not in x.name):
        raw, take, rel = p.read_bytes(), TAKES[p.parent.name == "alt_batchC"], p.relative_to(SRC).as_posix()
        for r in json.loads(raw)["rows"]:
            assert (take, r["id"]) not in rows, f"{r['id']} twice inside the {take} take"
            rows[(take, r["id"])], file_of[(take, r["id"])] = r, rel
        files[rel] = {"take": take, "sha256": hashlib.sha256(raw).hexdigest(), "rows": list(file_of.values()).count(rel)}
    for p in sorted(SRC.glob("authored-*.verdict.json")):
        j, meta = json.loads(p.read_bytes()), p.with_name(p.name[:-5] + ".meta.json")
        v = {e["id"]: e for e in v} if isinstance(v := j.get("verdicts", j), list) else v  # flat map, or {verdicts: map|list}
        if meta.exists():  # strongest: the sha256 of the exact take the verifier read (StopIteration if that take is gone)
            m = json.loads(meta.read_bytes())
            f, fps = next(f for f, x in files.items() if x["sha256"] == m["adjudicated_sha256"]), m.get("row_fingerprints", {})
            assert all(fingerprint(rows[(files[f]["take"], i)]) == h for i, h in fps.items()), "take edited after its verdict"
            how, strength = f"meta sha256 {m['adjudicated_sha256'][:12]} = `{f}`; {len(fps)} row fingerprints match", 0
        elif "file" in j:
            f, how, strength = next(f for f in files if f.split("/")[-1] == j["file"]), f"`file` field = `{j['file']}`", 1
        else:
            cover = [t for t in TAKES if set(v) <= {i for tk, i in rows if tk == t}]
            assert len(cover) == 1, f"{p.name}: cannot tell which take it adjudicated ({cover})"
            f, how, strength = next(f for f in files if files[f]["take"] == cover[0]), "the only take covering its ids", 2
        ok, fx = (sum(map(t, v.values())) for t in (lambda e: e.get("ok") is True, lambda e: bool(e.get("corrected"))))
        bound.append((strength, len(v), p.name, files[f]["take"], v, how, ok, fx))
    bound.sort(key=lambda b: b[:3])  # strongest evidence first, then a dedicated verdict before a sweep
    surv, excl = judge(rows, [(b[2], b[3], b[4]) for b in bound])
    head = sh("git", "rev-parse", "HEAD", text=True).strip()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:  # HEAD in scratch; the W17 patch applied THERE only
        tmp, tar = Path(td) / "tree", io.BytesIO(sh("git", "archive", head, "scripts", "course", "corpus/sentences"))
        tarfile.open(fileobj=tar).extractall(tmp, filter="data")
        sh("git", "apply", "-p1", str(PATCH), cwd=tmp, env={**os.environ, "GIT_CEILING_DIRECTORIES": td})  # no repo; never climb
        sys.path.insert(0, str(tmp / "scripts" / "export"))
        import exam_rules as er  # the patch's module, imported from the scratch copy
        ts, bank = er.TaughtSets(tmp), {s["slug"]: s for s in json.loads((tmp / "corpus/sentences/bank.json").read_bytes())}
    for i, cands in surv.items():
        whys = [why_not(c["row"], i.split(":")[1], er, ts, bank) for c in cands]
        excl += [{"id": i, "take": c["take"], "reason": f"re-check at {head[:8]}: {w}"} for c, w in zip(cands, whys) if w]
        surv[i] = [{**c, "row": {**c["row"], "ai_generated": bank[c["row"]["sentence"]]["provenance"].get("ai_generated") is True}}
                   for c, w in zip(cands, whys) if not w]  # the builder copies ai_generated from the stem sentence
    chosen = pair({i: c for i, c in surv.items() if c})
    excl += [{"id": i, "take": c["take"], "reason": f"superseded: the {chosen[i]['take']} take was used for this id"}
             for i, cs in surv.items() for c in cs if i in chosen and c["take"] != chosen[i]["take"]]
    selected, picked, rows_out, extras = {}, {}, [], {}
    for key in sorted(set(need) | {fk(i) for i in chosen}):
        pool, n = sorted((c for i, c in chosen.items() if fk(i) == key), key=rank), need.get(key, 0)
        selected[key] = {"need": n, "selected": [c["row"]["id"] for c in pool[:n]], "surplus": [c["row"]["id"] for c in pool[n:]]}
        picked |= {c["row"]["id"]: "selected" for c in pool[:n]}
    twin = lambda i: ("us" if i[:2] == "pp" else "pp") + i[2:]  # noqa: E731   a selected vid's other half rides along
    picked |= {twin(i): "twin (same journal row)" for i in list(picked) if chosen[i]["twin_ok"] and twin(i) not in picked}
    for i in sorted(picked, key=lambda i: (fk(i), rank(chosen[i]))):
        c, fam, ex = chosen[i], FAM[i[:2]], chosen[i]["row"].get("explanation")
        rows_out.append({k: c["row"][k] for k in SHAPE[fam]} | {"layer": "C", "needs_review": True, "source": SOURCE[fam]})
        extras[i] = {"role": picked[i], "take": c["take"], "file": file_of[(c["take"], i)], "status": c["status"],
                     "explanation": ex.get("pt-BR") if isinstance(ex, dict) else ex, "provenance": c["row"]["provenance"]}
    cat, n_sel = (lambda e: re.split(r" by | at |:", e["reason"])[0]), list(picked.values()).count("selected")
    counts = {"authored_rows": len(rows), "distinct_ids": len({i for _, i in rows}), "verdict_files": len(bound),
              "excluded": {k: sum(cat(e) == k for e in excl) for k in sorted({cat(e) for e in excl})}, "surviving_ids": len(chosen),
              "selected": n_sel, "twins": len(picked) - n_sel, "explanation_names_option_position":
              sorted(i for i, x in extras.items() if re.search("primeira|segunda|terceira", x["explanation"] or ""))}
    out = {"stage": "W18b assembly (pending; nothing applied)", "committed_tree": head, "counts": counts, "needed": need,
           "selected": selected, "rows": rows_out, "extras": extras, "excluded": sorted(excl, key=lambda e: (e["id"], e["take"]))}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print("every need met:", met := all(len(s["selected"]) == s["need"] for s in selected.values()), json.dumps(counts["excluded"]))
    md = [f"# W18b: authored paraphrase / usage assembly\n\nBy `scripts/assemble_authored_banks.py` on committed tree `{head[:12]}`"
          " (W17 patch applied to a scratch copy). Output: `research/derived/pending/authored_banks_final.json`.\n",
          "## Inventory\n\n| authored file | take | rows | sha256 |\n|---|---|---:|---|",
          *[f"| `{f}` | {x['take']} | {x['rows']} | `{x['sha256'][:12]}` |" for f, x in files.items()],
          "\n| verdict file | adjudicated take | bound by | ids | ok | corrected | rejected |\n|---|---|---|---:|---:|---:|---:|",
          *[f"| `{b[2]}` | {b[3]} | {b[5]} | {b[1]} | {b[6]} | {b[7]} | {b[1] - b[6] - b[7]} |" for b in bound],
          "\n## Counts\n\n```json", json.dumps(counts, indent=1),
          "```\n\n| family:level | need | available | selected |\n|---|---:|---:|---:|",
          *[f"| {k} | {s['need']} | {len(s['selected']) + len(s['surplus'])} | {len(s['selected'])} |" for k, s in selected.items()],
          f"\nEvery need met: **{'yes' if met else 'NO'}**.\n\n## Twelve selected items (authored option order: key is A)\n"]
    for i in [i for s in selected.values() if s["need"] for i in s["selected"][:4]]:  # 3 needed family-levels x 4 = 12
        r, x = chosen[i]["row"], extras[i]
        opts = " / ".join(f"{'ABCD'[n]}) {o}" for n, o in enumerate([r["correct"], *r.get("distractors", r.get("wrong", []))]))
        md.append(f"**{i}** ({x['take']}, {x['status']})  \nstem: {r.get('stem') or '(usage item)'} (target {r['target']})"
                  f"  \noptions: {opts}  \nkey: A  \nexplanation: {x['explanation']}\n")
    REPORT.write_text("\n".join(md) + "\n", "utf-8")

if __name__ == "__main__":
    main()
