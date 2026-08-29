#!/usr/bin/env python3
"""
audit_diagnostic.py
===================
Runs all 10 diagnostic checks on biogpt-v4 .json files across all 200 subfolders in
C:\\Users\\sayan\\OpenBioSet\\Dataset without making any file modifications.
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

COUNT_OP_KEYWORDS = ['dispense', 'mix', 'heat', 'detect', 'dispose', 'drain', 'split', 'gradient']
TEMPLATE_PHRASES = [
    "This protocol implements an automated workflow for",
    "It provides quantitative measurement and sample handling",
    "All operational steps are conducted on"
]

def main():
    if not DATASET_PATH.exists():
        print(f"Dataset path does not exist: {DATASET_PATH}")
        sys.exit(1)

    folders = sorted([f for f in DATASET_PATH.iterdir() if f.is_dir()], key=lambda p: p.name)

    results = {
        'check1': [],
        'check2': [],
        'check3': [],
        'check4': [],
        'check5': [],
        'check6': [],
        'check7': [],
        'check8': [],
        'check9': [],
        'check10': []
    }

    scanned_count = 0

    for folder in folders:
        jpath = folder / f"{folder.name}.json"
        if not jpath.exists():
            continue
        try:
            with open(jpath, 'r', encoding='utf-8') as f:
                d = json.load(f)
        except Exception:
            continue

        if d.get('_schema') != 'biogpt-v4':
            continue

        scanned_count += 1
        fname = folder.name
        msgs = d.get('messages', [])
        desc = msgs[1].get('content', '') if len(msgs) > 1 else ''
        bs = msgs[2].get('content', '') if len(msgs) > 2 else ''
        meta = d.get('metadata', {})
        bio = meta.get('bioscript', {})
        comp = bio.get('complexity', {})
        ident = meta.get('identity', {})
        source = meta.get('source', {})
        cfg = meta.get('cfg', {})
        ev = meta.get('evidence', {})
        notes = meta.get('notes', '')

        # -------------------------------------------------------------
        # CHECK 1: has_branch correctness
        # -------------------------------------------------------------
        has_if = bool(re.search(r'\bif\b', bs))
        stored_if = comp.get('has_branch')
        if has_if != stored_if:
            results['check1'].append(f"{fname} : has_branch stored={stored_if} but \"if\" {'found' if has_if else 'not found'} in .bs")

        # -------------------------------------------------------------
        # CHECK 2: has_repeat correctness
        # -------------------------------------------------------------
        has_rep = bool(re.search(r'\brepeat\b', bs))
        stored_rep = comp.get('has_repeat')
        if has_rep != stored_rep:
            results['check2'].append(f"{fname} : has_repeat stored={stored_rep} but \"repeat\" {'found' if has_rep else 'not found'} in .bs")

        # -------------------------------------------------------------
        # CHECK 3: has_split correctness
        # -------------------------------------------------------------
        has_sp = bool(re.search(r'\bsplit\b', bs))
        stored_sp = comp.get('has_split')
        if has_sp != stored_sp:
            results['check3'].append(f"{fname} : has_split stored={stored_sp} but \"split\" {'found' if has_sp else 'not found'} in .bs")

        # -------------------------------------------------------------
        # CHECK 4: has_gradient correctness
        # -------------------------------------------------------------
        has_gr = bool(re.search(r'\bgradient\b', bs))
        stored_gr = comp.get('has_gradient')
        if has_gr != stored_gr:
            results['check4'].append(f"{fname} : has_gradient stored={stored_gr} but \"gradient\" {'found' if has_gr else 'not found'} in .bs")

        # -------------------------------------------------------------
        # CHECK 5: num_steps correctness
        # -------------------------------------------------------------
        step_count = 0
        for line in bs.splitlines():
            line_s = line.strip()
            if not line_s or line_s.startswith('//') or line_s.startswith('#') or line_s.startswith('manifest') or line_s.startswith('module'):
                continue
            if line_s in ['repeat', 'if', 'else', '{', '}', '{}']:
                continue
            if any(re.search(r'\b' + kw + r'\b', line_s) for kw in COUNT_OP_KEYWORDS):
                step_count += 1
        stored_steps = comp.get('num_steps')
        if step_count != stored_steps:
            results['check5'].append(f"{fname} : stored={stored_steps} actual={step_count}")

        # -------------------------------------------------------------
        # CHECK 6: generic template notes
        # -------------------------------------------------------------
        found_templates = [tp for tp in TEMPLATE_PHRASES if tp in notes]
        if found_templates:
            results['check6'].append(f"{fname} : notes contains template phrase")

        # -------------------------------------------------------------
        # CHECK 7: category correctness
        # -------------------------------------------------------------
        cat = ident.get('category')
        desc_lower = desc.lower()

        # Check explicit rules
        if any(k in desc_lower for k in ['g6pd', 'blood disorder', 'hemoglobin', 'neonatal screening', 'rbc', 'sickle cell', 'thalassemia']):
            if cat != 'clinical_diagnostic':
                results['check7'].append(f"{fname} : category is \"{cat}\" (description indicates clinical_diagnostic)")
        elif any(k in desc_lower for k in ['elisa', 'antibody', 'antigen', 'tsh', 'igg']) and not any(k in desc_lower for k in ['crispr', 'cas9', 'cas12', 'cas13', 'recombineering']):
            if cat not in ['immunoassay', 'clinical_diagnostic']:
                results['check7'].append(f"{fname} : category is \"{cat}\" (description indicates immunoassay)")
        elif any(k in desc_lower for k in ['pcr', 'qpcr', 'ddpcr', 'lamp', 'amplification']) and not any(k in desc_lower for k in ['crispr', 'cas9', 'cas12', 'cas13', 'recombineering']):
            if cat not in ['nucleic_acid_amplification', 'clinical_diagnostic']:
                results['check7'].append(f"{fname} : category is \"{cat}\" (description indicates nucleic_acid_amplification)")
        elif any(k in desc_lower for k in ['apoptosis', 'caspase', 'cell viability', 'cytotoxicity']):
            if cat != 'cell_based':
                results['check7'].append(f"{fname} : category is \"{cat}\" (description indicates cell_based)")
        elif any(k in desc_lower for k in ['water', 'aerosol', 'air', 'environmental', 'heavy metal', 'particulate']):
            if cat != 'environmental_sensing_assay':
                results['check7'].append(f"{fname} : category is \"{cat}\" (description indicates environmental_sensing_assay)")

        # -------------------------------------------------------------
        # CHECK 8: all evidence arrays empty
        # -------------------------------------------------------------
        chem_ev = ev.get('chemical_evidence', [])
        op_ev = ev.get('operation_evidence', [])
        num_mis = ev.get('numeric_mismatches', [])
        if len(chem_ev) == 0 and len(op_ev) == 0 and len(num_mis) == 0:
            results['check8'].append(f"{fname} : all three evidence arrays are empty []")

        # -------------------------------------------------------------
        # CHECK 9: all source fields null
        # -------------------------------------------------------------
        st = source.get('title')
        sp = source.get('publisher')
        sd = source.get('doi')
        su = source.get('url')
        if st is None and sp is None and sd is None and su is None:
            results['check9'].append(f"{fname} : title, publisher, doi, and url are all null")

        # -------------------------------------------------------------
        # CHECK 10: cfg terminal node correctness
        # -------------------------------------------------------------
        edges = cfg.get('edges', [])
        source_nodes = {src for src, _ in edges}
        basic_blocks = cfg.get('basic_blocks', [])
        for bb in basic_blocks:
            bb_id = bb.get('id')
            bb_type = bb.get('type')
            has_outgoing = bb_id in source_nodes
            if not has_outgoing and bb_type != 'terminal':
                results['check10'].append(f"{fname} : node \"{bb_id}\" has no outgoing edges but type is \"{bb_type}\" (expected terminal)")
            elif has_outgoing and bb_type == 'terminal':
                results['check10'].append(f"{fname} : node \"{bb_id}\" has outgoing edges but type is \"terminal\"")

    print(f"Scanned {scanned_count} biogpt-v4 files.\n")
    print("===== DIAGNOSTIC REPORT =====\n")
    print(f"CHECK 1 - has_branch mismatches     : {len(results['check1'])}")
    print(f"CHECK 2 - has_repeat mismatches     : {len(results['check2'])}")
    print(f"CHECK 3 - has_split mismatches      : {len(results['check3'])}")
    print(f"CHECK 4 - has_gradient mismatches   : {len(results['check4'])}")
    print(f"CHECK 5 - num_steps mismatches      : {len(results['check5'])}")
    print(f"CHECK 6 - generic template notes    : {len(results['check6'])}")
    print(f"CHECK 7 - category mismatches       : {len(results['check7'])}")
    print(f"CHECK 8 - all evidence empty        : {len(results['check8'])}")
    print(f"CHECK 9 - all source fields null    : {len(results['check9'])}")
    print(f"CHECK 10 - cfg terminal wrong       : {len(results['check10'])}")
    print()

    check_titles = {
        'check1': 'CHECK 1 DETAIL (has_branch mismatches):',
        'check2': 'CHECK 2 DETAIL (has_repeat mismatches):',
        'check3': 'CHECK 3 DETAIL (has_split mismatches):',
        'check4': 'CHECK 4 DETAIL (has_gradient mismatches):',
        'check5': 'CHECK 5 DETAIL (num_steps mismatches):',
        'check6': 'CHECK 6 DETAIL (generic template notes):',
        'check7': 'CHECK 7 DETAIL (category mismatches):',
        'check8': 'CHECK 8 DETAIL (all evidence empty):',
        'check9': 'CHECK 9 DETAIL (all source fields null):',
        'check10': 'CHECK 10 DETAIL (cfg terminal wrong):'
    }

    for k in range(1, 11):
        ck = f"check{k}"
        items = results[ck]
        if items:
            print(f"{check_titles[ck]}")
            for item in items:
                print(f"  {item}")
            print()

if __name__ == '__main__':
    main()
