"""Aşama 3: klinik fayda (karar eğrisi), eşik metrikleri, yeniden kalibrasyon,
merkez-dışı-bırak (LOSO) doğrulama, spline'lı lojistik model ve alt grup performansı.

Bütün sonuçlar araştırma amaçlıdır; bireysel hasta kararı için kullanılamaz.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import (RepeatedStratifiedKFold, StratifiedKFold,
                                     cross_val_predict)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, SplineTransformer, StandardScaler

from . import config
from . import modeling as M


# ---------------------------------------------------------------------------
# Karar eğrisi analizi (Vickers & Elkin, 2006)
# ---------------------------------------------------------------------------
def net_benefit(y: np.ndarray, p: np.ndarray, threshold: float) -> float:
    """NB = TP/n − FP/n · (pt / (1 − pt))."""
    y = np.asarray(y).astype(int)
    pos = np.asarray(p) >= threshold
    n = len(y)
    tp = np.sum(pos & (y == 1))
    fp = np.sum(pos & (y == 0))
    return tp / n - fp / n * threshold / (1 - threshold)


def decision_curve(y: np.ndarray, preds: dict[str, np.ndarray],
                   thresholds: np.ndarray = np.round(np.arange(0.05, 0.81, 0.01), 2)) -> pd.DataFrame:
    y = np.asarray(y).astype(int)
    prev = y.mean()
    rows = []
    for t in thresholds:
        row = {"threshold": t, "treat_all": prev - (1 - prev) * t / (1 - t), "treat_none": 0.0}
        for name, p in preds.items():
            row[name] = net_benefit(y, p, t)
        rows.append(row)
    return pd.DataFrame(rows)


def bootstrap_net_benefit_diff(y, p_a, p_b, thresholds, n_boot=1000, seed=config.RANDOM_SEED):
    """İki model arasındaki NB farkı için yüzdelik bootstrap GA (eşik başına).

    Sınırlılık: kat-dışı tahminler sabit kabul edilir; model her bootstrap örneğinde yeniden
    eğitilmez. Bu nedenle GA'lar yalnızca örneklem değişkenliğini yansıtır, model kurma
    belirsizliğini içermez (olduğundan dar olabilir). Eşikler arasında çoklu karşılaştırma
    düzeltmesi yapılmaz; GA'lar betimsel okunmalıdır."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y).astype(int)
    p_a, p_b = np.asarray(p_a), np.asarray(p_b)
    out = []
    boots = [rng.integers(0, len(y), len(y)) for _ in range(n_boot)]
    for t in thresholds:
        d = [net_benefit(y[i], p_a[i], t) - net_benefit(y[i], p_b[i], t) for i in boots]
        out.append({"threshold": t, "nb_diff": net_benefit(y, p_a, t) - net_benefit(y, p_b, t),
                    "ci_low": np.quantile(d, 0.025), "ci_high": np.quantile(d, 0.975)})
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------
# Eşik seçimi yalnızca eğitim verisinde
# ---------------------------------------------------------------------------
def choose_threshold(y: np.ndarray, p: np.ndarray, rule: str) -> float:
    """'youden': duyarlılık+özgüllük−1 en büyük; 'sens90': duyarlılık ≥ 0,90 olan en yüksek eşik."""
    fpr, tpr, thr = roc_curve(y, p)
    thr = np.clip(thr, 0, 1)
    if rule == "youden":
        return float(thr[np.argmax(tpr - fpr)])
    if rule == "sens90":
        ok = np.flatnonzero(tpr >= 0.90)
        return float(thr[ok[0]])
    raise ValueError(rule)


def classification_metrics(y: np.ndarray, p: np.ndarray, threshold: float) -> dict:
    y = np.asarray(y).astype(int)
    pred = np.asarray(p) >= threshold
    tp = np.sum(pred & (y == 1)); fn = np.sum(~pred & (y == 1))
    tn = np.sum(~pred & (y == 0)); fp = np.sum(pred & (y == 0))
    div = lambda a, b: a / b if b else np.nan  # noqa: E731
    return {"threshold": threshold, "sensitivity": div(tp, tp + fn), "specificity": div(tn, tn + fp),
            "ppv": div(tp, tp + fp), "npv": div(tn, tn + fn), "positive_rate": pred.mean()}


