"""Aşama 3 boru hattı: karar eğrisi, eşik metrikleri, alt gruplar, yeniden kalibrasyon,
merkez-dışı-bırak doğrulama ve spline'lı lojistik model.

Önkoşul: scripts/run_phase2.py çalıştırılmış olmalı (kilitli test ayrımı yeniden kullanılır).

Çalıştırma (proje kökünden):
    python scripts/run_phase3.py
    python scripts/run_phase3.py --quick
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
from sklearn.base import clone  # noqa: E402
from sklearn.exceptions import ConvergenceWarning  # noqa: E402

from mrml import config, data_io  # noqa: E402
from mrml import modeling as M  # noqa: E402
from mrml import phase3 as P3  # noqa: E402
from mrml import plots_phase3 as PL  # noqa: E402

T = config.TABLES_DIR / "phase3"
PRIV = config.PRIVATE_DIR / "phase3"   # kişi düzeyi, yayımlanmaz
L2 = config.PRIMARY_MODEL


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def load_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    path = config.PRIVATE_DIR / "split_phase2.csv"
    if not path.exists():
        raise SystemExit("Önce scripts/run_phase2.py çalıştırın (kilitli test ayrımı yok).")
    split = pd.read_csv(path, index_col="row")["split"]
    return df[split == "dev"], df[split == "test"]


def main(quick: bool = False) -> None:
    T.mkdir(parents=True, exist_ok=True)
    PRIV.mkdir(parents=True, exist_ok=True)
    warnings.simplefilter("ignore", ConvergenceWarning)
    data_io.ensure_data()
    df = data_io.load_cleveland()
    dev, test = load_split(df)
    y_dev = dev[config.TARGET_BINARY].astype(int).to_numpy()
    repeats = 2 if quick else config.OUTER_REPEATS
    summary: dict = {"n_dev": len(dev), "n_test": len(test), "outer_repeats": repeats}

    # ---------------- 1) Doğrusal vs spline L2 (iç içe CV, aynı katlar) ----------------
    cv = {}
    for fs, feats in config.FEATURE_SETS.items():
        models = {k: v for k, v in M.build_models(feats).items() if k in ("baseline_age_sex", L2)}
        models["logreg_spline"] = P3.build_spline_pipeline(feats)
        cv[fs] = M.nested_cv(dev, y_dev, models, feats, n_repeats=repeats)
        cv[fs]["fold_scores"].assign(feature_set=fs).to_csv(T / f"cv_fold_scores_{fs}.csv", index=False)
        M.summarize_folds(cv[fs]["fold_scores"]).to_csv(T / f"cv_summary_{fs}.csv")
        cv[fs]["oof"].assign(row=dev.index.to_numpy()).to_csv(PRIV / f"oof_predictions_{fs}.csv", index=False)
        log(f"CV {fs}:\n{M.summarize_folds(cv[fs]['fold_scores'])[['roc_auc_mean', 'brier_mean', 'cal_slope_mean']]}")
    comp = pd.DataFrame([{"feature_set": fs, **M.paired_comparison(cv[fs]["fold_scores"], "logreg_spline", L2)}
                         for fs in cv]
                        + [{"feature_set": fs, **M.paired_comparison(cv[fs]["fold_scores"], "logreg_spline", L2,
                                                                     metric="brier")} for fs in cv])
    from mrml.stats import holm_adjust
    comp["p_holm"] = holm_adjust(comp["p_value"].tolist())   # 4 spline karşılaştırması = 1 aile
    comp = comp.round(4)
    comp.to_csv(T / "spline_vs_linear.csv", index=False)
    log(f"Spline − doğrusal:\n{comp[['feature_set', 'metric', 'mean_diff', 'ci_low', 'ci_high', 'p_value', 'p_holm']]}")

    # ---------------- 2) Karar eğrisi (kat-dışı tahminler) ----------------
    oof_pre, oof_full = cv["pre_angio"]["oof"], cv["full"]["oof"]
    preds = {"baseline": oof_pre["baseline_age_sex"], "l2_pre": oof_pre[L2],
             "spline_pre": oof_pre["logreg_spline"], "l2_full": oof_full[L2]}
    dc = P3.decision_curve(oof_pre["y"], preds)
    dc.round(4).to_csv(T / "decision_curve.csv", index=False)
    key_t = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    nb_tab = dc[dc["threshold"].isin(key_t)].round(4)
    nb_vs_all = P3.bootstrap_net_benefit_diff(oof_pre["y"], preds["l2_pre"], np.ones(len(oof_pre)), key_t)
    nb_full_pre = P3.bootstrap_net_benefit_diff(oof_pre["y"], preds["l2_full"], preds["l2_pre"], key_t)
    pd.concat([nb_vs_all.assign(comparison="l2_pre − treat_all"),
               nb_full_pre.assign(comparison="l2_full − l2_pre")]).round(4).to_csv(
        T / "net_benefit_differences.csv", index=False)
    log(f"Net fayda:\n{nb_tab}\n{nb_vs_all.round(4)}\n{nb_full_pre.round(4)}")

    # ---------------- 3) Eşik metrikleri (eşik yalnızca eğitim katında) ----------------
    thr_rows = []
    for fs, feats in config.FEATURE_SETS.items():
        pipe, grid = M.build_models(feats)[L2]
        r = P3.cv_threshold_metrics(dev, y_dev, pipe, grid, feats, n_repeats=repeats)
        r.assign(feature_set=fs).to_csv(T / f"threshold_folds_{fs}.csv", index=False)
        s = r.groupby("rule")[["threshold", "sensitivity", "specificity", "ppv", "npv", "positive_rate"]]
        thr_rows.append(s.mean().add_suffix("_mean").join(s.std().add_suffix("_sd")).assign(feature_set=fs))
    thr = pd.concat(thr_rows).round(3)
    thr.to_csv(T / "threshold_metrics.csv")
    log(f"Eşik metrikleri:\n{thr[[c for c in thr.columns if c.endswith('_mean')] + ['feature_set']]}")

    # ---------------- 4) Alt grup performansı ----------------
    sub_rows = []
    groups = {"Kadın": dev["sex"] == 0, "Erkek": dev["sex"] == 1,
              "Yaş < 55": dev["age"] < 55, "Yaş ≥ 55": dev["age"] >= 55}
    for fs in cv:
        oof = cv[fs]["oof"]
        for gname, mask in groups.items():
            g = pd.Series(np.where(mask.to_numpy(), gname, None))
            t = P3.subgroup_performance(oof["y"].to_numpy(), oof[L2].to_numpy(), g)
            sub_rows.append(t.assign(feature_set=fs))
    sub = pd.concat(sub_rows, ignore_index=True).round(4)
    sub.to_csv(T / "subgroup_performance.csv", index=False)
    # Gruplar arası FARK için doğrudan bootstrap GA (örtüşen GA'lar eşitlik kanıtı değildir)
    diff_rows = []
    for fs in cv:
        oof = cv[fs]["oof"]
        for a, b, mask in [("Kadın", "Erkek", (dev["sex"] == 0).to_numpy()),
                           ("Yaş < 55", "Yaş ≥ 55", (dev["age"] < 55).to_numpy())]:
            diff_rows.append({"feature_set": fs, "group_a": a, "group_b": b,
                              **P3.subgroup_difference(oof["y"].to_numpy(), oof[L2].to_numpy(), mask)})
    sub_diff = pd.DataFrame(diff_rows).round(4)
    sub_diff.to_csv(T / "subgroup_differences.csv", index=False)
    log(f"Alt grup farkları:\n{sub_diff}")
    log(f"Alt gruplar:\n{sub}")

    # ---------------- 5) Yeniden kalibrasyon (Aşama 2 transfer modeli) ----------------
    feats_tr = config.FEATURES_TRANSFER
    y_all = df[config.TARGET_BINARY].astype(int).to_numpy()
    pipe, grid = M.build_models(feats_tr)[L2]
    est_tr = M.make_search(pipe, grid, config.RANDOM_SEED).fit(df[feats_tr], y_all)
    recal_rows, recal_curves = [], {}
    for site, fname in config.OTHER_SITES.items():
        s = data_io.load_site(fname)
        ys = s[config.TARGET_BINARY].astype(int).to_numpy()
        p = est_tr.predict_proba(s[feats_tr])[:, 1]
        r = P3.cv_recalibration(ys, p, n_repeats=5 if quick else 20)
        recal_rows.append(r["summary"].reset_index().assign(site=site, n=len(s), events=int(ys.sum())))
        recal_curves[site] = {m: (ys, q) for m, q in r["oof"].items()}
    recal = pd.concat(recal_rows, ignore_index=True).round(4)
    recal.to_csv(T / "recalibration.csv", index=False)
    log(f"Yeniden kalibrasyon:\n{recal}")

    # ---------------- 6) Merkez-dışı-bırak (LOSO) ----------------
    feats_lo = config.FEATURES_LOSO
    sites = {"Cleveland": df}
    for site, fname in config.OTHER_SITES.items():
        sites[site] = data_io.load_site(fname)
    loso_tab, _ = P3.loso(sites, feats_lo)
    # Karşılaştırma: yalnızca Cleveland ile eğitilen aynı özellikli model
    pipe, grid = P3.loso_pipeline(feats_lo)
    est_cl = M.make_search(pipe, grid, config.RANDOM_SEED).fit(df[feats_lo], y_all)
    cl_rows = []
    for site in config.OTHER_SITES:
        d = sites[site]
        yy = d[config.TARGET_BINARY].astype(int).to_numpy()
        pp = est_cl.predict_proba(d[feats_lo])[:, 1]
        auc, lo, hi = M.bootstrap_ci(yy, pp)
        cl_rows.append({"held_out": site, "trained_on": "yalnız Cleveland", "n_test": len(d),
                        **M.metrics(yy, pp), "auc_ci_low": lo, "auc_ci_high": hi})
    loso_all = pd.concat([loso_tab.assign(trained_on="diğer 3 merkez"), pd.DataFrame(cl_rows)],
                         ignore_index=True).round(4)
    loso_all.to_csv(T / "loso.csv", index=False)
    missing_by_site = pd.DataFrame({s: d[feats_lo].isna().mean().round(3) for s, d in sites.items()})
    missing_by_site.to_csv(T / "loso_missing_by_site.csv")
    log(f"LOSO:\n{loso_all[['held_out', 'trained_on', 'n_test', 'roc_auc', 'auc_ci_low', 'auc_ci_high', 'prevalence', 'mean_pred', 'cal_slope']]}")

    # ---------------- 7) Spline biçimleri (bütün Cleveland) ----------------
    fs_feats = config.FEATURES_PRE_ANGIO
    sp_pipe, sp_grid = P3.build_spline_pipeline(fs_feats)
    sp = M.make_search(sp_pipe, sp_grid, config.RANDOM_SEED).fit(df[fs_feats], y_all)
    lin_pipe, lin_grid = M.build_models(fs_feats)[L2]
    lin = M.make_search(lin_pipe, lin_grid, config.RANDOM_SEED).fit(df[fs_feats], y_all)
    best_sp = sp.best_estimator_
    rng = np.random.default_rng(config.RANDOM_SEED)
    shapes, labels = {}, {"age": "Yaş (yıl)", "thalach": "Maks. kalp hızı (atım/dk)",
                          "oldpeak": "ST çökmesi (mm)", "chol": "Kolesterol (mg/dl)"}
    n_boot = 40 if quick else 200
    boots = [rng.integers(0, len(df), len(df)) for _ in range(n_boot)]
    fitted = [clone(best_sp).fit(df.iloc[i][fs_feats], y_all[i]) for i in boots]
    for var in labels:
        grid_v = np.linspace(*np.percentile(df[var], [2.5, 97.5]), 60)
        curves = np.array([P3.partial_logodds(e, df, var, grid_v, fs_feats) for e in fitted])
        shapes[var] = {"grid": grid_v, "spline": P3.partial_logodds(best_sp, df, var, grid_v, fs_feats),
                       "lo": np.percentile(curves, 2.5, axis=0), "hi": np.percentile(curves, 97.5, axis=0),
                       "linear": P3.partial_logodds(lin.best_estimator_, df, var, grid_v, fs_feats),
                       "label": labels[var], "rug": df[var].to_numpy()}
    pd.DataFrame({f"{v}_{k}": d[k] for v, d in shapes.items() for k in ("grid", "spline", "lo", "hi", "linear")}
                 ).round(4).to_csv(T / "spline_shapes.csv", index=False)

    # ---------------- 8) Kilitli test (spline, tek seferlik, bilgi amaçlı) ----------------
    y_test = test[config.TARGET_BINARY].astype(int).to_numpy()
    lt = []
    for fs, feats in config.FEATURE_SETS.items():
        pipe, grid = P3.build_spline_pipeline(feats)
        e = M.make_search(pipe, grid, config.RANDOM_SEED).fit(dev[feats], y_dev)
        p = e.predict_proba(test[feats])[:, 1]
        auc, lo, hi = M.bootstrap_ci(y_test, p)
        lt.append({"feature_set": fs, "model": "logreg_spline", **M.metrics(y_test, p),
                   "auc_ci_low": lo, "auc_ci_high": hi})
    pd.DataFrame(lt).round(4).to_csv(T / "locked_test_spline.csv", index=False)

    # ---------------- 9) Grafikler ----------------
    prev = float(oof_pre["y"].mean())
    figs = [
        PL.plot_decision_curve(dc, {"baseline": ("Referans (yaş+cinsiyet)", PL.GREY),
                                    "l2_pre": ("L2 — anjiyografi öncesi", PL.C_NO),
                                    "l2_full": ("L2 — tam (+ca, thal)", PL.C_YES)}, prev),
        PL.plot_recalibration(recal_curves),
        PL.plot_loso(loso_tab.reset_index(drop=True)),
        PL.plot_spline_shapes(shapes),
        PL.plot_subgroups(sub[sub["roc_auc"].notna()].reset_index(drop=True)),
    ]
    for f in figs:
        log(f"Grafik: {f.relative_to(config.PROJECT_ROOT)}")

    summary.update({
        "spline_vs_linear": comp.to_dict("records"),
        "threshold_metrics": thr.reset_index().to_dict("records"),
        "loso": loso_all.to_dict("records"),
        "spline_C": float(sp.best_params_["model__C"]),
    })
    (T / "phase3_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=float),
                                           encoding="utf-8")
    log("Bitti.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true")
    main(ap.parse_args().quick)
