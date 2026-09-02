#!/usr/bin/env python3
"""Generate the Phase-2 vocab patch from the CONFIRMED findings (reports/fable5_validation.md Phase 2).
Converts phase2_vocab_confirmed_apply.json (115 free-text fixes) into explicit machine-applicable edits:
full new senses arrays (+ romaji) per touched vocab -> phase2_vocab_patch.json, printing every
before->after diff for human review. AUTO ops: remove-sense, single-item replace, whole-list replace,
romaji. MANUAL dict resolves the 13 prose-y fixes (replace-sense with pos change, insert-sense, etc.).
vocab:1385390 (接見 level/relink defect) is EXCLUDED - handled separately, it is not a gloss edit.
Anchors every op against the DB's current value; any mismatch is a hard error (stale index protection).
Usage: fable5_vocab_patch_gen.py"""
from __future__ import annotations
import json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
FD = ROOT / "research" / "derived" / "fable5_validation"
REMOVE_ANY = re.compile(r"^\(?\s*(remove|delete)\b", re.I)   # any removal phrasing
REMOVE_SENSE = re.compile(r"^\(remove\s+—|sense", re.I)      # whole-SENSE removal (vs one gloss)
META = re.compile(r'remove|remover|drop |keep |gloss|array|element|pt: \[|en: \[|\["', re.I)
EXCLUDE = {"vocab:1385390"}  # level/relink defect, not a gloss edit

