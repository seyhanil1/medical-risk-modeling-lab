"""Veriyi indirme, bütünlük doğrulama (SHA-256) ve yükleme."""
from __future__ import annotations

import hashlib
import json
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import config


def sha256_of(path: Path, chunk_size: int = 1 << 16) -> str:
    """Bir dosyanın SHA-256 özetini hesaplar."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def download_zip(dest_dir: Path = config.RAW_DIR, url: str = config.UCI_ZIP_URL,
                 overwrite: bool = False) -> Path:
    """UCI arşivini indirir (varsa ve overwrite=False ise tekrar indirmez)."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / config.ZIP_FILENAME
    if dest.exists() and not overwrite:
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": "medical-risk-modeling-lab/0.1"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as out:
        out.write(resp.read())
    return dest


def extract_zip(zip_path: Path, extract_dir: Path = config.EXTRACT_DIR) -> Path:
    """Arşivi açar; zip içindeki yolların hedef klasörün dışına çıkmasını engeller."""
    extract_dir.mkdir(parents=True, exist_ok=True)
    root = extract_dir.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            target = (extract_dir / member).resolve()
            if root not in target.parents and target != root:
                raise ValueError(f"Güvensiz zip girdisi: {member}")
        zf.extractall(extract_dir)
    return extract_dir


def verify_checksums(files: dict[str, Path]) -> dict[str, dict]:
    """Beklenen ve ölçülen SHA-256 değerlerini karşılaştırır."""
    result = {}
    for name, path in files.items():
        actual = sha256_of(path)
        expected = config.EXPECTED_SHA256.get(name)
        result[name] = {
            "path": path.relative_to(config.PROJECT_ROOT).as_posix()
            if path.is_relative_to(config.PROJECT_ROOT) else str(path.name),
            "sha256": actual,
            "expected_sha256": expected,
            "matches": expected is None or actual == expected,
            "size_bytes": path.stat().st_size,
        }
    return result


def write_provenance(checks: dict[str, dict], out_path: Path | None = None) -> Path:
    """Kaynak, sürüm, lisans ve özet bilgilerini JSON olarak kaydeder."""
    out_path = out_path or config.METADATA_DIR / "provenance.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "dataset": "Heart Disease (UCI ML Repository id 45) — Cleveland subset",
        "subset_file": config.CLEVELAND_FILENAME,
        "source_page": config.UCI_DATASET_PAGE,
        "download_url": config.UCI_ZIP_URL,
        "doi": f"https://doi.org/{config.UCI_DOI}",
        "license": config.UCI_LICENSE,
        "version_note": (
            "UCI tek bir sürüm numarası yayımlamaz. Sürüm, DOI + arşivin SHA-256 özeti ile "
            "sabitlenmiştir. Bağış tarihi 1988-06-30 (UCI sayfası); heart-disease.names "
            "dosyası 'July, 1988' ve donör David W. Aha olarak belirtir. Arşivdeki dosyaların "
            "zaman damgası 2023-05-22'dir."
        ),
        "dataset_citation": (
            "Janosi, A., Steinbrunn, W., Pfisterer, M., & Detrano, R. (1989). Heart Disease "
            "[Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C52P4X"
        ),
        "introductory_paper": (
            "Detrano, R., Janosi, A., Steinbrunn, W., Pfisterer, M., Schmid, J., Sandhu, S., "
            "Guppy, K., Lee, S., & Froelicher, V. (1989). International application of a new "
            "probability algorithm for the diagnosis of coronary artery disease. American "
            "Journal of Cardiology, 64(5), 304-310. https://doi.org/10.1016/0002-9149(89)90524-9"
        ),
        "principal_investigators_requested_in_publications": [
            "Hungarian Institute of Cardiology, Budapest: Andras Janosi, M.D.",
            "University Hospital, Zurich: William Steinbrunn, M.D.",
            "University Hospital, Basel: Matthias Pfisterer, M.D.",
            "V.A. Medical Center, Long Beach and Cleveland Clinic Foundation: Robert Detrano, M.D., Ph.D.",
        ],
        "files": checks,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    out_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def load_raw_cleveland(path: Path | None = None) -> pd.DataFrame:
    """processed.cleveland.data dosyasını okur. '?' eksik değer olarak işaretlenir.

    Değerler ham haliyle (float) döner; tip dönüşümü `clean_types` ile yapılır.
    """
    path = path or config.EXTRACT_DIR / config.CLEVELAND_FILENAME
    df = pd.read_csv(path, header=None, names=config.COLUMNS, na_values=["?"],
                     skipinitialspace=True)
    return df


