"""Yayın paketinin dosya envanteri: hangi dosyalar depoya girer, lisansları ne?

Git veya ek bağımlılık gerektirmez: `.gitignore` kurallarını bu projede kullanılan alt kümeyle
(yorum, `dizin/`, kök-sabitli `a/b`, `*`/`?`/`[...]` jokerleri) uygular. Olumsuzlama (`!`)
desteklenmez; `.gitignore`'da varsa hata verir.

Kullanım (proje kökünden):
    python scripts/release_manifest.py           # RELEASE_MANIFEST.csv dosyasını yazar
    python scripts/release_manifest.py --check   # kayıtlı envanterle karşılaştırır (çıkış 1 = fark)

Envanter her dosya için yol, boyut, SHA-256, kategori ve lisans içerir. Kişi düzeyinde veri
taşıyan bir dosya yayın kümesindeyse veya bir dosya hiçbir lisans kapsamına girmiyorsa hata verir.
"""
from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "RELEASE_MANIFEST.csv"

# Her çalıştırmada içeriği değişen dosyalar: envanterde yer alır, ama --check yalnızca
# varlıklarını denetler, SHA-256'larını karşılaştırmaz.
VOLATILE = {
    "data/metadata/provenance.json",   # indirme zaman damgası
    "reports/release_audit.md",        # denetimin kendi çıktısı
}

# Kişi düzeyi veri belirtileri (CSV başlığında sütun adı olarak): satır/kişi kimliği ya da
# kişi bazlı gözlenen sonuç. ("num"/"disease" toplulaştırılmış tablolarda da sütun adı olduğu
# için belirti sayılmaz; kişi düzeyi tabloları zaten "row" ile anahtarlanır.)
PERSON_LEVEL_COLUMNS = {"row", "y", "patient", "patient_id", "id"}
PERSON_LEVEL_SUFFIX = re.compile(r"_(indices|ids|rows)$")


# ---------------------------------------------------------------------------
# .gitignore eşleştirme
# ---------------------------------------------------------------------------
def load_patterns(path: Path = ROOT / ".gitignore") -> list[str]:
    pats = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("!"):
            raise ValueError(f"Olumsuzlama desteklenmez: {line}")
        pats.append(line)
    return pats


def _seg_match(parts: list[str], pat_parts: list[str]) -> bool:
    return len(parts) >= len(pat_parts) and all(
        fnmatch.fnmatchcase(a, b) for a, b in zip(parts, pat_parts))


def is_ignored(rel: str, patterns: list[str]) -> bool:
    parts = rel.split("/")
    for pat in patterns:
        dir_only = pat.endswith("/")
        p = pat.rstrip("/").lstrip("/")
        if "/" in p:                                    # kök-sabitli desen
            pp = p.split("/")
            if dir_only:
                if len(parts) > len(pp) and _seg_match(parts, pp):
                    return True
            elif _seg_match(parts, pp):                 # dosya ya da altında bir şey
                return True
        else:                                           # herhangi bir düzeydeki ad
            candidates = parts[:-1] if dir_only else parts
            if any(fnmatch.fnmatchcase(c, p) for c in candidates):
                return True
    return False


def release_files(root: Path = ROOT) -> list[str]:
    pats = load_patterns(root / ".gitignore")
    out = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        # .git/ Git'in kendi deposudur; yayın içeriği değildir
        if rel == MANIFEST.name or rel.startswith(".git/") or is_ignored(rel, pats):
            continue
        out.append(rel)
    return sorted(out)


