# Aşama 1 Raporu — Klinik Veri Denetimi ve Araştırma Tasarımı

Tarih: 2026-11-17 · Veri: UCI Heart Disease, Cleveland alt kümesi · Model eğitilmedi.

## 1. İndirilen ve doğrulanan veri

| Öğe | Değer |
|---|---|
| Kaynak | <https://archive.ics.uci.edu/dataset/45/heart+disease> |
| DOI / Lisans | 10.24432/C52P4X · CC BY 4.0 |
| Sürüm | UCI sürüm numarası yayımlamaz → DOI + SHA-256 ile sabitlendi; bağış 1988-06-30 |
| `heart+disease.zip` SHA-256 | `b17cd273da9ce1caa4710fce80227ea454d4dbf9fcbc8e6a9121672751563adc` |
| `processed.cleveland.data` SHA-256 | `a74b7efa387bc9d108d7d0115d831fe9b414b29ae7124f331b622b4efa0427c8` |
| `heart-disease.names` SHA-256 | `ec7ed5aa4ed8321097808f47b836301c2a0c36f3bb09c40b8b43b622363e6b61` |
| Boyut | **303 × 14** — belge ile uyumlu (13 öznitelik + `num`) |
| Sınıf sayıları | 164 / 55 / 36 / 35 / 13 — `heart-disease.names` §10 ile birebir aynı |

Ayrıntı: `data/metadata/provenance.json`.

> **Yayın notu (Aşama 4).** Kişi düzeyindeki denetim çıktıları (`rows_with_missing.csv`,
> `consistency_issues.csv`) ve tam veri kopyası artık `data/private/` altına yazılır ve
> yayımlanmaz; `missing_summary.csv` satır numaralarını içermez; eksik veri grafiği değişken başına
> toplam sayıları gösterir. Yayımlanan özet: `reports/tables/consistency_summary.csv`.

## 2. Değişkenler

5 sürekli (`age`, `trestbps`, `chol`, `thalach`, `oldpeak`), 3 ikili (`sex`, `fbs`, `exang`),
3 nominal (`cp`, `restecg`, `thal`), 2 sıralı (`slope`, `ca`), hedef `num` (0–4) ve türetilmiş
`disease` (0/1). TR/EN sözlük: `docs/data_dictionary.md`. Bütün kodlar belgedeki alanlar
içindedir; kod dışı değer, imkânsız sıfır veya tekrar eden satır **yoktur**.

Belge/kaynak tutarsızlıkları: (i) UCI web tablosu `oldpeak` için "Integer" der, değerler ondalıklıdır;
(ii) web tablosu eksik değer göstermez, dosyada 6 eksik vardır; (iii) `num` için belge yalnızca 0/1'i
tanımlar ama veride 0–4 vardır.

## 3. Eksik veriler

6 hücre (%0,14), 6 satır (%2,0): `ca` 4, `thal` 2; her satırda en çok bir eksik. Eksik satırların
`num` dağılımı: 4 × 0, 1 × 1, 1 × 2. n çok küçük olduğu için eksiklik mekanizması (MCAR/MAR) test
edilemez. Aşama 1'de değer doldurulmadı/silinmedi.

## 4. Önemli istatistiksel bulgular (keşifsel, tek değişkenli)

Örneklem: %68 erkek (206), yaş 29–77 (medyan 56). İkili hedef: 164 yok (%54,1) / 139 var (%45,9).

| Değişken | Etki | Yön | Holm p |
|---|---|---|---|
| `thal` | V = 0,53 | normal %22 vs geri dönüşümlü defekt %76 hastalık | < 0,001 |
| `cp` | V = 0,52 | asemptomatik (4) %73; diğer tipler %18–30 | < 0,001 |
| `thalach` | r_rb = −0,49 | medyan 161 (yok) vs 142 (var) | < 0,001 |
| `ca` | V = 0,49 | 0 damar %26 → 3 damar %85 | < 0,001 |
| `oldpeak` | r_rb = 0,47 | medyan 0,2 vs 1,4 | < 0,001 |
| `exang` | V = 0,43 | %31 vs %77 | < 0,001 |
| `slope` | V = 0,39 | yukarı %25, düz %65, aşağı %57 (monoton değil) | < 0,001 |
| `sex` | V = 0,28 | kadın %26 vs erkek %55 | < 0,001 |
| `age` | r_rb = 0,27 | medyan 52 vs 58 | < 0,001 |
| `restecg` | V = 0,18 | `restecg=1` yalnızca n = 4 | 0,026 |
| `trestbps` | r_rb = 0,15 | medyanlar eşit (130) | 0,078 |
| `chol` | r_rb = 0,14 | 234,5 vs 249 | 0,078 |
| `fbs` | V = 0,03 | %45 vs %49 | 0,66 |

Testler: sürekli → Mann-Whitney U + rank-biserial r; kategorik → Pearson χ² + Cramér's V; 13 test
için Holm düzeltmesi. Gözlemler: "asemptomatik" göğüs ağrısının en yüksek hastalık oranına sahip
olması sezgiye aykırıdır ve örneklem seçimiyle (anjiyografiye sevk edilen hastalar) uyumludur.
`oldpeak`–`slope` (ρ = 0,59) ve `thalach`–`age` (ρ = −0,39) birbirleriyle ilişkilidir; bu nedenle
tek değişkenli etkiler toplanamaz. Bu bulgular **ilişkidir, nedensellik değildir**.

