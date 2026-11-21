"""Türkçe/İngilizce veri sözlüğü.

Kodların anlamları `heart-disease.names` (UCI arşivi) dosyasından alınmıştır. Belgede
açıkça tanımlanmayan noktalar `note_*` alanlarında belirtilmiştir; tahmin yapılmamıştır.

`plausible_range`: tutarlılık denetimi için kullanılan, klinik olarak *mümkün* değer
aralığıdır (normal aralık değildir). Bu aralığın dışı "hata" değil, "incelenmeli"
anlamına gelir.
"""
from __future__ import annotations

import pandas as pd

DATA_DICTIONARY: list[dict] = [
    dict(name="age", raw_index=3, kind="continuous", dtype="integer", unit="years / yıl",
         label_en="Age", label_tr="Yaş",
         codes_en="", codes_tr="", plausible_range=(18, 100),
         note_en="", note_tr=""),
    dict(name="sex", raw_index=4, kind="binary", dtype="integer", unit="",
         label_en="Sex", label_tr="Cinsiyet",
         codes_en="1 = male; 0 = female", codes_tr="1 = erkek; 0 = kadın",
         allowed={0, 1}, note_en="", note_tr=""),
    dict(name="cp", raw_index=9, kind="nominal", dtype="integer", unit="",
         label_en="Chest pain type", label_tr="Göğüs ağrısı tipi",
         codes_en="1 = typical angina; 2 = atypical angina; 3 = non-anginal pain; 4 = asymptomatic",
         codes_tr="1 = tipik anjina; 2 = atipik anjina; 3 = anjinal olmayan ağrı; 4 = asemptomatik",
         allowed={1, 2, 3, 4}, note_en="", note_tr=""),
    dict(name="trestbps", raw_index=10, kind="continuous", dtype="integer", unit="mm Hg",
         label_en="Resting blood pressure (on admission to the hospital)",
         label_tr="Dinlenme kan basıncı (hastaneye kabulde)",
         codes_en="", codes_tr="", plausible_range=(70, 250),
         note_en="Systolic is assumed but not stated in the source.",
         note_tr="Kaynakta sistolik olduğu açıkça yazmaz; yaygın varsayım sistoliktir."),
    dict(name="chol", raw_index=12, kind="continuous", dtype="integer", unit="mg/dl",
         label_en="Serum cholesterol", label_tr="Serum kolesterolü",
         codes_en="", codes_tr="", plausible_range=(100, 600),
         note_en="Total cholesterol is assumed; fasting status not documented.",
         note_tr="Total kolesterol olduğu varsayılır; açlık durumu belgelenmemiştir."),
    dict(name="fbs", raw_index=16, kind="binary", dtype="integer", unit="",
         label_en="Fasting blood sugar > 120 mg/dl", label_tr="Açlık kan şekeri > 120 mg/dl",
         codes_en="1 = true; 0 = false", codes_tr="1 = evet; 0 = hayır",
         allowed={0, 1}, note_en="", note_tr=""),
    dict(name="restecg", raw_index=19, kind="nominal", dtype="integer", unit="",
         label_en="Resting electrocardiographic results", label_tr="Dinlenme EKG sonucu",
         codes_en=("0 = normal; 1 = ST-T wave abnormality (T inversion and/or ST elevation/"
                   "depression > 0.05 mV); 2 = probable/definite LVH by Estes' criteria"),
         codes_tr=("0 = normal; 1 = ST-T dalga anormalliği (T inversiyonu ve/veya > 0,05 mV ST "
                   "yükselmesi/çökmesi); 2 = Estes kriterlerine göre olası/kesin sol ventrikül hipertrofisi"),
         allowed={0, 1, 2}, note_en="", note_tr=""),
    dict(name="thalach", raw_index=32, kind="continuous", dtype="integer", unit="beats/min / atım/dk",
         label_en="Maximum heart rate achieved (exercise test)",
         label_tr="Egzersiz testinde ulaşılan en yüksek kalp hızı",
         codes_en="", codes_tr="", plausible_range=(60, 220),
         note_en="Unit not stated in source; bpm is implied.",
         note_tr="Birim kaynakta yazmaz; atım/dk olduğu anlaşılır."),
    dict(name="exang", raw_index=38, kind="binary", dtype="integer", unit="",
         label_en="Exercise-induced angina", label_tr="Egzersizle tetiklenen anjina",
         codes_en="1 = yes; 0 = no", codes_tr="1 = evet; 0 = hayır",
         allowed={0, 1}, note_en="", note_tr=""),
    dict(name="oldpeak", raw_index=40, kind="continuous", dtype="float", unit="mm (assumed)",
         label_en="ST depression induced by exercise relative to rest",
         label_tr="Dinlenmeye göre egzersizle oluşan ST segment çökmesi",
         codes_en="", codes_tr="", plausible_range=(0.0, 7.0),
         note_en="UCI web table lists it as 'Integer' but values are decimal; unit not stated (mm is conventional).",
         note_tr="UCI web tablosu 'Integer' der, oysa değerler ondalıklıdır; birim belirtilmemiş (genelde mm)."),
    dict(name="slope", raw_index=41, kind="ordinal", dtype="integer", unit="",
         label_en="Slope of the peak exercise ST segment", label_tr="Zirve egzersiz ST segmentinin eğimi",
         codes_en="1 = upsloping; 2 = flat; 3 = downsloping",
         codes_tr="1 = yukarı eğimli; 2 = düz; 3 = aşağı eğimli",
         allowed={1, 2, 3}, note_en="", note_tr=""),
    dict(name="ca", raw_index=44, kind="ordinal", dtype="integer", unit="count / adet",
         label_en="Number of major vessels (0-3) colored by fluoroscopy",
         label_tr="Floroskopide boyanan ana damar sayısı (0-3)",
         codes_en="0-3", codes_tr="0-3", allowed={0, 1, 2, 3},
         note_en="Fluoroscopy finding; may be closely tied to the angiographic outcome (possible leakage).",
         note_tr="Floroskopi bulgusudur; anjiyografik sonuçla yakından ilişkili olabilir (olası sızıntı)."),
    dict(name="thal", raw_index=51, kind="nominal", dtype="integer", unit="",
         label_en="Thallium stress test result", label_tr="Talyum stres testi sonucu",
         codes_en="3 = normal; 6 = fixed defect; 7 = reversible defect",
         codes_tr="3 = normal; 6 = sabit defekt; 7 = geri dönüşümlü defekt",
         allowed={3, 6, 7},
         note_en="Source only says 'thal'; interpretation as thallium scintigraphy is the common reading.",
         note_tr="Kaynakta yalnızca 'thal' yazar; talyum sintigrafisi olarak yorumlanması yaygın okumadır."),
    dict(name="num", raw_index=58, kind="target", dtype="integer", unit="",
         label_en="Diagnosis of heart disease (angiographic disease status)",
         label_tr="Kalp hastalığı tanısı (anjiyografik hastalık durumu)",
         codes_en="0 = absence (<50% diameter narrowing); 1-4 = presence",
         codes_tr="0 = yok (<%50 çap daralması); 1-4 = var",
         allowed={0, 1, 2, 3, 4},
         note_en=("The .names file defines only 0 (<50%) and 1 (>50% narrowing in any major vessel) "
                  "yet the data contains 0-4; the meaning of 2-4 is not documented."),
         note_tr=("Belge yalnızca 0 (<%50) ve 1 (herhangi bir ana damarda >%50 daralma) değerlerini "
                  "tanımlar; veride 0-4 vardır ve 2-4'ün anlamı belgelenmemiştir.")),
]


