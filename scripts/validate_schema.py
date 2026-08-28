#!/usr/bin/env python3
"""
validate_schema.py
==================
Validates every .json file in the dataset against the biogpt-v3-optimum schema.
Run this after the agent has processed all 200 folders to catch any issues.

Usage:
  python scripts/validate_schema.py --dataset /path/to/dataset
  python scripts/validate_schema.py --dataset /path/to/dataset --fix-common   # auto-fix minor issues
"""

import json
import argparse
import logging
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("Install jsonschema first: pip install jsonschema")
    raise

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
log = logging.getLogger("validator")

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "biogpt_v3_optimum.json"

NOISE_FIELDS = {
    "authors", "sample_cohorts", "statistical_analysis",
    "key_biological_findings", "LOD_calculation",
}

PLACEHOLDER_STRINGS = ["TODO", "placeholder", "VERBATIM content of the .bs"]


def load_schema():
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)


def check_placeholder(data: dict) -> list[str]:
    """Check if assistant message is still a placeholder."""
    issues = []
    msgs = data.get("messages", [])
    for m in msgs:
        if m.get("role") == "assistant":
            content = m.get("content", "")
            for p in PLACEHOLDER_STRINGS:
                if p in content:
                    issues.append(f"assistant message contains placeholder: '{p}'")
    return issues


def check_noise_fields(data: dict) -> list[str]:
    """Check for noise fields that should have been removed."""
    issues = []
    meta = data.get("metadata", {})
    for field in NOISE_FIELDS:
        if field in meta:
            issues.append(f"noise field still present: metadata.{field}")
        if field in data:
            issues.append(f"noise field still present at root: {field}")
    return issues


def check_bs_in_assistant(data: dict) -> list[str]:
    """Check that assistant content looks like BioScript (has 'module' or 'manifest')."""
    issues = []
    msgs = data.get("messages", [])
    for m in msgs:
        if m.get("role") == "assistant":
            content = m.get("content", "")
            if content and "module" not in content and "manifest" not in content:
                issues.append("assistant content may not be valid BioScript (no 'module' or 'manifest' keyword found)")
    return issues


def validate_file(json_path: Path, schema: dict, fix_common: bool = False) -> dict:
    result = {
        "file": str(json_path),
        "valid_schema": False,
        "schema_errors": [],
        "warnings": [],
        "fixed": [],
    }

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        result["schema_errors"].append(f"INVALID JSON: {e}")
        return result

    # Schema validation
    try:
        jsonschema.validate(instance=data, schema=schema)
        result["valid_schema"] = True
    except jsonschema.ValidationError as e:
        result["schema_errors"].append(str(e.message))
    except jsonschema.SchemaError as e:
        result["schema_errors"].append(f"Schema itself is broken: {e}")

    # Extra checks
    result["warnings"].extend(check_placeholder(data))
    result["warnings"].extend(check_noise_fields(data))
    result["warnings"].extend(check_bs_in_assistant(data))

    # Auto-fix common issues
    if fix_common and data.get("_schema") != "biogpt-v3-optimum":
        data["_schema"] = "biogpt-v3-optimum"
        result["fixed"].append("added _schema field")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    return result


def main():
    parser = argparse.ArgumentParser(description="Validate BioGPT dataset JSONs against schema")
    parser.add_argument("--dataset", required=True, help="Path to dataset root folder")
    parser.add_argument("--fix-common", action="store_true", help="Auto-fix minor issues")
    parser.add_argument("--errors-only", action="store_true", help="Only print files with errors")
    args = parser.parse_args()

    dataset = Path(args.dataset).expanduser().resolve()
    schema  = load_schema()

    all_results = []
    pass_count = error_count = warn_count = 0

    folders = sorted(d for d in dataset.iterdir() if d.is_dir())
    for folder in folders:
        for jf in folder.glob("*.json"):
            if jf.suffix == ".bak":
                continue
            r = validate_file(jf, schema, fix_common=args.fix_common)
            all_results.append(r)

            if r["schema_errors"]:
                error_count += 1
                if not args.errors_only:
                    log.error("FAIL  %s", jf.name)
                for e in r["schema_errors"]:
                    log.error("      %s", e)
            elif r["warnings"]:
                warn_count += 1
                if not args.errors_only:
                    log.warning("WARN  %s", jf.name)
                    for w in r["warnings"]:
                        log.warning("      %s", w)
            else:
                pass_count += 1
                if not args.errors_only:
                    log.info("PASS  %s", jf.name)

    print("\n" + "="*55)
    print("  Validation Summary")
    print("="*55)
    print(f"  PASS  : {pass_count}")
    print(f"  WARN  : {warn_count}")
    print(f"  FAIL  : {error_count}")
    print(f"  TOTAL : {pass_count + warn_count + error_count}")
    print("="*55)

    if error_count > 0:
        exit(1)


if __name__ == "__main__":
    main()
