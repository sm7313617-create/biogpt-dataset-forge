# Antigravity Agent Prompt — BioGPT Dataset Forge
# Paste this entire prompt to Gemini 2.5 Flash in Antigravity IDE

---

You are a data pipeline agent working on the BioGPT dataset project.
Your job is to process a folder of biological protocol data and perform
two tasks in sequence.

═══════════════════════════════════════════════════════════
TASK 1 — Fix double file extensions (only where needed)
═══════════════════════════════════════════════════════════

Scan every file in the current protocol folder.
If a file has a duplicated extension like:
  description.txt.txt   → rename to  description.txt
  output.dot.dot        → rename to  output.dot
  layout.png.png        → rename to  layout.png
  protocol.json.json    → rename to  protocol.json
  protocol.bs.bs        → rename to  protocol.bs
  protocol.ir.ir        → rename to  protocol.ir

Rules:
- Only rename if the last two extensions are identical.
- If extensions are already clean (description.txt, output.dot etc.)
  leave the file completely unchanged.
- Never rename files that have two DIFFERENT extensions (e.g. file.tar.gz).
- Do not create backups. Rename in place.

═══════════════════════════════════════════════════════════
TASK 2 — Rewrite the .json file into the unified BioGPT schema
═══════════════════════════════════════════════════════════

After Task 1 is done, find the single .json file in this folder.
Read ALL 6 files in the folder:
  1. The .bs file   (BioScript code — this becomes messages[assistant].content VERBATIM)
  2. The .txt file  (natural language protocol description — source for messages[user].content)
  3. The .json file (existing metadata — extract whatever is useful)
  4. The .ir file   (compiler intermediate representation — goes into metadata.ir.content VERBATIM)
  5. The .dot file  (control flow graph — parse basic_blocks and edges for metadata.cfg)
  6. The .png file  (chip layout diagram — do NOT include in JSON, visual only, skip it)