def _threshold_fold(pipe, grid, X, y, tr, te, fold, seed, rules):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        search = M.make_search(pipe, grid, seed + fold).fit(X.iloc[tr], y[tr])
        best = search.best_estimator_ if hasattr(search, "best_estimator_") else search
        # Eşik: eğitim katının kendi kat-dışı tahminlerinden (test katı görülmeden)
        inner = StratifiedKFold(config.INNER_SPLITS, shuffle=True, random_state=seed + fold)
        p_tr = cross_val_predict(clone(best), X.iloc[tr], y[tr], cv=inner, method="predict_proba")[:, 1]
    p_te = search.predict_proba(X.iloc[te])[:, 1]
    rows = []
    for rule in rules:
        t = choose_threshold(y[tr], p_tr, rule)
        rows.append({"fold": fold, "rule": rule, **classification_metrics(y[te], p_te, t)})
    return rows


def cv_threshold_metrics(X: pd.DataFrame, y: np.ndarray, pipe, grid, features: list[str],
                         rules=("youden", "sens90"), n_repeats: int = config.OUTER_REPEATS,
                         seed: int = config.RANDOM_SEED, n_jobs: int = -1) -> pd.DataFrame:
    y = np.asarray(y).astype(int)
    X = X[features].reset_index(drop=True)
    outer = RepeatedStratifiedKFold(n_splits=config.OUTER_SPLITS, n_repeats=n_repeats,
                                    random_state=seed)
    res = Parallel(n_jobs=n_jobs)(delayed(_threshold_fold)(pipe, grid, X, y, tr, te, i, seed, rules)
                                  for i, (tr, te) in enumerate(outer.split(X, y)))
    return pd.DataFrame([r for rows in res for r in rows])


# ---------------------------------------------------------------------------
# Yeniden kalibrasyon (hedef merkezde, merkez içi CV ile dürüst değerlendirme)
# ---------------------------------------------------------------------------
def _logit(p, eps=1e-6):
    p = np.clip(np.asarray(p, float), eps, 1 - eps)
    return np.log(p / (1 - p))


def fit_recalibration(y: np.ndarray, p: np.ndarray, method: str) -> tuple[float, float]:
    """Dönüş (a, b): yeni logit = a + b · eski logit."""
    lp = _logit(p)
    if method == "none":
        return 0.0, 1.0
    if method == "intercept":
        (a,), _ = M.logistic_newton(np.ones((len(lp), 1)), y, offset=lp)
        return float(a), 1.0
    if method == "logistic":
        (a, b), _ = M.logistic_newton(np.column_stack([np.ones_like(lp), lp]), y)
        return float(a), float(b)
    raise ValueError(method)


def apply_recalibration(p: np.ndarray, a: float, b: float) -> np.ndarray:
    return 1 / (1 + np.exp(-(a + b * _logit(p))))


def cv_recalibration(y: np.ndarray, p: np.ndarray, methods=("none", "intercept", "logistic"),
                     n_splits: int = 5, n_repeats: int = 20, seed: int = config.RANDOM_SEED) -> dict:
    """Merkez verisinin bir kısmında yeniden kalibre et, kalan kısımda değerlendir.

    Dönüş: {'summary': yöntem başına ortalama metrikler, 'oof': yöntem başına kat-dışı olasılık}
    """
    y = np.asarray(y).astype(int)
    p = np.asarray(p, float)
    cv = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=seed)
    rows = []
    oof = {m: np.zeros(len(y)) for m in methods}
    cnt = np.zeros(len(y))
    for i, (tr, te) in enumerate(cv.split(p.reshape(-1, 1), y)):
        cnt[te] += 1
        for m in methods:
            a, b = fit_recalibration(y[tr], p[tr], m)
            q = apply_recalibration(p[te], a, b)
            oof[m][te] += q
            rows.append({"fold": i, "method": m, "a": a, "b": b,
                         "brier": np.mean((q - y[te]) ** 2),
                         "mean_pred": q.mean(), "prevalence": y[te].mean()})
    oof = {m: v / cnt for m, v in oof.items()}
    folds = pd.DataFrame(rows)
    summ = folds.groupby("method")[["a", "b", "brier", "mean_pred", "prevalence"]].mean()
    for m in methods:
        cs = M.calibration_stats(y, oof[m])
        summ.loc[m, "oof_cal_slope"] = cs["cal_slope"]
        summ.loc[m, "oof_cal_intercept"] = cs["cal_intercept"]
        summ.loc[m, "oof_auc"] = roc_auc_score(y, oof[m])
    return {"summary": summ.loc[list(methods)], "oof": oof}


