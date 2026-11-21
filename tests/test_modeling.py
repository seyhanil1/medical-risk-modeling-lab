"""Aşama 2 modelleme testleri: sızıntısızlık, tekrarlanabilirlik, metrik doğruluğu."""
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from mrml import config
from mrml import modeling as M


def _synthetic(n=200, seed=0, signal=1.5):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "age": rng.normal(55, 9, n), "sex": rng.integers(0, 2, n).astype(float),
        "cp": rng.integers(1, 5, n).astype(float), "trestbps": rng.normal(130, 17, n),
        "chol": rng.normal(245, 50, n), "fbs": rng.integers(0, 2, n).astype(float),
        "restecg": rng.integers(0, 3, n).astype(float), "thalach": rng.normal(150, 22, n),
        "exang": rng.integers(0, 2, n).astype(float), "oldpeak": rng.exponential(1, n),
        "slope": rng.integers(1, 4, n).astype(float), "ca": rng.integers(0, 4, n).astype(float),
        "thal": rng.choice([3.0, 6.0, 7.0], n),
    })
    lin = signal * (df["oldpeak"] - 1) - 0.05 * (df["thalach"] - 150) + 0.8 * (df["cp"] == 4)
    y = (rng.uniform(size=n) < 1 / (1 + np.exp(-lin))).astype(int)
    df.loc[rng.choice(n, 5, replace=False), "ca"] = np.nan
    return df, y


def test_preprocessor_fits_only_on_training_rows():
    """Atama/ölçekleme istatistikleri yalnızca fit edilen satırlardan gelmeli."""
    df, _ = _synthetic()
    prep = M.build_preprocessor(config.FEATURES_FULL)
    train = df.iloc[:100]
    prep.fit(train)
    scaler = prep.named_transformers_["num"].named_steps["scale"]
    imputer = prep.named_transformers_["num"].named_steps["impute"]
    num_cols = [c for c in M.NUMERIC if c in config.FEATURES_FULL]
    assert np.allclose(imputer.statistics_, train[num_cols].median().to_numpy())
    assert not np.allclose(imputer.statistics_, df[num_cols].median().to_numpy())
    assert scaler.mean_ is not None


def test_preprocessor_handles_unseen_category_and_missing():
    df, _ = _synthetic()
    prep = M.build_preprocessor(config.FEATURES_FULL).fit(df[df["restecg"] != 1])
    new = df.iloc[:3].copy()
    new["restecg"] = 1.0
    new["thal"] = np.nan
    out = prep.transform(new)
    assert np.isfinite(out).all()


def test_pre_angio_set_excludes_ca_and_thal():
    assert "ca" not in config.FEATURES_PRE_ANGIO and "thal" not in config.FEATURES_PRE_ANGIO
    prep = M.build_preprocessor(config.FEATURES_PRE_ANGIO)
    df, _ = _synthetic()
    names = prep.fit(df).get_feature_names_out()
    assert not any("ca" == n.split("__")[1].split("_")[0] for n in names)
    assert not any(n.startswith("cat__thal") for n in names)


def test_logistic_newton_matches_sklearn_unpenalized():
    df, y = _synthetic(400)
    X = np.column_stack([np.ones(len(y)), df[["age", "oldpeak", "thalach"]].to_numpy()])
    beta, cov = M.logistic_newton(X, y)
    sk = LogisticRegression(C=np.inf, max_iter=10000, tol=1e-10).fit(X[:, 1:], y)
    assert np.allclose(beta[1:], sk.coef_[0], atol=1e-4)
    assert np.allclose(beta[0], sk.intercept_[0], atol=1e-3)
    assert (np.diag(cov) > 0).all()


def test_calibration_stats_ideal_and_overconfident():
    rng = np.random.default_rng(1)
    p = rng.uniform(0.05, 0.95, 20000)
    y = (rng.uniform(size=p.size) < p).astype(int)
    good = M.calibration_stats(y, p)
    assert good["cal_slope"] == pytest.approx(1, abs=0.06)
    assert good["cal_intercept"] == pytest.approx(0, abs=0.05)
    lp = np.log(p / (1 - p))
    over = 1 / (1 + np.exp(-2 * lp))           # aşırı kendinden emin -> eğim ~0.5
    assert M.calibration_stats(y, over)["cal_slope"] == pytest.approx(0.5, abs=0.04)


def test_corrected_ttest_is_more_conservative():
    rng = np.random.default_rng(2)
    d = rng.normal(0.02, 0.03, 50)
    corr = M.corrected_resampled_ttest(d, n_train=194, n_test=48)
    from scipy import stats as st
    naive_p = st.ttest_1samp(d, 0).pvalue
    assert corr["p_value"] > naive_p
    assert corr["ci_low"] < corr["mean_diff"] < corr["ci_high"]


def test_bootstrap_ci_contains_point_estimate():
    df, y = _synthetic(150)
    p = 1 / (1 + np.exp(-(df["oldpeak"] - 1)))
    est, lo, hi = M.bootstrap_ci(y, p, n_boot=300)
    assert lo <= est <= hi and 0 <= lo and hi <= 1


def test_nested_cv_reproducible_and_shapes():
    df, y = _synthetic(120)
    models = {k: v for k, v in M.build_models(config.FEATURES_FULL).items()
              if k in ("baseline_age_sex", "logreg_l2")}
    a = M.nested_cv(df, y, models, config.FEATURES_FULL, n_splits=3, n_repeats=2, n_jobs=1)
    b = M.nested_cv(df, y, models, config.FEATURES_FULL, n_splits=3, n_repeats=2, n_jobs=1)
    assert len(a["fold_scores"]) == 2 * 3 * 2
    assert a["oof"].shape == (120, 3)
    assert a["oof"][["baseline_age_sex", "logreg_l2"]].notna().all().all()
    pd.testing.assert_frame_equal(a["fold_scores"], b["fold_scores"])


def test_nested_cv_detects_signal():
    df, y = _synthetic(300, signal=2.0)
    models = {"logreg_l2": M.build_models(config.FEATURES_FULL)["logreg_l2"]}
    r = M.nested_cv(df, y, models, config.FEATURES_FULL, n_splits=3, n_repeats=1, n_jobs=1)
    assert r["fold_scores"]["roc_auc"].mean() > 0.75


def test_paired_comparison_zero_for_identical_models():
    fs = pd.DataFrame({"model": ["a"] * 5 + ["b"] * 5, "fold": list(range(5)) * 2,
                       "roc_auc": [0.8, 0.82, 0.79, 0.81, 0.8] * 2, "n_train": 80, "n_test": 20})
    r = M.paired_comparison(fs, "a", "b")
    assert r["mean_diff"] == 0


def test_odds_ratio_table_reference_coding():
    df, y = _synthetic(400)
    df["disease"] = y
    tab, ll, n = M.odds_ratio_table(df, ["age", "cp", "oldpeak"])
    terms = tab["term"].tolist()
    assert "cp=1.0 (ref 1)" not in terms and "cp=4.0 (ref 1)" in terms
    assert "age (per 10)" in terms
    assert (tab["or_ci_low"] <= tab["odds_ratio"]).all() and (tab["odds_ratio"] <= tab["or_ci_high"]).all()
    assert ll < 0 and n == 400


def test_likelihood_ratio_test():
    r = M.likelihood_ratio_test(-100.0, -97.0, 3)
    assert r["lr_stat"] == pytest.approx(6.0)
    assert 0.1 < r["p_value"] < 0.12
