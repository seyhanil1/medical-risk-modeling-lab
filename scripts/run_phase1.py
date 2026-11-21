"""Aşama 1 boru hattı: indir -> doğrula -> denetle -> betimle -> grafikle.

Çalıştırma (proje kökünden):
    python scripts/run_phase1.py            # veri yoksa indirir
    python scripts/run_phase1.py --refresh  # arşivi yeniden indirir

Model eğitimi YAPMAZ.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from mrml import audit, config, data_io, dictionary, plots  # noqa: E402
from mrml import stats as mstats  # noqa: E402


def main(refresh: bool = False) -> None:
    zip_path = data_io.download_zip(overwrite=refresh)
    data_io.extract_zip(zip_path)
    files = {
        config.ZIP_FILENAME: zip_path,
        config.CLEVELAND_FILENAME: config.EXTRACT_DIR / config.CLEVELAND_FILENAME,
        config.NAMES_FILENAME: config.EXTRACT_DIR / config.NAMES_FILENAME,
        # Aşama 2-3 dış değerlendirmede kullanılan diğer merkez dosyaları
        **{f: config.EXTRACT_DIR / f for f in config.OTHER_SITES.values()},
    }
    checks = data_io.verify_checksums(files)
    prov = data_io.write_provenance(checks)
    bad = [k for k, v in checks.items() if not v["matches"]]
    if bad:
        raise SystemExit(f"SHA-256 uyuşmazlığı: {bad}. Kaynak değişmiş olabilir; inceleyin.")
    print(f"[ok] Kaynak ve özetler kaydedildi: {prov.relative_to(config.PROJECT_ROOT)}")

    df = data_io.load_cleveland()
    res = audit.run_audit(df)
    print(f"[ok] Boyut: {res['shape']}")

    private = config.PRIVATE_DIR / "phase1"
    for d in (config.TABLES_DIR, config.PRIVATE_DIR, private, config.DOCS_DIR):
        d.mkdir(parents=True, exist_ok=True)

    # Kişi düzeyi (yayımlanmaz): tipleri düzeltilmiş tam veri; değerler değiştirilmedi.
    df.to_csv(config.PRIVATE_DIR / "cleveland_typed.csv", index_label="row")

    res["dtypes"].to_csv(config.TABLES_DIR / "variable_types.csv")
    res["missing"].to_csv(config.TABLES_DIR / "missing_summary.csv")
    # Kişi düzeyi denetim çıktıları (yayımlanmaz): hasta satırları ve satır+değer listeleri
    res["missing_rows"].to_csv(private / "rows_with_missing.csv", index_label="row")
    res["consistency"].to_csv(private / "consistency_issues.csv", index=False)
    # Yayımlanan toplulaştırılmış sürüm: kontrol türü başına sayı
    (res["consistency"].groupby(["variable", "check", "severity"]).size()
        .rename("n_records").reset_index()
        .to_csv(config.TABLES_DIR / "consistency_summary.csv", index=False))
    res["target_distribution"].to_csv(config.TABLES_DIR / "target_distribution.csv")
    dictionary.as_frame().to_csv(config.TABLES_DIR / "data_dictionary.csv", index=False)
    (config.DOCS_DIR / "data_dictionary.md").write_text(
        dictionary.to_markdown(res["dtypes"]), encoding="utf-8")

    desc_all = mstats.describe_continuous(df)
    desc_by = mstats.describe_continuous(df, by=config.TARGET_BINARY)
    pd.concat([desc_all, desc_by]).to_csv(config.TABLES_DIR / "descriptive_continuous.csv", index=False)
    with open(config.TABLES_DIR / "categorical_crosstabs.csv", "w", encoding="utf-8", newline="") as fh:
        for col in config.CATEGORICAL:
            fh.write(f"# {col}\n")
            mstats.categorical_crosstab(df, col).to_csv(fh)
            fh.write("\n")
    tests = mstats.univariate_tests(df)
    tests.to_csv(config.TABLES_DIR / "univariate_tests.csv", index=False)
    corr = mstats.spearman_matrix(df)
    corr.round(3).to_csv(config.TABLES_DIR / "spearman_correlation.csv")
    mstats.missing_vs_target(df).to_csv(config.TABLES_DIR / "missing_vs_target.csv")

    summary = {
        "shape": res["shape"],
        "missing_cells": int(df[config.COLUMNS].isna().sum().sum()),
        "rows_with_missing": int(len(res["missing_rows"])),
        "duplicates": res["duplicates"],
        "consistency_issue_counts": res["consistency"]["severity"].value_counts().to_dict(),
        "target_num_counts": {str(k): int(v) for k, v in res["target_distribution"]["n"].items()},
        "target_binary_counts": {str(k): int(v) for k, v in
                                 df[config.TARGET_BINARY].value_counts().sort_index().items()},
    }
    (config.TABLES_DIR / "audit_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    figs = [
        plots.plot_target_distribution(df),
        plots.plot_missingness(df),
        plots.plot_continuous_by_class(df),
        plots.plot_categorical_rates(df),
        plots.plot_correlation(corr),
        plots.plot_effect_sizes(tests),
        plots.plot_age_sex(df),
    ]
    for f in figs:
        print(f"[ok] Grafik: {f.relative_to(config.PROJECT_ROOT)}")
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(tests)
        print(desc_by)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true", help="UCI arşivini yeniden indir")
    main(ap.parse_args().refresh)
