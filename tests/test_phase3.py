"""Aşama 3 testleri: net fayda, eşik seçimi, yeniden kalibrasyon, LOSO, spline, alt gruplar."""
import numpy as np
import pandas as pd
import pytest

from mrml import config
from mrml import phase3 as P3


def _data(n=300, seed=0):
    rng = np.random.default_rng(seed)
    p = rng.uniform(0.02, 0.98, n)
    y = (rng.uniform(size=n) < p).astype(int)
    return y, p


def test_net_benefit_known_values():
    y = np.array([1, 1, 0, 0])
    p = np.array([0.9, 0.6, 0.7, 0.1])
    # pt = 0.5: TP=2, FP=1, n=4 -> 2/4 - 1/4 * 1 = 0.25
    assert P3.net_benefit(y, p, 0.5) == pytest.approx(0.25)


def test_treat_all_equals_net_benefit_of_all_positive():
    y, p = _data()
    dc = P3.decision_curve(y, {"all": np.ones_like(p)}, thresholds=np.array([0.1, 0.3, 0.5]))
    assert np.allclose(dc["all"], dc["treat_all"])
    assert (dc["treat_none"] == 0).all()


def test_perfect_model_net_benefit_equals_prevalence():
    y, _ = _data()
    dc = P3.decision_curve(y, {"perfect": y.astype(float)}, thresholds=np.array([0.2, 0.6]))
    assert np.allclose(dc["perfect"], y.mean())


def test_choose_threshold_rules():
    y, p = _data(2000)
    t90 = P3.choose_threshold(y, p, "sens90")
    m = P3.classification_metrics(y, p, t90)
    assert m["sensitivity"] >= 0.90
    ty = P3.choose_threshold(y, p, "youden")
    assert 0.2 < ty < 0.8
    with pytest.raises(ValueError):
        P3.choose_threshold(y, p, "bogus")


def test_classification_metrics_consistency():
    y = np.array([1, 1, 0, 0, 1, 0])
    p = np.array([0.9, 0.2, 0.8, 0.1, 0.7, 0.3])
    m = P3.classification_metrics(y, p, 0.5)
    assert m["sensitivity"] == pytest.approx(2 / 3)
    assert m["specificity"] == pytest.approx(2 / 3)
    assert m["ppv"] == pytest.approx(2 / 3)
    assert m["positive_rate"] == pytest.approx(0.5)


def test_recalibration_recovers_known_miscalibration():
    rng = np.random.default_rng(3)
    true_p = rng.uniform(0.05, 0.95, 5000)
    y = (rng.uniform(size=true_p.size) < true_p).astype(int)
    lp = np.log(true_p / (1 - true_p))
    shifted = 1 / (1 + np.exp(-(lp - 1.0)))               # sistematik eksik tahmin
    a, b = P3.fit_recalibration(y, shifted, "intercept")
    assert a == pytest.approx(1.0, abs=0.1) and b == 1.0
    over = 1 / (1 + np.exp(-(2 * lp)))                     # aşırı uç tahminler
    a, b = P3.fit_recalibration(y, over, "logistic")
    assert b == pytest.approx(0.5, abs=0.05)
    assert P3.fit_recalibration(y, shifted, "none") == (0.0, 1.0)


def test_cv_recalibration_improves_brier_for_shifted_predictions():
    rng = np.random.default_rng(4)
    true_p = rng.uniform(0.3, 0.98, 600)
    y = (rng.uniform(size=true_p.size) < true_p).astype(int)
    lp = np.log(true_p / (1 - true_p))
    shifted = 1 / (1 + np.exp(-(lp - 1.5)))
    r = P3.cv_recalibration(y, shifted, n_repeats=2)["summary"]
    assert r.loc["intercept", "brier"] < r.loc["none", "brier"]
    assert abs(r.loc["intercept", "oof_cal_intercept"]) < abs(r.loc["none", "oof_cal_intercept"])


