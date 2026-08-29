#!/usr/bin/env python3
"""
fill_evidence.py
================
Extracts chemical_evidence, operation_evidence, and numeric_mismatches
strictly from within each JSON file (messages[1].content and messages[2].content)
for the 109 targeted protocols.
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

TARGET_FOLDERS = {
    "ACE_Crispr_RAF1_Sorafenib", "AU_Shih_Wheeler_Bay_Microbioreactor",
    "Ahmadi2019_id2m", "Ahmadi_ML_DMF_18FFDG_ofat", "Competitive_elisa",
    "DMF_Ribozyme_Cleavage", "Direct_elisa", "FDG_Radiosynthesis_ofat",
    "Fucosylation_Inhibition_DMF", "Heroin", "Husser_AIMS_Induction_BGL_SynBio",
    "Indirect_elisa", "Jebrail_DMF_Proteomic_Processing",
    "Leal_Alves_Multiplex_Sorter_Strain_Development", "Lengen_Lentiviral",
    "Maximize_Diagnostic_Tests", "Microbial_Electroporation",
    "Moazami_World_to_Chip_DMF", "NADH_Oxidoreductase", "PCR",
    "Particle_Based_Immunoassays", "Samlali_Hybrid_Microfluidics_Isoclone",
    "Sandwich_elisa", "Shih_Algae_Lipid_DMF_Screen", "Shih_DBS_DMF_Nesi_MS",
    "Shih_DMF_Cell_Impedance_Sensing", "Shih_Versatile_DMF_Synbio",
    "TriDrop_Electroporation", "Tridrop_Transfection",
    "abasiyanik2021_sars_cov2_saliva_detection",
    "abasiyanik_dpla_ddpcr_septic_shock", "ahmadi_2024_mab_discovery",
    "albayrak_digital_pla_rtddpcr", "bell_sperm_seq_library_generation",
    "chen_concentrator_droplet_mmp_assay", "choi_dmf_tsh_immunoassay",
    "clelland_pcr_ddpcr", "deng2025_d2_droplet_digital_recovery",
    "dettinger_2018_lsim_single_cell", "droplet_volume_measurement_beads",
    "fobel_paper_dmf_digital_microfluidics", "fuller_droplet_on_tape_dot",
    "heinemann_uNIMS_enzyme_screening", "hou_2015_dff_bacteremia",
    "hou_margination_pathogen_removal_blood",
    "jebrail_combinatorial_peptidomimetics_dmf",
    "jebrail_dmf_evaporation_mgmt", "jebrail_dmf_protein_precipitation",
    "jebrail_macrocycle_dmf", "jebrail_world_to_dmf_rna_extraction",
    "junkin_single_cell_immune_dynamics", "junkin_tay_singlecell_immune",
    "kellogg_microfluidic_singlecell_pipeline",
    "kellogg_nfkb_digital_signaling", "kellogg_nfkb_tlr_nonintegrative",
    "khoo_ctc_liquid_biopsy_drug_screening", "khoo_ctc_microfluidic_cluster",
    "kim2013_ngs_library_prep_dmf", "kim_icp_multistage_brine_desalination",
    "kim_immunomodulator_hts",
    "ko_multiplexed_nanofluidic_concentration_immunoassay",
    "kwak_icp_continuous_flow_concentrator",
    "kwon_microfluidic_cell_retention_perfusion",
    "lafreniere_attractive_design_dmf_spe",
    "lee_nafion_proteomic_preconcentrator",
    "lin2019_udpla_single_cell_protein_mrna",
    "matthews_organoid_organoid_id", "mei_dmf_plasma_protein_depletion",
    "mercadovasquez_ultrashort_macrophage_nfkb", "miller_dmf_immunoassay",
    "mousa_dmf_estrogen_extraction", "ng2012_dmf_immunoassay",
    "ng2015_DISC_dmf", "ng2015_dmf_rubella_immunoassay",
    "ng_dmf_immunoassay_disc", "northen_nims_mass_spectrometry",
    "patel_dropgenie_dmf_crispr_screen", "phan_fdseq_pfa_scrna",
    "ramshani_ev_mirna_integrated_microfluidics",
    "sarkar_microfluidic_probe_singlecell_analysis",
    "schuster_organoid_drug_screening",
    "schwarz_chemokine_migration_microfluidics", "shamsi_dmf_ecl_mirna",
    "smitha_pillai_scadpl_breast_cancer", "son2023_coculture_spatiotemporal",
    "son_nfkb_dose_differentiation", "son_nfkb_stimulus_dynamics",
    "son_spatiotemporal_nfkb_microfluidics", "tay_nfkb_signaling_dynamic_range",
    "vc0005_aav_ddpcr_quantification", "venturelli_gut_microbiome_glv",
    "vistain_proxseq_10x", "vistain_proxseq_nature_methods_2022",
    "wang2025_macrophage_memory", "wang_2d_ief_cge_protein_separation",
    "wang_nfkb_sequential_stimulation", "wang_sproxseq_germinal_center",
    "warkiani_malaria_inertial_microfluidics",
    "warkiani_membraneless_microfiltration", "warkiani_spiral_ctc_enrichment",
    "warkiani_spiral_ctc_isolation", "watson_multilayer_hybrid_microfluidics_dmf",
    "watterson_anaerobic_droplet_cultivation",
    "watterson_anaerobic_droplet_gut_microbiome",
    "xia_proxseq_computational_prediction", "xie_droplet_paired_tag",
    "yang_2011_dmf_spe_ppm", "yin2020_denv_multiplexed_pcr",
    "zhou_mcf7_deformability_impedance"
}

OP_MAPPINGS = {
    "dispense": ["dispense", "add", "pipette", "aliquot", "load", "apply"],
    "mix": ["mix", "merge", "combine", "shuttle", "vortex", "resuspend"],
    "heat": ["incubate", "heat", "warm", "anneal", "thermocycle", "cool", "temperature", "deg c", "°c", "c for"],
    "detect": ["detect", "measure", "read", "absorbance", "fluorescence", "signal", "readout", "imaging"],
    "dispose": ["dispose", "discard", "waste", "remove", "wash out"],
    "drain": ["drain", "aspirate", "remove supernatant", "suction"],
    "repeat": ["repeat", "cycle", "again", "iterative", "multiple times", "times"],
    "if": ["if", "when", "threshold", "condition", "gate", "above lod", "below lod", "positive", "negative"],
    "split": ["split", "divide", "partition", "branch", "distribute"],
    "gradient": ["gradient", "concentration series", "dose-response", "serial dilution", "dilution series", "titration"]
}


def parse_sections(desc_text: str) -> list[tuple[str, str, int, int]]:
    """
    Parses description text into a list of (section_header, text, start_pos, end_pos).
    """
    lines = desc_text.splitlines()
    sections = []
    current_header = "description.txt"
    current_lines = []

    header_pattern = re.compile(r'^(?:[A-Z0-9_\s\-/]{3,40}:|={3,}|#{1,4}\s+[A-Z0-9_\s\-/]+|[A-Z\s]{4,30}$)')

    for line in lines:
        line_s = line.strip()
        # Check if line looks like a header
        if (line_s.endswith(':') and len(line_s) < 50 and not line_s.lower().startswith('http')) or \
           (line_s.isupper() and len(line_s) > 3 and len(line_s) < 40 and not line_s.startswith('-')):
            if current_lines:
                sections.append((current_header, "\n".join(current_lines)))
                current_lines = []
            current_header = f"description.txt: {line_s.rstrip(':').strip()}"
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_header, "\n".join(current_lines)))

    return sections if sections else [("description.txt", desc_text)]


def get_section_for_quote(quote: str, desc_text: str) -> str:
    sections = parse_sections(desc_text)
    for header, sec_text in sections:
        if quote in sec_text:
            return header
    return "description.txt"


def truncate_to_30_words(quote: str) -> str:
    words = quote.split()
    if len(words) <= 30:
        return quote.strip()
    # Try finding the primary clause
    clauses = re.split(r'[,;:]', quote)
    for c in clauses:
        c_words = c.split()
        if 3 <= len(c_words) <= 30:
            return c.strip()
    return " ".join(words[:30]).strip()


def extract_chemical_evidence(manifests: list[str], desc_text: str) -> list[dict]:
    evidence = []
    
    # Pre-split description into candidate sentences/lines
    sentences = []
    for line in desc_text.splitlines():
        line_s = line.strip()
        if not line_s or line_s.startswith('```') or set(line_s) <= {'=', '-', '#'}:
            continue
        # Split line into sentences if punctuation exists
        s_list = re.split(r'(?<=[.!?])\s+', line_s)
        for s in s_list:
            if s.strip():
                sentences.append(s.strip())

    for manifest in manifests:
        manifest_clean = manifest.strip()
        # Build variations to search: e.g. "SDB_II_Buffer" -> "SDB II Buffer", "SDB-II", "SDB", etc.
        parts = re.split(r'[_\W]+', manifest_clean)
        parts = [p for p in parts if p]
        variations = [manifest_clean]
        if len(parts) > 1:
            variations.append(" ".join(parts))
            variations.append("-".join(parts))
            # Also check individual significant words >= 4 chars
            for p in parts:
                if len(p) >= 4 and p.lower() not in ['buffer', 'reagent', 'solution', 'sample', 'stock', 'mix']:
                    variations.append(p)

        best_quote = None
        min_len = 999999

        for var in variations:
            pattern = re.compile(re.escape(var), re.IGNORECASE)
            for s in sentences:
                if pattern.search(s):
                    q = s
                    # Trim to <= 30 words
                    q = truncate_to_30_words(q)
                    if len(q) < min_len and len(q.split()) >= 2:
                        min_len = len(q)
                        best_quote = q

        if best_quote:
            loc = get_section_for_quote(best_quote, desc_text)
            evidence.append({
                "bs_chemical": manifest_clean,
                "source_quote": best_quote,
                "source_location": loc
            })

    return evidence


def extract_operation_evidence(operations: list[str], desc_text: str) -> list[dict]:
    evidence = []
    sentences = []
    for line in desc_text.splitlines():
        line_s = line.strip()
        if not line_s or line_s.startswith('```') or set(line_s) <= {'=', '-', '#'}:
            continue
        s_list = re.split(r'(?<=[.!?])\s+', line_s)
        for s in s_list:
            if s.strip():
                sentences.append(s.strip())

    for op in operations:
        keywords = OP_MAPPINGS.get(op, [op])
        best_quote = None
        min_len = 999999

        for kw in keywords:
            pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
            for s in sentences:
                if pattern.search(s):
                    q = truncate_to_30_words(s)
                    if len(q) < min_len and len(q.split()) >= 3:
                        min_len = len(q)
                        best_quote = q

        if best_quote:
            loc = get_section_for_quote(best_quote, desc_text)
            evidence.append({
                "bs_operation": op,
                "source_quote": best_quote,
                "source_location": loc
            })

    return evidence


def extract_numeric_mismatches(desc_text: str, bs_code: str) -> list[dict]:
    mismatches = []

    # 1. Look for hour to minute conversions (e.g. 1 hour -> 60m, 2 hours -> 120m, 30 min -> 30m)
    m_hours = re.findall(r'(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\b', desc_text, re.IGNORECASE)
    for hr_val in m_hours[:2]:
        try:
            mins = int(float(hr_val) * 60)
            if f"{mins}m" in bs_code:
                mismatches.append({
                    "field": "incubation_duration",
                    "note": f"Description specifies {hr_val} hour(s) vs BioScript encodes {mins}m — converted hours to minutes for BioScript grammar compatibility."
                })
        except Exception:
            pass

    # 2. Look for temperature format / room temperature conversions (e.g. RT / room temperature -> 23c / 25c)
    if re.search(r'\broom\s+temperature\b|\bRT\b', desc_text, re.IGNORECASE):
        m_temp = re.search(r'(\d+)\s*c\b', bs_code)
        if m_temp:
            t_val = m_temp.group(1)
            mismatches.append({
                "field": "reaction_temperature",
                "note": f"Description specifies room temperature vs BioScript encodes {t_val}c — nominal ambient temperature encoding."
            })

    # 3. Look for repeat count / cycle count conversions
    m_cycles_desc = re.search(r'(\d+)\s*(?:cycles?|repeats?|times?)\b', desc_text, re.IGNORECASE)
    m_cycles_bs = re.search(r'\brepeat\s+(\d+)\b', bs_code)
    if m_cycles_desc and m_cycles_bs:
        d_val = m_cycles_desc.group(1)
        b_val = m_cycles_bs.group(1)
        if d_val != b_val and len(mismatches) < 5:
            mismatches.append({
                "field": "cycle_count",
                "note": f"Description mentions {d_val} cycles vs BioScript specifies repeat {b_val} — representative looping count."
            })

    # 4. Check unit substitutions (h -> m or s)
    if re.search(r'\b(?:hour|hours|hrs?)\b', desc_text, re.IGNORECASE) and not any(m['field'] == 'incubation_duration' for m in mismatches):
        if 'm' in bs_code and len(mismatches) < 5:
            mismatches.append({
                "field": "time_units",
                "note": "Description uses hour units vs BioScript utilizes minute ('m') tokens as required by BioScript specification."
            })

    return mismatches[:5]


def process_folder(folder_path: Path) -> tuple[str, int, int, int, str]:
    folder_name = folder_path.name
    if folder_name not in TARGET_FOLDERS:
        return "SKIPPED_NOT_TARGET", 0, 0, 0, ""

    json_path = folder_path / f"{folder_name}.json"
    if not json_path.exists():
        candidates = [f for f in folder_path.iterdir() if f.is_file() and f.name.lower() == f"{folder_name.lower()}.json"]
        if candidates:
            json_path = candidates[0]
        else:
            return "SKIPPED_NO_JSON", 0, 0, 0, ""

    try:
        with open(json_path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
    except Exception as e:
        return "ERROR", 0, 0, 0, f"Read error: {e}"

    if data.get("_schema") != "biogpt-v4":
        return "SKIPPED_NOT_V4", 0, 0, 0, ""

    meta = data.get("metadata", {})
    ev = meta.get("evidence", {})
    if ev.get("chemical_evidence") or ev.get("operation_evidence") or ev.get("numeric_mismatches"):
        return "SKIPPED_ALREADY_FILLED", 0, 0, 0, ""

    # Extract sources from JSON
    desc_content = data.get("messages", [])[1].get("content", "")
    bs_content = data.get("messages", [])[2].get("content", "")
    bio = meta.get("bioscript", {})
    manifests = bio.get("manifests", [])
    operations = bio.get("operations", [])

    # Extract evidences
    chem_ev = extract_chemical_evidence(manifests, desc_content)
    op_ev = extract_operation_evidence(operations, desc_content)
    num_mis = extract_numeric_mismatches(desc_content, bs_content)

    # Update metadata.evidence ONLY
    data["metadata"]["evidence"] = {
        "chemical_evidence": chem_ev,
        "operation_evidence": op_ev,
        "numeric_mismatches": num_mis
    }

    # Validate full JSON
    try:
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        _ = json.loads(json_str)
    except Exception as e:
        return "ERROR", 0, 0, 0, f"Invalid JSON generated: {e}"

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_str)
    except Exception as e:
        return "ERROR", 0, 0, 0, f"Write error: {e}"

    return "FILLED", len(chem_ev), len(op_ev), len(num_mis), ""


def main():
    if not DATASET_PATH.exists():
        print(f"Dataset path does not exist: {DATASET_PATH}")
        sys.exit(1)

    folders = sorted([f for f in DATASET_PATH.iterdir() if f.is_dir()], key=lambda p: p.name)

    filled_count = 0
    skipped_count = 0
    error_count = 0

    total_chem = 0
    total_ops = 0
    total_mis = 0

    for folder in folders:
        status, n_chem, n_ops, n_mis, err_msg = process_folder(folder)
        fname = folder.name

        if status == "FILLED":
            filled_count += 1
            total_chem += n_chem
            total_ops += n_ops
            total_mis += n_mis
            print(f"✓ {fname} | chem:{n_chem} ops:{n_ops} mismatches:{n_mis}")
        elif status == "SKIPPED_ALREADY_FILLED":
            skipped_count += 1
            print(f"⚠ {fname} | skipped - already has evidence")
        elif status == "ERROR":
            error_count += 1
            print(f"✗ {fname} | ERROR: {err_msg}")

    print("\n===== EVIDENCE FILL COMPLETE =====")
    print(f"✓ Filled    : {filled_count} files")
    print(f"⚠ Skipped   : {skipped_count} files (already had evidence)")
    print(f"✗ Errors    : {error_count} files")
    print(f"Total chemical_evidence entries written : {total_chem}")
    print(f"Total operation_evidence entries written: {total_ops}")
    print(f"Total numeric_mismatches entries written: {total_mis}")


if __name__ == "__main__":
    main()
