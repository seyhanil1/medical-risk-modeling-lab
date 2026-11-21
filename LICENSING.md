# Licensing

This repository contains material under **different licences**. The table below says which
licence applies to which files. If a file is not listed, the licence of its directory applies.

| Scope | Licence | Copyright | Full text |
|---|---|---|---|
| **Source code**: `src/`, `scripts/`, `tests/`, `pyproject.toml`, `requirements*.txt`, `.gitignore` | **MIT** | © 2026 Seyhan Anıl Kaya | [`LICENSE`](LICENSE) (also [`LICENSES/MIT.txt`](LICENSES/MIT.txt)) |
| **Original written and visual content**: `README.md`, `LICENSING.md`, `THIRD_PARTY_NOTICES.md`, `CITATION.cff`, `RELEASE_MANIFEST.csv`, `reports/**/*.md`, `reports/figures/*.png`, `docs/decisions.md`, `docs/research_plan.md` | **CC BY 4.0** | © 2026 Seyhan Anıl Kaya | [`LICENSES/CC-BY-4.0.txt`](LICENSES/CC-BY-4.0.txt) |
| **Adapted content**: `docs/data_dictionary.md`, `docs/tripod_ai_checklist.md` | **CC BY 4.0** (adaptation) | Adaptation © 2026 Seyhan Anıl Kaya; underlying material by third parties (see below) | [`LICENSES/CC-BY-4.0.txt`](LICENSES/CC-BY-4.0.txt) |
| **Derived aggregate tables**: `reports/tables/**`, `data/metadata/provenance.json` | **CC BY 4.0** | © 2026 Seyhan Anıl Kaya; computed from the UCI Heart Disease data (CC BY 4.0, attribution below) | [`LICENSES/CC-BY-4.0.txt`](LICENSES/CC-BY-4.0.txt) |
| **Third-party material**: UCI data, TRIPOD+AI, Python dependencies | Their own licences | Their respective owners | [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) |

## No data at the patient level are in this repository

Two folders are **excluded** via `.gitignore`:
- `data/raw/`: the UCI Heart Disease files
- `data/private/`: every person-level output (patient rows, per-person predictions paired with
  observed outcomes, row-keyed files)

To recreate them, run `python scripts/run_phase1.py`, `run_phase2.py` and `run_phase3.py`. Phase 1
downloads the official archive from the UCI Machine Learning Repository and verifies its SHA-256
checksums, which are pinned in `src/mrml/config.py`. `RELEASE_MANIFEST.csv` lists every published
file with its licence.

## How to attribute this work

Cite the repository as described in [`CITATION.cff`](CITATION.cff). When you reuse figures or
reports, credit both "Seyhan Anıl Kaya, Medical Risk Modeling Lab (2026), CC BY 4.0" and the UCI
Heart Disease data set (Janosi, Steinbrunn, Pfisterer & Detrano, 1989,
https://doi.org/10.24432/C52P4X, CC BY 4.0).

## Not medical advice

Neither licence grants any fitness for clinical use. The code, models and reports are for research
and education only and must not be used for diagnosis, treatment or clinical decision support.
