"""Aşama 3 grafikleri."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import config
from .plots import C_NO, C_YES, GRID, INK2, SURFACE, _save, plt
from .plots_phase2 import _calib_points

GREY = "#52514e"
GREEN = "#1baf7a"
VIOLET = "#6250d6"


def plot_decision_curve(dc: pd.DataFrame, labels: dict[str, tuple[str, str]], prevalence: float,
                        out_dir: Path = config.FIGURES_DIR) -> Path:
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.plot(dc["threshold"], dc["treat_all"], color=INK2, linewidth=1.2, linestyle=":",
            label="Herkesi sevk et")
    ax.plot(dc["threshold"], dc["treat_none"], color=INK2, linewidth=1.2, label="Kimseyi sevk etme")
    for col, (lab, color) in labels.items():
        ax.plot(dc["threshold"], dc[col], color=color, linewidth=2, label=lab)
    ax.set_ylim(-0.05, prevalence + 0.03)
    ax.set_xlim(dc["threshold"].min(), dc["threshold"].max())
    ax.set_xlabel("Eşik olasılığı (pt)")
    ax.set_ylabel("Net fayda")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.set_title("Karar eğrisi — kat-dışı tahminler (geliştirme, n = 242); varsayımsal sevk kararı",
                 loc="left")
    fig.tight_layout()
    return _save(fig, "p3_01_decision_curve.png", out_dir)


def plot_recalibration(curves: dict[str, dict[str, tuple[np.ndarray, np.ndarray]]],
                       out_dir: Path = config.FIGURES_DIR) -> Path:
    """curves: merkez -> {yöntem -> (y, p)}"""
    n = len(curves)
    fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 4.4), sharey=True)
    styles = {"none": ("Özgün model", GREY), "intercept": ("Kesişim güncelleme", C_NO),
              "logistic": ("Lojistik yeniden kalibrasyon", C_YES)}
    for ax, (site, d) in zip(np.atleast_1d(axes), curves.items()):
        ax.plot([0, 1], [0, 1], color=GRID, linestyle="--", linewidth=1)
        for m, (y, p) in d.items():
            lab, color = styles[m]
            mp, my, _ = _calib_points(np.asarray(y), np.asarray(p), 5)
            ax.plot(mp, my, color=color, linewidth=2, marker="o", markersize=6,
                    markeredgecolor=SURFACE, label=lab)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal")
        ax.set_title(site, loc="left")
        ax.set_xlabel("Öngörülen")
    np.atleast_1d(axes)[0].set_ylabel("Gözlenen")
    np.atleast_1d(axes)[0].legend(frameon=False, fontsize=7.5, loc="upper left")
    fig.suptitle("Hedef merkezde yeniden kalibrasyon (merkez içi 5-kat CV, kat-dışı; 5 nicelik grubu)",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return _save(fig, "p3_02_recalibration.png", out_dir)


def plot_loso(tab: pd.DataFrame, out_dir: Path = config.FIGURES_DIR) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    y = np.arange(len(tab))
    ax = axes[0]
    ax.hlines(y, tab["auc_ci_low"], tab["auc_ci_high"], color=C_NO, linewidth=2)
    ax.plot(tab["roc_auc"], y, "o", color=C_NO, markersize=8, markeredgecolor=SURFACE)
    ax.axvline(0.5, color=INK2, linestyle="--", linewidth=1)
    ax.set_yticks(y, tab["held_out"])
    ax.set_xlim(0.4, 1)
    ax.set_xlabel("ROC AUC (%95 bootstrap GA)")
    ax.set_title("Dışarıda bırakılan merkezde ayrıştırma", loc="left")
    ax.grid(axis="y", visible=False)
    ax = axes[1]
    w = 0.38
    ax.barh(y - w / 2, tab["prevalence"] * 100, height=w, color=C_YES, label="Gözlenen oran")
    ax.barh(y + w / 2, tab["mean_pred"] * 100, height=w, color=C_NO, label="Ortalama öngörü")
    ax.set_yticks(y, [""] * len(y))
    ax.set_xlim(0, 100)
    ax.set_xlabel("%")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("Kalibrasyon-genelde", loc="left")
    ax.grid(axis="y", visible=False)
    fig.suptitle("Merkez-dışı-bırak doğrulama (diğer 3 merkezle eğitilen L2 model)", x=0.01,
                 ha="left", fontweight="bold")
    fig.tight_layout()
    return _save(fig, "p3_03_loso.png", out_dir)


def plot_spline_shapes(shapes: dict[str, dict], out_dir: Path = config.FIGURES_DIR) -> Path:
    """shapes: değişken -> {'grid', 'spline', 'lo', 'hi', 'linear', 'label', 'rug'}"""
    fig, axes = plt.subplots(1, len(shapes), figsize=(4.2 * len(shapes), 3.9))
    for ax, (var, d) in zip(np.atleast_1d(axes), shapes.items()):
        ax.fill_between(d["grid"], d["lo"], d["hi"], color=C_NO, alpha=0.18, linewidth=0,
                        label="Spline %95 bootstrap bandı")
        ax.plot(d["grid"], d["spline"], color=C_NO, linewidth=2, label="Spline (L2)")
        ax.plot(d["grid"], d["linear"], color=C_YES, linewidth=1.6, linestyle="--",
                label="Doğrusal (L2)")
        ax.axhline(0, color=INK2, linewidth=0.8)
        ymin = ax.get_ylim()[0]
        ax.plot(d["rug"], np.full(len(d["rug"]), ymin), "|", color=INK2, markersize=6, alpha=0.4)
        ax.set_xlabel(d["label"])
        ax.set_title(var, loc="left")
    np.atleast_1d(axes)[0].set_ylabel("Log-odds (medyana göre)")
    np.atleast_1d(axes)[0].legend(frameon=False, fontsize=7.5, loc="upper left")
    fig.suptitle("Spline ile tahmin edilen ilişki biçimi (ön-anjiyo modeli, n = 303; diğer değişkenler referans profilde)",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return _save(fig, "p3_04_spline_shapes.png", out_dir)


def plot_subgroups(tab: pd.DataFrame, out_dir: Path = config.FIGURES_DIR) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(10, 0.55 * len(tab) + 1.6))
    y = np.arange(len(tab))
    labels = [f"{r.feature_set} · {r.group} (n={r.n})" for r in tab.itertuples()]
    ax = axes[0]
    ax.hlines(y, tab["auc_ci_low"], tab["auc_ci_high"], color=C_NO, linewidth=2)
    ax.plot(tab["roc_auc"], y, "o", color=C_NO, markersize=7, markeredgecolor=SURFACE)
    ax.set_yticks(y, labels, fontsize=8)
    ax.set_xlim(0.5, 1)
    ax.set_xlabel("ROC AUC (%95 GA)")
    ax.set_title("Ayrıştırma", loc="left")
    ax.grid(axis="y", visible=False)
    ax = axes[1]
    w = 0.38
    ax.barh(y - w / 2, tab["observed"] * 100, height=w, color=C_YES, label="Gözlenen")
    ax.barh(y + w / 2, tab["mean_pred"] * 100, height=w, color=C_NO, label="Ortalama öngörü")
    ax.set_yticks(y, [""] * len(y))
    ax.set_xlim(0, 100)
    ax.set_xlabel("%")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("Kalibrasyon-genelde", loc="left")
    ax.grid(axis="y", visible=False)
    fig.suptitle("Alt grup performansı — L2, kat-dışı tahminler (geliştirme kümesi)", x=0.01,
                 ha="left", fontweight="bold")
    fig.tight_layout()
    return _save(fig, "p3_05_subgroups.png", out_dir)
