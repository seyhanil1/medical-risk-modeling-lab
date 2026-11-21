"""Proje genelinde kullanılan sabitler ve göreli yollar.

Bütün yollar proje kök dizinine göre hesaplanır; sabit yerel bilgisayar yolu yoktur.
"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
EXTRACT_DIR = RAW_DIR / "uci_zip"
# Kişi düzeyindeki bütün çıktılar (hasta satırları, kişi bazlı tahmin + gözlenen sonuç,
# satır numarası anahtarlı dosyalar) yalnızca burada tutulur. Klasör .gitignore ile yayın
# dışıdır; içeriği run_phase1-3.py ile yeniden üretilir. Bkz. README "Data not published".
PRIVATE_DIR = DATA_DIR / "private"
METADATA_DIR = DATA_DIR / "metadata"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"
DOCS_DIR = PROJECT_ROOT / "docs"

# --- Kaynak bilgileri (UCI Machine Learning Repository, dataset id 45) ---
UCI_DATASET_PAGE = "https://archive.ics.uci.edu/dataset/45/heart+disease"
UCI_ZIP_URL = "https://archive.ics.uci.edu/static/public/45/heart+disease.zip"
UCI_DOI = "10.24432/C52P4X"
UCI_LICENSE = "CC BY 4.0 (Creative Commons Attribution 4.0 International)"

ZIP_FILENAME = "heart+disease.zip"
CLEVELAND_FILENAME = "processed.cleveland.data"
NAMES_FILENAME = "heart-disease.names"

# İlk indirmede (2026-11-17) ölçülen SHA-256 özetleri. Dosya değişirse testler ve
# yükleyici uyarı verir; bu, verinin sessizce değişmesine karşı bir korumadır.
EXPECTED_SHA256 = {
    ZIP_FILENAME: "b17cd273da9ce1caa4710fce80227ea454d4dbf9fcbc8e6a9121672751563adc",
    CLEVELAND_FILENAME: "a74b7efa387bc9d108d7d0115d831fe9b414b29ae7124f331b622b4efa0427c8",
    NAMES_FILENAME: "ec7ed5aa4ed8321097808f47b836301c2a0c36f3bb09c40b8b43b622363e6b61",
    "processed.hungarian.data": "d1ad108f785768cd3d7e82dc522e6f5a61eea93cccfb3a46ee8076f73fc3d796",
    "processed.switzerland.data": "834a405ccf5b66ab4056bb77794adc8df0b7125186454c0a1d002d33c6c3b314",
    "processed.va.data": "e7c93d8d0d2acdadfa4c5e8de768e2191e7f618b952e29623f1f0d5949ff6b8f",
}

# Aşama 2: keşifsel transfer testi için diğer UCI merkezleri (yalnızca dış değerlendirme)
OTHER_SITES = {
    "Hungary": "processed.hungarian.data",
    "Switzerland": "processed.switzerland.data",
    "Long Beach VA": "processed.va.data",
}

EXPECTED_N_ROWS = 303
EXPECTED_N_COLS = 14

# heart-disease.names, bölüm 7'deki 14 özniteliğin sırası
COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal", "num",
]
TARGET_RAW = "num"
TARGET_BINARY = "disease"

CONTINUOUS = ["age", "trestbps", "chol", "thalach", "oldpeak"]
BINARY = ["sex", "fbs", "exang"]
NOMINAL = ["cp", "restecg", "thal"]
ORDINAL = ["slope", "ca"]
CATEGORICAL = BINARY + NOMINAL + ORDINAL
FEATURES = CONTINUOUS + CATEGORICAL

# --- Aşama 2: özellik setleri (önceden belirlendi, docs/research_plan.md) ---
# Anjiyografi öncesi: demografi, semptom, dinlenme ölçümleri, egzersiz EKG.
FEATURES_PRE_ANGIO = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
                      "thalach", "exang", "oldpeak", "slope"]
# Tam set: + floroskopi (ca) ve talyum sintigrafisi (thal)
FEATURES_FULL = FEATURES_PRE_ANGIO + ["ca", "thal"]
# Transfer: diğer merkezlerde büyük ölçüde eksik olan slope/ca/thal çıkarıldı
FEATURES_TRANSFER = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
                     "thalach", "exang", "oldpeak"]
FEATURE_SETS = {"pre_angio": FEATURES_PRE_ANGIO, "full": FEATURES_FULL}
# Aşama 3 merkez-dışı-bırak (LOSO): merkezlerde sistematik eksik olan chol (İsviçre %100)
# ve fbs (İsviçre %61) de çıkarıldı; aksi halde eksiklik deseni merkezi kodlar.
FEATURES_LOSO = ["age", "sex", "cp", "trestbps", "restecg", "thalach", "exang", "oldpeak"]
SPLINE_VARS = ["age", "trestbps", "chol", "thalach", "oldpeak"]

TEST_SIZE = 0.20          # kilitli test kümesi oranı
OUTER_SPLITS = 5
OUTER_REPEATS = 10
INNER_SPLITS = 5
N_BOOTSTRAP = 2000
PRIMARY_MODEL = "logreg_l2"   # önceden belirlenmiş birincil model

RANDOM_SEED = 42
