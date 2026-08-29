#!/usr/bin/env python3
"""
fix_dataset.py
==============
Applies the 3 targeted fixes (Fix A: cfg terminal, Fix B: category re-inference,
Fix C: non-template notes) across all biogpt-v4 protocol files in OpenBioSet/Dataset.
"""

import sys
import json
import re
from pathlib import Path

# Configure stdout encoding
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DATASET_PATH = Path(r"C:\Users\sayan\OpenBioSet\Dataset")

TEMPLATE_PHRASES = [
    "This protocol implements an automated workflow for",
    "It provides quantitative measurement and sample handling",
    "All operational steps are conducted on"
]

CATEGORY_RULES = [
    ("synthetic_biology", [
        "crispr", "cas9", "cas12", "cas13", "gene circuit",
        "synthetic biology", "recombineering", "mage",
        "lentiviral", "transfection", "electroporation",
        "yeast competent", "ribozyme", "isoclone",
        "strain development"
    ]),
    ("cell_based", [
        "apoptosis", "caspase", "cell viability",
        "cytotoxicity", "cell culture", "single cell",
        "mammalian cell", "live/dead", "hepatotoxicity",
        "organoid", "impedance sensing"
    ]),
    ("nucleic_acid_amplification", [
        "pcr", "qpcr", "ddpcr", "rt-pcr", "lamp", "amplification",
        "rca", "nasba", "bisulfite", "dna methylome",
        "sequencing", "pyrosequencing", "isothermal"
    ]),
    ("immunoassay", [
        "elisa", "immunoassay", "antibody", "antigen",
        "tsh", "igg", "igm", "sandwich", "competitive elisa",
        "immunoprecipitation", "proximity ligation"
    ]),
    ("clinical_diagnostic", [
        "blood typing", "hemagglutination", "g6pd",
        "hemoglobin", "neonatal", "sickle cell", "thalassemia",
        "septic shock", "rubella", "zika", "sars", "bacteremia",
        "malaria", "ctc", "plasma separation", "newborn screening",
        "lysosomal storage", "nance horan", "succinylacetone",
        "dbs", "dried blood spot"
    ]),
    ("drug_detection", [
        "drug", "fentanyl", "heroin", "morphine", "oxycodone",
        "diazepam", "narcotic", "antibiotic mic", "ciprofloxacin",
        "tnt", "explosive", "estrogen detection", "steroid"
    ]),
    ("protein_assay", [
        "protein quantification", "bradford", "bca",
        "anthocyanin", "flavonoid", "ascorbic acid",
        "phenolic", "lipid peroxide", "dpph", "hydrogen peroxide",
        "total soluble sugar", "glucose", "lactate", "enzyme",
        "nadh", "glycosylation", "fucosylation", "proteomics",
        "maldi", "metabolomics", "mass spectrometry"
    ]),
    ("environmental_sensing_assay", [
        "aerosol", "air sampling", "water quality",
        "heavy metal", "particulate", "environmental",
        "desalination", "brine", "ion detection"
    ]),
    ("sample_preparation", [
        "extraction", "isolation", "purification",
        "lysis", "precipitation", "separation",
        "library preparation", "ngs", "rna extraction",
        "protein precipitation", "spe", "preconcentrator"
    ])
]


