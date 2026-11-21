"""Keşifsel veri analizi (EDA) grafikleri. Hepsi PNG olarak `reports/figures/` altına yazılır."""
from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import config  # noqa: E402
from .dictionary import get  # noqa: E402

# Doğrulanmış kategorik paletin ilk iki yuvası (mavi / turuncu): renk körlüğünde ayırt edilebilir.
C_NO = "#2a78d6"
C_YES = "#eb6834"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
SURFACE = "#fcfcfb"
LABELS = {0: "Hastalık yok (num=0)", 1: "Hastalık var (num 1–4)"}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold", "figure.dpi": 110,
})


def _save(fig, name: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return path


def plot_target_distribution(df: pd.DataFrame, out_dir: Path = config.FIGURES_DIR) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [5, 2]})
    counts = df["num"].value_counts().sort_index()
    colors = [C_NO] + [C_YES] * (len(counts) - 1)
    bars = axes[0].bar(counts.index.astype(str), counts.values, color=colors, width=0.7,
                       edgecolor=SURFACE, linewidth=2)
    for b, v in zip(bars, counts.values):
        axes[0].annotate(f"{v} (%{v / counts.sum() * 100:.1f})", (b.get_x() + b.get_width() / 2, v),
                         ha="center", va="bottom", fontsize=9, color=INK2, xytext=(0, 2),
                         textcoords="offset points")
    axes[0].set_title("Ham hedef: num (0–4)")
    axes[0].set_xlabel("num")
    axes[0].set_ylabel("Hasta sayısı")
    bin_counts = df[config.TARGET_BINARY].value_counts().sort_index()
    bars = axes[1].bar(["0", "1"], bin_counts.values, color=[C_NO, C_YES], width=0.7,
                       edgecolor=SURFACE, linewidth=2)
    for b, v in zip(bars, bin_counts.values):
        axes[1].annotate(f"{v} (%{v / bin_counts.sum() * 100:.1f})", (b.get_x() + b.get_width() / 2, v),
                         ha="center", va="bottom", fontsize=9, color=INK2, xytext=(0, 2),
                         textcoords="offset points")
    axes[1].set_title("İkili hedef: disease")
    axes[1].set_xlabel("disease (0 = num 0; 1 = num 1–4)")
    for ax in axes:
        ax.set_ylim(0, max(counts.max(), bin_counts.max()) * 1.15)
        ax.grid(axis="x", visible=False)
    fig.suptitle("Sınıf dağılımı — Cleveland (n = %d)" % len(df), x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return _save(fig, "01_target_distribution.png", out_dir)


def plot_missingness(df: pd.DataFrame, out_dir: Path = config.FIGURES_DIR) -> Path:
    """Değişken başına toplam eksik sayısı (toplulaştırılmış; kayıt düzeyinde desen göstermez)."""
    miss = df[config.COLUMNS].isna()
    counts = miss.sum()
    rows = int(miss.any(axis=1).sum())
    fig, ax = plt.subplots(figsize=(9, 3.0))
    colors = [C_YES if v > 0 else GRID for v in counts.values]
    bars = ax.bar(config.COLUMNS, counts.values, color=colors, width=0.7, edgecolor=SURFACE,
                  linewidth=2)
    for b, v in zip(bars, counts.values):
        ax.annotate(f"{int(v)} (%{v / len(df) * 100:.1f})", (b.get_x() + b.get_width() / 2, v),
                    ha="center", va="bottom", fontsize=8, color=INK2, xytext=(0, 2),
                    textcoords="offset points")
    ax.set_xticks(range(len(config.COLUMNS)), config.COLUMNS, rotation=45, ha="right")
    ax.set_ylabel("Eksik hücre sayısı")
    ax.set_ylim(0, max(counts.max(), 1) * 1.35)
    ax.grid(axis="x", visible=False)
    ax.set_title(f"Eksik değerler: {int(counts.sum())} hücre, {rows} kayıt (n = {len(df)})",
                 loc="left")
    fig.tight_layout()
    return _save(fig, "02_missingness.png", out_dir)


def plot_continuous_by_class(df: pd.DataFrame, out_dir: Path = config.FIGURES_DIR) -> Path:
    cols = config.CONTINUOUS
    fig, axes = plt.subplots(2, len(cols), figsize=(3.2 * len(cols), 6.2),
                             gridspec_kw={"height_ratios": [3, 1.4]})
    for j, col in enumerate(cols):
        ax = axes[0, j]
        data = df[[col, config.TARGET_BINARY]].dropna()
        bins = np.histogram_bin_edges(data[col].astype(float), bins=18)
        for k, c in [(0, C_NO), (1, C_YES)]:
            vals = data.loc[data[config.TARGET_BINARY] == k, col].astype(float)
            ax.hist(vals, bins=bins, color=c, alpha=0.55, label=LABELS[k], density=True,
                    edgecolor=SURFACE, linewidth=0.6)
        d = get(col)
        ax.set_title(col + "\n" + textwrap.fill(d["label_tr"], 26), fontsize=9)
        ax.set_yticks([])
        ax.grid(axis="y", visible=False)
        bx = axes[1, j]
        groups = [data.loc[data[config.TARGET_BINARY] == k, col].astype(float) for k in (0, 1)]
        bp = bx.boxplot(groups, orientation="horizontal", widths=0.6, patch_artist=True,
                        medianprops={"color": INK, "linewidth": 1.5},
                        flierprops={"marker": "o", "markersize": 3, "markerfacecolor": INK2,
                                    "markeredgecolor": "none"})
        for patch, c in zip(bp["boxes"], (C_NO, C_YES)):
            patch.set_facecolor(c)
            patch.set_alpha(0.7)
            patch.set_edgecolor(INK2)
        bx.set_yticks([1, 2], ["0", "1"])
        bx.set_xlabel(d["unit"] or col, fontsize=8)
        bx.set_xlim(axes[0, j].get_xlim())
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", ncol=2, frameon=False)
    fig.suptitle("Sürekli değişkenlerin sınıflara göre dağılımı (yoğunluk + kutu grafiği)",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return _save(fig, "03_continuous_by_class.png", out_dir)


def plot_categorical_rates(df: pd.DataFrame, out_dir: Path = config.FIGURES_DIR) -> Path:
    cols = config.CATEGORICAL
    ncol = 4
    nrow = int(np.ceil(len(cols) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.4 * ncol, 3.2 * nrow))
    axes = axes.ravel()
    overall = df[config.TARGET_BINARY].mean() * 100
    for ax, col in zip(axes, cols):
        sub = df[[col, config.TARGET_BINARY]].dropna()
        g = sub.groupby(col)[config.TARGET_BINARY].agg(["mean", "size"])
        x = g.index.astype(str)
        bars = ax.bar(x, g["mean"] * 100, color=C_YES, width=0.65, edgecolor=SURFACE, linewidth=2)
        for b, (rate, n) in zip(bars, g.itertuples(index=False)):
            ax.annotate(f"%{rate * 100:.0f}\nn={n}", (b.get_x() + b.get_width() / 2, rate * 100),
                        ha="center", va="bottom", fontsize=8, color=INK2, xytext=(0, 2),
                        textcoords="offset points")
        ax.axhline(overall, color=INK2, linestyle="--", linewidth=1)
        ax.set_ylim(0, 118)
        ax.set_title(textwrap.fill(f"{col} — {get(col)['label_tr']}", 34), fontsize=9)
        ax.grid(axis="x", visible=False)
        ax.set_xlabel("kod")
    for ax in axes[len(cols):]:
        ax.axis("off")
    axes[0].set_ylabel("Hastalık oranı (%)")
    axes[ncol].set_ylabel("Hastalık oranı (%)")
    fig.suptitle(f"Kategorik değişken düzeylerinde hastalık oranı (kesikli çizgi = genel oran %{overall:.1f})",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return _save(fig, "04_categorical_disease_rates.png", out_dir)


def plot_correlation(corr: pd.DataFrame, out_dir: Path = config.FIGURES_DIR) -> Path:
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(corr.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)), corr.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(corr)), corr.index)
    for i in range(len(corr)):
        for j in range(len(corr)):
            v = corr.iat[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8,
                    color="white" if abs(v) > 0.55 else INK)
    ax.grid(False)
    fig.colorbar(im, ax=ax, shrink=0.8, label="Spearman ρ")
    ax.set_title("Spearman sıra korelasyonu (sürekli + sıralı değişkenler ve num)", loc="left")
    fig.tight_layout()
    return _save(fig, "05_spearman_correlation.png", out_dir)


