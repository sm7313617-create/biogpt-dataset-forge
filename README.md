# 🧬 biogpt-dataset-forge

> Dataset hygiene and schema normalisation pipeline for the **BioGPT** project —
> converting 200 raw biological protocol folders into a unified, training-ready
> dataset for fine-tuning Qwen 3B / 7B / 14B language models on BioScript code generation.

---

## What this project does

BioGPT is a fine-tuned LLM that translates natural-language biological protocols
into valid **BioScript** code for execution on microfluidic biochips.

This repo contains the **data pipeline** that:

1. **Fixes double file extensions** across ~100 protocol folders
   (`description.txt.txt` → `description.txt`, `output.dot.dot` → `output.dot`, etc.)

2. **Rewrites every protocol's `.json` file** into the unified `biogpt-v3-optimum` schema,
   using an AI agent (Gemini 2.5 Flash via Antigravity IDE) that reads all 6 files
   in each folder and assembles the correct structure automatically.

3. **Exports a training-ready `.jsonl`** file for HuggingFace SFTTrainer.

---

## Project structure

```
biogpt-dataset-forge/
│
├── README.md
├── .gitignore
├── requirements.txt
│
├── scripts/
│   ├── biogpt_dataset_fixer.py     # Python fallback / validation script
│   ├── validate_schema.py          # Validates every .json against the schema
│   ├── export_jsonl.py             # Exports biogpt_train_ready.jsonl
│   └── stats.py                    # Dataset statistics and quality report
│
├── schema/
│   └── biogpt_v3_optimum.json      # The canonical schema (source of truth)
│
├── prompts/
│   └── agent_prompt.md             # The exact prompt pasted into Antigravity agent
│
├── tests/
│   └── sample_data/                # 2-3 sample protocol folders for testing
│
├── docs/
│   └── schema_guide.md             # Field-by-field explanation of the schema
│
└── .github/
    └── workflows/
        └── validate.yml            # CI: validate all JSONs on every push
```

---

## The two dataset formats (before this pipeline)

| Format | Source | Has `messages[]` | Has `steps`/`cfg` | Trainable |
|--------|--------|:-:|:-:|:-:|
| **Your format** | Your 100 protocols | ✅ | ❌ | Partially |
| **Friend's format** | Friend's 100 protocols | ❌ | ✅ | ❌ |
| **biogpt-v3-optimum** | After this pipeline | ✅ | ✅ | ✅ |

---

## Quick start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/biogpt-dataset-forge.git
cd biogpt-dataset-forge

# Install dependencies
pip install -r requirements.txt

# Validate all JSONs in your dataset
python scripts/validate_schema.py --dataset /path/to/your/dataset

# Export training JSONL
python scripts/export_jsonl.py --dataset /path/to/your/dataset --out train.jsonl

# Full stats report
python scripts/stats.py --dataset /path/to/your/dataset
```

---

## The agent pipeline (Antigravity + Gemini 2.5 Flash)

The main data transformation is handled by an AI agent.
See [`prompts/agent_prompt.md`](prompts/agent_prompt.md) for the exact prompt.

The agent processes each of the 200 protocol folders and:
- Reads `.bs`, `.txt`, `.json`, `.ir`, `.dot` (skips `.png`)
- Rewrites the `.json` in-place with the unified schema
- Pastes `.bs` verbatim into `messages[assistant].content`
- Pastes `.ir` verbatim into `metadata.ir.content`
- Parses `.dot` into `metadata.cfg`

---

## Training usage (HuggingFace / TRL)

```python
from datasets import load_dataset
from trl import SFTTrainer

dataset = load_dataset("json", data_files="biogpt_train_ready.jsonl")
# messages[] is already in chat format — apply_chat_template handles the rest
```

Model targets: `Qwen/Qwen2.5-3B`, `Qwen/Qwen2.5-7B`, `Qwen/Qwen2.5-14B`
Method: QLoRA, r=16, lora_alpha=32

---

## Contributing

This is an active research project. If you are adding new protocols:
1. Follow the `biogpt-v3-optimum` schema exactly (see `schema/biogpt_v3_optimum.json`)
2. Run `python scripts/validate_schema.py` before committing
3. The CI pipeline will also validate on push

---

## License

MIT