def clean_types(df: pd.DataFrame) -> pd.DataFrame:
    """Tamsayı kodlu değişkenleri boş değer destekli Int64'e çevirir.

    Değer değiştirilmez; yalnızca gösterim tipi düzeltilir. Tamsayı olmayan bir kod
    bulunursa hata verir (sessiz yuvarlama yapılmaz).
    """
    out = df.copy()
    int_cols = [c for c in config.COLUMNS if c != "oldpeak"]
    for col in int_cols:
        s = out[col]
        non_int = s.dropna() % 1 != 0
        if non_int.any():
            raise ValueError(f"{col} sütununda tamsayı olmayan değer var: "
                             f"{s.dropna()[non_int].unique()[:5]}")
        out[col] = s.astype("Int64")
    out["oldpeak"] = out["oldpeak"].astype(float)
    return out


def add_binary_target(df: pd.DataFrame) -> pd.DataFrame:
    """num (0-4) -> disease (0 = num 0, 1 = num 1-4). Ham `num` korunur."""
    out = df.copy()
    out[config.TARGET_BINARY] = (out[config.TARGET_RAW] > 0).astype("Int64")
    out.loc[out[config.TARGET_RAW].isna(), config.TARGET_BINARY] = pd.NA
    return out


def load_cleveland(path: Path | None = None) -> pd.DataFrame:
    """Ham veriyi okur, tipleri düzeltir ve ikili hedefi ekler."""
    return add_binary_target(clean_types(load_raw_cleveland(path)))


def ensure_data(verify: bool = True) -> Path:
    """Veri yoksa indirir ve açar; isteğe bağlı olarak SHA-256 doğrulaması yapar."""
    cleveland = config.EXTRACT_DIR / config.CLEVELAND_FILENAME
    if not cleveland.exists():
        zip_path = download_zip()
        extract_zip(zip_path)
    if verify:
        actual = sha256_of(cleveland)
        expected = config.EXPECTED_SHA256[config.CLEVELAND_FILENAME]
        if actual != expected:
            raise RuntimeError(
                f"SHA-256 uyuşmazlığı: {cleveland.name} beklenen {expected}, bulunan {actual}")
    return cleveland


__all__ = [
    "sha256_of", "download_zip", "extract_zip", "verify_checksums", "write_provenance",
    "load_raw_cleveland", "clean_types", "add_binary_target", "load_cleveland", "ensure_data",
]


def load_site(filename: str, zero_as_missing: tuple[str, ...] = ("trestbps", "chol")) -> pd.DataFrame:
    """Diğer UCI merkezlerinden işlenmiş dosyayı okur (Aşama 2 transfer testi).

    Bu dosyalarda bazı ölçümler için 0 eksik değer yerine kullanılmıştır (ör. İsviçre'de
    bütün `chol` değerleri 0). Fizyolojik olarak imkânsız sıfırlar NaN yapılır.
    """
    path = config.EXTRACT_DIR / filename
    actual = sha256_of(path)
    expected = config.EXPECTED_SHA256.get(filename)
    if expected and actual != expected:
        raise RuntimeError(f"SHA-256 uyuşmazlığı: {filename}")
    df = load_raw_cleveland(path)
    for col in zero_as_missing:
        df.loc[df[col] == 0, col] = float("nan")
    return add_binary_target(clean_types(df))