# ---- MANUAL ops for prose-y fixes (op sequence per slug; indexes are ORIGINAL sense_order) ----
M = {
    "vocab:2846738": [{"t": "replace_sense", "i": 1, "pos": ["pref"],
                       "en": ["how many (before a counter, e.g. 何人, 何時)", "how much"],
                       "pt": ["quantos/quantas (antes de um contador)", "quanto"]}],
    "vocab:1451160": [{"t": "set_pt", "i": 0, "v": ["movimento"]}],
    "vocab:1415000": [{"t": "set_pos", "i": 1, "v": ["adj-na"]}],
    "vocab:1277450": [{"t": "set_pt", "i": 0, "v": ["gostar de", "preferido"]}],
    "vocab:1206900": [{"t": "set_en", "i": 0, "v": ["student", "pupil"]}],
    "vocab:1577985": [{"t": "set_en", "i": 0, "v": ["to be (animate; humble/courteous form of いる)", "to exist", "to stay"]},
                      {"t": "set_pt", "i": 0, "v": ["estar (forma humilde/cortês de いる)", "ficar", "existir"]},
                      {"t": "set_misc", "i": 0, "v": ["hum"]}],
    "vocab:1612690": [{"t": "set_en", "i": 0, "v": ["there is", "to be (polite)", "exists (polite)"]}],
    "vocab:1432850": [{"t": "replace_sense", "i": 1, "pos": None,
                       "en": ["to circulate (of blood)", "to be conveyed (of feelings)"],
                       "pt": ["circular (o sangue)", "ser transmitido (sentimentos)"]}],
    "vocab:1006380": [{"t": "set_pt", "i": 2, "v": ["bem longe", "lá longe"]}],
    "vocab:1166510": [{"t": "set_en", "i": 2, "v": ["just keeps (doing/getting)", "only continues to", "increasingly (in one direction)"]}],
    "vocab:1165790": [{"t": "set_pt", "i": 0, "v": ["geral", "comum", "normal"]}],
    "vocab:1509350": [{"t": "replace_sense", "i": 1, "pos": None,
                       "en": ["kink", "crease", "curl"], "pt": ["cacho", "dobra", "vinco"]}],
    "vocab:1223010": [{"t": "insert_sense", "i": 0, "pos": ["n"],
                       "en": ["regulation", "control", "restriction"],
                       "pt": ["regulamentação", "controle", "restrição"]},
                      {"t": "set_pos", "i": 0, "v": ["vs", "vt"]}],  # old verb sense keeps only verb pos
    # --- wrong-lexeme senses where the verifier's replacement was pt-only: EN mirror authored here ---
    "vocab:1610400": [{"t": "replace_sense", "i": 1, "pos": None,  # 点ける carried 付ける's diary sense
                       "en": ["to light (a candle, cigarette)", "to set fire to"],
                       "pt": ["acender (vela, cigarro)", "atear fogo em"]}],
    "vocab:1597040": [{"t": "replace_sense", "i": 2, "pos": None,  # 立つ carried 経つ's time sense
                       "en": ["to depart (on a journey)", "to leave"],
                       "pt": ["partir (de viagem)", "sair"]}],
    "vocab:1586270": [{"t": "replace_sense", "i": 1, "pos": None,  # 開く(あく) carried ひらく's event sense
                       "en": ["to open (of a shop, business)"],
                       "pt": ["abrir (loja, estabelecimento)"]}],
    "vocab:1588320": [{"t": "replace_sense", "i": 1, "pos": None,  # 写す carried 映す + 移す senses
                       "en": ["to describe", "to portray"],
                       "pt": ["descrever", "retratar"]},
                      {"t": "remove_sense", "i": 2}],
    "vocab:1198920": [{"t": "replace_sense", "i": 1, "pos": None,  # ほどける carried とける's problem sense
                       "en": ["to be cleared up (of tension, a misunderstanding)", "to dissolve"],
                       "pt": ["dissipar-se", "desfazer-se (mal-entendido, tensão)"]}],
    # --- audit round 2: gloss-level removes ("Remove 'X'; keep Y") + pasted/pt-only fixes ---
    "vocab:1000420": [{"t": "set_pt", "i": 0, "v": ["aquele", "aquela"]}],  # あの is adnominal; drop 'aquilo'
    "vocab:1266970": [{"t": "set_en", "i": 0, "v": ["door (especially sliding)"]},  # gate/portão = 門
                      {"t": "set_pt", "i": 0, "v": ["porta (de correr)"]}],
    "vocab:1498040": [{"t": "set_pt", "i": 0, "v": ["carregar nas costas (esp. uma criança)",
                                                    "cavalinho (carregar nas costas)"]}],
    "vocab:1291330": [{"t": "replace_sense", "i": 1, "pos": None,  # 差す carried 刺す's sting sense
                       "en": ["to shine (of the sun, light)"], "pt": ["brilhar (sol, luz)"]}],
    "vocab:1301940": [{"t": "set_en", "i": 0, "v": ["umbrella", "parasol"]}],
    "vocab:1369940": [{"t": "replace_sense", "i": 1, "pos": None,  # 尋ねる carried 訪ねる's visit sense
                       "en": ["to search for", "to look for"], "pt": ["procurar", "buscar"]}],
    "vocab:1379640": [{"t": "replace_sense", "i": 1, "pos": None,  # さかり; s1 pt still had もり's meaning
                       "en": ["rutting", "being in heat (of animals)", "mating season"],
                       "pt": ["cio (de animais)", "época de acasalamento"]}],
    "vocab:1483090": [{"t": "set_pt", "i": 0, "v": ["eles"]}],
    "vocab:1601990": [{"t": "set_pt", "i": 0, "v": ["por enquanto", "por ora"]}],
    "vocab:1611000": [{"t": "replace_sense", "i": 0, "pos": None,  # 生る carried 成る's become sense
                       "en": ["to bear fruit"], "pt": ["dar fruto", "frutificar"]}],
    "vocab:2020680": [{"t": "set_pt", "i": 0, "v": ["hora (sufixo)",
                                                    "...horas (ao indicar o horário: 3時 = três horas)"]}],
    # --- verifier fixes were pt-only text: full sense authored by hand (en + pt) ---
    "vocab:1000580": [{"t": "replace_sense", "i": 0, "pos": None,  # 彼(あれ) carried かれ's he/boyfriend
                       "en": ["that person (distant from both speaker and listener)", "that"],
                       "pt": ["aquela pessoa", "aquele (pessoa distante de ambos)"]},
                      {"t": "remove_sense", "i": 1}],
    "vocab:1472630": [{"t": "replace_sense", "i": 0, "pos": None,  # さかずき = sake cup, not generic cup
                       "en": ["sake cup", "small cup for alcoholic drinks"],
                       "pt": ["cálice de saquê", "taça para bebidas alcoólicas"]}],
    "vocab:1551240": [{"t": "replace_sense", "i": 0, "pos": None,  # 立ち carried 達's plural suffix
                       "en": ["departure", "setting off", "start"],
                       "pt": ["partida", "saída", "início"]}],
    # --- format-artifact anchors resolved by hand ---
    "vocab:1390980": [{"t": "set_pt", "i": 0, "v": ["lavar roupa", "lavagem de roupa"]}],
    "vocab:1582300": [{"t": "set_pt", "i": 1, "v": ["(depreciativo) alguém/algo como", "um mero"]}],
    "vocab:1340000": [{"t": "set_en", "i": 0, "v": ["departure", "to depart", "to leave"]},
                      {"t": "set_pt", "i": 0, "v": ["partida", "partir", "sair"]}],
    "vocab:1408810": [{"t": "set_item", "f": "en", "i": 1, "k": 0,
                       "old": "to strike (a clock the hour)", "v": "to strike (the hour; of a clock)"}],
    "vocab:1586265": [{"t": "set_en", "i": 0, "v": ["to be empty", "to be uncrowded"]},  # vacant = あく
                      {"t": "set_pt", "i": 0, "v": ["estar vazio", "estar com pouca gente"]}],
    "vocab:1048830": [{"t": "set_item", "f": "pt", "i": 1, "k": 1,
                       "old": "cardapio fixo (refeicao servida em etapas)",
                       "v": "cardápio fixo (refeição servida em etapas)"}],
    "vocab:1074330": [{"t": "set_pt", "i": 0, "v": ["liquidação", "promoção", "queima de estoque"]}],
}


