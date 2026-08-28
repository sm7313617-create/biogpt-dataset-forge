#!/usr/bin/env python3
"""
stats.py
========
Prints a quality and coverage report for the full dataset.

Usage:
  python scripts/stats.py --dataset /path/to/dataset
"""

import json
import argparse
from pathlib import Path
from collections import Counter

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    args = parser.parse_args()
    dataset = Path(args.dataset).expanduser().resolve()

    total = 0
    schema_ok = 0
    has_placeholder = 0
    categories = Counter()
    operations = Counter()
    num_steps_list = []
    has_repeat = has_branch = has_split = 0
    missing_ir = missing_cfg = missing_evidence = 0

    for folder in sorted(d for d in dataset.iterdir() if d.is_dir()):
        for jf in folder.glob("*.json"):
            if ".bak" in jf.name:
                continue
            try:
                with open(jf, encoding="utf-8") as f:
                    d = json.load(f)
            except Exception:
                continue

            total += 1
            if d.get("_schema") == "biogpt-v3-optimum":
                schema_ok += 1

            # Placeholder check
            msgs = d.get("messages", [])
            for m in msgs:
                if m.get("role") == "assistant" and "TODO" in m.get("content", ""):
                    has_placeholder += 1

            meta = d.get("metadata", {})

            # Category
            cat = meta.get("identity", {}).get("category", "unknown")
            categories[cat] += 1

            # Bioscript
            bs = meta.get("bioscript", {})
            for op in bs.get("operations", []):
                operations[op] += 1
            comp = bs.get("complexity", {})
            steps = comp.get("num_steps", 0)
            if steps:
                num_steps_list.append(steps)
            if comp.get("has_repeat"):  has_repeat  += 1
            if comp.get("has_branch"):  has_branch  += 1
            if comp.get("has_split"):   has_split   += 1

            # Missing sections
            if not meta.get("ir", {}).get("content"):
                missing_ir += 1
            if not meta.get("cfg", {}).get("basic_blocks"):
                missing_cfg += 1
            if not meta.get("evidence", {}).get("chemical_evidence"):
                missing_evidence += 1

    avg_steps = sum(num_steps_list) / len(num_steps_list) if num_steps_list else 0

    print("\n" + "="*55)
    print("  BioGPT Dataset Statistics")
    print("="*55)
    print(f"  Total protocols         : {total}")
    print(f"  Schema v3-optimum       : {schema_ok} / {total}")
    print(f"  Placeholder (not ready) : {has_placeholder}")
    print(f"  Missing IR content      : {missing_ir}")
    print(f"  Missing CFG             : {missing_cfg}")
    print(f"  Missing evidence        : {missing_evidence}")
    print()
    print("  Complexity breakdown:")
    print(f"    has_repeat  : {has_repeat}")
    print(f"    has_branch  : {has_branch}")
    print(f"    has_split   : {has_split}")
    print(f"    avg_steps   : {avg_steps:.1f}")
    print()
    print("  Categories:")
    for cat, count in categories.most_common():
        print(f"    {cat:<35} : {count}")
    print()
    print("  Operations (across all protocols):")
    for op, count in operations.most_common():
        print(f"    {op:<20} : {count}")
    print("="*55)

if __name__ == "__main__":
    main()
