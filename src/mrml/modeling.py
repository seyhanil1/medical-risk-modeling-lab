"""Aşama 2: sızıntısız önişleme, model tanımları, iç içe çapraz doğrulama ve metrikler.

Bütün önişleme adımları (atama, ölçekleme, one-hot) bir scikit-learn `Pipeline` içindedir;
böylece her eğitim katında yeniden fit edilir ve test katından bilgi sızmaz.

Bu kod araştırma amaçlıdır; çıktıları bireysel hasta kararı için kullanılamaz.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import stats as st
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GridSearchCV, RepeatedStratifiedKFold, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from . import config

NUMERIC = ["age", "trestbps", "chol", "thalach", "oldpeak", "ca"]
BINARY = ["sex", "fbs", "exang"]
NOMINAL = ["cp", "restecg", "slope", "thal"]


# ---------------------------------------------------------------------------
# Önişleme ve modeller
# ---------------------------------------------------------------------------
def build_preprocessor(features: list[str], slope_nominal: bool = True,
                       scale: bool = True, add_indicator: bool = True) -> ColumnTransformer:
    """Seçilen özellikler için önişleyici.

    - Sayısal (ca dahil, sıralı sayı olarak): medyan atama + eksiklik göstergesi + ölçekleme
    - İkili: en sık değer ataması
    - Nominal (cp, restecg, thal; varsayılan olarak slope): en sık değer + one-hot
    """
    nominal = [c for c in NOMINAL if c in features and (slope_nominal or c != "slope")]
    numeric = [c for c in NUMERIC if c in features] + (
        ["slope"] if "slope" in features and not slope_nominal else [])
    binary = [c for c in BINARY if c in features]
    num_steps = [("impute", SimpleImputer(strategy="median", add_indicator=add_indicator))]
    if scale:
        num_steps.append(("scale", StandardScaler()))
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline(num_steps), numeric))
    if binary:
        transformers.append(("bin", SimpleImputer(strategy="most_frequent"), binary))
    if nominal:
        transformers.append(("cat", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), nominal))
    return ColumnTransformer(transformers, remainder="drop", verbose_feature_names_out=True)


def build_models(features: list[str], seed: int = config.RANDOM_SEED,
                 slope_nominal: bool = True) -> dict[str, tuple[Pipeline, dict]]:
    """Model adı -> (pipeline, hiperparametre ızgarası). Izgaralar küçük tutuldu (n = 303)."""
    def pipe(est, scale=True, feats=features):
        return Pipeline([("prep", build_preprocessor(feats, slope_nominal, scale)), ("model", est)])

    return {
        # Referans: yalnızca yaş + cinsiyet, cezasız lojistik regresyon
        "baseline_age_sex": (pipe(LogisticRegression(C=np.inf, max_iter=2000),
                                  feats=["age", "sex"]), {}),
        "logreg_l2": (pipe(LogisticRegression(l1_ratio=0.0, max_iter=5000)),
                      {"model__C": np.logspace(-3, 2, 11)}),
        "logreg_enet": (pipe(LogisticRegression(solver="saga", max_iter=20000, random_state=seed)),
                        {"model__C": np.logspace(-2, 1, 6), "model__l1_ratio": [0.2, 0.5, 0.8, 1.0]}),
        "random_forest": (pipe(RandomForestClassifier(n_estimators=300, max_features="sqrt",
                                                      random_state=seed, n_jobs=1), scale=False),
                          {"model__max_depth": [3, None], "model__min_samples_leaf": [3, 10]}),
        "hist_gb": (pipe(HistGradientBoostingClassifier(max_iter=200, early_stopping=False,
                                                        random_state=seed), scale=False),
                    {"model__learning_rate": [0.03, 0.1], "model__max_depth": [2, 3]}),
    }


def make_search(pipeline: Pipeline, grid: dict, seed: int) -> Pipeline | GridSearchCV:
    """İç döngü: log-loss (uygun/proper skor) ile hiperparametre seçimi."""
    if not grid:
        return clone(pipeline)
    inner = StratifiedKFold(config.INNER_SPLITS, shuffle=True, random_state=seed)
    return GridSearchCV(clone(pipeline), grid, scoring="neg_log_loss", cv=inner, n_jobs=1)


# ---------------------------------------------------------------------------
# Metrikler
# ---------------------------------------------------------------------------
def logistic_newton(X: np.ndarray, y: np.ndarray, offset: np.ndarray | None = None,
                    max_iter: int = 100, tol: float = 1e-10) -> tuple[np.ndarray, np.ndarray]:
    """Cezasız lojistik regresyon (Newton-Raphson). X sabit sütunu içermelidir.

    Dönüş: (katsayılar, kovaryans matrisi = Fisher bilgisinin tersi).
    """
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    off = np.zeros(len(y)) if offset is None else np.asarray(offset, float)
    beta = np.zeros(X.shape[1])
    for _ in range(max_iter):
        eta = X @ beta + off
        p = 1 / (1 + np.exp(-eta))
        w = p * (1 - p)
        H = X.T @ (X * w[:, None])
        step = np.linalg.solve(H, X.T @ (y - p))
        beta += step
        if np.max(np.abs(step)) < tol:
            break
    p = 1 / (1 + np.exp(-(X @ beta + off)))
    H = X.T @ (X * (p * (1 - p))[:, None])
    return beta, np.linalg.inv(H)


def calibration_stats(y: np.ndarray, p: np.ndarray, eps: float = 1e-6) -> dict:
    """Kalibrasyon eğimi (ideal 1) ve kalibrasyon-genelde kesişimi (CITL, ideal 0)."""
    p = np.clip(np.asarray(p, float), eps, 1 - eps)
    lp = np.log(p / (1 - p))
    y = np.asarray(y, float)
    (a, b), _ = logistic_newton(np.column_stack([np.ones_like(lp), lp]), y)
    (citl,), _ = logistic_newton(np.ones((len(y), 1)), y, offset=lp)
    return {"cal_slope": float(b), "cal_intercept": float(citl), "cal_slope_intercept": float(a)}


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    y = np.asarray(y).astype(int)
    p = np.asarray(p, float)
    out = {"roc_auc": roc_auc_score(y, p), "pr_auc": average_precision_score(y, p),
           "brier": brier_score_loss(y, p), "log_loss": log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)),
           "mean_pred": float(p.mean()), "prevalence": float(y.mean())}
    out.update(calibration_stats(y, p))
    return out


def bootstrap_ci(y: np.ndarray, p: np.ndarray, metric=roc_auc_score,
                 n_boot: int = config.N_BOOTSTRAP, seed: int = config.RANDOM_SEED,
                 alpha: float = 0.05) -> tuple[float, float, float]:
    """Yüzdelik bootstrap güven aralığı (sınıf oranı korunarak tabakalı)."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y).astype(int)
    p = np.asarray(p, float)
    idx0, idx1 = np.flatnonzero(y == 0), np.flatnonzero(y == 1)
    vals = np.empty(n_boot)
    for b in range(n_boot):
        idx = np.concatenate([rng.choice(idx0, len(idx0)), rng.choice(idx1, len(idx1))])
        vals[b] = metric(y[idx], p[idx])
    lo, hi = np.quantile(vals, [alpha / 2, 1 - alpha / 2])
    return float(metric(y, p)), float(lo), float(hi)


