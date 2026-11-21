"""Yayın öncesi otomatik denetim.

Kontroller:
  1. Rakam tutarlılığı: raporlardaki temel sayılar, üretilen tablolarla aynı mı?
  2. Rapor yapısı: TRIPOD+AI listesinde 52 alt madde var mı; atıf yapılan rapor bölümleri mevcut mu?
  3. Yapısal sızıntı kontrolü: her model önişlemeyi Pipeline içinde mi yapıyor?
  4. Gizlilik: kişisel/mutlak dosya yolu, e-posta adresi veya gizli anahtar kalıbı var mı?
  5. Dosya boyutları.

Çalıştırma (proje kökünden, bütün aşamalar çalıştırıldıktan sonra):
    python scripts/audit_release.py
Çıktı: reports/release_audit.md (ve başarısız kontrol varsa çıkış kodu 1).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402

from mrml import config  # noqa: E402
from mrml import modeling as M  # noqa: E402
from mrml import phase3 as P3  # noqa: E402

T2 = ROOT / "reports" / "tables" / "phase2"
T3 = ROOT / "reports" / "tables" / "phase3"
FR = ROOT / "reports" / "final_report.md"
R2 = ROOT / "reports" / "phase2_report.md"
R3 = ROOT / "reports" / "phase3_report.md"
README = ROOT / "README.md"
CHECKLIST = ROOT / "docs" / "tripod_ai_checklist.md"

results: list[dict] = []


def record(group: str, name: str, ok: bool, detail: str = "") -> None:
    results.append({"group": group, "check": name, "ok": bool(ok), "detail": detail})


def norm(text: str) -> str:
    return text.replace("−", "-").replace(" ", " ")


def fmt(x: float, d: int, lang: str) -> str:
    s = f"{x:.{d}f}"
    return s.replace(".", ",") if lang == "tr" else s


def expect(name: str, value: float, d: int, files: dict[Path, str]) -> None:
    for path, lang in files.items():
        token = fmt(value, d, lang)
        ok = token in norm(path.read_text(encoding="utf-8"))
        record("1-tutarlılık", f"{name} = {token} → {path.name}", ok,
               "" if ok else "rapor metninde bulunamadı")


# ---------------------------------------------------------------------------
def check_numbers() -> None:
    cv2p = pd.read_csv(T2 / "cv_summary_pre_angio.csv", index_col=0)
    cv2f = pd.read_csv(T2 / "cv_summary_full.csv", index_col=0)
    comp2 = pd.read_csv(T2 / "cv_paired_comparisons.csv").set_index("comparison")
    test2 = pd.read_csv(T2 / "locked_test_results.csv")
    tr2 = pd.read_csv(T2 / "transfer_results.csv").set_index("site")
    orA = pd.read_csv(T2 / "odds_ratios_model_A.csv").set_index("term")
    s2 = json.loads((T2 / "phase2_summary.json").read_text(encoding="utf-8"))
    spl = pd.read_csv(T3 / "spline_vs_linear.csv")
    sub = pd.read_csv(T3 / "subgroup_performance.csv")
    thr = pd.read_csv(T3 / "threshold_metrics.csv")
    dc = pd.read_csv(T3 / "decision_curve.csv").set_index("threshold")
    rec = pd.read_csv(T3 / "recalibration.csv")

    all3 = {FR: "tr", README: "en"}
    tr_only = {FR: "tr"}
    expect("CV AUC L2 ön-anjiyo", cv2p.loc["logreg_l2", "roc_auc_mean"], 3, {**all3, R2: "tr"})
    expect("CV AUC L2 tam", cv2f.loc["logreg_l2", "roc_auc_mean"], 3, {**all3, R2: "tr"})
    expect("CV AUC referans", cv2p.loc["baseline_age_sex", "roc_auc_mean"], 3, {**all3, R2: "tr"})
    a4 = comp2.loc["logreg_l2: full − pre_angio (AS4)"]
    for k in ("mean_diff", "ci_low", "ci_high"):
        expect(f"AS4 {k}", a4[k], 3, {**all3, R2: "tr"})
    l2t = test2[(test2.model == "logreg_l2")].set_index("feature_set")
    expect("Kilitli test AUC ön-anjiyo", l2t.loc["pre_angio", "roc_auc"], 3, {FR: "tr", R2: "tr"})
    expect("Kilitli test AUC tam", l2t.loc["full", "roc_auc"], 3, {FR: "tr", R2: "tr"})
    for site in config.OTHER_SITES:
        expect(f"Transfer AUC {site}", tr2.loc[site, "roc_auc"], 3, {**all3, R2: "tr"})
    expect("OR erkek", orA.loc["sex", "odds_ratio"], 2, {**all3, R2: "tr"})
    expect("OR cp=4", orA.loc["cp=4 (ref 1)", "odds_ratio"], 2, {**all3, R2: "tr"})
    expect("OR oldpeak", orA.loc["oldpeak (per 1)", "odds_ratio"], 2, {**tr_only, R2: "tr"})
    expect("LRT p (B vs A)", s2["AS2"]["lrt_B_vs_A"]["p_value"], 3, {**tr_only, R2: "tr"})
    sp = spl[(spl.feature_set == "pre_angio") & (spl.metric == "roc_auc")].iloc[0]
    expect("Spline − doğrusal AUC (ön-anjiyo)", sp["mean_diff"], 3, {**all3, R3: "tr"})
    expect("Spline nominal p", sp["p_value"], 3, {**tr_only, R3: "tr"})
    expect("Spline Holm p", sp["p_holm"], 3, {**tr_only, R3: "tr"})
    w = sub[(sub.feature_set == "pre_angio") & (sub.group == "Kadın")].iloc[0]
    expect("Kadın CITL", w["cal_intercept"], 2, {**all3, R3: "tr"})
    expect("Kadın gözlenen %", w["observed"] * 100, 1, {R3: "tr"})
    expect("Kadın öngörülen %", w["mean_pred"] * 100, 1, {R3: "tr"})
    t90 = thr[(thr.feature_set == "pre_angio") & (thr.rule == "sens90")].iloc[0]
    expect("sens90 duyarlılık", t90["sensitivity_mean"], 2, {**tr_only, R3: "tr"})
    expect("sens90 özgüllük", t90["specificity_mean"], 2, {**tr_only, R3: "tr"})
    for t in (0.2, 0.3, 0.4):
        expect(f"NB L2 ön-anjiyo pt={t}", dc.loc[t, "l2_pre"], 3, {R3: "tr"})
        expect(f"NB herkesi sevk pt={t}", dc.loc[t, "treat_all"], 3, {R3: "tr"})
    va = rec[(rec.site == "Long Beach VA") & (rec.method == "logistic")].iloc[0]
    expect("VA lojistik yeniden kal. eğimi", va["oof_cal_slope"], 2, {**tr_only, R3: "tr"})

    # Örneklem tanımları
    for path in (FR, README):
        txt = norm(path.read_text(encoding="utf-8"))
        for token in ("303", "139", "242", "111", "61", "28"):
            record("1-tutarlılık", f"örneklem sayısı {token} → {path.name}", token in txt)


def check_structure() -> None:
    txt = CHECKLIST.read_text(encoding="utf-8")
    rows = [ln for ln in txt.splitlines() if re.match(r"^\| (\d+[a-g]?) \|", ln)]
    items = [re.match(r"^\| (\d+[a-g]?) \|", ln).group(1) for ln in rows]
    record("2-yapı", "TRIPOD+AI alt madde sayısı = 52", len(items) == 52, f"bulunan {len(items)}")
    record("2-yapı", "TRIPOD+AI maddeleri tekrarsız", len(set(items)) == len(items))
    statuses = {"✅": 0, "⚠️": 0, "➖": 0, "❌": 0}
    for ln in rows:
        for k in statuses:
            if f"| {k}" in ln:
                statuses[k] += 1
    record("2-yapı", "her maddenin tek bir durumu var", sum(statuses.values()) == len(rows),
           json.dumps(statuses, ensure_ascii=False))
    fr = FR.read_text(encoding="utf-8")
    sections = set(re.findall(r"^## (\d+)\.", fr, flags=re.M))
    cited = set(re.findall(r"FR §(\d+)", txt))
    missing = sorted(cited - sections, key=int)
    record("2-yapı", "kontrol listesinde atıf yapılan FR bölümleri mevcut", not missing,
           f"eksik: {missing}" if missing else f"{len(cited)} bölüm")
    for f in ("reports/phase1_report.md", "reports/phase2_report.md", "reports/phase3_report.md",
              "docs/data_dictionary.md", "docs/decisions.md", "docs/research_plan.md"):
        record("2-yapı", f"belge mevcut: {f}", (ROOT / f).exists())
    for png in re.findall(r"\(reports/figures/([\w.]+\.png)\)", README.read_text(encoding="utf-8")):
        record("2-yapı", f"README grafiği mevcut: {png}", (ROOT / "reports" / "figures" / png).exists())


def check_leakage_structure() -> None:
    """Her modelin ilk adımı önişleme ('prep') olan bir Pipeline olmalı; aksi halde atama/
    ölçekleme CV dışında yapılmış olabilir."""
    models = {}
    for fs, feats in config.FEATURE_SETS.items():
        for name, (pipe, _) in M.build_models(feats).items():
            models[f"{fs}/{name}"] = pipe
        models[f"{fs}/spline"] = P3.build_spline_pipeline(feats)[0]
    models["loso"] = P3.loso_pipeline(config.FEATURES_LOSO)[0]
    for name, pipe in models.items():
        ok = isinstance(pipe, Pipeline) and pipe.steps[0][0] == "prep"
        record("3-sızıntı", f"{name}: önişleme Pipeline içinde", ok)
    split = pd.read_csv(config.PRIVATE_DIR / "split_phase2.csv")
    record("3-sızıntı", "kilitli test boyutu 61 ve geliştirme 242",
           (split["split"] == "test").sum() == 61 and (split["split"] == "dev").sum() == 242)


TEXT_EXT = {".py", ".md", ".txt", ".toml", ".csv", ".json", ".log", ".cfg", ".ini", ".yml",
            ".yaml", ".names", ".data", ""}
SKIP_DIRS = {".venv", "__pycache__", ".pytest_cache", ".git"}


def iter_files():
    for p in ROOT.rglob("*"):
        if p.is_file() and not (set(p.relative_to(ROOT).parts) & SKIP_DIRS):
            yield p


def check_privacy_and_size() -> None:
    home = str(Path.home())
    home_variants = {home, home.replace("\\", "/"), Path.home().name}
    patterns = {
        "mutlak Windows kullanıcı yolu": re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+", re.I),
        "mutlak Unix ev dizini": re.compile(r"(?<![\w.])/(home|Users)/[A-Za-z0-9_.-]+/"),
        "e-posta adresi": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
        "gizli anahtar kalıbı": re.compile(
            r"(api[_-]?key|secret|passw(or)?d|token)\s*[:=]\s*['\"][^'\"]{8,}|-----BEGIN [A-Z ]*PRIVATE KEY|"
            r"\bsk-[A-Za-z0-9]{20,}|\bghp_[A-Za-z0-9]{20,}|\bAKIA[0-9A-Z]{16}\b", re.I),
    }
    # Kaynak belgelerdeki bilinen, kamuya açık e-postalar (UCI donör adresi) izinlidir
    allowed_emails = {"aha@ics.uci.edu"}
    # Denetimin kendisi ve kendi çıktı raporu taranmaz (aksi halde önceki bulgular yeniden sayılır)
    skip = {Path(__file__).resolve(), (ROOT / "reports" / "release_audit.md").resolve()}
    hits = []
    for p in iter_files():
        if p.resolve() in skip:
            continue
        data = p.read_bytes()
        for hv in home_variants:
            if len(hv) > 3 and hv.encode("utf-8") in data:
                hits.append((p, "kullanıcı ev dizini / kullanıcı adı"))
        if p.suffix.lower() not in TEXT_EXT:
            continue
        text = data.decode("utf-8", errors="ignore")
        for label, rx in patterns.items():
            for m in rx.finditer(text):
                if label == "e-posta adresi" and m.group(0).lower() in allowed_emails:
                    continue
                # Eşleşen metin rapora yazılmaz (gerçek bir sır olabilir); yalnızca konum ve tür
                line = text.count("\n", 0, m.start()) + 1
                hits.append((p, f"{label}, satır {line}"))
    record("4-gizlilik", "kişisel yol / e-posta / gizli anahtar yok", not hits,
           "; ".join(f"{h[0].relative_to(ROOT)} ({h[1]})" for h in hits[:15]))

    files = list(iter_files())
    total = sum(p.stat().st_size for p in files)
    big = [(p, p.stat().st_size) for p in files if p.stat().st_size > 1_000_000]
    record("5-boyut", f"toplam boyut {total / 1e6:.2f} MB (.venv hariç), {len(files)} dosya", total < 50e6)
    record("5-boyut", "1 MB üstü dosya yok", not big,
           "; ".join(f"{p.relative_to(ROOT)} {s / 1e6:.1f} MB" for p, s in big))


# Yayımlanmayan kişi düzeyi çıktılar ve onları üreten betik (yeniden üretilebilirlik)
PRIVATE_OUTPUTS = {
    "cleveland_typed.csv": "run_phase1.py",
    "phase1/rows_with_missing.csv": "run_phase1.py",
    "phase1/consistency_issues.csv": "run_phase1.py",
    "split_phase2.csv": "run_phase2.py",
    "phase2/locked_test_predictions.csv": "run_phase2.py",
    "phase3/oof_predictions_pre_angio.csv": "run_phase3.py",
    "phase3/oof_predictions_full.csv": "run_phase3.py",
}


def check_inventory() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import release_manifest as RM

    rows = RM.build()
    probs = RM.problems(rows)
    record("6-envanter", f"yayın kümesi: {len(rows)} dosya, lisans kapsamı ve kişi düzeyi veri denetimi",
           not probs, "; ".join(probs[:10]))
    diffs = RM.compare(rows, RM.read()) if RM.MANIFEST.exists() else ["RELEASE_MANIFEST.csv yok"]
    record("6-envanter", "RELEASE_MANIFEST.csv güncel", not diffs, "; ".join(diffs[:10]))
    pats = RM.load_patterns()
    for rel, script in PRIVATE_OUTPUTS.items():
        path = config.PRIVATE_DIR / rel
        relpath = path.relative_to(ROOT).as_posix()
        produced = path.name.split("_pre_angio")[0].split("_full")[0] in \
            (ROOT / "scripts" / script).read_text(encoding="utf-8")
        record("6-envanter", f"{relpath}: yayın dışı, {script} üretir",
               RM.is_ignored(relpath, pats) and produced and path.exists(),
               "" if path.exists() else "dosya yok (betik çalıştırılmamış)")
        if path.exists():
            record("6-envanter", f"{relpath}: kişi düzeyi belirtisi algılanıyor",
                   RM.person_level_reason(path) is not None)
    # Diskte yayın dışı klasörler dışında kişi düzeyi dosya kalmamalı
    stray = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*.csv")
             if p.is_file() and not RM.is_ignored(p.relative_to(ROOT).as_posix(), pats)
             and p.name != RM.MANIFEST.name and RM.person_level_reason(p)]
    record("6-envanter", "yayın kümesinde kişi düzeyi CSV yok", not stray, "; ".join(stray))
    for raw in (ROOT / "data" / "raw").rglob("*"):
        if raw.is_file() and not RM.is_ignored(raw.relative_to(ROOT).as_posix(), pats):
            record("6-envanter", f"ham veri dışlanmamış: {raw.name}", False)
    for f in ("LICENSE", "LICENSES/MIT.txt", "LICENSES/CC-BY-4.0.txt", "LICENSING.md",
              "THIRD_PARTY_NOTICES.md", "CITATION.cff"):
        record("6-envanter", f"lisans/atıf dosyası yayın kümesinde: {f}",
               f in {r["path"] for r in rows})


def check_tests_count() -> None:
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT,
                         capture_output=True, text=True, encoding="utf-8", errors="ignore").stdout
    m = re.search(r"(\d+) tests? collected", out)
    n = int(m.group(1)) if m else -1
    ok = f"{n} tests" in README.read_text(encoding="utf-8")
    record("1-tutarlılık", f"README test sayısı = {n}", ok)


def main() -> int:
    check_numbers()
    check_structure()
    check_leakage_structure()
    check_privacy_and_size()
    check_inventory()
    check_tests_count()
    df = pd.DataFrame(results)
    n_fail = int((~df["ok"]).sum())
    lines = ["# Yayın Öncesi Otomatik Denetim", "",
             f"Toplam kontrol: {len(df)} · Başarısız: **{n_fail}**", "",
             "| Grup | Kontrol | Sonuç | Ayrıntı |", "|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['group']} | {r['check']} | {'✅' if r['ok'] else '❌'} | {r['detail']} |")
    (ROOT / "reports" / "release_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(df.groupby("group")["ok"].agg(["count", "sum"]))
    if n_fail:
        print(df[~df["ok"]].to_string())
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
