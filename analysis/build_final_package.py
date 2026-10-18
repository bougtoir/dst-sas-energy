"""Build the FINAL Energy and Buildings submission zip.

Journal upload set only — internal qc/ reports and dev artifacts are
excluded (they remain in the repo, not the upload set).
"""
import os, zipfile, glob
ROOT = os.path.join(os.path.dirname(__file__), "..")
B = os.path.join(ROOT, "manuscript", "build")
os.makedirs(B, exist_ok=True)

INCLUDE = [
    ("manuscript/build/manuscript.docx", "manuscript.docx"),
    ("manuscript/build/manuscript_review_inline.docx",
     "manuscript_review_inline.docx"),
    ("manuscript/highlights.md", "highlights.md"),
    ("manuscript/cover_letter.md", "cover_letter.md"),
    ("manuscript/cover_letter_Energy_and_Buildings.docx",
     "cover_letter_Energy_and_Buildings.docx"),
    ("manuscript/build/references.txt", "references.txt"),
    ("manuscript/build/manuscript_filled.md", "manuscript_source.md"),
    ("figures/fig1_concept.png", "graphical_abstract.png"),
]
for g in sorted(glob.glob(os.path.join(ROOT, "figures", "*.png"))):
    INCLUDE.append((g, f"figures/{os.path.basename(g)}"))
for g in sorted(glob.glob(os.path.join(ROOT, "tables", "*.csv"))):
    INCLUDE.append((g, f"tables/{os.path.basename(g)}"))
# supporting analysis outputs as supplement
for g in sorted(glob.glob(os.path.join(ROOT, "analysis", "*.csv"))):
    INCLUDE.append((g, f"supplement/analysis/{os.path.basename(g)}"))
for g in sorted(glob.glob(os.path.join(ROOT, "literature", "*.csv"))):
    INCLUDE.append((g, f"supplement/literature/{os.path.basename(g)}"))

zp = os.path.join(B, "dst_sas_energy_Energy_and_Buildings_FINAL_submission.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for src, arc in INCLUDE:
        if os.path.exists(src):
            z.write(src, arc)
        else:
            print("MISSING", src)
print("wrote", zp)