def corrected_resampled_ttest(diffs: np.ndarray, n_train: int, n_test: int) -> dict:
    """Nadeau & Bengio (2003) düzeltilmiş tekrarlı-örnekleme t testi.

    Tekrarlı k-kat CV'de katlar bağımsız olmadığından olağan t testi aşırı iyimserdir;
    varyans (1/J + n_test/n_train) ile düzeltilir.
    """
    d = np.asarray(diffs, float)
    J = len(d)
    var = d.var(ddof=1)
    se = np.sqrt((1 / J + n_test / n_train) * var)
    t = d.mean() / se if se > 0 else np.inf
    p = 2 * st.t.sf(abs(t), df=J - 1)
    half = st.t.ppf(0.975, J - 1) * se
    return {"mean_diff": float(d.mean()), "ci_low": float(d.mean() - half),
            "ci_high": float(d.mean() + half), "t": float(t), "p_value": float(p)}


# ---------------------------------------------------------------------------
# İç içe çapraz doğrulama
# ---------------------------------------------------------------------------
def _fit_predict_fold(name, pipeline, grid, X, y, train_idx, test_idx, fold_id, repeat, seed,
                      perm_features):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        est = make_search(pipeline, grid, seed + fold_id)
        est.fit(X.iloc[train_idx], y[train_idx])
    p = est.predict_proba(X.iloc[test_idx])[:, 1]
    row = {"model": name, "fold": fold_id, "repeat": repeat,
           "n_train": len(train_idx), "n_test": len(test_idx),
           **metrics(y[test_idx], p)}
    if grid:
        row["best_params"] = str(est.best_params_)
    imp = None
    if perm_features is not None:
        r = permutation_importance(est, X.iloc[test_idx], y[test_idx], scoring="roc_auc",
                                   n_repeats=10, random_state=seed + fold_id, n_jobs=1)
        imp = pd.Series(r.importances_mean, index=X.columns)[perm_features]
    return row, (name, repeat, test_idx, p), imp


