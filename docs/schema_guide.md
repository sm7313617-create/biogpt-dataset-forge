# BioGPT Schema Guide — biogpt-v3-optimum

Complete field-by-field explanation for anyone authoring or reviewing protocol JSONs.

---

## Top-level fields

| Field | Type | Description |
|-------|------|-------------|
| `_schema` | string | Always `"biogpt-v3-optimum"`. Used by scripts to identify the format. |
| `messages` | array | The training signal. 3 items: system, user, assistant. |
| `metadata` | object | Everything else — traceability, structure, quality control. |

---

## messages[]

### messages[0] — system
Fixed string. Never change it. Every protocol uses the same system prompt.

### messages[1] — user
Reconstructed from the `.txt` description file. Must follow this structure:
```
ASSAY TYPE: <title and platform>

REAGENTS USED:
  - <Reagent_A>: <one-line description>
  - <Reagent_B>: <one-line description>

STEPS:
1. <Step name> [<volume uL | temp C | duration min>]: <description>
2. ...

INTERPRETATION: <LODs, time resolution, success criteria>
```
**Critical:** embed numbers from the paper directly into the step text inside `[brackets]`.
This is what teaches the model numerical precision.

### messages[2] — assistant
**VERBATIM content of the `.bs` file.** Never paraphrase. Never summarise.
Copy byte-for-byte. This is the training target.

---

## metadata.identity

| Field | Values | Notes |
|-------|--------|-------|
| `protocol_id` | `fa_aerosol_2004_001` | initials\_shortassay\_year\_NNN |
| `category` | see enum | Used for stratified train/val/test split |
| `adaptation_status` | `adapted_authored` / `directly_translated` / `synthetic` | |

---

## metadata.bioscript

Mirrors the `.bs` file structurally. Filled FROM the `.bs` file, never written by hand.

**complexity.num_steps** is used for curriculum ordering — sort the training set by
num_steps ASC so the model sees simple protocols before complex ones.

---

## metadata.steps

Each step maps ONE natural-language instruction to ONE BioScript block.
`key_conditions` numbers must match the numbers embedded in messages[user].content.
Both pull from the same source: the paper / `.txt` file.

---

## metadata.cfg

Parsed from the `.dot` file. Never invented.
For simple linear protocols (no branching) this may be empty arrays.

---

## metadata.ir

VERBATIM content of the `.ir` file. Future use for compiler backend training.

---

## metadata.evidence

Keeps the dataset honest. Every chemical and operation in the `.bs` must trace
to a direct quote from the `.txt`/paper. No quote = flag it.

**numeric_mismatches** — when the `.bs` uses a number that doesn't exactly match
the paper (e.g. `repeat 3 times` when the paper says "repeatable" without a count),
explain the approximation here.

---

## Fields that must NEVER appear in the JSON

These are noise — they add tokens without helping the model generate BioScript:

- `authors`
- `sample_cohorts`
- `statistical_analysis`
- `key_biological_findings`
- `LOD_calculation`
- `instrument` (catalog numbers)
- `primers_probes.sequences_reference`

---

## Validation

Run before every commit:
```bash
python scripts/validate_schema.py --dataset /path/to/dataset
```

A protocol is **training-ready** when:
1. `_schema == "biogpt-v3-optimum"`
2. `messages[assistant].content` contains no "TODO" or placeholder text
3. Schema validator returns PASS
