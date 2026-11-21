# Veri Sözlüğü / Data Dictionary — UCI Heart Disease (Cleveland)

Kaynak: `heart-disease.names` (UCI arşivi). `#` = 76 öznitelikli ham veritabanındaki sıra.
Source: `heart-disease.names` (UCI archive). `#` = position in the 76-attribute raw database.

| Değişken | # | Tür / Kind | Birim | Türkçe | English | Kodlar (TR) | Codes (EN) | Gözlenen | Eksik |
|---|---|---|---|---|---|---|---|---|---|
| `age` | 3 | continuous (integer) | years / yıl | Yaş | Age |  |  | 29–77 | 0 |
| `sex` | 4 | binary (integer) |  | Cinsiyet | Sex | 1 = erkek; 0 = kadın | 1 = male; 0 = female | 0, 1 | 0 |
| `cp` | 9 | nominal (integer) |  | Göğüs ağrısı tipi | Chest pain type | 1 = tipik anjina; 2 = atipik anjina; 3 = anjinal olmayan ağrı; 4 = asemptomatik | 1 = typical angina; 2 = atypical angina; 3 = non-anginal pain; 4 = asymptomatic | 1, 2, 3, 4 | 0 |
| `trestbps` | 10 | continuous (integer) | mm Hg | Dinlenme kan basıncı (hastaneye kabulde) | Resting blood pressure (on admission to the hospital) |  |  | 94–200 | 0 |
| `chol` | 12 | continuous (integer) | mg/dl | Serum kolesterolü | Serum cholesterol |  |  | 126–564 | 0 |
| `fbs` | 16 | binary (integer) |  | Açlık kan şekeri > 120 mg/dl | Fasting blood sugar > 120 mg/dl | 1 = evet; 0 = hayır | 1 = true; 0 = false | 0, 1 | 0 |
| `restecg` | 19 | nominal (integer) |  | Dinlenme EKG sonucu | Resting electrocardiographic results | 0 = normal; 1 = ST-T dalga anormalliği (T inversiyonu ve/veya > 0,05 mV ST yükselmesi/çökmesi); 2 = Estes kriterlerine göre olası/kesin sol ventrikül hipertrofisi | 0 = normal; 1 = ST-T wave abnormality (T inversion and/or ST elevation/depression > 0.05 mV); 2 = probable/definite LVH by Estes' criteria | 0, 1, 2 | 0 |
| `thalach` | 32 | continuous (integer) | beats/min / atım/dk | Egzersiz testinde ulaşılan en yüksek kalp hızı | Maximum heart rate achieved (exercise test) |  |  | 71–202 | 0 |
| `exang` | 38 | binary (integer) |  | Egzersizle tetiklenen anjina | Exercise-induced angina | 1 = evet; 0 = hayır | 1 = yes; 0 = no | 0, 1 | 0 |
| `oldpeak` | 40 | continuous (float) | mm (assumed) | Dinlenmeye göre egzersizle oluşan ST segment çökmesi | ST depression induced by exercise relative to rest |  |  | 0.0–6.2 | 0 |
| `slope` | 41 | ordinal (integer) |  | Zirve egzersiz ST segmentinin eğimi | Slope of the peak exercise ST segment | 1 = yukarı eğimli; 2 = düz; 3 = aşağı eğimli | 1 = upsloping; 2 = flat; 3 = downsloping | 1, 2, 3 | 0 |
| `ca` | 44 | ordinal (integer) | count / adet | Floroskopide boyanan ana damar sayısı (0-3) | Number of major vessels (0-3) colored by fluoroscopy | 0-3 | 0-3 | 0, 1, 2, 3 | 4 |
| `thal` | 51 | nominal (integer) |  | Talyum stres testi sonucu | Thallium stress test result | 3 = normal; 6 = sabit defekt; 7 = geri dönüşümlü defekt | 3 = normal; 6 = fixed defect; 7 = reversible defect | 3, 6, 7 | 2 |
| `num` | 58 | target (integer) |  | Kalp hastalığı tanısı (anjiyografik hastalık durumu) | Diagnosis of heart disease (angiographic disease status) | 0 = yok (<%50 çap daralması); 1-4 = var | 0 = absence (<50% diameter narrowing); 1-4 = presence | 0, 1, 2, 3, 4 | 0 |

## Notlar / Notes

- **`trestbps`** — TR: Kaynakta sistolik olduğu açıkça yazmaz; yaygın varsayım sistoliktir.  
  EN: Systolic is assumed but not stated in the source.
- **`chol`** — TR: Total kolesterol olduğu varsayılır; açlık durumu belgelenmemiştir.  
  EN: Total cholesterol is assumed; fasting status not documented.
- **`thalach`** — TR: Birim kaynakta yazmaz; atım/dk olduğu anlaşılır.  
  EN: Unit not stated in source; bpm is implied.
- **`oldpeak`** — TR: UCI web tablosu 'Integer' der, oysa değerler ondalıklıdır; birim belirtilmemiş (genelde mm).  
  EN: UCI web table lists it as 'Integer' but values are decimal; unit not stated (mm is conventional).
- **`ca`** — TR: Floroskopi bulgusudur; anjiyografik sonuçla yakından ilişkili olabilir (olası sızıntı).  
  EN: Fluoroscopy finding; may be closely tied to the angiographic outcome (possible leakage).
- **`thal`** — TR: Kaynakta yalnızca 'thal' yazar; talyum sintigrafisi olarak yorumlanması yaygın okumadır.  
  EN: Source only says 'thal'; interpretation as thallium scintigraphy is the common reading.
- **`num`** — TR: Belge yalnızca 0 (<%50) ve 1 (herhangi bir ana damarda >%50 daralma) değerlerini tanımlar; veride 0-4 vardır ve 2-4'ün anlamı belgelenmemiştir.  
  EN: The .names file defines only 0 (<50%) and 1 (>50% narrowing in any major vessel) yet the data contains 0-4; the meaning of 2-4 is not documented.

Türetilmiş değişken / Derived variable:

- **`disease`** — TR: `num > 0` ise 1 (kalp hastalığı kayıtlı), `num == 0` ise 0. EN: 1 if `num > 0` (disease recorded), 0 if `num == 0`.
