#!/usr/bin/env python3
"""Generate one JSON Schema per entity from the measured shapes, wired to the shared patterns.

Why generate rather than hand-write: twenty-three entities with 500+ field paths between them cannot
be hand-maintained against a corpus that is still being built, and a schema that has drifted from the
data is worse than none — it teaches you to ignore the gate. So the field inventory comes from
contracts/_shapes.json (what the data actually is) and the SEMANTICS come from the tables below (what
a field means, which is a judgement no measurement can make).

WHAT MAY BE MEASURED, AND WHAT MAY NOT
--------------------------------------
The 2026-08-26 contract audit found the first version of this generator had turned every small value
set it happened to see into an `enum`, which made the contract a photograph of that day's corpus:
`generated` was pinned to the export date, `strokes` to the stroke counts already drawn, `spans_levels`
to n4/n5, `locale` to pt-BR. 44 of 45 legitimate-future probes failed. The rule that came out of it:

  * MEASURE what is monotone-safe. `required` (a field on 100% of records) can only ever be broken by
    DELETING a field, which is exactly the drift a contract should catch. Types, nesting and array-ness
    are the same. Keep measuring these.
  * NEVER MEASURE a vocabulary. An `enum` is broken by ADDING a value, so a measured enum fails on the
    first legitimate new record and the documented remedy — regenerate — simply re-measures whatever the
    data now says. It can therefore never catch the drift it was built to catch (the "regeneration
    tautology"). A vocabulary must come from somewhere a human had to change on purpose:
      - DESIGN-OWNED   — design/unlock_enums.json, design/lesson_schema.md, design/schema_v2.md, …
                         The document is the authority and the DATA is what gets checked against it.
      - PRODUCER-OWNED — parsed out of the code that emits the value (dissect.py's POS_MAP, …), so the
                         contract can never be narrower than the pipeline feeding it.
      - CURATED        — a genuinely closed set that no document owns, written out here with its source
                         cited, so widening it is a visible edit to this file rather than a re-run.
    Anything with no such source is a plain `string`. A field with no declared vocabulary is honest;
    a field with a measured one is a trap.
  * Integers and booleans are never a vocabulary at all. A count, an ordinal and a stroke number are
    quantities; infer_shapes.py no longer even collects their value sets.

`required` is still measured: a field on 100% of records is required, one on 97% is not.
`$ref: common#/$defs/StableId` is decided: `slug` is the public address on a registry, and no amount
of counting reveals that.

`additionalProperties: false` is set only where the inventory enumerates keys exhaustively — the
record root and one level in. Deeper than that the walker samples rather than enumerates, so the
schema stays open and says so, instead of failing valid data.

Reads:  contracts/_shapes.json  (run infer_shapes.py first)
        design/unlock_enums.json, scripts/ingest/dissect.py, scripts/ingest/conjugate.py, …
Writes: contracts/<entity>.schema.json
"""
from __future__ import annotations

import ast
import copy
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
SHAPES = ROOT / "contracts" / "_shapes.json"
OUT = ROOT / "contracts"
COMMON = "common.schema.json"

# Two schemas are hand-authored and this generator must never write them (see main()).
HANDWRITTEN = {"capability_lesson_map", "kana_family"}

LEVELS = ["pre-n5", "n5", "n4", "n3", "n2", "n1"]
LEVEL_SET = set(LEVELS)
LEVEL_RE = "|".join(LEVELS)
ID_LIKE = re.compile(r"^[a-z][a-z0-9_]*:[^\s]+$")

# An enum is only ever proposed for a string field on an entity with at least this many records.
# course_manifest and speak_path have exactly one record each, so EVERY scalar in them looked like a
# closed set: `generated` became the enum ["2026-08-26"] and totals.units the enum [72].
MIN_RECORDS_FOR_ENUM = 50
MAX_ENUM_VALUE_LEN = 40   # past this it is prose, a path or an id, not a vocabulary