Now REWRITE the .json file using EXACTLY this schema structure.
Keep the filename identical (e.g. Aerosol_Sampling.json stays Aerosol_Sampling.json).
Only the content inside changes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TARGET JSON SCHEMA (fill every field from the files you read):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{
  "_schema": "biogpt-v3-optimum",

  "messages": [
    {
      "role": "system",
      "content": "You are BioGPT, an expert compiler architect. Translate the provided natural language biological protocol into valid, deterministic BioScript code for execution on a microfluidic biochip."
    },
    {
      "role": "user",
      "content": "<Reconstruct from the .txt file. Structure it as:
                  ASSAY TYPE: <title and platform>
                  REAGENTS USED:
                    - <each reagent with one-line description>
                  STEPS:
                  1. <Step name> [<volume uL | temp C | duration min where available>]: <description>
                  2. ...
                  INTERPRETATION: <LODs, time resolution, what success confirms>
                  Pull all numbers (volumes, temps, durations) directly from the .txt file
                  and embed them in the step text inside square brackets.>"
    },
    {
      "role": "assistant",
      "content": "<VERBATIM exact content of the .bs file. Do not paraphrase or summarise. Copy byte-for-byte.>"
    }
  ],

  "metadata": {

    "identity": {
      "protocol_id":        "<e.g. fa_aerosol_2004_001 — initials_shortassay_year_NNN>",
      "protocol_name":      "<Full title from .txt or existing .json>",
      "bs_file":            "<relative path to .bs file>",
      "ir_file":            "<relative path to .ir file>",
      "dot_file":           "<relative path to .dot file>",
      "authored_by":        "<from existing .json if present, else unknown>",
      "category":           "<environmental_sensing_assay | clinical_diagnostic | nucleic_acid_amplification | immunoassay | sample_preparation | cell_based | synthetic_biology>",
      "adaptation_status":  "<adapted_authored | directly_translated | synthetic>"
    },

    "source": {
      "title":     "<paper title from existing .json or .txt>",
      "publisher": "<journal or conference from existing .json or .txt>",
      "doi":       "<doi from existing .json or .txt>",
      "url":       "<url from existing .json or .txt>",
      "platform":  "<e.g. Digital Microfluidic LoC | Bio-Rad QX200 ddPCR>"
    },

    "bioscript": {
      "module":     "<module name declared at top of .bs file>",
      "manifests":  ["<list every manifest declared in .bs file>"],
      "operations": ["<list every operation used in .bs file: dispense mix heat detect dispose repeat split gradient>"],
      "complexity": {
        "has_repeat":   "<true if repeat block exists in .bs else false>",
        "has_branch":   "<true if if/else exists in .bs else false>",
        "has_split":    "<true if split exists in .bs else false>",
        "has_gradient": "<true if gradient exists in .bs else false>",
        "num_steps":    "<count of top-level operations in .bs file>"
      }
    },

    "steps": {
      "items": [
        {
          "id":        "<S1, S2, S3 ...>",
          "name":      "<human readable step name>",
          "bb":        "<BB1, BB2 ... matching the .dot file basic block>",
          "inputs":    ["<reagent names from this step>"],
          "operation": "<mix | heat | mix+heat | mix+heat+detect | detect>",
          "key_conditions": {
            "temperature_C":  "<number or null>",
            "duration_min":   "<number or null>",
            "duration_s":     "<number or null>",
            "volume_uL":      "<number or null>",
            "cycles":         "<number or null>",
            "voltage_V":      "<number or null>"
          },
          "output":           "<variable name used in .bs for this step output>",
          "detection_module": "<fluorescence | colorimetric | ddpcrDetection | null>",
          "branch": "<null if no branch, or object with pass/fail conditions matching .dot>"
        }
      ]
    },

    "cfg": {
      "basic_blocks": [
        "<parse every node from the .dot file as: { id, label, type, content or condition+action }>"
      ],
      "edges": [
        "<parse every edge from the .dot file as: [source_bb_id, target_bb_id]>"
      ]
    },

    "ir": {
      "content": "<VERBATIM exact content of the .ir file. Copy byte-for-byte.>"
    },

    "validation": {
      "validated":         false,
      "validation_score":  0.0,
      "validation_status": "pending_v2"
    },

    "evidence": {
      "chemical_evidence": [
        {
          "bs_chemical":     "<manifest name from .bs>",
          "source_quote":    "<exact quote from .txt file that mentions this reagent>",
          "source_location": "<section or line reference in .txt>"
        }
      ],
      "operation_evidence": [
        {
          "bs_operation":    "<the exact BioScript line e.g. reaction = mix A with B for 5s>",
          "source_quote":    "<exact quote from .txt that justifies this operation>",
          "source_location": "<section or line reference in .txt>"
        }
      ],
      "numeric_mismatches": [
        {
          "field": "<field name where .bs number differs from .txt>",
          "note":  "<explain why — what approximation was made and why>"
        }
      ]
    },

    "notes": "<Free text. Explain: (1) any BioScript primitives used as stand-ins, (2) protocol steps omitted because no BioScript primitive exists, (3) substrate or device-mechanic modelling decisions. Extract from existing .json notes field if present.>"

  }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES FOR TASK 2:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. messages[assistant].content = VERBATIM .bs file content. Never paraphrase.
2. metadata.ir.content = VERBATIM .ir file content. Never paraphrase.
3. metadata.cfg = parsed from .dot file. Never invented.
4. messages[user].content = reconstructed from .txt file with numbers embedded.
5. The output filename MUST be identical to the input .json filename.
6. Do NOT include these fields anywhere in the output JSON — they are noise:
     authors, sample_cohorts, statistical_analysis, key_biological_findings,
     LOD_calculation, instrument catalog numbers, primers_probes.sequences_reference
7. If a field cannot be found in any of the 6 files, write null for that field.
   Never invent or hallucinate values.
8. The .png file is visual only — do not reference or include it in the JSON.
9. Validate that the output is valid JSON before writing. No trailing commas.
   No comments inside the JSON output.

═══════════════════════════════════════════════════════════
ITERATION INSTRUCTIONS (for processing all 200 folders):
═══════════════════════════════════════════════════════════

Process folders one at a time in this order:
  1. Run Task 1 on the current folder (rename only if needed).
  2. Run Task 2 on the current folder (rewrite .json).
  3. Print a one-line status: DONE: <folder_name> | renames: <N> | json: rewritten
  4. Move to the next folder.
  5. After all folders print a final summary table:
       Total folders processed | Total files renamed | Total JSONs rewritten | Errors

If any file in a folder is missing (e.g. no .ir file), skip that file's
contribution to the JSON (write null for that section) and continue.
Do not stop the pipeline for a missing file.

Start now. Process the dataset folder at the path I will give you next.
