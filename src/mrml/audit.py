"""Veri kalitesi denetimi: boyut, tipler, eksik değerler, tekrarlar, tutarsızlıklar.

Bu modül veriyi değiştirmez; yalnızca bulguları tablo olarak döndürür.
"""
from __future__ import annotations

import pandas as pd

from . import config
from .dictionary import DATA_DICTIONARY


def check_shape(df: pd.DataFrame) -> dict:
    n_rows, n_cols = df[config.COLUMNS].shape
    return {
        "n_rows": n_rows, "n_cols": n_cols,
        "expected_rows": config.EXPECTED_N_ROWS, "expected_cols": config.EXPECTED_N_COLS,
        "ok": n_rows == config.EXPECTED_N_ROWS and n_cols == config.EXPECTED_N_COLS,
    }


def dtype_summary(df: pd.DataFrame) -> pd.DataFrame:
    kinds = {d["name"]: d["kind"] for d in DATA_DICTIONARY}
    rows = []
    for col in config.COLUMNS:
        s = df[col]
        rows.append({
            "variable": col, "kind": kinds[col], "pandas_dtype": str(s.dtype),
            "n_unique": int(s.nunique(dropna=True)),
            "n_missing": int(s.isna().sum()),
            "observed": (f"{s.min()}–{s.max()}" if kinds[col] == "continuous"
                         else ", ".join(str(v) for v in sorted(s.dropna().unique()))),
        })
    return pd.DataFrame(rows).set_index("variable")


def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    miss = df[config.COLUMNS].isna()
    out = pd.DataFrame({
        "n_missing": miss.sum(),
        "pct_missing": (miss.mean() * 100).round(2),
    })
    return out


def missing_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Herhangi bir değişkeni eksik olan satırlar."""
    return df[df[config.COLUMNS].isna().any(axis=1)]


def duplicate_summary(df: pd.DataFrame) -> dict:
    feats = [c for c in config.COLUMNS if c != config.TARGET_RAW]
    exact = df.duplicated(subset=config.COLUMNS, keep=False)
    feat_only = df.duplicated(subset=feats, keep=False)
    return {
        "n_exact_duplicate_rows": int(exact.sum()),
        "exact_duplicate_indices": df.index[exact].tolist(),
        "n_feature_duplicate_rows": int(feat_only.sum()),
        "feature_duplicate_indices": df.index[feat_only].tolist(),
        "note": ("Veride hasta kimliği yoktur (ham veritabanındaki id/isim alanları bu dosyada "
                 "bulunmaz), bu yüzden aynı hastanın tekrar kaydı yalnızca değer eşleşmesiyle "
                 "aranabilir."),
    }


def consistency_issues(df: pd.DataFrame) -> pd.DataFrame:
    """Kod alanı dışı değerler, mümkün aralık dışı değerler ve mantıksal kontroller."""
    issues = []
    for d in DATA_DICTIONARY:
        col = d["name"]
        s = df[col]
        if "allowed" in d:
            bad = s.notna() & ~s.isin(list(d["allowed"]))
            for idx in df.index[bad]:
                issues.append({"row": idx, "variable": col, "value": s[idx],
                               "check": "kod alanı dışı / out of code domain", "severity": "error"})
        if "plausible_range" in d:
            lo, hi = d["plausible_range"]
            bad = s.notna() & ((s < lo) | (s > hi))
            for idx in df.index[bad]:
                issues.append({"row": idx, "variable": col, "value": s[idx],
                               "check": f"mümkün aralık dışı [{lo}, {hi}] / outside plausible range",
                               "severity": "review"})
    # Sıfır değerleri: diğer UCI alt kümelerinde chol=0 eksik veri olarak kullanılmıştır.
    for col in ["trestbps", "chol"]:
        for idx in df.index[df[col] == 0]:
            issues.append({"row": idx, "variable": col, "value": 0,
                           "check": "fizyolojik olarak imkânsız sıfır / implausible zero",
                           "severity": "error"})
    # Egzersizde ulaşılan kalp hızının yaşa göre tahmini maksimumu (220 - yaş) belirgin
    # şekilde aşması nadir ama mümkündür; yalnızca bilgilendirme amaçlı işaretlenir.
    over = df["thalach"] > (220 - df["age"]) + 20
    for idx in df.index[over.fillna(False)]:
        issues.append({"row": idx, "variable": "thalach", "value": df.at[idx, "thalach"],
                       "check": "thalach > (220 - yaş) + 20 / well above age-predicted max",
                       "severity": "info"})
    return pd.DataFrame(issues, columns=["row", "variable", "value", "check", "severity"])


def target_distribution(df: pd.DataFrame) -> pd.DataFrame:
    counts = df[config.TARGET_RAW].value_counts().sort_index()
    out = pd.DataFrame({"n": counts, "pct": (counts / counts.sum() * 100).round(2)})
    out.index.name = config.TARGET_RAW
    return out


def run_audit(df: pd.DataFrame) -> dict:
    return {
        "shape": check_shape(df),
        "dtypes": dtype_summary(df),
        "missing": missing_summary(df),
        "missing_rows": missing_rows(df),
        "duplicates": duplicate_summary(df),
        "consistency": consistency_issues(df),
        "target_distribution": target_distribution(df),
    }