## 5. Oluşturulan dosyalar

- Kod: `src/mrml/{config,data_io,dictionary,audit,stats,plots}.py`, `scripts/run_phase1.py`
- Testler: `tests/{conftest,test_data,test_units}.py`
- Belgeler: `README.md`, `docs/{data_dictionary,decisions,research_plan}.md`, bu rapor
- Veri: `data/raw/…`, `data/metadata/provenance.json`, `data/private/cleveland_typed.csv`
  (kişi düzeyi; Aşama 4 kararıyla yayımlanmaz)
- Tablolar (`reports/tables/`): `audit_summary.json`, `variable_types`, `missing_summary`,
  `consistency_summary`, `target_distribution`, `data_dictionary`,
  `descriptive_continuous`, `categorical_crosstabs`, `univariate_tests`, `spearman_correlation`,
  `missing_vs_target` (.csv)

## 6. Grafikler (`reports/figures/`)

1. `01_target_distribution.png` — `num` 0–4 ve ikili `disease`
2. `02_missingness.png` — eksik hücre haritası
3. `03_continuous_by_class.png` — sürekli değişkenler: histogram + kutu grafiği
4. `04_categorical_disease_rates.png` — düzey başına hastalık oranı ve n
5. `05_spearman_correlation.png` — Spearman korelasyon matrisi
6. `06_univariate_effect_sizes.png` — etki büyüklükleri (Holm p ile)
7. `07_sample_age_sex.png` — örneklemin yaş/cinsiyet bileşimi

## 7. Test sonuçları

`python -m pytest -q` → **21 passed** (8 gerçek veri bütünlüğü testi: SHA-256, boyut, belgedeki sınıf
sayıları, eksik değer konumu, tekrarsızlık, kod alanı, tipler; 13 birim testi: `?` ayrıştırma,
tip dönüşümü, zip yol aşımı koruması, tutarlılık kontrolleri, Holm, Cramér's V, sözlük
kapsamı, sabit yol yokluğu, grafik üretimi).

## 8. Bilimsel sınırlılıklar

- **Örneklem büyüklüğü.** n = 303, 139 olay. Kabaca 10–15 olay/parametre kuralına göre one-hot
  sonrası ~20 parametreli bir model sınırdadır; aşırı uyum riski yüksektir, tek test ayrımı
  kararsız olur. `restecg = 1` (n = 4) ve `num = 4` (n = 13) gibi hücreler istatistiksel olarak
  bilgi taşımaz.
- **Örneklem seçimi (spektrum yanlılığı).** Hastalar koroner anjiyografiye sevk edilmiş kişilerdir;
  genel popülasyonu veya birinci basamağı temsil etmez. %46'lık hastalık sıklığı popülasyon
  prevalansından çok yüksektir; olasılıklar başka ortama aktarılamaz.
- **Zaman ve klinik bağlam.** Veri 1980'ler Cleveland Clinic'ten; tanı yöntemleri, tedavi ve risk
  faktörü dağılımları değişmiştir. Etnik köken, ilaç, sigara gibi değişkenler bu alt kümede yoktur.
- **Bileşim.** %68 erkek; kadınlarda (n = 97, 25 olay) tahminler belirsizdir. Yaş 29–77.
- **Hedef tanımı.** `num` kodlaması kısmen belgelenmemiştir; `disease` > %50 daralma ile tanımlı
  anjiyografik bir durumdur (gelecekteki olay/ölüm değildir). Eşik kendisi tartışmalı bir klinik
  tanımdır.
- **Sızıntı / kullanım zamanı.** `ca` (floroskopi) ve `thal` (talyum) anjiyografiye yakın ileri
  testlerdir; bunlarla kurulan model "anjiyografi öncesi tarama" senaryosunu temsil etmez.
- **Eksik veri.** Az (6 hücre) ama mekanizması bilinemez; kimlik bilgisi olmadığından tekrar
  hasta kaydı yalnızca değer eşleşmesiyle aranabildi.
- **Ölçüm belirsizliği.** `trestbps` (sistolik?), `chol` (açlık?), `oldpeak` (mm?) birimleri
  kaynakta tam belgelenmemiştir.
- **Dış doğrulama yok.** Diğer UCI alt kümeleri farklı ülke/prevalans içerir ve `ca`/`thal`'de çok
  eksiktir; tam bir dış doğrulama sağlamaz, yalnızca keşifsel transfer testi olabilir.
- **Çoklu karşılaştırma ve keşifsel analiz.** Holm uygulandı, ancak bu bulgular hipotez üreticidir.

## 9. Aşama 2 önerisi

Ayrıntı: `docs/research_plan.md`. Özet: sızıntısız scikit-learn pipeline; tekrarlı katmanlı
5-kat CV + iç içe CV ile hiperparametre seçimi; birincil model L2 lojistik regresyon, referans
yaş+cinsiyet modeli, karşılaştırma için ağaç modelleri; **iki özellik seti** (anjiyografi öncesi
bilgiler vs. + `ca`/`thal`); ROC AUC + kalibrasyon + Brier; eksik veri için kat içi atama ve tam
vaka duyarlılık analizi; diğer UCI alt kümelerinde keşifsel transfer testi; TRIPOD+AI uyumlu rapor.
