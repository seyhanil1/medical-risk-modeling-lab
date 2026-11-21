"""Aşama 2 boru hattı: kilitli test ayrımı, iç içe CV, son değerlendirme, OR modeli,
duyarlılık analizleri ve keşifsel transfer testi.

Çalıştırma (proje kökünden):
    python scripts/run_phase2.py
    python scripts/run_phase2.py --quick   # hızlı duman testi (2 tekrar)

Araştırma amaçlıdır: bireysel risk hesaplama, arayüz veya deployment içermez.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.exceptions import ConvergenceWarning  # noqa: E402
from sklearn.metrics import brier_score_loss, roc_auc_score  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402

from mrml import config, data_io  # noqa: E402
from mrml import modeling as M  # noqa: E402
from mrml import plots_phase2 as P  # noqa: E402

T = config.TABLES_DIR / "phase2"
PRIV = config.PRIVATE_DIR / "phase2"   # kişi düzeyi, yayımlanmaz
F = config.FIGURES_DIR


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def locked_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    dev, test = train_test_split(df, test_size=config.TEST_SIZE, stratify=df[config.TARGET_BINARY],
                                 random_state=config.RANDOM_SEED)
    split = pd.Series("dev", index=df.index)
    split[test.index] = "test"
    config.PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    split.rename("split").to_csv(config.PRIVATE_DIR / "split_phase2.csv", index_label="row")
    return dev.sort_index(), test.sort_index()


def main(quick: bool = False) -> None:
    T.mkdir(parents=True, exist_ok=True)
    PRIV.mkdir(parents=True, exist_ok=True)
    data_io.ensure_data()
    df = data_io.load_cleveland()
    dev, test = locked_split(df)
    y_dev = dev[config.TARGET_BINARY].astype(int).to_numpy()
    y_test = test[config.TARGET_BINARY].astype(int).to_numpy()
    log(f"Geliştirme n={len(dev)} (olay {y_dev.sum()}), kilitli test n={len(test)} (olay {y_test.sum()})")
    repeats = 2 if quick else config.OUTER_REPEATS
    summary: dict = {"n_dev": len(dev), "n_test": len(test), "events_dev": int(y_dev.sum()),
                     "events_test": int(y_test.sum()), "outer_repeats": repeats}

    # ---------------- 1) İç içe CV (geliştirme kümesi) ----------------
    cv = {}
    for fs_name, feats in config.FEATURE_SETS.items():
        t0 = time.time()
        cv[fs_name] = M.nested_cv(dev, y_dev, M.build_models(feats), feats, n_repeats=repeats,
                                  permutation_for=(config.PRIMARY_MODEL,))
        cv[fs_name]["fold_scores"].assign(feature_set=fs_name).to_csv(
            T / f"cv_fold_scores_{fs_name}.csv", index=False)
        s = M.summarize_folds(cv[fs_name]["fold_scores"])
        s.to_csv(T / f"cv_summary_{fs_name}.csv")
        oof_m = pd.DataFrame({m: M.metrics(cv[fs_name]["oof"]["y"], cv[fs_name]["oof"][m])
                              for m in M.build_models(feats)}).T.round(4)
        oof_m.to_csv(T / f"oof_metrics_{fs_name}.csv")
        cv[fs_name]["permutation"].to_csv(T / f"permutation_{fs_name}.csv")
        log(f"CV {fs_name} tamam ({time.time() - t0:.0f} sn)\n{s[['roc_auc_mean', 'roc_auc_sd', 'brier_mean', 'cal_slope_mean']]}")

    # ---------------- 2) Eşleştirilmiş karşılaştırmalar ----------------
    comps = []
    for fs_name in config.FEATURE_SETS:
        fs = cv[fs_name]["fold_scores"]
        for m in ["logreg_l2", "logreg_enet", "random_forest", "hist_gb"]:
            comps.append({"comparison": f"{fs_name}: {m} − baseline_age_sex",
                          **M.paired_comparison(fs, m, "baseline_age_sex")})
        for m in ["logreg_enet", "random_forest", "hist_gb"]:
            comps.append({"comparison": f"{fs_name}: {m} − logreg_l2",
                          **M.paired_comparison(fs, m, "logreg_l2")})
    for m in M.build_models(config.FEATURES_FULL):
        if m == "baseline_age_sex":
            continue
        comps.append({"comparison": f"{m}: full − pre_angio (AS4)",
                      **M.paired_comparison(cv["full"]["fold_scores"], m, m,
                                            fold_scores_b=cv["pre_angio"]["fold_scores"])})
    comps = pd.DataFrame(comps)
    # Çoklu karşılaştırma: tablodaki bütün karşılaştırmalar tek aile kabul edilir (Holm)
    from mrml.stats import holm_adjust
    comps["p_holm"] = holm_adjust(comps["p_value"].tolist())
    comps = comps.round(4)
    comps.to_csv(T / "cv_paired_comparisons.csv", index=False)
    log(f"Karşılaştırmalar:\n{comps[['comparison', 'mean_diff', 'ci_low', 'ci_high', 'p_value', 'p_holm']]}")

    # ---------------- 3) Duyarlılık analizleri (birincil model) ----------------
    sens = []
    for fs_name, feats in config.FEATURE_SETS.items():
        base = cv[fs_name]["fold_scores"].query("model == @config.PRIMARY_MODEL")
        sens.append({"feature_set": fs_name, "variant": "birincil (atama, slope nominal)",
                     "n": len(dev), "roc_auc": base["roc_auc"].mean(), "brier": base["brier"].mean()})
        cc = dev.dropna(subset=feats)
        r = M.nested_cv(cc, cc[config.TARGET_BINARY].astype(int).to_numpy(),
                        {config.PRIMARY_MODEL: M.build_models(feats)[config.PRIMARY_MODEL]},
                        feats, n_repeats=repeats)["fold_scores"]
        sens.append({"feature_set": fs_name, "variant": "tam vaka", "n": len(cc),
                     "roc_auc": r["roc_auc"].mean(), "brier": r["brier"].mean()})
        r = M.nested_cv(dev, y_dev, {config.PRIMARY_MODEL: M.build_models(
            feats, slope_nominal=False)[config.PRIMARY_MODEL]}, feats, n_repeats=repeats)["fold_scores"]
        sens.append({"feature_set": fs_name, "variant": "slope sıralı sayısal", "n": len(dev),
                     "roc_auc": r["roc_auc"].mean(), "brier": r["brier"].mean()})
    sens = pd.DataFrame(sens).round(4)
    sens.to_csv(T / "sensitivity.csv", index=False)
    log(f"Duyarlılık:\n{sens}")

    # ---------------- 4) Kilitli test: tek seferlik değerlendirme ----------------
    rows, test_preds, coefs = [], {}, []
    for fs_name, feats in config.FEATURE_SETS.items():
        for m, (pipe, grid) in M.build_models(feats).items():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ConvergenceWarning)
                est = M.make_search(pipe, grid, config.RANDOM_SEED)
                est.fit(dev[feats], y_dev)
            p = est.predict_proba(test[feats])[:, 1]
            test_preds[(fs_name, m)] = p
            met = M.metrics(y_test, p)
            auc, lo, hi = M.bootstrap_ci(y_test, p)
            _, blo, bhi = M.bootstrap_ci(y_test, p, metric=lambda a, b: -brier_score_loss(a, b))
            rows.append({"feature_set": fs_name, "model": m,
                         "primary": m == config.PRIMARY_MODEL,
                         "best_params": str(getattr(est, "best_params_", {})),
                         **met, "auc_ci_low": lo, "auc_ci_high": hi,
                         "brier_ci_low": -bhi, "brier_ci_high": -blo})
            if m == config.PRIMARY_MODEL:
                best = est.best_estimator_
                names = best.named_steps["prep"].get_feature_names_out()
                coefs.append(pd.DataFrame({"feature_set": fs_name, "feature": names,
                                           "std_coef": best.named_steps["model"].coef_[0]}))
    test_tab = pd.DataFrame(rows).round(4)
    test_tab.to_csv(T / "locked_test_results.csv", index=False)
    pd.concat(coefs).round(4).to_csv(T / "final_logreg_l2_coefficients.csv", index=False)
    pd.DataFrame({f"{k[0]}|{k[1]}": v for k, v in test_preds.items()} | {"y": y_test},
                 index=test.index).to_csv(PRIV / "locked_test_predictions.csv", index_label="row")
    log(f"Kilitli test:\n{test_tab[['feature_set', 'model', 'roc_auc', 'auc_ci_low', 'auc_ci_high', 'brier', 'cal_slope']]}")
    # Kilitli testte AS4 farkı (eşleştirilmiş bootstrap)
    rng = np.random.default_rng(config.RANDOM_SEED)
    pa, pf = test_preds[("pre_angio", "logreg_l2")], test_preds[("full", "logreg_l2")]
    i0, i1 = np.flatnonzero(y_test == 0), np.flatnonzero(y_test == 1)
    diffs = []
    for _ in range(config.N_BOOTSTRAP):
        idx = np.concatenate([rng.choice(i0, len(i0)), rng.choice(i1, len(i1))])
        diffs.append(roc_auc_score(y_test[idx], pf[idx]) - roc_auc_score(y_test[idx], pa[idx]))
    summary["locked_test_auc_diff_full_minus_pre"] = {
        "diff": float(roc_auc_score(y_test, pf) - roc_auc_score(y_test, pa)),
        "ci_low": float(np.quantile(diffs, 0.025)), "ci_high": float(np.quantile(diffs, 0.975))}

    # ---------------- 5) AS2: çok değişkenli odds oranları (bütün Cleveland) ----------------
    vars_a = ["age", "sex", "cp", "thalach", "exang", "oldpeak", "slope"]
    vars_b = vars_a + ["trestbps", "chol", "fbs"]
    tab_a, ll_a, n_a = M.odds_ratio_table(df, vars_a)
    tab_b, ll_b, n_b = M.odds_ratio_table(df, vars_b)
    lrt = M.likelihood_ratio_test(ll_a, ll_b, df_diff=3)
    tab_a.round(4).to_csv(T / "odds_ratios_model_A.csv", index=False)
    tab_b.round(4).to_csv(T / "odds_ratios_model_B.csv", index=False)
    summary["AS2"] = {"n": n_a, "events": int(df[config.TARGET_BINARY].sum()),
                      "params_model_A": len(tab_a) - 1, "lrt_B_vs_A": lrt}
    log(f"OR modeli A:\n{tab_a.round(3)}\nLRT B vs A: {lrt}")

    # ---------------- 6) Keşifsel transfer (diğer UCI merkezleri) ----------------
    feats = config.FEATURES_TRANSFER
    pipe, grid = M.build_models(feats)[config.PRIMARY_MODEL]
    y_all = df[config.TARGET_BINARY].astype(int).to_numpy()
    est = M.make_search(pipe, grid, config.RANDOM_SEED).fit(df[feats], y_all)
    ref = M.nested_cv(df, y_all, {"logreg_l2": (pipe, grid)}, feats, n_repeats=repeats)
    ref_m = M.metrics(ref["oof"]["y"], ref["oof"]["logreg_l2"])
    tr_rows = [{"site": "Cleveland (iç CV)", "n": len(df), "n_complete": len(df.dropna(subset=feats)),
                **ref_m, "auc_ci_low": np.nan, "auc_ci_high": np.nan}]
    for site, fname in config.OTHER_SITES.items():
        s = data_io.load_site(fname)
        ys = s[config.TARGET_BINARY].astype(int).to_numpy()
        p = est.predict_proba(s[feats])[:, 1]
        auc, lo, hi = M.bootstrap_ci(ys, p)
        tr_rows.append({"site": site, "n": len(s), "n_complete": len(s.dropna(subset=feats)),
                        **M.metrics(ys, p), "auc_ci_low": lo, "auc_ci_high": hi})
        cc = s.dropna(subset=feats)
        if 30 <= len(cc) < len(s) and 0 < cc[config.TARGET_BINARY].mean() < 1:
            yc = cc[config.TARGET_BINARY].astype(int).to_numpy()
            pc = est.predict_proba(cc[feats])[:, 1]
            auc, lo, hi = M.bootstrap_ci(yc, pc)
            tr_rows.append({"site": f"{site} (tam vaka)", "n": len(cc), "n_complete": len(cc),
                            **M.metrics(yc, pc), "auc_ci_low": lo, "auc_ci_high": hi})
    tr = pd.DataFrame(tr_rows).round(4)
    tr.to_csv(T / "transfer_results.csv", index=False)
    log(f"Transfer:\n{tr[['site', 'n', 'roc_auc', 'auc_ci_low', 'auc_ci_high', 'prevalence', 'mean_pred', 'cal_slope']]}")

    # ---------------- 7) Grafikler ----------------
    figs = [
        P.plot_cv_auc({k: v["fold_scores"] for k, v in cv.items()}),
        P.plot_roc({k: v["oof"] for k, v in cv.items()}),
        P.plot_calibration({
            "Ön-anjiyo, kat-dışı (n=242)": (cv["pre_angio"]["oof"]["y"], cv["pre_angio"]["oof"]["logreg_l2"], P.C_NO),
            "Tam, kat-dışı (n=242)": (cv["full"]["oof"]["y"], cv["full"]["oof"]["logreg_l2"], P.C_YES),
        }),
        P.plot_odds_ratios(tab_a, title=f"AS2 — çok değişkenli lojistik regresyon (n = {n_a}); ilişki, nedensellik değil"),
        P.plot_permutation({k: v["permutation"] for k, v in cv.items()}),
        P.plot_transfer(tr[~tr["site"].str.contains("iç CV")].reset_index(drop=True)),
    ]
    for f in figs:
        log(f"Grafik: {f.relative_to(config.PROJECT_ROOT)}")

    summary["cv_summary"] = {k: M.summarize_folds(v["fold_scores"]).to_dict("index") for k, v in cv.items()}
    (T / "phase2_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=float),
                                           encoding="utf-8")
    log("Bitti.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true", help="2 tekrar ile hızlı çalıştırma")
    main(ap.parse_args().quick)