# ---------------------------------------------------------------------------
# Merkez-dışı-bırak (LOSO)
# ---------------------------------------------------------------------------
def loso_pipeline(features: list[str], seed: int = config.RANDOM_SEED):
    """Eksiklik göstergesi YOK: merkezler arası sistematik eksiklik merkezi kodlamasın."""
    pipe = Pipeline([("prep", M.build_preprocessor(features, add_indicator=False)),
                     ("model", LogisticRegression(l1_ratio=0.0, max_iter=5000))])
    return pipe, {"model__C": np.logspace(-3, 2, 11)}


def loso(sites: dict[str, pd.DataFrame], features: list[str],
         target: str = config.TARGET_BINARY, seed: int = config.RANDOM_SEED) -> tuple[pd.DataFrame, dict]:
    rows, preds = [], {}
    for held in sites:
        train = pd.concat([d for s, d in sites.items() if s != held], ignore_index=True)
        test = sites[held]
        pipe, grid = loso_pipeline(features, seed)
        est = M.make_search(pipe, grid, seed).fit(train[features], train[target].astype(int))
        yt = test[target].astype(int).to_numpy()
        p = est.predict_proba(test[features])[:, 1]
        preds[held] = (yt, p)
        auc, lo, hi = M.bootstrap_ci(yt, p)
        rows.append({"held_out": held, "n_train": len(train), "n_test": len(test),
                     "events_test": int(yt.sum()), **M.metrics(yt, p),
                     "auc_ci_low": lo, "auc_ci_high": hi, "C": est.best_params_["model__C"]})
    return pd.DataFrame(rows), preds


# ---------------------------------------------------------------------------
# Spline'lı lojistik regresyon
# ---------------------------------------------------------------------------
def build_spline_pipeline(features: list[str], n_knots: int = 4) -> tuple[Pipeline, dict]:
    """Sürekli değişkenler için kübik B-spline (4 düğüm, nicelik konumlu, doğrusal dış
    değerleme) + L2 lojistik regresyon. Not: sklearn 'restricted cubic spline' sunmaz;
    doğrusal dış değerleme kuyruklarda benzer bir kısıt sağlar."""
    spline_vars = [c for c in config.SPLINE_VARS if c in features]
    other = [c for c in features if c not in spline_vars]
    base = M.build_preprocessor(other) if other else None
    transformers = [("spl", Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("spline", SplineTransformer(n_knots=n_knots, degree=3, knots="quantile",
                                     extrapolation="linear", include_bias=False)),
        ("scale", StandardScaler()),
    ]), spline_vars)]
    if base is not None:
        transformers += base.transformers
    prep = ColumnTransformer(transformers, remainder="drop")
    pipe = Pipeline([("prep", prep), ("model", LogisticRegression(l1_ratio=0.0, max_iter=5000))])
    return pipe, {"model__C": np.logspace(-3, 2, 11)}


def partial_logodds(est, df: pd.DataFrame, var: str, grid: np.ndarray, features: list[str]) -> np.ndarray:
    """Diğer değişkenler referans profilde (sayısal medyan, kategorik en sık) sabitken,
    `var` boyunca log-odds; ızgaranın medyanına göre merkezlenir."""
    ref = {}
    for c in features:
        s = df[c].dropna()
        ref[c] = float(s.median()) if c in config.CONTINUOUS else float(s.mode().iloc[0])
    X = pd.DataFrame([ref] * len(grid))
    X[var] = grid
    p = np.clip(est.predict_proba(X[features])[:, 1], 1e-9, 1 - 1e-9)
    lo = np.log(p / (1 - p))
    center = np.interp(float(df[var].median()), grid, lo)
    return lo - center