def clean_text(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r'\[cite:\s*\d+\]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def infer_category(desc_text: str) -> str:
    desc_lower = desc_text.lower()
    for cat_name, keywords in CATEGORY_RULES:
        if any(kw in desc_lower for kw in keywords):
            return cat_name
    return "general_assay"


def generate_notes(desc_text: str, platform: str, title: str, category: str, folder_name: str) -> str:
    text_clean = desc_text.replace('\r\n', '\n').replace('\r', '\n')

    # Extract assay target / name
    m_title = re.search(r'^(?:Title|Paper|ASSAY TYPE|Protocol)\s*:\s*(.+)$', text_clean, re.IGNORECASE | re.MULTILINE)
    if m_title:
        assay_name = clean_text(m_title.group(1).strip())
    elif title:
        assay_name = clean_text(title)
    else:
        assay_name = folder_name.replace('_', ' ')

    assay_name = assay_name.rstrip('.')

    # Platform phrasing
    if platform:
        plat_clean = clean_text(platform).rstrip(';,')
        plat_str = f"The assay is performed on a {plat_clean} platform."
    else:
        plat_str = "The assay is performed using an automated microfluidic setup."

    # Extract technical details: LOD / Readout / Reagents / Application
    m_lod = re.search(r'(?:LOD|limit of detection|sensitivity|detection limit)\s*(?:is|of|:)?\s*([^.\n]+)', text_clean, re.IGNORECASE)
    m_readout = re.search(r'(?:Readout|Detection modality|Readout modality|Detection method)\s*:\s*([^.\n]+)', text_clean, re.IGNORECASE)
    
    # Collect key reagents
    reagents = []
    for line in text_clean.splitlines():
        line_s = line.strip()
        if line_s.startswith('-') or line_s.startswith('*'):
            item = clean_text(line_s.lstrip('-* ').strip())
            if item and not item.startswith('http') and not item.startswith('cite:'):
                item_name = item.split('(')[0].split(';')[0].strip()
                if item_name and len(item_name) < 40:
                    reagents.append(item_name)

    if m_lod and len(m_lod.group(1).strip()) < 80:
        lod_val = clean_text(m_lod.group(1).strip()).rstrip('.')
        tech_str = f"It achieves a reported detection limit of {lod_val}."
    elif m_readout and len(m_readout.group(1).strip()) < 80:
        readout_val = clean_text(m_readout.group(1).strip()).rstrip('.')
        tech_str = f"Detection and quantification are carried out using {readout_val}."
    elif len(reagents) >= 2:
        tech_str = f"Key reagents used in the assay include {reagents[0]} and {reagents[1]}."
    elif len(reagents) == 1:
        tech_str = f"Key reaction components include {reagents[0]}."
    else:
        cat_display = category.replace('_', ' ')
        tech_str = f"The protocol enables reliable sample processing for {cat_display}."

    s1 = f"This protocol details {assay_name}."
    s2 = plat_str
    s3 = tech_str

    notes = f"{s1} {s2} {s3}"
    return notes


def fix_protocol(folder_path: Path) -> tuple[str, list[str]]:
    """
    Applies Fix A, Fix B, and Fix C to the folder's JSON file.
    Returns (status, applied_fixes)
    """
    folder_name = folder_path.name
    json_path = folder_path / f"{folder_name}.json"
    if not json_path.exists():
        # Look for case-insensitive match
        candidates = [f for f in folder_path.iterdir() if f.is_file() and f.name.lower() == f"{folder_name.lower()}.json"]
        if candidates:
            json_path = candidates[0]
        else:
            return "SKIPPED_NOT_V4", []

    try:
        with open(json_path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
    except Exception as e:
        return f"ERROR: Read failed: {e}", []

    if data.get("_schema") != "biogpt-v4":
        return "SKIPPED_NOT_V4", []

    applied_fixes = []

    # -------------------------------------------------------------
    # FIX A: CFG Terminal Node
    # -------------------------------------------------------------
    cfg = data.get("metadata", {}).get("cfg", {})
    edges = cfg.get("edges", [])
    source_nodes = {src for src, _ in edges}
    basic_blocks = cfg.get("basic_blocks", [])

    fix_a_changed = False
    for bb in basic_blocks:
        bb_id = bb.get("id")
        old_type = bb.get("type")
        if bb_id not in source_nodes:
            if old_type != "terminal":
                bb["type"] = "terminal"
                fix_a_changed = True
        # If in source_nodes, keep existing type as-is

    if fix_a_changed:
        applied_fixes.append("cfg:A")

    # -------------------------------------------------------------
    # FIX B: Category Re-inference
    # -------------------------------------------------------------
    desc_content = data.get("messages", [])[1].get("content", "")
    ident = data.get("metadata", {}).get("identity", {})
    old_category = ident.get("category")
    new_category = infer_category(desc_content)

    if new_category != old_category:
        ident["category"] = new_category
        applied_fixes.append("cat:B")

    # -------------------------------------------------------------
    # FIX C: Template Notes Rewrite
    # -------------------------------------------------------------
    old_notes = data.get("metadata", {}).get("notes", "")
    has_template = any(tp in old_notes for tp in TEMPLATE_PHRASES)

    if has_template:
        source_info = data.get("metadata", {}).get("source", {})
        platform = source_info.get("platform")
        title = source_info.get("title")
        new_notes = generate_notes(desc_content, platform, title, ident.get("category", new_category), folder_name)
        data["metadata"]["notes"] = new_notes
        applied_fixes.append("notes:C")

    # -------------------------------------------------------------
    # Validation and Serialization
    # -------------------------------------------------------------
    try:
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        _ = json.loads(json_str)
    except Exception as e:
        return f"ERROR: Invalid JSON generated: {e}", []

    # Write file if any fix was applied
    if applied_fixes:
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(json_str)
        except Exception as e:
            return f"ERROR: Write failed: {e}", []

    return "OK", applied_fixes


def main():
    if not DATASET_PATH.exists():
        print(f"Dataset path does not exist: {DATASET_PATH}")
        sys.exit(1)

    folders = sorted([f for f in DATASET_PATH.iterdir() if f.is_dir()], key=lambda p: p.name)

    count_fix_a = 0
    count_fix_b = 0
    count_fix_c = 0
    count_errors = 0
    count_skipped = 0

    empty_evidence_folders = []

    for folder in folders:
        status, fixes = fix_protocol(folder)
        fname = folder.name

        if status == "SKIPPED_NOT_V4":
            count_skipped += 1
            continue
        elif status.startswith("ERROR"):
            count_errors += 1
            print(f"✗ {fname} | {status}")
            continue

        # Check evidence for reminder
        jpath = folder / f"{folder.name}.json"
        try:
            with open(jpath, "r", encoding="utf-8") as f:
                d = json.load(f)
                ev = d.get("metadata", {}).get("evidence", {})
                if (not ev.get("chemical_evidence") and
                    not ev.get("operation_evidence") and
                    not ev.get("numeric_mismatches")):
                    empty_evidence_folders.append(fname)
        except Exception:
            pass

        if "cfg:A" in fixes:
            count_fix_a += 1
        if "cat:B" in fixes:
            count_fix_b += 1
        if "notes:C" in fixes:
            count_fix_c += 1

        if fixes:
            fixes_str = " ".join(fixes)
            print(f"✓ {fname} | {fixes_str}")
        else:
            print(f"✓ {fname} | clean")

    print("\n===== FIX COMPLETE =====")
    print(f"Fix A (cfg terminal) applied : {count_fix_a} files")
    print(f"Fix B (category)     applied : {count_fix_b} files")
    print(f"Fix C (notes)        applied : {count_fix_c} files")
    print(f"✗ Errors                     : {count_errors} files")
    print(f"Skipped (not biogpt-v4)      : {count_skipped} files")
    print()
    print(f"CHECK 8 REMINDER — these {len(empty_evidence_folders)} files have empty evidence arrays and require MANUAL human review to fill in:")
    print(empty_evidence_folders)


if __name__ == "__main__":
    main()
