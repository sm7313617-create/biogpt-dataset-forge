#!/usr/bin/env python3
"""
export_jsonl.py
===============
Exports all validated protocol JSONs as a HuggingFace-ready .jsonl file.
Only exports protocols where:
  - _schema == biogpt-v3-optimum
  - messages[] has system + user + assistant
  - assistant content is not a placeholder

Usage:
  python scripts/export_jsonl.py --dataset /path/to/dataset --out train.jsonl
  python scripts/export_jsonl.py --dataset /path/to/dataset --out train.jsonl --split 0.8
"""

import json
import random
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
log = logging.getLogger("export")

PLACEHOLDER_STRINGS = ["TODO", "placeholder", "VERBATIM content of the .bs"]

CATEGORY_ORDER = [
    "sample_preparation",
    "environmental_sensing_assay",
    "immunoassay",
    "nucleic_acid_amplification",
    "clinical_diagnostic",
    "cell_based",
    "synthetic_biology",
]


def is_ready(data: dict) -> tuple[bool, str]:
    """Returns (ready, reason_if_not)."""
    if data.get("_schema") != "biogpt-v3-optimum":
        return False, "wrong or missing _schema"
    msgs = data.get("messages", [])
    if len(msgs) != 3:
        return False, f"messages count is {len(msgs)}, expected 3"
    roles = [m.get("role") for m in msgs]
    if roles != ["system", "user", "assistant"]:
        return False, f"unexpected roles: {roles}"
    assistant_content = msgs[2].get("content", "")
    for p in PLACEHOLDER_STRINGS:
        if p in assistant_content:
            return False, f"assistant content is placeholder (contains '{p}')"
    return True, ""


def complexity_sort_key(data: dict) -> int:
    """Sort by num_steps for curriculum learning (simple protocols first)."""
    try:
        return data["metadata"]["bioscript"]["complexity"]["num_steps"]
    except (KeyError, TypeError):
        return 999


def category_sort_key(data: dict) -> int:
    try:
        cat = data["metadata"]["identity"]["category"]
        return CATEGORY_ORDER.index(cat) if cat in CATEGORY_ORDER else 99
    except (KeyError, TypeError):
        return 99


def to_training_line(data: dict) -> dict:
    """Strip to messages[] only — what SFTTrainer sees."""
    return {
        "messages": [
            {"role": m["role"], "content": m["content"]}
            for m in data["messages"]
            if m.get("role") in ("system", "user", "assistant")
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Export BioGPT dataset to JSONL")
    parser.add_argument("--dataset", required=True, help="Path to dataset root folder")
    parser.add_argument("--out", default="biogpt_train_ready.jsonl", help="Output JSONL file")
    parser.add_argument("--split", type=float, default=None,
                        help="If set (e.g. 0.8), also write train/val/test splits")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for splits")
    parser.add_argument("--curriculum", action="store_true", default=True,
                        help="Sort by num_steps ASC for curriculum learning (default: on)")
    args = parser.parse_args()

    dataset = Path(args.dataset).expanduser().resolve()
    out_path = Path(args.out)

    all_data = []
    skipped  = []

    for folder in sorted(d for d in dataset.iterdir() if d.is_dir()):
        for jf in folder.glob("*.json"):
            if ".bak" in jf.name:
                continue
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                log.warning("Skip (parse error) %s: %s", jf, e)
                skipped.append({"file": str(jf), "reason": str(e)})
                continue

            ready, reason = is_ready(data)
            if not ready:
                log.warning("Skip (%s): %s", reason, jf.name)
                skipped.append({"file": str(jf), "reason": reason})
                continue

            all_data.append(data)

    log.info("Collected %d ready protocols, skipped %d", len(all_data), len(skipped))

    # Curriculum sort: category order first, then num_steps ascending
    if args.curriculum:
        all_data.sort(key=lambda d: (category_sort_key(d), complexity_sort_key(d)))
        log.info("Sorted by curriculum (category + num_steps ASC)")

    # Write main JSONL
    with open(out_path, "w", encoding="utf-8") as f:
        for d in all_data:
            f.write(json.dumps(to_training_line(d), ensure_ascii=False) + "\n")
    log.info("Written: %s (%d lines)", out_path, len(all_data))

    # Optional train/val/test split
    if args.split:
        random.seed(args.seed)
        indices = list(range(len(all_data)))
        random.shuffle(indices)
        n_train = int(len(indices) * args.split)
        n_val   = int(len(indices) * (1 - args.split) / 2)
        train_idx = indices[:n_train]
        val_idx   = indices[n_train:n_train + n_val]
        test_idx  = indices[n_train + n_val:]

        for split_name, idx_list in [("train", train_idx), ("val", val_idx), ("test", test_idx)]:
            split_path = out_path.parent / f"biogpt_{split_name}.jsonl"
            with open(split_path, "w", encoding="utf-8") as f:
                for i in idx_list:
                    f.write(json.dumps(to_training_line(all_data[i]), ensure_ascii=False) + "\n")
            log.info("Written: %s (%d lines)", split_path, len(idx_list))

    # Skipped report
    if skipped:
        skip_path = out_path.parent / "biogpt_skipped.json"
        with open(skip_path, "w", encoding="utf-8") as f:
            json.dump(skipped, f, indent=2)
        log.info("Skipped report: %s", skip_path)

    print("\n" + "="*45)
    print("  Export Summary")
    print("="*45)
    print(f"  Exported  : {len(all_data)}")
    print(f"  Skipped   : {len(skipped)}")
    print(f"  Output    : {out_path}")
    print("="*45)


if __name__ == "__main__":
    main()
