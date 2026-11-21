"""Yayın dosyaları: lisanslar, atıf, veri dışlama ve README bağlantıları.

Bu testler veri gerektirmez; yeni bir klonda da çalışır.
"""
import re
import tomllib
from pathlib import Path

import mrml
from mrml import config

ROOT = config.PROJECT_ROOT
AUTHOR = "Seyhan Anıl Kaya"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_mit_license_with_holder_and_year():
    text = _read("LICENSE")
    assert text.startswith("MIT License")
    assert f"Copyright (c) 2026 {AUTHOR}" in text
    assert "THE SOFTWARE IS PROVIDED \"AS IS\"" in text
    assert _read("LICENSES/MIT.txt") == text


def test_cc_by_4_legal_code_is_complete():
    text = _read("LICENSES/CC-BY-4.0.txt")
    assert text.startswith("Attribution 4.0 International")
    for marker in ("Section 1 -- Definitions.", "Section 3 -- License Conditions.",
                   "Section 8 -- Interpretation."):
        assert marker in text


def test_licensing_scopes_are_separated():
    text = _read("LICENSING.md")
    for token in ("MIT", "CC BY 4.0", "src/", "reports/figures", AUTHOR, "THIRD_PARTY_NOTICES.md",
                  "10.24432/C52P4X"):
        assert token in text
    notices = _read("THIRD_PARTY_NOTICES.md")
    for token in ("Janosi", "Detrano", "CC BY 4.0", "10.1136/bmj-2023-078378", "not redistributed"):
        assert token in notices


def test_citation_cff_metadata_consistent():
    cff = _read("CITATION.cff")
    assert re.search(r"^cff-version: 1\.2\.0$", cff, re.M)
    assert re.search(r'^title: "Medical Risk Modeling Lab"$', cff, re.M)
    assert 'given-names: "Seyhan Anıl"' in cff and 'family-names: "Kaya"' in cff
    version = re.search(r'^version: "([^"]+)"$', cff, re.M).group(1)
    pyproject = tomllib.loads(_read("pyproject.toml"))["project"]
    assert version == pyproject["version"] == mrml.__version__
    # Projeye DOI uydurulmadı: üst düzeyde doi alanı yok (yalnızca referanslarda)
    assert not re.search(r"^doi:", cff, re.M)
    assert "10.24432/C52P4X" in cff


def test_raw_and_person_level_data_are_git_ignored():
    lines = {ln.strip() for ln in _read(".gitignore").splitlines()
             if ln.strip() and not ln.lstrip().startswith("#")}
    assert {"data/raw/", "data/private/", ".venv/"} <= lines


def _rm():
    import importlib
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    return importlib.import_module("release_manifest")


def test_gitignore_matcher_semantics():
    rm = _rm()
    pats = ["data/raw/", "data/private/", "__pycache__/", "*.py[cod]", ".venv/",
            "reports/*_run.log"]
    ign = lambda p: rm.is_ignored(p, pats)  # noqa: E731
    assert ign("data/raw/heart+disease.zip") and ign("data/raw/uci_zip/processed.va.data")
    assert ign("data/private/phase3/oof_predictions_full.csv")
    assert ign("src/mrml/__pycache__/x.cpython-314.pyc") and ign("a/b.pyc")
    assert ign(".venv/Lib/site-packages/x.py") and ign("reports/phase1_run.log")
    assert not ign("data/metadata/provenance.json") and not ign("reports/tables/loso.csv")
    assert not ign("reports/x/phase1_run.log")          # kök-sabitli desen alt klasöre inmez
    assert not ign("data/raw")                           # dizin deseni, aynı adlı dosyayı kapsamaz


def test_person_level_detector(tmp_path):
    rm = _rm()
    (tmp_path / "a.csv").write_text("row,age,sex\n1,50,1\n", encoding="utf-8")
    (tmp_path / "b.csv").write_text("baseline,logreg,y\n0.2,0.3,1\n", encoding="utf-8")
    (tmp_path / "c.csv").write_text(",n_missing,row_indices\nca,4,\"1, 2\"\n", encoding="utf-8")
    (tmp_path / "d.csv").write_text("num,n,pct\n0,164,54.1\n", encoding="utf-8")
    (tmp_path / "e.json").write_text('{"x": {"duplicate_indices": [3, 4]}}', encoding="utf-8")
    (tmp_path / "f.json").write_text('{"x": {"duplicate_indices": []}}', encoding="utf-8")
    assert rm.person_level_reason(tmp_path / "a.csv")
    assert rm.person_level_reason(tmp_path / "b.csv")
    assert rm.person_level_reason(tmp_path / "c.csv")
    assert rm.person_level_reason(tmp_path / "d.csv") is None      # toplulaştırılmış
    assert rm.person_level_reason(tmp_path / "e.json")
    assert rm.person_level_reason(tmp_path / "f.json") is None


def test_release_manifest_is_current_and_clean():
    """Yayın kümesi: her dosyanın lisans kapsamı var, kişi düzeyi veri yok, envanter güncel."""
    rm = _rm()
    rows = rm.build()
    assert rm.problems(rows) == []
    assert not any(r["path"].startswith(("data/raw/", "data/private/")) for r in rows)
    assert rm.compare(rows, rm.read()) == []


def test_readme_attribution_and_links():
    readme = _read("README.md")
    for token in ("CC BY 4.0", "10.24432/C52P4X", "10.1016/0002-9149(89)90524-9", AUTHOR,
                  "not included in this repository", "run_phase1.py", "Janosi"):
        assert token in readme
    # Bütün göreli bağlantılar mevcut dosyalara işaret etmeli
    for target in re.findall(r"\]\(((?!https?://|#)[^)\s]+)\)", readme):
        assert (ROOT / target).exists(), target