# ---------------------------------------------------------------------------
# Alt grup performansı (TRIPOD+AI madde 14, 23a)
# ---------------------------------------------------------------------------
def subgroup_performance(y: np.ndarray, p: np.ndarray, groups: pd.Series,
                         n_boot: int = 1000) -> pd.DataFrame:
    rows = []
    y = np.asarray(y).astype(int)
    p = np.asarray(p, float)
    for g in groups.dropna().unique():
        m = (groups == g).to_numpy()
        yy, pp = y[m], p[m]
        row = {"group": g, "n": int(m.sum()), "events": int(yy.sum()),
               "observed": yy.mean(), "mean_pred": pp.mean(),
               "brier": float(np.mean((pp - yy) ** 2))}
        if 0 < yy.sum() < len(yy):
            auc, lo, hi = M.bootstrap_ci(yy, pp, n_boot=n_boot)
            citl, clo, chi = M.bootstrap_ci(yy, pp, metric=_citl, n_boot=n_boot)
            row.update(roc_auc=auc, auc_ci_low=lo, auc_ci_high=hi,
                       cal_intercept=citl, citl_ci_low=clo, citl_ci_high=chi)
        rows.append(row)
    return pd.DataFrame(rows)


def _citl(y, p):
    """Kalibrasyon-genelde (yalnızca kesişim, logit ofsetli). Eğim modeli uydurulmaz; küçük
    bootstrap örneklerinde eğim uydurması ıraksayabilir (tekil Hessian)."""
    lp = _logit(p)
    (a,), _ = M.logistic_newton(np.ones((len(lp), 1)), np.asarray(y, float), offset=lp)
    return float(a)


def subgroup_difference(y: np.ndarray, p: np.ndarray, mask_a: np.ndarray, n_boot: int = 2000,
                        seed: int = config.RANDOM_SEED) -> dict:
    """A − B farkı (AUC ve CITL) için yüzdelik bootstrap GA; her grup kendi içinde,
    sınıf oranı korunarak yeniden örneklenir. Tahminler sabit kabul edilir (model yeniden
    eğitilmez), bu yüzden GA'lar model belirsizliğini içermez."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y).astype(int)
    p = np.asarray(p, float)
    mask_a = np.asarray(mask_a, bool)

    def strat(idx):
        i0, i1 = idx[y[idx] == 0], idx[y[idx] == 1]
        return np.concatenate([rng.choice(i0, len(i0)), rng.choice(i1, len(i1))])

    ia, ib = np.flatnonzero(mask_a), np.flatnonzero(~mask_a)
    est_auc = roc_auc_score(y[ia], p[ia]) - roc_auc_score(y[ib], p[ib])
    est_citl = _citl(y[ia], p[ia]) - _citl(y[ib], p[ib])
    d_auc, d_citl = np.empty(n_boot), np.empty(n_boot)
    for b in range(n_boot):
        a, c = strat(ia), strat(ib)
        d_auc[b] = roc_auc_score(y[a], p[a]) - roc_auc_score(y[c], p[c])
        d_citl[b] = _citl(y[a], p[a]) - _citl(y[c], p[c])
    q = lambda v: np.quantile(v, [0.025, 0.975])  # noqa: E731
    (alo, ahi), (clo, chi) = q(d_auc), q(d_citl)
    return {"n_a": int(mask_a.sum()), "events_a": int(y[ia].sum()),
            "n_b": int((~mask_a).sum()), "events_b": int(y[ib].sum()),
            "auc_diff": est_auc, "auc_diff_ci_low": alo, "auc_diff_ci_high": ahi,
            "citl_diff": est_citl, "citl_diff_ci_low": clo, "citl_diff_ci_high": chi}
