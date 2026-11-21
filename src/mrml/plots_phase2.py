"""Aşama 2 grafikleri: CV performansı, ROC, kalibrasyon, odds oranları, önem, transfer."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve

from . import config
from .plots import C_NO, C_YES, GRID, INK, INK2, SURFACE, _save, plt

# Doğrulanmış kategorik paletten sabit sırayla (model kimliği; sıraya göre değil)
MODEL_COLORS = {
    "baseline_age_sex": "#52514e",
    "logreg_l2": "#2a78d6",
    "logreg_enet": "#1baf7a",
    "random_forest": "#eb6834",
    "hist_gb": "#6250d6",
}
MODEL_LABELS = {
    "baseline_age_sex": "Referans (yaş+cinsiyet)",
    "logreg_l2": "Lojistik L2 (birincil)",
    "logreg_enet": "Lojistik Elastic-Net",
    "random_forest": "Random Forest",
    "hist_gb": "Gradyan artırma",
}
SET_LABELS = {"pre_angio": "Anjiyografi öncesi", "full": "Tam (+ca, thal)"}


def plot_cv_auc(fold_scores: dict[str, pd.DataFrame], out_dir: Path = config.FIGURES_DIR) -> Path:
    models = list(MODEL_LABELS)
    fig, ax = plt.subplots(figsize=(9, 4.6))
    width = 0.36
    for k, (fs_name, color) in enumerate([("pre_angio", C_NO), ("full", C_YES)]):
        fs = fold_scores[fs_name]
        data = [fs.loc[fs["model"] == m, "roc_auc"].to_numpy() for m in models]
        pos = np.arange(len(models)) + (k - 0.5) * width
        bp = ax.boxplot(data, positions=pos, widths=width * 0.85, patch_artist=True,
                        medianprops={"color": INK, "linewidth": 1.5},
                        flierprops={"marker": "o", "markersize": 3, "markerfacecolor": INK2,
                                    "markeredgecolor": "none"})
        for b in bp["boxes"]:
            b.set_facecolor(color)
            b.set_alpha(0.75)
            b.set_edgecolor(INK2)
        for x, d in zip(pos, data):
            ax.annotate(f"{d.mean():.3f}", (x, d.max()), xytext=(0, 3), textcoords="offset points",
                        ha="center", fontsize=7.5, color=INK2)
    ax.set_xticks(range(len(models)), [MODEL_LABELS[m] for m in models], rotation=15, ha="right")
    ax.set_ylabel("ROC AUC (dış kat)")
    ax.grid(axis="x", visible=False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=C_NO, label=SET_LABELS["pre_angio"]),
                       Patch(color=C_YES, label=SET_LABELS["full"])], frameon=False, loc="lower right")
    ax.set_title("İç içe CV: 5 kat × 10 tekrar (geliştirme kümesi, n = 242); sayı = ortalama", loc="left")
    fig.tight_layout()
    return _save(fig, "p2_01_cv_auc.png", out_dir)


def plot_roc(oof: dict[str, pd.DataFrame], out_dir: Path = config.FIGURES_DIR) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), sharey=True)
    for ax, fs_name in zip(axes, ["pre_angio", "full"]):
        o = oof[fs_name]
        for m in MODEL_LABELS:
            fpr, tpr, _ = roc_curve(o["y"], o[m])
            from sklearn.metrics import roc_auc_score
            auc = roc_auc_score(o["y"], o[m])
            ax.plot(fpr, tpr, color=MODEL_COLORS[m], linewidth=2 if m == "logreg_l2" else 1.4,
                    label=f"{MODEL_LABELS[m]} ({auc:.3f})")
        ax.plot([0, 1], [0, 1], color=GRID, linestyle="--", linewidth=1)
        ax.set_xlabel("1 − özgüllük")
        ax.set_title(SET_LABELS[fs_name], loc="left")
        ax.legend(frameon=False, fontsize=8, loc="lower right")
        ax.set_aspect("equal")
    axes[0].set_ylabel("Duyarlılık")
    fig.suptitle("Kat-dışı ROC eğrileri (10 tekrar ortalaması olasılıklar)", x=0.01, ha="left",
                 fontweight="bold")
    fig.tight_layout()
    return _save(fig, "p2_02_roc_oof.png", out_dir)


def _calib_points(y, p, n_bins):
    q = pd.qcut(p, n_bins, duplicates="drop")
    g = pd.DataFrame({"y": y, "p": p, "bin": q}).groupby("bin", observed=True)
    return g["p"].mean().to_numpy(), g["y"].mean().to_numpy(), g.size().to_numpy()


def plot_calibration(curves: dict[str, tuple[np.ndarray, np.ndarray, str]],
                     out_dir: Path = config.FIGURES_DIR, n_bins: int = 8) -> Path:
    """curves: etiket -> (y, p, renk)"""
    fig, ax = plt.subplots(figsize=(5.8, 5.4))
    ax.plot([0, 1], [0, 1], color=GRID, linestyle="--", linewidth=1, label="Mükemmel kalibrasyon")
    for label, (y, p, color) in curves.items():
        mp, my, n = _calib_points(np.asarray(y), np.asarray(p), n_bins)
        ax.plot(mp, my, color=color, linewidth=2, marker="o", markersize=7,
                markeredgecolor=SURFACE, markeredgewidth=1.5, label=label)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.set_xlabel("Ortalama öngörülen olasılık")
    ax.set_ylabel("Gözlenen hastalık oranı")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title(f"Kalibrasyon — lojistik L2 ({n_bins} nicelik grubu)", loc="left")
    fig.tight_layout()
    return _save(fig, "p2_03_calibration.png", out_dir)


def plot_odds_ratios(tab: pd.DataFrame, out_dir: Path = config.FIGURES_DIR,
                     name: str = "p2_04_odds_ratios.png", title: str = "") -> Path:
    t = tab[tab["term"] != "const"].iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.5, 0.42 * len(t) + 1.4))
    y = np.arange(len(t))
    ax.hlines(y, t["or_ci_low"], t["or_ci_high"], color=C_NO, linewidth=2)
    ax.plot(t["odds_ratio"], y, "o", color=C_NO, markersize=8, markeredgecolor=SURFACE,
            markeredgewidth=1.5)
    ax.axvline(1, color=INK2, linestyle="--", linewidth=1)
    ax.set_xscale("log")
    ax.set_yticks(y, t["term"])
    for yi, (o, lo, hi) in zip(y, t[["odds_ratio", "or_ci_low", "or_ci_high"]].to_numpy()):
        ax.annotate(f"{o:.2f} [{lo:.2f}, {hi:.2f}]", (max(hi, o), yi), xytext=(5, 0),
                    textcoords="offset points", va="center", fontsize=8, color=INK2)
    lo_all, hi_all = t["or_ci_low"].min(), t["or_ci_high"].max()
    ax.set_xlim(lo_all / 1.5, hi_all * 6)
    ax.set_xlabel("Odds oranı (log ölçek), %95 Wald GA")
    ax.grid(axis="y", visible=False)
    ax.set_title(title, loc="left")
    fig.tight_layout()
    return _save(fig, name, out_dir)


def plot_permutation(perm: dict[str, pd.DataFrame], out_dir: Path = config.FIGURES_DIR) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6), sharex=True)
    for ax, fs_name, color in zip(axes, ["pre_angio", "full"], [C_NO, C_YES]):
        p = perm[fs_name]
        m = p.mean().sort_values()
        lo, hi = p.quantile(0.1)[m.index], p.quantile(0.9)[m.index]
        ax.barh(m.index, m.values, color=color, height=0.6, edgecolor=SURFACE, linewidth=2)
        ax.hlines(range(len(m)), lo, hi, color=INK2, linewidth=1)
        ax.axvline(0, color=INK2, linewidth=0.8)
        ax.set_title(SET_LABELS[fs_name], loc="left")
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("ROC AUC düşüşü (permütasyon)")
    fig.suptitle("Permütasyon önemi — lojistik L2, dış katlarda (çubuk = ortalama, çizgi = %10–90)",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return _save(fig, "p2_05_permutation_importance.png", out_dir)


def plot_transfer(tab: pd.DataFrame, out_dir: Path = config.FIGURES_DIR) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    y = np.arange(len(tab))
    ax = axes[0]
    ax.hlines(y, tab["auc_ci_low"], tab["auc_ci_high"], color=C_NO, linewidth=2)
    ax.plot(tab["roc_auc"], y, "o", color=C_NO, markersize=8, markeredgecolor=SURFACE)
    ax.axvline(0.5, color=INK2, linestyle="--", linewidth=1)
    ax.set_yticks(y, tab["site"])
    ax.set_xlim(0.4, 1)
    ax.set_xlabel("ROC AUC (%95 bootstrap GA)")
    ax.set_title("Ayrıştırma", loc="left")
    ax.grid(axis="y", visible=False)
    ax = axes[1]
    w = 0.38
    ax.barh(y - w / 2, tab["prevalence"] * 100, height=w, color=C_YES, label="Gözlenen oran")
    ax.barh(y + w / 2, tab["mean_pred"] * 100, height=w, color=C_NO, label="Ortalama öngörü")
    ax.set_yticks(y, [""] * len(y))
    ax.set_xlim(0, 100)
    ax.set_xlabel("%")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("Kalibrasyon-genelde (prevalans uyumu)", loc="left")
    ax.grid(axis="y", visible=False)
    fig.suptitle("Keşifsel transfer: Cleveland'da eğitilen L2 model (transfer özellik seti)",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return _save(fig, "p2_06_transfer.png", out_dir)