def split_glosses(fix: str) -> list[str]:
    """Paren-aware split on ';' or ',' at depth 0 — one gloss per element; separators inside parens survive."""
    out, depth, cur = [], 0, ""
    for ch in fix:
        if ch in "(（":
            depth += 1
        elif ch in ")）":
            depth -= 1
        if ch in ",;" and depth == 0:
            out.append(cur.strip()); cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def main() -> int:
    conf = json.loads((FD / "phase2_vocab_confirmed_apply.json").read_text(encoding="utf-8"))
    con = sqlite3.connect(DB)
    errors: list[str] = []
    # current DB state per slug
    by_slug: dict[str, list] = {}
    vinfo: dict[str, tuple] = {}
    for f in conf:
        s = f["slug"]
        if s in by_slug or s in EXCLUDE:
            continue
        row = con.execute("SELECT id, headword, kana, romaji FROM vocab WHERE slug=?", (s,)).fetchone()
        if not row:
            errors.append(f"{s}: not in DB"); continue
        vinfo[s] = row
        by_slug[s] = [dict(zip(("so", "pos", "field", "misc", "en", "pt"), r)) for r in con.execute(
            "SELECT sense_order,pos,field_tags,misc_tags,gloss_en,gloss_pt FROM vocab_sense "
            "WHERE vocab_id=? ORDER BY sense_order", (row[0],))]

    # build op lists
    ops: dict[str, list] = {s: list(M.get(s, [])) for s in by_slug}
    handled_manual = set(M)
    for f in conf:
        s, fld, fix, cur = f["slug"], f["field"], f["fix"].strip(), f.get("current", "")
        if s in EXCLUDE or s in handled_manual:
            continue
        if fld == "romaji":
            v = re.sub(r"^romaji:\s*", "", fix).strip().strip('"')
            ops[s].append({"t": "romaji", "old": cur, "v": v}); continue
        m_item = re.match(r"^senses\[(\d+)\]\.(en|pt)\[(\d+)\]$", fld)
        m_list = re.match(r"^senses\[(\d+)\]\.(en|pt)$", fld)
        if REMOVE_ANY.match(fix):
            if not REMOVE_SENSE.search(fix[:60]):
                errors.append(f"{s}: gloss-level remove needs a MANUAL op: {fix[:60]!r}"); continue
            i = int((m_item or m_list).group(1))
            ops[s].append({"t": "remove_sense", "i": i})
        elif m_item:
            ops[s].append({"t": "set_item", "f": m_item.group(2), "i": int(m_item.group(1)),
                           "k": int(m_item.group(3)), "old": cur, "v": fix})
        elif m_list:
            ops[s].append({"t": f"set_{m_list.group(2)}", "i": int(m_list.group(1)),
                           "old": cur, "v": split_glosses(fix)})
        else:
            errors.append(f"{s}: unhandled field {fld}")

    # mirror fix for 通 pt 'telefonemas' (confirmed issue names the pt mirror explicitly)
    if "vocab:1432840" in by_slug:
        ops["vocab:1432840"].append({"t": "set_pt", "i": 2, "v": ["contador para cartas e documentos"]})

    # apply ops -> new senses arrays
    patch: dict[str, dict] = {}
    for s, sl in by_slug.items():
        senses = [{"pos": json.loads(x["pos"]), "field": json.loads(x["field"] or "[]"),
                   "misc": json.loads(x["misc"] or "[]"),
                   "en": json.loads(x["en"]), "pt": json.loads(x["pt"])} for x in sl]
        removed: set[int] = set()
        inserts: list = []
        romaji = None
        for op in ops[s]:
            t = op["t"]
            if t == "remove_sense":
                if op["i"] >= len(senses):
                    errors.append(f"{s}: remove index {op['i']} out of range"); continue
                removed.add(op["i"])
            elif t == "romaji":
                if vinfo[s][3] != op["old"]:
                    errors.append(f"{s}: romaji anchor mismatch ({vinfo[s][3]!r} != {op['old']!r})")
                romaji = op["v"]
            elif t == "set_item":
                lst = senses[op["i"]][op["f"]]
                if op["k"] >= len(lst) or (op["old"] is not None and lst[op["k"]] != op["old"]):
                    errors.append(f"{s}: item anchor mismatch at senses[{op['i']}].{op['f']}[{op['k']}] "
                                  f"(db={lst[op['k'] if op['k'] < len(lst) else -1]!r} vs {op['old']!r})")
                    continue
                lst[op["k"]] = op["v"]
            elif t in ("set_en", "set_pt"):
                fldk = t[4:]
                if "old" in op and op["old"] and ", ".join(senses[op["i"]][fldk]) != op["old"]:
                    errors.append(f"{s}: list anchor mismatch at senses[{op['i']}].{fldk} "
                                  f"(db={', '.join(senses[op['i']][fldk])!r} vs {op['old']!r})")
                    continue
                senses[op["i"]][fldk] = op["v"]
            elif t == "set_pos":
                senses[op["i"]]["pos"] = op["v"]
            elif t == "set_misc":
                senses[op["i"]]["misc"] = op["v"]
            elif t == "replace_sense":
                sn = senses[op["i"]]
                sn["en"], sn["pt"] = op["en"], op["pt"]
                if op.get("pos"):
                    sn["pos"] = op["pos"]
            elif t == "insert_sense":
                inserts.append(op)
        new = [x for i, x in enumerate(senses) if i not in removed]
        for op in sorted(inserts, key=lambda o: o["i"]):
            new.insert(op["i"], {"pos": op["pos"], "field": [], "misc": [], "en": op["en"], "pt": op["pt"]})
        # normalize: one gloss per element (split on commas outside parens), then guard rails
        for x in new:
            for fk in ("en", "pt"):
                x[fk] = [g2 for g in x[fk] for g2 in split_glosses(g)] if any(
                    re.search(r"[,;]", re.sub(r"\([^)]*\)", "", g)) for g in x[fk]) else x[fk]
        if not new:
            errors.append(f"{s}: patch would leave ZERO senses")
        for x in new:
            for fk in ("en", "pt"):
                if not x[fk] or any(not g.strip() for g in x[fk]):
                    errors.append(f"{s}: empty gloss in {fk}")
                for g in x[fk]:
                    if META.search(g) or len(g) > 90:
                        errors.append(f"{s}: meta/pasted text in {fk} gloss: {g[:60]!r}")
        entry: dict = {"senses": new}
        if romaji:
            entry["romaji"] = romaji
        patch[s] = entry

    if errors:
        print("ERRORS — patch NOT written:")
        for e in errors:
            print(" ", e)
        return 1

    # review printout: full before -> after
    for s, entry in sorted(patch.items()):
        _, hw, kana, rom = vinfo[s]
        old = by_slug[s]
        print(f"\n===== {s} {hw}({kana}) =====")
        if "romaji" in entry:
            print(f"  romaji: {rom} -> {entry['romaji']}")
        for i, x in enumerate(old):
            print(f"  OLD s[{i}] pos={x['pos']} en={x['en']} pt={x['pt']}")
        for i, x in enumerate(entry["senses"]):
            print(f"  NEW s[{i}] pos={json.dumps(x['pos'])} misc={json.dumps(x['misc'])} "
                  f"en={json.dumps(x['en'], ensure_ascii=False)} pt={json.dumps(x['pt'], ensure_ascii=False)}")

    out = FD / "phase2_vocab_patch.json"
    out.write_text(json.dumps({"patch": patch}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\npatch written: {out} ({len(patch)} vocab)")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
