"""Assemble submission package: manuscript.docx/md, figures, tables,
registry, evidence/novelty tables, qc docs -> manuscript/build/submission.zip
"""
import os, zipfile, glob

ROOT = os.path.join(os.path.dirname(__file__), "..")
B = os.path.join(ROOT, "manuscript", "build")
os.makedirs(B, exist_ok=True)

INCLUDE = [
    ("manuscript/build/manuscript.docx", "manuscript.docx"),
    ("manuscript/build/manuscript_filled.md", "manuscript.md"),
    ("manuscript/build/references.txt", "references.txt"),
    ("manuscript/cover_letter.md", "cover_letter.md"),
    ("manuscript/cover_letter.docx", "cover_letter.docx"),
    ("analysis/manuscript_values.csv", "manuscript_values.csv"),
    ("literature/evidence_table.csv", "literature/evidence_table.csv"),
    ("literature/novelty_matrix.csv", "literature/novelty_matrix.csv"),
]
for g in sorted(glob.glob(os.path.join(ROOT, "qc", "*.md"))):
    INCLUDE.append((g, f"qc/{os.path.basename(g)}"))
for g in [os.path.join(ROOT, "FINAL_HANDOFF.txt"),
          os.path.join(ROOT, "manuscript", "build",
                       "manuscript_review_inline.docx"),
          os.path.join(ROOT, "literature",
                       "behavioral_parameter_evidence.csv")]:
    if os.path.exists(g):
        INCLUDE.append((g, os.path.basename(g)))
for g in sorted(glob.glob(os.path.join(ROOT, "figures", "*.png"))):
    INCLUDE.append((g, f"figures/{os.path.basename(g)}"))
for g in sorted(glob.glob(os.path.join(ROOT, "tables", "*.csv"))):
    INCLUDE.append((g, f"tables/{os.path.basename(g)}"))
for g in sorted(glob.glob(os.path.join(ROOT, "analysis", "*.csv"))):
    INCLUDE.append((g, f"analysis/{os.path.basename(g)}"))

zp = os.path.join(B, "dst_sas_energy_submission.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for src, arc in INCLUDE:
        if os.path.exists(src):
            z.write(src, arc)
        else:
            print("MISSING", src)
print("wrote", zp)
