#!/usr/bin/env python3
"""
process_biogpt_v4.py
====================
Batch processor for converting all protocol folders in OpenBioSet/Dataset
into the biogpt-v4 schema according to rigorous extraction rules.
"""

import os
import sys
import re
import json
from pathlib import Path

# Configure stdout encoding
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DATASET_PATH = Path(r"C:\Users\sayan\OpenBioSet\Dataset")

SYSTEM_PROMPT = (
    "You are BioGPT, an expert compiler architect. Translate the provided "
    "natural language biological protocol into valid, deterministic BioScript "
    "code for execution on a microfluidic biochip."
)

ALL_OP_KEYWORDS = [
    "dispense", "mix", "heat", "detect", "dispose", "drain",
    "repeat", "split", "gradient", "if"
]

COUNT_OP_KEYWORDS = [
    "dispense", "mix", "heat", "detect", "dispose", "drain",
    "split", "gradient"
]

VALID_CATEGORIES = [
    "environmental_sensing_assay",
    "clinical_diagnostic",
    "nucleic_acid_amplification",
    "immunoassay",
    "sample_preparation",
    "cell_based",
    "synthetic_biology",
    "drug_detection",
    "protein_assay",
    "general_assay",
]


def clean_citations(text: str) -> str:
    """Removes citation markers like [cite: 58] from text."""
    if not text:
        return text
    cleaned = re.sub(r'\[cite:\s*\d+\]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def extract_source_and_metadata_from_desc(desc_raw: str, folder_name: str):
    """
    Extracts source fields, category, and notes from description.txt.
    """
    text_clean = desc_raw.replace('\r\n', '\n').replace('\r', '\n')
    lines = [l.strip() for l in text_clean.splitlines() if l.strip()]

    # 1. Title
    title = None
    m_title = re.search(r'^(?:Title|Paper|ASSAY TYPE|Protocol)\s*:\s*(.+)$', text_clean, re.IGNORECASE | re.MULTILINE)
    if m_title:
        title = clean_citations(m_title.group(1).strip())
    else:
        for l in lines:
            if l.startswith('```') or set(l) <= {'=', '-', '#'}:
                continue
            if l.lower().startswith('protocol description'):
                continue
            if ':' in l:
                k = l.split(':', 1)[0].strip().lower()
                if k in ['source link', 'link', 'url', 'paper doi', 'doi', 'journal', 'publisher', 'platform', 'institution']:
                    continue
            title = clean_citations(l)
            break
    if title:
        title = title.strip().strip('"').strip("'")
        if title.startswith('```'):
            title = title.lstrip('`').strip()

    # 2. Publisher
    publisher = None
    m_pub = re.search(r'^(?:Journal|Published in|Conference|Publisher)\s*:\s*(.+)$', text_clean, re.IGNORECASE | re.MULTILINE)
    if m_pub:
        publisher = clean_citations(m_pub.group(1).strip())
        if publisher:
            publisher = publisher.strip('"').strip("'")

    # 3. DOI
    doi = None
    m_doi = re.search(r'(?:Paper\s+)?DOI\s*:\s*(?:https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/[^\s\]\)\>]+)', text_clean, re.IGNORECASE)
    if not m_doi:
        m_doi = re.search(r'\b(10\.\d{4,9}/[^\s\]\)\>]+)', text_clean)
    if m_doi:
        doi = clean_citations(m_doi.group(1).strip().rstrip('.,;)'))
        if doi.startswith('http'):
            doi = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', doi)

    # 4. URL
    url = None
    m_url = re.search(r'(?:Source\s+Link|Link|URL)\s*:\s*(https?://[^\s\]\)\>]+)', text_clean, re.IGNORECASE)
    if not m_url:
        m_url = re.search(r'(https?://[^\s\]\)\>]+)', text_clean)
    if m_url:
        url = clean_citations(m_url.group(1).strip().rstrip('.,;)'))

    # 5. Platform
    platform = None
    m_plat = re.search(r'^(?:Platform|Instrument|Device|Chip)\s*:\s*(.+)$', text_clean, re.IGNORECASE | re.MULTILINE)
    if m_plat:
        platform = clean_citations(m_plat.group(1).strip())
    else:
        lower = text_clean.lower()
        if any(w in lower for w in ['digital microfluidic', 'dmf', 'electrowetting', 'ewod']):
            platform = "Digital Microfluidics (DMF)"
        elif any(w in lower for w in ['ddpcr', 'droplet digital pcr', 'qx200']):
            platform = "Bio-Rad QX200 ddPCR"
        elif any(w in lower for w in ['opentrons', 'ot-2']):
            platform = "OpenTrons OT-2"
        elif any(w in lower for w in ['qpcr', 'rt-pcr', 'thermocycler', 'real-time pcr', 'taqman', 'pcr']):
            platform = "qPCR Thermocycler"
        elif any(w in lower for w in ['elisa', 'plate reader', 'microplate', 'microwell', 'absorbance']):
            platform = "Microwell Plate Reader"
        else:
            platform = None

    # 6. Category
    lower = text_clean.lower()
    if any(k in lower for k in ['elisa', 'immunoassay', 'antibody', 'tsh', 'antigen', 'igg', 'igm', 'flisa', 'sandwich immunoassay', 'competitive elisa']):
        category = "immunoassay"
    elif any(k in lower for k in ['pcr', 'qpcr', 'ddpcr', 'rt-pcr', 'lamp', 'amplification', 'rca', 'nasba', 'reverse transcription']):
        category = "nucleic_acid_amplification"
    elif any(k in lower for k in ['cell viability', 'apoptosis', 'caspase', 'cytotoxicity', 'cell culture', 'single cell', 'mammalian cell', 'live/dead']):
        category = "cell_based"
    elif any(k in lower for k in ['blood typing', 'hemagglutination', 'clinical', 'septic shock', 'saliva detection', 'pathogen detection', 'biomarker']):
        category = "clinical_diagnostic"
    elif any(k in lower for k in ['dna extraction', 'rna isolation', 'sample prep', 'purification', 'alkaline lysis', 'depletion', 'extraction', 'isolation']):
        category = "sample_preparation"
    elif any(k in lower for k in ['crispr', 'gene circuit', 'synthetic biology', 'recombineering', 'mage', 'cas9', 'cas12', 'cas13', 'carmen']):
        category = "synthetic_biology"
    elif any(k in lower for k in ['drug', 'toxin', 'narcotic', 'antibiotic', 'ciprofloxacin', 'cocaine', 'morphine', 'sorafenib', 'staurosporine']):
        category = "drug_detection"
    elif any(k in lower for k in ['protein quantification', 'western blot', 'bradford', 'bca', 'anthocyanin', 'flavonoid', 'ascorbic acid', 'enzyme assay', 'glucose']):
        category = "protein_assay"
    elif any(k in lower for k in ['water', 'soil', 'air', 'environmental', 'aerosol', 'heavy metal', 'particulate', 'airborne']):
        category = "environmental_sensing_assay"
    else:
        category = "general_assay"

    # 7. Notes (2-3 sentences plain English summary)
    target_summary = title if title else folder_name.replace('_', ' ')
    plat_str = f"on a {platform} system" if platform else "in an automated microfluidic setup"
    
    m_obj = re.search(r'^(?:Objective|Goal|Summary|Purpose|ASSAY TYPE)\s*:\s*(.+)$', text_clean, re.IGNORECASE | re.MULTILINE)
    if m_obj and m_obj.group(1).strip() != title:
        obj_text = clean_citations(m_obj.group(1).strip()).rstrip('.')
        sentence_1 = f"This protocol describes {target_summary} designed for {category.replace('_', ' ')} applications."
        sentence_2 = f"It focuses on {obj_text}."
        sentence_3 = f"The assay operations and liquid handling are executed {plat_str}."
        notes = f"{sentence_1} {sentence_2} {sentence_3}"
    else:
        sentence_1 = f"This protocol implements an automated workflow for {target_summary}."
        sentence_2 = f"It provides quantitative measurement and sample handling categorized under {category.replace('_', ' ')}."
        sentence_3 = f"All operational steps are conducted {plat_str}."
        notes = f"{sentence_1} {sentence_2} {sentence_3}"

    return {
        "title": title,
        "publisher": publisher,
        "doi": doi,
        "url": url,
        "platform": platform,
        "category": category,
        "notes": notes
    }


def parse_bs_file(bs_raw: str) -> dict:
    """
    Extracts manifests, operations, complexity flags, and num_steps from BioScript text.
    """
    manifests = []
    step_count = 0

    for line in bs_raw.splitlines():
        line_s = line.strip()
        if not line_s or line_s.startswith('//') or line_s.startswith('#'):
            continue
        
        # Manifests
        m_man = re.search(r'\bmanifest\s+([A-Za-z0-9_]+)', line_s)
        if m_man:
            manifests.append(m_man.group(1))
            continue

        if line_s.startswith('module'):
            continue

        # Check if line contains any operation keyword
        if any(re.search(r'\b' + kw + r'\b', line_s) for kw in COUNT_OP_KEYWORDS):
            step_count += 1

    # Operations present in entire file
    operations = []
    for kw in ALL_OP_KEYWORDS:
        if re.search(r'\b' + kw + r'\b', bs_raw):
            operations.append(kw)

    has_repeat = bool(re.search(r'\brepeat\b', bs_raw))
    has_branch = bool(re.search(r'\bif\b', bs_raw))
    has_split = bool(re.search(r'\bsplit\b', bs_raw))
    has_gradient = bool(re.search(r'\bgradient\b', bs_raw))

    return {
        "manifests": manifests,
        "operations": operations,
        "complexity": {
            "has_repeat": has_repeat,
            "has_branch": has_branch,
            "has_split": has_split,
            "has_gradient": has_gradient,
            "num_steps": step_count
        }
    }


def parse_dot_file(dot_raw: str) -> tuple[list, list]:
    """
    Parses output.dot into basic_blocks and edges.
    """
    if not dot_raw or not dot_raw.strip():
        return [], []

    edges = []
    for line in dot_raw.splitlines():
        line_s = line.strip()
        if not line_s:
            continue
        edge_m = re.search(r'([A-Za-z0-9_]+)\s*->\s*([A-Za-z0-9_]+)', line_s)
        if edge_m:
            edges.append([edge_m.group(1), edge_m.group(2)])

    sources_set = {src for src, _ in edges}

    raw_nodes = []
    for line in dot_raw.splitlines():
        line_s = line.strip()
        if not line_s or line_s.startswith('strict digraph') or line_s.startswith('digraph') or line_s == '}':
            continue
        if '->' in line_s:
            continue

        node_m = re.match(r'^([A-Za-z0-9_]+)(?:\s*\[(.*)\])?\s*;?$', line_s)
        if node_m:
            nid = node_m.group(1)
            attr_str = node_m.group(2) or ''
            
            lbl_m = re.search(r'label\s*=\s*"([^"]*)"', attr_str)
            if not lbl_m:
                lbl_m = re.search(r'label\s*=\s*([^,\]\s]+)', attr_str)
            label = lbl_m.group(1) if lbl_m else nid
            raw_nodes.append((nid, label))

    basic_blocks = []
    for idx, (nid, label) in enumerate(raw_nodes):
        lbl_lower = label.lower()
        if 'main' in lbl_lower or idx == 0:
            ntype = "entry"
        elif '_t' in nid or '_t' in label:
            ntype = "branch_true"
        elif '_f' in nid or '_f' in label:
            ntype = "branch_false"
        elif '_j' in nid or '_j' in label:
            ntype = "join"
        elif (nid not in sources_set) or ('exit' in lbl_lower) or ('end' in lbl_lower):
            ntype = "terminal"
        else:
            ntype = "sequential"

        basic_blocks.append({
            "id": nid,
            "label": label,
            "type": ntype
        })

    return basic_blocks, edges


def extract_existing_json_fields(existing_data: dict, folder_name: str) -> dict:
    """
    Extracts and preserves identity, evidence, and validation fields from existing JSON.
    """
    meta = existing_data.get("metadata", {})
    if not isinstance(meta, dict):
        meta = {}
    
    ident = meta.get("identity", existing_data.get("identity", {}))
    if not isinstance(ident, dict):
        ident = {}

    prot = existing_data.get("protocol", {})
    if not isinstance(prot, dict):
        prot = {}

    # identity.protocol_id
    protocol_id = (
        ident.get("protocol_id")
        or meta.get("protocol_id")
        or existing_data.get("protocol_id")
        or prot.get("protocol_id")
        or prot.get("metadata", {}).get("protocol_id")
    )
    if not protocol_id:
        protocol_id = folder_name.lower().replace(" ", "_").replace("-", "_") + "_001"

    # identity.protocol_name
    protocol_name = (
        ident.get("protocol_name")
        or meta.get("protocol_name")
        or existing_data.get("protocol_name")
        or prot.get("protocol_name")
        or prot.get("metadata", {}).get("protocol_name")
        or prot.get("name")
        or prot.get("title")
    )
    if not protocol_name:
        protocol_name = folder_name

    # identity.adaptation_status
    adaptation_status = (
        ident.get("adaptation_status")
        or meta.get("adaptation_status")
        or existing_data.get("adaptation_status")
        or prot.get("adaptation_status")
        or prot.get("metadata", {}).get("adaptation_status")
        or "adapted_authored"
    )

    # identity.authored_by
    authored_by = (
        ident.get("authored_by")
        or meta.get("authored_by")
        or existing_data.get("authored_by")
        or prot.get("authored_by")
        or None
    )

    # evidence
    ev = meta.get("evidence", existing_data.get("evidence", {}))
    if not isinstance(ev, dict):
        ev = {}
    chemical_evidence = ev.get("chemical_evidence", [])
    operation_evidence = ev.get("operation_evidence", [])
    numeric_mismatches = ev.get("numeric_mismatches", [])

    # validation block
    val = meta.get("validation", existing_data.get("validation", {}))
    if not isinstance(val, dict):
        val = {}
    validated = val.get("validated", meta.get("validated", existing_data.get("validated", False)))
    validation_score = val.get("validation_score", meta.get("validation_score", existing_data.get("validation_score", 0.0)))
    validation_status = val.get("validation_status", meta.get("validation_status", existing_data.get("validation_status", "pending_v2")))

    return {
        "protocol_id": protocol_id,
        "protocol_name": protocol_name,
        "adaptation_status": adaptation_status,
        "authored_by": authored_by,
        "chemical_evidence": chemical_evidence,
        "operation_evidence": operation_evidence,
        "numeric_mismatches": numeric_mismatches,
        "validation": {
            "validated": validated,
            "validation_score": validation_score,
            "validation_status": validation_status
        }
    }


def process_folder(folder_path: Path, current_idx: int, total_count: int) -> tuple[str, str, str]:
    """
    Processes a single protocol folder.
    Returns (status, folder_name, message)
      status: 'DONE', 'SKIPPED', 'ERROR'
    """
    folder_name = folder_path.name

    # Step 2: Check required files
    desc_file = folder_path / "description.txt"
    ir_file = folder_path / "output.ir"
    dot_file = folder_path / "output.dot"

    # Case-insensitive match for .bs and .json
    all_files = list(folder_path.iterdir())
    bs_candidates = [f for f in all_files if f.is_file() and f.name.lower() == f"{folder_name.lower()}.bs"]
    json_candidates = [f for f in all_files if f.is_file() and f.name.lower() == f"{folder_name.lower()}.json"]

    missing = []
    if not desc_file.exists():
        missing.append("description.txt")
    if not bs_candidates:
        missing.append(f"{folder_name}.bs")
    if not json_candidates:
        missing.append(f"{folder_name}.json")
    if not ir_file.exists():
        missing.append("output.ir")
    if not dot_file.exists():
        missing.append("output.dot")

    if missing:
        missing_str = ", ".join(missing)
        print(f"⚠ Skipped {folder_name} - missing: {missing_str}")
        return "SKIPPED", folder_name, f"missing: {missing_str}"

    bs_file = bs_candidates[0]
    json_file = json_candidates[0]

    # Step 3: Read all 5 files fully
    try:
        with open(desc_file, "r", encoding="utf-8", errors="ignore") as f:
            desc_content = f.read()
        with open(bs_file, "r", encoding="utf-8", errors="ignore") as f:
            bs_content = f.read()
        with open(ir_file, "r", encoding="utf-8", errors="ignore") as f:
            ir_content = f.read()
        with open(dot_file, "r", encoding="utf-8", errors="ignore") as f:
            dot_content = f.read()
        with open(json_file, "r", encoding="utf-8", errors="ignore") as f:
            existing_json = json.load(f)
    except Exception as e:
        print(f"✗ ERROR {folder_name} - read failure: {e}")
        return "ERROR", folder_name, f"read failure: {e}"

    # Extract components
    source_meta = extract_source_and_metadata_from_desc(desc_content, folder_name)
    bs_meta = parse_bs_file(bs_content)
    basic_blocks, edges = parse_dot_file(dot_content)
    existing_meta = extract_existing_json_fields(existing_json, folder_name)

    # Step 4: Assemble biogpt-v4 JSON
    output_dict = {
        "_schema": "biogpt-v4",
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": desc_content
            },
            {
                "role": "assistant",
                "content": bs_content
            }
        ],
        "metadata": {
            "identity": {
                "protocol_id": existing_meta["protocol_id"],
                "protocol_name": existing_meta["protocol_name"],
                "category": source_meta["category"],
                "adaptation_status": existing_meta["adaptation_status"],
                "authored_by": existing_meta["authored_by"]
            },
            "source": {
                "title": source_meta["title"],
                "publisher": source_meta["publisher"],
                "doi": source_meta["doi"],
                "url": source_meta["url"],
                "platform": source_meta["platform"]
            },
            "bioscript": {
                "manifests": bs_meta["manifests"],
                "operations": bs_meta["operations"],
                "complexity": bs_meta["complexity"]
            },
            "cfg": {
                "basic_blocks": basic_blocks,
                "edges": edges
            },
            "ir": {
                "content": ir_content
            },
            "validation": existing_meta["validation"],
            "evidence": {
                "chemical_evidence": existing_meta["chemical_evidence"],
                "operation_evidence": existing_meta["operation_evidence"],
                "numeric_mismatches": existing_meta["numeric_mismatches"]
            },
            "notes": source_meta["notes"]
        }
    }

    # Validate JSON serializability before writing
    try:
        json_str = json.dumps(output_dict, indent=2, ensure_ascii=False)
        _ = json.loads(json_str)
    except Exception as e:
        print(f"✗ ERROR {folder_name} - invalid JSON: {e}")
        return "ERROR", folder_name, f"invalid JSON: {e}"

    # Write output to the exact original JSON path
    try:
        with open(json_file, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"✓ Done {folder_name} ({current_idx}/{total_count})")
        return "DONE", folder_name, "success"
    except Exception as e:
        print(f"✗ ERROR {folder_name} - write failure: {e}")
        return "ERROR", folder_name, f"write failure: {e}"


def main():
    if not DATASET_PATH.exists():
        print(f"Dataset path does not exist: {DATASET_PATH}")
        sys.exit(1)

    # Step 1: Scan and sort all subfolders
    all_subfolders = sorted([f for f in DATASET_PATH.iterdir() if f.is_dir()], key=lambda p: p.name)
    total_count = len(all_subfolders)

    processed_count = 0
    skipped_count = 0
    error_count = 0
    skipped_folders = []
    error_folders = []

    for idx, folder_path in enumerate(all_subfolders, start=1):
        status, fname, msg = process_folder(folder_path, idx, total_count)
        if status == "DONE":
            processed_count += 1
        elif status == "SKIPPED":
            skipped_count += 1
            skipped_folders.append(fname)
        elif status == "ERROR":
            error_count += 1
            error_folders.append(fname)

    # Step 6: Final Summary
    print("\n===== COMPLETE =====")
    print(f"✓ Processed : {processed_count}")
    print(f"⚠ Skipped   : {skipped_count}")
    print(f"✗ Errors    : {error_count}")
    print(f"Skipped folders : {skipped_folders}")
    print(f"Error folders   : {error_folders}")


if __name__ == "__main__":
    main()