# ---------------------------------------------------------------------------
# Sınıflandırma (LICENSING.md ile aynı kapsam)
# ---------------------------------------------------------------------------
def classify(rel: str) -> tuple[str, str]:
    if rel == "LICENSE" or rel == "LICENSES/MIT.txt":
        return "license-text", "MIT (license text)"
    if rel == "LICENSES/CC-BY-4.0.txt":
        return "license-text", "CC BY 4.0 legal code (Creative Commons, verbatim)"
    if rel.startswith(("src/", "scripts/", "tests/")) or rel in {
            "pyproject.toml", "requirements.txt", "requirements-lock.txt", ".gitignore", ".gitattributes"}:
        return "code", "MIT"
    if rel in {"docs/data_dictionary.md", "docs/tripod_ai_checklist.md"}:
        return "adapted-content", "CC BY 4.0 (adaptation; see THIRD_PARTY_NOTICES.md)"
    if rel.startswith("reports/figures/") and rel.endswith(".png"):
        return "figure", "CC BY 4.0"
    if rel.startswith("reports/tables/") or rel == "data/metadata/provenance.json":
        return "aggregate-table", "CC BY 4.0 (derived from UCI data, CC BY 4.0)"
    if rel in {"README.md", "LICENSING.md", "THIRD_PARTY_NOTICES.md", "CITATION.cff"} or (
            rel.startswith(("reports/", "docs/")) and rel.endswith(".md")):
        return "content", "CC BY 4.0"
    return "UNCLASSIFIED", "UNKNOWN"


def person_level_reason(path: Path) -> str | None:
    """Dosya kişi düzeyinde veri taşıyor gibi görünüyorsa nedenini döndürür."""
    if path.suffix.lower() == ".csv":
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines()
                 if ln and not ln.startswith("#")]
        if not lines:
            return None
        cols = {c.strip().strip('"').lower() for c in next(csv.reader([lines[0]]))}
        hit = cols & PERSON_LEVEL_COLUMNS
        if hit:
            return f"kişi düzeyi sütun: {sorted(hit)}"
        suf = [c for c in cols if PERSON_LEVEL_SUFFIX.search(c)]
        if suf:
            return f"satır kimliği listesi sütunu: {suf}"
    if path.suffix.lower() == ".json":
        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if PERSON_LEVEL_SUFFIX.search(str(k)) and isinstance(v, list) and v:
                        return f"boş olmayan satır kimliği listesi: {k}"
                    r = walk(v)
                    if r:
                        return r
            elif isinstance(o, list):
                for v in o:
                    r = walk(v)
                    if r:
                        return r
            return None
        return walk(json.loads(path.read_text(encoding="utf-8")))
    return None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(root: Path = ROOT) -> list[dict]:
    rows = []
    for rel in release_files(root):
        cat, lic = classify(rel)
        p = root / rel
        rows.append({"path": rel, "bytes": p.stat().st_size, "sha256": sha256(p),
                     "category": cat, "license": lic,
                     "person_level": person_level_reason(p) or ""})
    return rows


def problems(rows: list[dict]) -> list[str]:
    out = []
    for r in rows:
        if r["category"] == "UNCLASSIFIED":
            out.append(f"lisans kapsamı yok: {r['path']}")
        if r["person_level"]:
            out.append(f"kişi düzeyi veri yayın kümesinde: {r['path']} ({r['person_level']})")
        if r["path"].startswith(("data/raw/", "data/private/")):
            out.append(f"yayımlanmaması gereken klasör: {r['path']}")
    return out


def write(rows: list[dict], path: Path = MANIFEST) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "bytes", "sha256", "category", "license"],
                           lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})


def read(path: Path = MANIFEST) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def compare(current: list[dict], recorded: list[dict]) -> list[str]:
    cur = {r["path"]: r for r in current}
    rec = {r["path"]: r for r in recorded}
    diffs = [f"envantere eklenmemiş dosya: {p}" for p in sorted(cur.keys() - rec.keys())]
    diffs += [f"envanterde olup diskte olmayan dosya: {p}" for p in sorted(rec.keys() - cur.keys())]
    for p in sorted(cur.keys() & rec.keys()):
        if p not in VOLATILE and cur[p]["sha256"] != rec[p]["sha256"]:
            diffs.append(f"içerik değişmiş: {p}")
    return diffs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    rows = build()
    errs = problems(rows)
    if args.check:
        if not MANIFEST.exists():
            errs.append("RELEASE_MANIFEST.csv yok")
        else:
            errs += compare(rows, read())
    else:
        if not errs:
            write(rows)
    total = sum(r["bytes"] for r in rows)
    by_cat: dict[str, int] = {}
    for r in rows:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
    print(f"{len(rows)} dosya, {total / 1e6:.2f} MB · " +
          ", ".join(f"{k}: {v}" for k, v in sorted(by_cat.items())))
    for e in errs:
        print("HATA:", e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