def _site(n, seed, shift=0.0):
    rng = np.random.default_rng(seed)
    d = pd.DataFrame({
        "age": rng.normal(55, 9, n), "sex": rng.integers(0, 2, n).astype(float),
        "cp": rng.integers(1, 5, n).astype(float), "trestbps": rng.normal(130, 15, n),
        "restecg": rng.integers(0, 3, n).astype(float), "thalach": rng.normal(145, 20, n),
        "exang": rng.integers(0, 2, n).astype(float), "oldpeak": rng.exponential(1, n),
    })
    lin = shift + 1.2 * (d["oldpeak"] - 1) + 0.9 * (d["cp"] == 4) - 0.03 * (d["thalach"] - 145)
    d["disease"] = (rng.uniform(size=n) < 1 / (1 + np.exp(-lin))).astype(int)
    return d


def test_loso_holds_out_each_site_once():
    sites = {"A": _site(120, 1), "B": _site(100, 2, 0.5), "C": _site(90, 3, -0.5)}
    tab, preds = P3.loso(sites, config.FEATURES_LOSO)
    assert list(tab["held_out"]) == ["A", "B", "C"]
    assert (tab["n_train"] + tab["n_test"] == 310).all()
    assert (tab["roc_auc"] > 0.65).all()
    assert set(preds) == {"A", "B", "C"}


def test_loso_pipeline_has_no_missing_indicator():
    pipe, _ = P3.loso_pipeline(config.FEATURES_LOSO)
    d = _site(80, 5)
    d.loc[:10, "trestbps"] = np.nan
    names = pipe.named_steps["prep"].fit(d).get_feature_names_out()
    assert not any("missingindicator" in n for n in names)


def test_spline_pipeline_fits_and_expands_continuous():
    d = _site(200, 6)
    feats = config.FEATURES_LOSO
    pipe, grid = P3.build_spline_pipeline(feats)
    pipe.fit(d[feats], d["disease"])
    names = pipe.named_steps["prep"].get_feature_names_out()
    spline_cols = [n for n in names if n.startswith("spl__")]
    n_cont = len([c for c in config.SPLINE_VARS if c in feats])
    assert len(spline_cols) == n_cont * 5          # 4 düğüm, derece 3, sabit yok -> 5 baz
    assert pipe.predict_proba(d[feats]).shape == (200, 2)


def test_partial_logodds_centered_at_median():
    d = _site(200, 7)
    feats = config.FEATURES_LOSO
    pipe, _ = P3.build_spline_pipeline(feats)
    pipe.fit(d[feats], d["disease"])
    grid = np.linspace(d["oldpeak"].min(), d["oldpeak"].max(), 50)
    lo = P3.partial_logodds(pipe, d, "oldpeak", grid, feats)
    assert np.interp(d["oldpeak"].median(), grid, lo) == pytest.approx(0, abs=1e-9)
    assert lo[-1] > lo[0]                           # oldpeak ile artan ilişki


def test_subgroup_performance_rows():
    y, p = _data(400)
    g = pd.Series(np.where(np.arange(400) < 150, "A", "B"))
    t = P3.subgroup_performance(y, p, g, n_boot=100)
    assert set(t["group"]) == {"A", "B"}
    assert t["n"].sum() == 400
    assert (t["auc_ci_low"] <= t["roc_auc"]).all()


def test_subgroup_difference_zero_for_identical_halves():
    y, p = _data(400)
    y2, p2 = np.concatenate([y, y]), np.concatenate([p, p])
    mask = np.arange(800) < 400
    r = P3.subgroup_difference(y2, p2, mask, n_boot=200)
    assert r["auc_diff"] == pytest.approx(0, abs=1e-12)
    assert r["citl_diff"] == pytest.approx(0, abs=1e-9)
    assert r["auc_diff_ci_low"] <= 0 <= r["auc_diff_ci_high"]


def test_subgroup_difference_detects_miscalibrated_group():
    rng = np.random.default_rng(9)
    p = rng.uniform(0.05, 0.95, 3000)
    y = (rng.uniform(size=p.size) < p).astype(int)
    mask = np.arange(p.size) < 1500
    lp = np.log(p / (1 - p))
    p_shift = p.copy()
    p_shift[mask] = 1 / (1 + np.exp(-(lp[mask] + 1.0)))   # A grubunda fazla tahmin
    r = P3.subgroup_difference(y, p_shift, mask, n_boot=200)
    assert r["citl_diff_ci_high"] < 0                       # A'da CITL daha negatif
