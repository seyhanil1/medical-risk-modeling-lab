"""Gerçek veriden bağımsız birim testleri (sentetik girdilerle)."""
import zipfile

import numpy as np
import pandas as pd
import pytest

from mrml import audit, config, data_io, dictionary
from mrml import stats as mstats


def _synthetic(n=40, seed=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "age": rng.integers(30, 75, n), "sex": rng.integers(0, 2, n),
        "cp": rng.integers(1, 5, n), "trestbps": rng.integers(100, 180, n),
        "chol": rng.integers(150, 350, n), "fbs": rng.integers(0, 2, n),
        "restecg": rng.integers(0, 3, n), "thalach": rng.integers(100, 180, n),
        "exang": rng.integers(0, 2, n), "oldpeak": rng.uniform(0, 4, n).round(1),
        "slope": rng.integers(1, 4, n), "ca": rng.integers(0, 4, n),
        "thal": rng.choice([3, 6, 7], n), "num": rng.integers(0, 5, n),
    }).astype(float)
    return data_io.add_binary_target(data_io.clean_types(df))


def test_sha256_of_known_bytes(tmp_path):
    p = tmp_path / "x.txt"
    p.write_bytes(b"abc")
    assert data_io.sha256_of(p) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_load_raw_parses_question_mark_as_missing(tmp_path):
    p = tmp_path / "d.data"
    p.write_text("63.0,1.0,1.0,145.0,233.0,1.0,2.0,150.0,0.0,2.3,3.0,?,6.0,0\n"
                 "67.0,1.0,4.0,160.0,286.0,0.0,2.0,108.0,1.0,1.5,2.0,3.0,?,2\n")
    df = data_io.load_cleveland(p)
    assert df["ca"].isna().sum() == 1 and df["thal"].isna().sum() == 1
    assert df["disease"].tolist() == [0, 1]


def test_clean_types_rejects_non_integer_codes():
    df = _synthetic().astype({"cp": float})
    df.loc[0, "cp"] = 2.5
    with pytest.raises(ValueError):
        data_io.clean_types(df[config.COLUMNS].astype(float))


def test_binary_target_keeps_missing():
    df = pd.DataFrame({c: [1.0, 1.0] for c in config.COLUMNS})
    df.loc[1, "num"] = np.nan
    out = data_io.add_binary_target(data_io.clean_types(df))
    assert out["disease"].isna().tolist() == [False, True]


def test_extract_zip_blocks_path_traversal(tmp_path):
    zp = tmp_path / "evil.zip"
    with zipfile.ZipFile(zp, "w") as zf:
        zf.writestr("../escape.txt", "x")
    with pytest.raises(ValueError):
        data_io.extract_zip(zp, tmp_path / "out")


def test_consistency_flags_bad_codes_and_zeros():
    df = _synthetic()
    df.loc[0, "cp"] = 9
    df.loc[1, "chol"] = 0
    issues = audit.consistency_issues(df)
    errs = issues[issues["severity"] == "error"]
    assert {(0, "cp"), (1, "chol")} <= set(zip(errs["row"], errs["variable"]))


def test_duplicates_detected():
    df = _synthetic()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    assert audit.duplicate_summary(df)["n_exact_duplicate_rows"] == 2


def test_holm_adjust_known_values():
    adj = mstats.holm_adjust([0.01, 0.04, 0.03])
    assert np.allclose(adj, [0.03, 0.06, 0.06])


def test_cramers_v_bounds():
    assert mstats.cramers_v(np.array([[10, 0], [0, 10]])) == pytest.approx(1.0)
    assert mstats.cramers_v(np.array([[10, 10], [10, 10]])) == pytest.approx(0.0)


def test_univariate_tests_cover_all_features():
    out = mstats.univariate_tests(_synthetic(80))
    assert set(out["variable"]) == set(config.FEATURES)
    assert (out["p_holm"] >= out["p_value"] - 1e-12).all()


def test_dictionary_covers_all_columns_bilingually():
    names = [d["name"] for d in dictionary.DATA_DICTIONARY]
    assert names == config.COLUMNS
    for d in dictionary.DATA_DICTIONARY:
        assert d["label_tr"] and d["label_en"]
    md = dictionary.to_markdown()
    assert "disease" in md and "Veri Sözlüğü" in md


def test_config_has_no_absolute_user_paths():
    src = (config.PROJECT_ROOT / "src" / "mrml" / "config.py").read_text(encoding="utf-8")
    assert "C:\\" not in src and "/Users/" not in src and "Desktop" not in src


def test_plots_write_files(tmp_path):
    from mrml import plots
    df = _synthetic(60)
    paths = [plots.plot_target_distribution(df, tmp_path),
             plots.plot_categorical_rates(df, tmp_path),
             plots.plot_effect_sizes(mstats.univariate_tests(df), tmp_path)]
    assert all(p.exists() and p.stat().st_size > 1000 for p in paths)