# --- reading the vocabularies out of the documents and the producers ----------------------------
def _literal(path: Path, name: str):
    """Read one module-level literal out of a .py file WITHOUT importing it.

    Importing dissect.py would drag in sudachipy and jaconv just to read a dict of strings, and a
    contract generator that cannot run without the NLP stack installed is a contract generator nobody
    runs. ast.literal_eval sees the same values the interpreter would.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return ast.literal_eval(node.value)
    raise SystemExit(f"{path.relative_to(ROOT)}: no module-level `{name}` — the producer moved and the "
                     f"contract generator can no longer read its vocabulary. Fix this table, do not "
                     f"fall back to measuring the data.")


DESIGN_ENUMS = json.loads((ROOT / "design" / "unlock_enums.json").read_text(encoding="utf-8"))
_DISSECT = ROOT / "scripts" / "ingest" / "dissect.py"
_CONJ = ROOT / "scripts" / "ingest" / "conjugate.py"
_ROLES = ROOT / "scripts" / "export" / "build_role_exercises.py"
_FORMATION = ROOT / "scripts" / "validate" / "validate_grammar_formation.py"

POS_VALUES = sorted(set(_literal(_DISSECT, "POS_MAP").values()))
INFLECTION_VALUES = sorted(set(_literal(_DISSECT, "INFLECTION_MAP").values()))
PARTICLE_FUNCTION_VALUES = sorted(set(_literal(_DISSECT, "PARTICLE_FUNCTION_MAP").values()))
CONJ_FORM_VALUES = sorted(set(_literal(_CONJ, "VERB_FORMS")) | set(_literal(_CONJ, "ADJ_FORMS")))
ROLE_VALUES = sorted(_literal(_ROLES, "ASKABLE"))
FORMATION_BASE_VALUES = sorted(_literal(_FORMATION, "BASES"))


def vocabulary(values, owner: str, source: str, doc: str) -> dict:
    """A closed value set that came from somewhere a human owns, not from the sample."""
    return {
        "type": "string",
        "enum": sorted(values),
        "description": f"{doc} Vocabulary owner: {owner} — {source}. Widening it is an edit there, "
                       f"never a side effect of regenerating this schema from the data.",
        "x-vocabulary": {"owner": owner, "source": source},
    }


def design(key: str, source: str, doc: str, prefix: str = "") -> dict:
    return vocabulary([prefix + v for v in DESIGN_ENUMS[key]], "design", source, doc)


def plain(doc: str) -> dict:
    """No vocabulary exists for this field, so the contract does not invent one."""
    return {"type": "string", "description": doc}


# --- semantics: what a field NAME means wherever it appears -------------------------------------
REF_BY_NAME = {
    "level": "Level",
    "layer": "Layer",
    "locale": "Locale",
    "level_confidence": "LevelTag/properties/level_confidence",
    "level_agreement": "LevelTag/properties/level_agreement",
    "needs_review": "Provenance/properties/needs_review",
    "ai_generated": "Provenance/properties/ai_generated",
    "source": "Provenance/properties/source",
}
# Same idea, but these win even when the node has children: `level_sources` is an OPEN map whose keys
# are whichever community lists were consulted (spec §1.5 expects that set to grow), so its measured
# children must never become a closed key list.
# (Pointed at LevelTag's own property rather than straight at $defs/LevelSources — which is where that
# property points — so build_manifest.py's ts_type() still recognises the tail and keeps emitting a real
# TypeScript type for the field instead of `unknown`.)
REF_BY_NAME_WITH_CHILDREN = {"level_sources": "LevelTag/properties/level_sources"}

# Fields whose value is the record's own public address.
ID_FIELDS = {"slug", "id"}

# Whole-field shapes keyed by NAME, applied wherever the name appears. Each one replaces a measured
# enum that the audit showed pins the corpus to one day, one asset state or one release.
SHAPE_BY_NAME: dict[str, dict] = {
    "generated": {
        "type": "string", "format": "date", "pattern": r"^\d{4}-\d{2}-\d{2}$",
        "description": "The date this artifact was exported. Was once enumed to the day it happened to "
                       "be built, which failed the gate on every later export.",
    },
    "schema_version": {
        "type": "string", "pattern": r"^\d+\.\d+$",
        "description": "MAJOR.MINOR of the record format. A version field exists to be bumped; an enum "
                       "over the current value means it never can be.",
    },
    "audio": {
        "type": "string", "pattern": r"^(pending|[A-Za-z0-9_./-]+\.(mp3|m4a|ogg|wav|opus))$",
        "description": "The audio asset, or the literal `pending` while the TTS pipeline "
                       "(design/listening.md) has not produced it yet. The first real filename must not "
                       "fail the build.",
    },
    "path": {
        "type": "string", "minLength": 1, "pattern": r"^[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*$",
        "description": "A repository-relative path to the referenced file.",
    },
    "license": {
        "type": "string", "minLength": 1,
        "description": "The upstream dataset's licence identifier (see ATTRIBUTION.md). Free text: a new "
                       "dataset brings a new licence, which is not a contract violation.",
    },
}

# Array fields whose items are answer OPTIONS. A one-option question and a repeated option are both
# broken items; design/listening.md names those invariants and nothing enforced them.
OPTION_ARRAYS = {"distractors"}

# Whole-field shapes keyed by "<entity>.<dotted path>". This is where the vocabularies live: each entry
# names its owner, and nothing here is derived from the corpus sample.
SHAPE_BY_PATH: dict[str, dict] = {}


def _register(entries: dict[str, dict]) -> None:
    SHAPE_BY_PATH.update(entries)


# ---- DESIGN-OWNED: the document is the authority, the data is what gets checked -----------------
_exercise_type = vocabulary(
    ["recognition", "cloze", "particle_choice", "sentence_build", "reading", "listening",
     "production", "handwriting", "matching", "ordering"],
    "design", "design/lesson_schema.md ('Exercise records', the ten `type` values)",
    "What kind of exercise this is.")
_unlock_type = design("unlock_type", "design/unlock_enums.json#unlock_type",
                      "What kind of item this lesson makes available.")
_grammar_register = vocabulary(
    ["neutral", "plain", "casual", "polite", "formal", "written", "honorific", "humble",
     "colloquial", "literary", "dated", "masculine", "feminine", "slang"],
    "design", "design/schema_v2.md ('Grammar': the register array) + the grammar_point table comment",
    "Registers this grammar point belongs to.")
_vocab_register = vocabulary(
    ["colloquial", "slang", "vulgar", "honorific", "humble", "polite", "familiar", "archaic"],
    "design", "design/schema_v2.md ('Vocab': the neutral register enum from JMdict misc)",
    "Register tags for this word or sense.")
_strand = vocabulary(
    ["meaning-input", "meaning-output", "language-focused", "fluency"],
    "design", "design/learning_science.md R77 (Nation's four strands)",
    "Which of the four strands this component trains.")
_exam_section = vocabulary(
    ["kanji_reading", "orthography", "context_fill", "grammar_form", "sentence_order",
     "paraphrase", "usage", "text_grammar", "reading_comp"],
    "design", "design/exam_simulator.md (the written-section table)",
    "Which exam section this item is drawn from.")

_register({
    "lesson.exercises[].type": _exercise_type,
    "lesson.unlocks[].type": _unlock_type,
    "topic.lessons[].unlocks[].type": _unlock_type,
    "lesson.feature_unlocks[]": design(
        "feature", "design/unlock_enums.json#feature", "An app feature this lesson turns on.",
        prefix="feat:"),
    "lesson.srs.introduces_cards[].deck": design(
        "deck", "design/unlock_enums.json#deck", "The SRS deck these cards land in."),
    "grammar.register[]": _grammar_register,
    "grammar.caution": vocabulary(
        ["none", "rough", "offensive", "sensitive"],
        "design", "design/schema_v2.md ('Grammar': caution)",
        "How careful a learner has to be with this pattern."),
    "vocab.register[]": _vocab_register,
    "vocab.senses[].register[]": _vocab_register,
    "vocab.lexeme_type": vocabulary(
        ["word", "suru_verb", "counter", "prefix", "suffix", "expression", "aux"],
        "design", "design/schema_v2.md (the `vocab` table, lexeme_type)",
        "What kind of lexical item this entry is."),
    "vocab.verb_class": vocabulary(
        ["ichidan", "godan", "suru_irregular", "kuru_irregular"],
        "design", "design/schema_v2.md (the `vocab` table, verb_class)",
        "Inflection class, null for anything that is not a verb."),
    "vocab.adj_class": vocabulary(
        ["i_adj", "na_adj"],
        "design", "design/schema_v2.md (the `vocab` table, adj_class)",
        "Adjective class, null for anything that is not an adjective."),
    "reading.length_band": vocabulary(
        ["short", "paragraph", "long"],
        "design", "design/reading_practice.md (length_band)",
        "Roughly how long the passage is."),
    "exam_item.script[].speaker": vocabulary(
        ["M1", "M2", "F1", "F2", "N"],
        "design", "design/listening.md (speaker registry — dialogue voices plus narrator)",
        "Locale-neutral speaker slot the TTS pipeline maps to a voice."),
    "sentence.provenance.pt_source": vocabulary(
        ["ai", "tatoeba", "human"],
        "design", "design/schema_v2.md (the `sentence` table, pt_source)",
        "Where the pt-BR translation came from. Selection beats generation (spec §1.2)."),
    "sentence.provenance.pt_validated_against": vocabulary(
        ["en", "dict", "both", "none"],
        "design", "design/schema_v2.md (the `sentence` table, pt_validated_against)",
        "What the Layer-B translation was machine-checked against."),
    "speak_unit.checkpoint[].type": _exam_section,
    "speak_unit.drills[].strand": _strand,
    "speak_unit.production[].strand": _strand,
    "speak_unit.fluency.strand": _strand,
})

# ---- PRODUCER-OWNED: parsed from the code that emits the value ---------------------------------
_token_pos = vocabulary(
    POS_VALUES, "producer", "scripts/ingest/dissect.py POS_MAP (Sudachi/UniDic 品詞 → neutral enum)",
    "Part of speech, Layer A, mechanical from the analyzer.")
_conj_form = vocabulary(
    CONJ_FORM_VALUES, "producer", "scripts/ingest/conjugate.py VERB_FORMS + ADJ_FORMS",
    "Which inflected form this is.")
_conj_class = vocabulary(
    ["ichidan", "godan", "suru_irregular", "kuru_irregular", "i_adj", "na_adj"],
    "producer", "scripts/ingest/conjugate.py (verb_class ∪ adj_class — the conjugation bank keys on both)",
    "Inflection class this table was generated from.")
_conj_kind = vocabulary(
    ["verb", "adjective"], "producer", "scripts/ingest/conjugate.py (VERB_FORMS vs ADJ_FORMS)",
    "Whether this is a verb or an adjective paradigm.")

_register({
    "sentence.tokens[].pos": _token_pos,
    "reading.tokens[].pos": _token_pos,
    "sentence.tokens[].inflection": vocabulary(
        INFLECTION_VALUES, "producer", "scripts/ingest/dissect.py INFLECTION_MAP (Sudachi 活用形)",
        "Inflected form of this token, Layer A."),
    "sentence.particles[].function_type": vocabulary(
        PARTICLE_FUNCTION_VALUES, "producer",
        "scripts/ingest/dissect.py PARTICLE_FUNCTION_MAP (Sudachi 助詞 subtype)",
        "Standard joshi classification for this particle."),
    "sentence.tokens[].split_mode": vocabulary(
        ["A", "B", "C"], "producer", "SudachiPy split modes (A short / B middle / C long)",
        "Which Sudachi split mode produced this token."),
    "conjugation.conjugations[].form": _conj_form,
    "exercise_conjugation.form": _conj_form,
    "conjugation.class": _conj_class,
    "exercise_conjugation.class": _conj_class,
    "conjugation.kind": _conj_kind,
    "exercise_conjugation.kind": _conj_kind,
    "exercise_role.role": vocabulary(
        ROLE_VALUES, "producer", "scripts/export/build_role_exercises.py ASKABLE",
        "Which sentence role the drill asks about."),
    "grammar.formation_steps.variants[].base": vocabulary(
        FORMATION_BASE_VALUES, "producer", "scripts/validate/validate_grammar_formation.py BASES",
        "What the formation step attaches to."),
    "speak_unit.checkpoint[].via": vocabulary(
        ["new-word", "phrase", "review"], "producer",
        "scripts/export/build_speaking_checkpoints.py (how the item was selected for this unit)",
        "Why this checkpoint item is in this unit."),
})

# ---- CURATED: closed in reality, owned by no document, so written out here ----------------------
_kana_group_type = vocabulary(
    ["base", "dakuten", "handakuten", "long-vowel", "sokuon", "yoon"],
    "curated", "contracts/kana_family.schema.json (the hand-authored kana chart contract)",
    "How this kana group relates to the base chart.")

_register({
    "kana.type": _kana_group_type,
    "kanji.readings[].type": vocabulary(
        ["on", "kun", "nanori"], "curated", "KANJIDIC2 reading types (Layer A source vocabulary)",
        "Reading class. `nanori` readings are name-only and are not taught."),
    "family.type": vocabulary(
        ["semantic_field", "kanji_component", "phonetic_series", "word_family", "conjugation_class",
         "particle_set", "contrast_pair", "function_set"],
        "curated", "scripts/ingest/migrations/001_init.sql (the `family.type` column comment)",
        "What kind of grouping this family is."),
    "family.members[].member_type": vocabulary(
        ["kanji", "vocab", "grammar"], "curated",
        "scripts/ingest/migrations/001_init.sql (the `family_member.member_type` column comment)",
        "Which registry the member id belongs to."),
    "stroke_kana.kind": vocabulary(
        ["hiragana", "katakana"], "curated", "the two kana scripts",
        "Which script this glyph belongs to."),
    "speak_path.stages[].approx_band": {
        "type": "string",
        "pattern": f"^({LEVEL_RE})(/({LEVEL_RE}))?$",
        "description": "Roughly where this stage sits against the JLPT ladder — one Level, or a pair "
                       "when the stage straddles two. A pattern rather than an enum so the bands can be "
                       "re-cut without a schema change (spec §1.6).",
    },
})

# ---- DELIBERATELY UNTYPED: a small value set today, but no vocabulary anyone owns ---------------
_register({
    "grammar.nuance_tags[]": plain(
        "Free semantic tags on a grammar point. No document defines the tag set, so the contract does "
        "not pretend one is closed — an authored tag nobody declared should be caught by review, not by "
        "an enum measured from the corpus."),
    "grammar.usage_contexts[]": plain("Situations this pattern belongs to. No declared taxonomy."),
    "grammar.related[]": plain("Keys of related grammar points. A reference list, not a vocabulary."),
    "sentence.pattern[].role": plain(
        "Slot role inside the sentence pattern, as the pattern builder labelled it. No declared "
        "taxonomy; scripts/export/build_role_exercises.py consumes only the subset it can ask about."),
    "sentence.clause_structure": plain("Coarse clause shape of the sentence. No declared taxonomy."),
    "sentence.tokens[].pos_coarse": plain(
        "Raw Sudachi/UniDic 品詞 大分類, kept verbatim for traceability. Third-party analyzer output: "
        "the project does not own this vocabulary and must not constrain it (design/schema_v2.md §B "
        "makes token analyzer output immutable)."),
    "sentence.tokens[].pos_fine": plain(
        "Raw Sudachi/UniDic 品詞 細分類, kept verbatim. Third-party analyzer output, see pos_coarse."),
    "vocab.senses[].misc[]": plain(
        "JMdict misc tags for this sense, verbatim (`uk`, `hum`, `col`, …). JMdict owns roughly eighty "
        "of them and adds more; this corpus carries whichever the entry had."),
    "sentence.provenance.tier": plain("Dissection tier this sentence was processed at."),
    "exercise_role.particle": plain("The particle that pins the asked-about role, when one does."),
    "topic.theme": plain("Free thematic label for the topic. No declared taxonomy."),
    "course.topics[].theme": plain("Free thematic label for the topic. No declared taxonomy."),
})

# ---- exam_item: one file family, fourteen question shapes ---------------------------------------
# The BRANCHES are structural and hand-declared — which id prefixes share a question shape, and what
# that shape must carry. The `required` list inside each branch is then measured (a key on 100% of that
# prefix's records), which is safe in the way an enum is not: measurement can only be broken by
# DELETING a field. `must` is the floor the measurement has to reproduce; if it ever stops being 100%
# present, generation fails loudly rather than quietly emitting a weaker contract.
EXAM_BRANCHES: list[dict] = [
    {"name": "word-level multiple choice", "prefixes": ["kr", "or"],
     "must": ["stem", "correct", "distractors"],
     "doc": "kanji_reading / orthography: a word in isolation, four options."},
    {"name": "multiple choice inside a sentence", "prefixes": ["cf", "gf"],
     "must": ["stem", "correct", "distractors", "sentence"],
     "doc": "context_fill / grammar_form: the gap sits in a real corpus sentence."},
    {"name": "ordering", "prefixes": ["so"],
     "must": ["pieces", "answer"],
     "doc": "sentence_order: the learner rebuilds the sentence from shuffled pieces."},
    {"name": "passage multiple choice", "prefixes": ["tg", "rc"],
     "must": ["reading", "correct", "distractors"], "any_of": [["stem", "question"]],
     "doc": "text_grammar / reading_comp: the item hangs off a reading passage, and the prompt is "
            "carried by `stem` or by `question` depending on the section."},
    {"name": "paraphrase", "prefixes": ["pp"],
     "must": ["stem", "correct", "distractors", "sentence", "target"],
     "doc": "paraphrase: pick the sentence that means the same thing."},
    {"name": "usage", "prefixes": ["us"],
     "must": ["correct", "sentence", "target", "wrong"],
     "doc": "usage: pick the sentence that uses the target word correctly."},
    {"name": "listening", "prefixes": ["lt", "lp", "ls", "lr", "lg"],
     "must": ["audio", "script", "question", "correct", "distractors"],
     "doc": "the five listening sections: a spoken script, its audio, and options."},
]


def ref(name: str) -> dict:
    return {"$ref": f"{COMMON}#/$defs/{name}"}


def type_schema(types: list[str], info: dict | None = None) -> dict:
    """Turn the observed JSON types into a type constraint, keeping null optional-but-allowed."""
    ts = [t for t in types if t != "null"]
    node: dict = {}
    if not ts:
        return {"type": "null"}
    # An integer-only field stays integer; a field seen as both int and float is a number.
    if set(ts) == {"integer", "number"}:
        ts = ["number"]
    node["type"] = ts[0] if len(ts) == 1 else ts
    if "null" in types:
        node["type"] = ([node["type"]] if isinstance(node["type"], str) else node["type"]) + ["null"]
    # A quantity gets a range, never a value set. `minimum: 0` is the real invariant behind a count,
    # an ordinal and a stroke number; "the sizes we have already exported" is not.
    if info and set(ts) <= {"integer", "number"} and isinstance(info.get("min"), (int, float)):
        if info["min"] >= 0:
            node["minimum"] = 0
    return node


class Node:
    """A point in the reconstructed record tree."""

    def __init__(self) -> None:
        self.info: dict | None = None
        self.children: dict[str, "Node"] = {}
        self.item: "Node | None" = None      # for arrays: the shape of one element


def parse_path(path: str) -> list[tuple[str, bool]]:
    """'example_words[].gloss.en' -> [('example_words', True), ('gloss', False), ('en', False)]"""
    out = []
    for seg in path.split("."):
        is_array = seg.endswith("[]")
        out.append((seg[:-2] if is_array else seg, is_array))
    return out


def build_tree(fields: dict) -> Node:
    """Rebuild the record tree from the flat dotted paths.

    The subtlety is that `distractors` and `distractors[]` are two facts about the same field — the
    first says it is an array, the second says its elements are strings — and they must land on
    different nodes. A trailing `[]` always means "descend into the element", so both facts survive;
    letting them share a node makes the element type silently overwrite the array type.
    """
    root = Node()
    for path, info in fields.items():
        cur = root
        for name, is_array in parse_path(path):
            if name:
                cur.children.setdefault(name, Node())
                cur = cur.children[name]
            if is_array:
                cur.item = cur.item or Node()
                cur = cur.item
        cur.info = info
    return root


def is_locale(node: Node) -> str | None:
    """A locale object is any object with a pt-BR key. String values -> LocaleText, arrays -> list."""
    pt = node.children.get("pt-BR")
    if pt is None or pt.info is None:
        return None
    return "LocaleTextList" if "array" in pt.info["types"] else "LocaleText"


def nullable(schema: dict, info: dict | None) -> dict:
    """A $ref cannot be relaxed by adding `type: null` beside it — the ref wins. Wrap it instead."""
    if info and "null" in info.get("types", []):
        if schema.get("type") == "null":
            return schema
        return {"anyOf": [schema, {"type": "null"}]}
    return schema


NOTE_NAME = re.compile(r"(^|_)(note|notes|description|explanation|meaning|meanings|comment)s?$")


def all_null(info: dict | None) -> bool:
    return bool(info) and info["types"] == ["null"]


def enum_candidate(name: str, info: dict, records: int) -> list[str] | None:
    """The measured value set, but only where measuring one is defensible.

    Every rejection below is a probe from the 2026-08-26 audit that a legitimate future record failed.
    """
    vals = info.get("values")
    if not vals or not all(isinstance(v, str) for v in vals):
        return None                                   # integers/booleans are quantities, never enums
    if records < MIN_RECORDS_FOR_ENUM:
        return None                                   # one record makes every field look closed
    if any(len(v) > MAX_ENUM_VALUE_LEN or " " in v or "/" in v for v in vals):
        return None                                   # prose, a path or a ratio, not a vocabulary
    if any(ID_LIKE.match(v) for v in vals):
        return None                                   # a foreign key list, not a vocabulary
    return list(vals)


def emit(node: Node, name: str, path: str, entity: str, records: int, depth: int) -> dict:
    info = node.info
    loc = is_locale(node)
    if loc:
        return nullable(ref(loc), info)

    # 1. A hand-owned shape or vocabulary wins over anything measurable.
    spec = SHAPE_BY_PATH.get(f"{entity}.{path}") or SHAPE_BY_NAME.get(name)
    if spec is not None and not node.children and node.item is None:
        return nullable(copy.deepcopy(spec), info)

    if name in REF_BY_NAME_WITH_CHILDREN and info:
        return nullable(ref(REF_BY_NAME_WITH_CHILDREN[name]), info)

    if name in REF_BY_NAME and info and not node.children:
        return nullable({"$ref": f"{COMMON}#/$defs/{REF_BY_NAME[name]}"}, info)

    if name in ID_FIELDS and info and "string" in info["types"] and not node.children:
        return nullable(ref("StableId"), info)

    # 2. A level is a level wherever it appears (spec §1.6). The audit found ten level-valued fields
    #    that were not literally named `level` and had been frozen to the levels shipped so far —
    #    family.spans_levels, kanji.readings[].introduced_at_level, every level_sources.<list> value.
    if info and info.get("values") and set(info["values"]) <= LEVEL_SET:
        return nullable(ref("Level"), info)

    # 3. A short list of stable ids is a foreign-key column, not a vocabulary. Saying so makes the edge
    #    visible to a reader and stops the next regeneration freezing today's targets — speak_unit.stage
    #    had become an enum of the twelve stages that exist, chunk_phrases an enum of sixteen sentences.
    if info and info.get("values") and all(isinstance(v, str) and ID_LIKE.match(v)
                                           for v in info["values"]):
        return nullable(ref("IdRef"), info)

    # 4. A field that is null on every record so far. `{"type": "null"}` says "and it must stay empty",
    #    which is the opposite of what an unwritten Layer-C prose field means.
    if all_null(info):
        if NOTE_NAME.search(name):
            return {"anyOf": [ref("LocaleText"), {"type": "null"}],
                    "description": "Authorable Layer-C prose. Empty on every record today; typed as the "
                                   "locale object it will hold rather than pinned to null."}
        return {"type": ["string", "null"],
                "description": "Empty on every record today; left nullable rather than pinned to null."}

    schema = type_schema(info["types"], info) if info else {"type": "object"}

    # 5. Nothing above claimed this field, so the measurement is allowed to — under the filters in
    #    enum_candidate(), which are the audit's own rejected probes turned into rules.
    if info:
        vals = enum_candidate(name, info, records)
        if vals is not None:
            schema["enum"] = vals + ([None] if "null" in info["types"] else [])
            schema["x-vocabulary"] = {
                "owner": "measured",
                "source": "contracts/_shapes.json — no design document or producer owns this field, "
                          "and the observed set is small, closed and free of prose, ids and paths.",
            }

    if node.children:
        props, required = {}, []
        for k, child in sorted(node.children.items()):
            props[k] = emit(child, k, f"{path}.{k}" if path else k, entity, records, depth + 1)
            # A field that is null on every record is not a field a consumer can rely on; requiring it
            # forces every future writer to keep writing null.
            if child.info and child.info.get("required") and not all_null(child.info):
                required.append(k)
        # Keep whatever type_schema worked out — an object field that is sometimes null must stay
        # ["object", "null"]. Hard-coding "object" here silently dropped the null and failed 568 valid
        # records whose optional sub-object is absent.
        if "type" not in schema:
            schema["type"] = "object"
        schema["properties"] = props
        if required:
            schema["required"] = required
        # Keys are enumerated exhaustively only for the first two levels (see module docstring).
        if depth <= 1:
            schema["additionalProperties"] = False

    if node.item is not None:
        schema["items"] = emit(node.item, name, f"{path}[]", entity, records, depth + 1)
        if name in OPTION_ARRAYS:
            schema["minItems"] = 2
            schema["uniqueItems"] = True

    return schema


def exam_branches(shape: dict) -> list[dict]:
    """Turn the per-prefix inventory into if/then branches, one per question shape."""
    variants = shape.get("variants") or {}
    if not variants:
        return []
    out, covered = [], set()
    for branch in EXAM_BRANCHES:
        present = [p for p in branch["prefixes"] if p in variants]
        if not present:
            continue
        covered.update(present)
        always = set.intersection(*(set(variants[p]["always"]) for p in present))
        missing = [k for k in branch["must"] if k not in always]
        if missing:
            raise SystemExit(
                f"exam_item branch {branch['name']!r} ({'/'.join(present)}): {missing} is not on 100% "
                f"of those items any more. The question shape changed — fix the data or edit "
                f"EXAM_BRANCHES on purpose; do not let the contract quietly weaken.")
        required = sorted(always | set(branch["must"]))
        then: dict = {"required": required}
        for group in branch.get("any_of", []):
            then.setdefault("anyOf", []).extend({"required": [k]} for k in group)
        n = sum(variants[p]["records"] for p in present)
        out.append({
            "title": branch["name"],
            "description": f"{branch['doc']} Applies to ids prefixed {', '.join(present)} "
                           f"({n} items). `required` is measured at 100% presence per prefix; the "
                           f"branch itself is declared in build_schemas.py.",
            "if": {"required": ["id"], "properties": {"id": {"pattern": f"^({'|'.join(present)}):"}}},
            "then": then,
        })
    unknown = sorted(set(variants) - covered)
    if unknown:
        raise SystemExit(
            f"exam_item: id prefixes {unknown} match no declared branch. A new question shape needs a "
            f"branch in EXAM_BRANCHES (and a section entry in design/exam_simulator.md).")
    if out:
        prefixes = "|".join(sorted(covered))
        out.insert(0, {
            "title": "known section",
            "description": "Every item's id names one of the declared exam sections. A typo'd prefix "
                           "would otherwise match no branch and be validated by the envelope alone.",
            "properties": {"id": {"pattern": f"^({prefixes}):"}},
        })
    return out


# One-line purpose per entity. Measurement cannot produce these.
ABOUT = {
    "kanji": "One kanji character: readings, meanings, radical decomposition and the level it is taught at. Layer A apart from the pt-BR meanings.",
    "vocab": "One dictionary word, keyed by its JMdict entry. Carries senses, pitch, inflection class and the consensus level.",
    "grammar": "One grammar point: its forms, how it is formed, what it contrasts with, and the pedagogy around it.",
    "sentence": "One fully dissected example sentence — the unit the whole corpus is built on. A sentence lives here ONCE and everything else references it by id.",
    "family": "A group of items that behave alike (a conjugation class, a particle set, a semantic field), with the rule that governs the group.",
    "conjugation": "The full inflection table for one verb or adjective. It is addressed by the vocab entry it belongs to, so `slug` here is a foreign key into vocab, not a new address.",
    "kana": "One hiragana or katakana character and the family it belongs to.",
    "kana_family": "The kana chart, as ordered groups (base, dakuten, yoon...). Keyed by script.",
    "reading": "A short reading passage gated to a lesson, with its tokens and translation.",
    "stroke_order": "Ordered stroke steps for one kanji, for animating how it is written.",
    "stroke_lines": "Raw stroke path geometry for one kanji.",
    "stroke_kana": "Stroke data for one kana character, including the shadow guides used when tracing.",
    "capability": "Something a learner can DO once a set of lessons is complete. The bridge between the syllabus and the exam.",
    "capability_lesson_map": "Which capabilities each lesson contributes to. Keyed by lesson id.",
    "exam_item": "One JLPT-style practice question, drawn from the corpus so every item is also findable in a lesson. The id prefix names the section, and each section has its own required shape.",
    "exercise_conjugation": "One generated conjugation drill: a prompt form, the correct inflection, and three distractors.",
    "exercise_role": "One generated particle-role drill, derived mechanically from a sentence's own particles.",
    "course": "A course root for one level: its ordered topics and the overview shown before the first lesson.",
    "topic": "A block of lessons that closes one theme, and the items it unlocks.",
    "lesson": "The leaf unit a learner sits down to. Holds objectives, explanation, exercises and the items it introduces — all corpus content by REFERENCE, never embedded.",
    "speak_path": "The root of the situation-ordered path (Fala Primeiro): its stages and totals.",
    "speak_unit": "One unit of the speaking path: phrases, drills and a checkpoint for a single situation.",
    "course_manifest": "The index an API reads first: every course, where its root lives, and how much is in it.",
}

def main() -> int:
    if not SHAPES.exists():
        print("run scripts/contracts/infer_shapes.py first", file=sys.stderr)
        return 2
    shapes = json.loads(SHAPES.read_text(encoding="utf-8"))["entities"]

    # The two map-packed schemas are hand-authored. Assert that up front rather than relying on a
    # `continue` deep in the loop: a new map entity would otherwise get no schema at all and become
    # invisible to both validate_contracts.py and build_manifest.py, which glob contracts/*.schema.json.
    map_entities = {e for e, v in shapes.items() if v["kind"] == "map"}
    if map_entities != HANDWRITTEN:
        print(f"map-packed entities {sorted(map_entities)} do not match the hand-authored set "
              f"{sorted(HANDWRITTEN)}. Write the missing schema by hand (a map's contract is about its "
              f"key space) and add it to HANDWRITTEN.", file=sys.stderr)
        return 2
    for e in sorted(HANDWRITTEN):
        if not (OUT / f"{e}.schema.json").exists():
            print(f"hand-authored contract contracts/{e}.schema.json is missing", file=sys.stderr)
            return 2

    written = []
    for entity, v in shapes.items():
        if not v["records"]:
            continue
        if entity in HANDWRITTEN:
            continue
        tree = build_tree(v["fields"])
        props, required = {}, []
        for k, child in sorted(tree.children.items()):
            props[k] = emit(child, k, k, entity, v["records"], 0)
            if child.info and child.info.get("required") and not all_null(child.info):
                required.append(k)

        # Which field holds this record's OWN address? `id` when it is a prefixed string — on
        # exercise_conjugation the `slug` is the vocab the drill is about, a foreign key, and treating
        # it as the primary key reports 17,368 "duplicates" that are nothing of the sort. Fall back to
        # `slug` for the registries, where `id` is an integer storage row number.
        id_field = None
        if "id" in tree.children and "string" in v["fields"]["id"]["types"]:
            id_field = "id"
        elif "slug" in tree.children and "string" in v["fields"]["slug"]["types"]:
            id_field = "slug"

        doc = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"https://yomineko.dev/contracts/{entity}.schema.json",
            "title": entity,
            "description": ABOUT.get(entity, ""),
            "x-yomineko": {
                "entity": entity,
                "records": v["records"],
                "packing": v["kind"],
                "glob": v["glob"],
                "stable_id_field": id_field,
                "generated_by": "scripts/contracts/build_schemas.py from contracts/_shapes.json",
                "vocabulary_policy": "Types, nesting and `required` are measured from the data. Value "
                                     "sets are not: every `enum` here is either declared in a design "
                                     "document, parsed from the code that produces the value, or "
                                     "curated in build_schemas.py with its source named in "
                                     "x-vocabulary. See contracts/README.md.",
            },
            "type": "object",
            "properties": props,
            "additionalProperties": False,
        }
        if required:
            doc["required"] = required
        branches = exam_branches(v)
        if branches:
            doc["allOf"] = branches
        path = OUT / f"{entity}.schema.json"
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append((entity, len(props), len(required), len(branches)))

    for e, p, r, b in written:
        extra = f", {b} shape branches" if b else ""
        print(f"  {e:22} {p:>3} properties, {r:>3} required{extra}")
    print(f"\n{len(written)} schemas -> contracts/  "
          f"({len(HANDWRITTEN)} hand-authored, untouched: {', '.join(sorted(HANDWRITTEN))})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