def plot_effect_sizes(tests: pd.DataFrame, out_dir: Path = config.FIGURES_DIR) -> Path:
    t = tests.copy()
    t["abs"] = t["effect_size"].abs()
    t = t.sort_values("abs")
    fig, ax = plt.subplots(figsize=(7.5, 5))
    colors = [C_NO if typ == "continuous" else C_YES for typ in t["type"]]
    ax.barh(t["variable"], t["abs"], color=colors, height=0.6, edgecolor=SURFACE, linewidth=2)
    for y, (v, p, meas) in enumerate(zip(t["abs"], t["p_holm"], t["effect_measure"])):
        ptxt = "p_Holm<0.001" if p < 0.001 else f"p_Holm={p:.3f}"
        ax.annotate(f"{v:.2f}  ({ptxt})", (v, y), xytext=(4, 0), textcoords="offset points",
                    va="center", fontsize=8, color=INK2)
    ax.set_xlim(0, max(t["abs"]) * 1.45)
    ax.set_xlabel("|etki büyüklüğü|")
    ax.grid(axis="y", visible=False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=C_NO, label="sürekli: |rank-biserial r|"),
                       Patch(color=C_YES, label="kategorik: Cramér's V")],
              loc="lower right", frameon=False)
    ax.set_title("Tek değişkenli ilişki gücü — disease ile (keşifsel; nedensellik değil)", loc="left")
    fig.tight_layout()
    return _save(fig, "06_univariate_effect_sizes.png", out_dir)


def plot_age_sex(df: pd.DataFrame, out_dir: Path = config.FIGURES_DIR) -> Path:
    """Örneklem bileşimi: yaş dağılımı cinsiyete göre (genellenebilirlik için)."""
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    bins = np.arange(25, 81, 5)
    for sex, c, lab in [(0, C_NO, "Kadın (sex=0)"), (1, C_YES, "Erkek (sex=1)")]:
        n = int((df["sex"] == sex).sum())
        ax.hist(df.loc[df["sex"] == sex, "age"].astype(float), bins=bins, color=c, alpha=0.6,
                label=f"{lab}, n={n}", edgecolor=SURFACE, linewidth=1)
    ax.set_xlabel("Yaş (yıl)")
    ax.set_ylabel("Hasta sayısı")
    ax.legend(frameon=False)
    ax.grid(axis="x", visible=False)
    ax.set_title("Örneklem bileşimi: yaş ve cinsiyet", loc="left")
    fig.tight_layout()
    return _save(fig, "07_sample_age_sex.png", out_dir)