def as_frame() -> pd.DataFrame:
    rows = []
    for d in DATA_DICTIONARY:
        r = {k: v for k, v in d.items() if k not in ("allowed", "plausible_range")}
        r["allowed_values"] = ", ".join(str(x) for x in sorted(d["allowed"])) if "allowed" in d else ""
        r["plausible_range"] = (f"{d['plausible_range'][0]}–{d['plausible_range'][1]}"
                                if "plausible_range" in d else "")
        rows.append(r)
    return pd.DataFrame(rows)


def get(name: str) -> dict:
    for d in DATA_DICTIONARY:
        if d["name"] == name:
            return d
    raise KeyError(name)


def to_markdown(stats: pd.DataFrame | None = None) -> str:
    """Veri sözlüğünü Markdown tablo olarak üretir. `stats` verilirse gözlemlenen
    aralık ve eksik sayısı da eklenir."""
    lines = [
        "# Veri Sözlüğü / Data Dictionary — UCI Heart Disease (Cleveland)",
        "",
        "Kaynak: `heart-disease.names` (UCI arşivi). `#` = 76 öznitelikli ham veritabanındaki sıra.",
        "Source: `heart-disease.names` (UCI archive). `#` = position in the 76-attribute raw database.",
        "",
        "| Değişken | # | Tür / Kind | Birim | Türkçe | English | Kodlar (TR) | Codes (EN) | Gözlenen | Eksik |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for d in DATA_DICTIONARY:
        obs, miss = "", ""
        if stats is not None and d["name"] in stats.index:
            obs = stats.loc[d["name"], "observed"]
            miss = str(stats.loc[d["name"], "n_missing"])
        lines.append(
            f"| `{d['name']}` | {d['raw_index']} | {d['kind']} ({d['dtype']}) | {d['unit']} | "
            f"{d['label_tr']} | {d['label_en']} | {d['codes_tr']} | {d['codes_en']} | {obs} | {miss} |")
    lines += ["", "## Notlar / Notes", ""]
    for d in DATA_DICTIONARY:
        if d["note_tr"]:
            lines.append(f"- **`{d['name']}`** — TR: {d['note_tr']}  \n  EN: {d['note_en']}")
    lines += ["", "Türetilmiş değişken / Derived variable:", "",
              "- **`disease`** — TR: `num > 0` ise 1 (kalp hastalığı kayıtlı), `num == 0` ise 0. "
              "EN: 1 if `num > 0` (disease recorded), 0 if `num == 0`.", ""]
    return "\n".join(lines)
