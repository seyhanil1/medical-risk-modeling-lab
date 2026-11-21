"""Açıklayıcı istatistikler ve tek değişkenli (keşifsel) ilişki testleri.

Buradaki testler *ilişki* tanımlar; nedensellik veya bağımsız öngörü değeri iddia etmez.
Her değişken kendi tam vakaları (complete cases) üzerinde değerlendirilir.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as st

from . import config


def describe_continuous(df: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    def _desc(s: pd.Series) -> dict:
        s = s.dropna().astype(float)
        q1, med, q3 = np.percentile(s, [25, 50, 75])
        return {"n": len(s), "mean": s.mean(), "sd": s.std(ddof=1), "median": med,
                "q1": q1, "q3": q3, "min": s.min(), "max": s.max(),
                "skew": st.skew(s, bias=False)}
    rows = []
    groups = [("all", df)] if by is None else [(f"{by}={k}", g) for k, g in df.groupby(by)]
    for gname, g in groups:
        for col in config.CONTINUOUS:
            rows.append({"group": gname, "variable": col, **_desc(g[col])})
    return pd.DataFrame(rows).round(3)


def categorical_crosstab(df: pd.DataFrame, col: str, target: str = config.TARGET_BINARY) -> pd.DataFrame:
    sub = df[[col, target]].dropna()
    ct = pd.crosstab(sub[col], sub[target])
    ct.columns = [f"{target}={c}" for c in ct.columns]
    ct["n"] = ct.sum(axis=1)
    ct["pct_of_sample"] = (ct["n"] / ct["n"].sum() * 100).round(1)
    ct["disease_rate_pct"] = (ct[f"{target}=1"] / ct["n"] * 100).round(1)
    ct.index.name = col
    return ct


def cramers_v(table: np.ndarray) -> float:
    chi2 = st.chi2_contingency(table, correction=False)[0]
    n = table.sum()
    r, k = table.shape
    return float(np.sqrt(chi2 / (n * (min(r, k) - 1))))


def holm_adjust(pvals: list[float]) -> list[float]:
    """Holm-Bonferroni düzeltmesi (aile bazlı hata oranı kontrolü)."""
    p = np.asarray(pvals, dtype=float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        adj[i] = min(running, 1.0)
    return adj.tolist()


def univariate_tests(df: pd.DataFrame, target: str = config.TARGET_BINARY) -> pd.DataFrame:
    """Her öznitelik için hedefle tek değişkenli ilişki testi.

    Sürekli: Mann-Whitney U (dağılım varsayımı yok) + rank-biserial etki büyüklüğü
             (pozitif = hastalık grubunda daha yüksek değerler).
    Kategorik: Pearson ki-kare (beklenen hücre < 5 varsa 2x2 için Fisher kesin testi)
             + Cramér's V.
    """
    rows = []
    for col in config.CONTINUOUS:
        sub = df[[col, target]].dropna()
        a = sub.loc[sub[target] == 1, col].astype(float)
        b = sub.loc[sub[target] == 0, col].astype(float)
        u, p = st.mannwhitneyu(a, b, alternative="two-sided")
        rbc = 2 * u / (len(a) * len(b)) - 1
        rows.append({"variable": col, "type": "continuous", "test": "Mann-Whitney U",
                     "n": len(sub), "statistic": u, "p_value": p,
                     "effect_size": rbc, "effect_measure": "rank-biserial r",
                     "summary": f"median {b.median():g} (0) vs {a.median():g} (1)"})
    for col in config.CATEGORICAL:
        sub = df[[col, target]].dropna()
        table = pd.crosstab(sub[col], sub[target]).to_numpy()
        chi2, p, dof, expected = st.chi2_contingency(table, correction=False)
        test = "Pearson chi-square"
        if table.shape == (2, 2) and (expected < 5).any():
            _, p = st.fisher_exact(table)
            test = "Fisher exact"
        rows.append({"variable": col, "type": "categorical", "test": test, "n": len(sub),
                     "statistic": chi2, "p_value": p, "effect_size": cramers_v(table),
                     "effect_measure": "Cramér's V",
                     "summary": f"dof={dof}; min expected={expected.min():.1f}"})
    out = pd.DataFrame(rows)
    out["p_holm"] = holm_adjust(out["p_value"].tolist())
    out["abs_effect"] = out["effect_size"].abs()
    return out.sort_values("abs_effect", ascending=False).drop(columns="abs_effect").reset_index(drop=True)


def spearman_matrix(df: pd.DataFrame) -> pd.DataFrame:
    cols = config.CONTINUOUS + config.ORDINAL + [config.TARGET_RAW]
    return df[cols].astype(float).corr(method="spearman")


def missing_vs_target(df: pd.DataFrame) -> pd.DataFrame:
    """Eksik değeri olan satırların hedef dağılımı (eksikliğin rastgele olup olmadığına
    dair yalnızca betimsel ipucu — n çok küçükse test yapılmaz)."""
    has_missing = df[config.COLUMNS].isna().any(axis=1)
    return pd.crosstab(has_missing.rename("has_missing"), df[config.TARGET_RAW], margins=True)