def nested_cv(X: pd.DataFrame, y: np.ndarray, models: dict, features: list[str],
              n_splits: int = config.OUTER_SPLITS, n_repeats: int = config.OUTER_REPEATS,
              seed: int = config.RANDOM_SEED, n_jobs: int = -1,
              permutation_for: tuple[str, ...] = ()) -> dict:
    """Dış döngü: tekrarlı tabakalı k-kat. İç döngü: GridSearchCV (make_search).

    Bütün modeller aynı dış katları kullanır, böylece eşleştirilmiş karşılaştırma yapılabilir.

    Dönüş:
      fold_scores: kat başına metrikler
      oof: tekrarlar üzerinden ortalaması alınmış kat-dışı olasılıklar (model başına)
      permutation: (istenirse) kat başına permütasyon önemi
    """
    y = np.asarray(y).astype(int)
    X = X[features].reset_index(drop=True)
    outer = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=seed)
    splits = list(outer.split(X, y))
    jobs = []
    for name, (pipe, grid) in models.items():
        for fold_id, (tr, te) in enumerate(splits):
            perm = features if name in permutation_for else None
            jobs.append(delayed(_fit_predict_fold)(name, pipe, grid, X, y, tr, te, fold_id,
                                                   fold_id // n_splits, seed, perm))
    results = Parallel(n_jobs=n_jobs)(jobs)

    fold_scores = pd.DataFrame([r[0] for r in results])
    oof_sum = {m: np.zeros(len(y)) for m in models}
    oof_cnt = {m: np.zeros(len(y)) for m in models}
    for _, (name, _rep, te, p), _imp in results:
        oof_sum[name][te] += p
        oof_cnt[name][te] += 1
    oof = pd.DataFrame({m: oof_sum[m] / oof_cnt[m] for m in models})
    oof["y"] = y
    perm_rows = [imp.rename(f"{r[0]['model']}_{r[0]['fold']}") for r in results
                 for imp in [r[2]] if imp is not None]
    permutation = pd.DataFrame(perm_rows) if perm_rows else None
    return {"fold_scores": fold_scores, "oof": oof, "permutation": permutation}


def summarize_folds(fold_scores: pd.DataFrame,
                    cols=("roc_auc", "pr_auc", "brier", "log_loss", "cal_slope", "cal_intercept")) -> pd.DataFrame:
    g = fold_scores.groupby("model")[list(cols)]
    out = g.mean().add_suffix("_mean").join(g.std().add_suffix("_sd"))
    return out[[f"{c}_{s}" for c in cols for s in ("mean", "sd")]].round(4)


def paired_comparison(fold_scores: pd.DataFrame, a: str, b: str, metric: str = "roc_auc",
                      fold_scores_b: pd.DataFrame | None = None) -> dict:
    """a - b farkı; aynı dış katlarda eşleştirilmiş, Nadeau-Bengio düzeltmeli."""
    fb = fold_scores if fold_scores_b is None else fold_scores_b
    sa = fold_scores[fold_scores["model"] == a].set_index("fold")
    sb = fb[fb["model"] == b].set_index("fold")
    d = (sa[metric] - sb[metric]).dropna()
    n_tr = int(sa["n_train"].mean())
    n_te = int(sa["n_test"].mean())
    return {"a": a, "b": b, "metric": metric, "n_folds": len(d),
            **corrected_resampled_ttest(d.to_numpy(), n_tr, n_te)}


# ---------------------------------------------------------------------------
# Çok değişkenli ilişki modeli (AS2) — cezasız lojistik regresyon, odds oranları
# ---------------------------------------------------------------------------
OR_SCALING = {"age": 10, "thalach": 10, "trestbps": 10, "chol": 10, "oldpeak": 1}
OR_REFERENCE = {"cp": 1, "slope": 1, "restecg": 0, "thal": 3}


def design_matrix(df: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    """Odds oranı modeli için tasarım matrisi (sabit + ölçekli sürekli + referans kodlu dummy)."""
    cols = {"const": np.ones(len(df))}
    for v in variables:
        if v in OR_REFERENCE:
            ref = OR_REFERENCE[v]
            for lvl in sorted(df[v].dropna().unique()):
                if lvl != ref:
                    cols[f"{v}={lvl} (ref {ref})"] = (df[v] == lvl).astype(float).to_numpy()
        elif v in OR_SCALING:
            cols[f"{v} (per {OR_SCALING[v]})"] = df[v].astype(float).to_numpy() / OR_SCALING[v]
        else:
            cols[v] = df[v].astype(float).to_numpy()
    return pd.DataFrame(cols, index=df.index)


def odds_ratio_table(df: pd.DataFrame, variables: list[str],
                     target: str = config.TARGET_BINARY) -> tuple[pd.DataFrame, float, int]:
    """Wald %95 GA'lı odds oranları. Dönüş: (tablo, log-olabilirlik, n)."""
    sub = df[variables + [target]].dropna()
    X = design_matrix(sub, variables)
    y = sub[target].astype(int).to_numpy()
    beta, cov = logistic_newton(X.to_numpy(), y)
    se = np.sqrt(np.diag(cov))
    z = beta / se
    tab = pd.DataFrame({
        "term": X.columns, "coef": beta, "se": se,
        "odds_ratio": np.exp(beta), "or_ci_low": np.exp(beta - 1.959964 * se),
        "or_ci_high": np.exp(beta + 1.959964 * se), "p_value": 2 * st.norm.sf(np.abs(z)),
    })
    p = 1 / (1 + np.exp(-(X.to_numpy() @ beta)))
    ll = float(np.sum(y * np.log(p) + (1 - y) * np.log(1 - p)))
    return tab, ll, len(sub)


def likelihood_ratio_test(ll_small: float, ll_big: float, df_diff: int) -> dict:
    stat = 2 * (ll_big - ll_small)
    return {"lr_stat": float(stat), "df": df_diff, "p_value": float(st.chi2.sf(stat, df_diff))}
