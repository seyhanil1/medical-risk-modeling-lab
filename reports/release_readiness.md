# Yayın Hazırlık Raporu — Aşama 4 (Son Bilimsel Denetim)

Tarih: 2026-11-18 · Kapsam: kod, raporlar, README, TRIPOD+AI listesi, yeniden üretilebilirlik,
lisans ve gizlilik. Yeni model veya araştırma özelliği eklenmedi.
Git başlatılmadı; commit, push, depo oluşturma veya deployment yapılmadı.

## 0. Sonuç

**Durum: teknik olarak yayına hazır; yayın öncesi sizin vermeniz gereken 3 karar var (§9).**

| Kontrol | Sonuç |
|---|---|
| Testler (proje ortamı / temiz ortam) | **49 / 49 geçti** · 49 / 49 geçti |
| Temiz ortamda sıfırdan yeniden üretim (kurulum + veri indirme + Aşama 1–3) | **93 / 93 çıktı dosyası bayt düzeyinde aynı** |
| Otomatik denetim (`scripts/audit_release.py` → `reports/release_audit.md`) | **111 / 111 kontrol geçti** |
| Rapor ↔ tablo rakam tutarlılığı | 78 / 78 (final rapor, README, aşama raporları) |
| Kişisel yol / e-posta / gizli anahtar | Bulunmadı (tarayıcı yem dosyasıyla doğrulandı) |
| Toplam boyut (.venv hariç) | 2,96 MB, 130 dosya, 1 MB üstü dosya yok |
| TRIPOD+AI | 52 / 52 alt madde eşlendi: ✅ 31 · ⚠️ 18 · ➖ 3 |
| Bilimsel sonucu değiştiren düzeltme | **Var — §1'de ayrıca listelendi** |

## 1. Bilimsel sonucu veya yorumu DEĞİŞTİREN düzeltmeler

Bunlar sayısal sonuçları değiştirmedi; tablolar aynı kaldı. Ama **anlamlılık iddialarını ve
yorumları** değiştirdi. Hepsi final raporda, README'de ve ilgili aşama raporunda düzeltildi.

| # | Önceki ifade | Düzeltilmiş ifade | Neden |
|---|---|---|---|
| S1 | AS4: `ca`/`thal` AUC'yi anlamlı artırdı (p = 0,009) | +0,045 [0,012, 0,079]; nominal p = 0,009, **Holm p = 0,080**; yön dört modelde aynı | 18 karşılaştırmada çoklu test düzeltmesi yoktu |
| S2 | Gradyan artırma tam sette L2'den kötü (p = 0,046) | Nominal p = 0,046, **Holm p = 0,27**; anlamlı fark gösterilemedi | Aynı |
| S3 | RF ve gradyan artırma (ön-anjiyo) referanstan anlamlı iyi (p = 0,008 / 0,005) | Holm p = 0,080 / 0,059 | Aynı |
| S4 | Spline modeli "daha kötü" | "Daha iyi olduğuna dair kanıt yok; düşük performans yönünde sinyal" (nominal p = 0,011, aile içi Holm p = 0,043; tam sette anlamsız) | Holm + yorumun gücü |
| S5 | Kadın/erkek ayrıştırması "benzer; GA'lar örtüşüyor" | Örtüşme eşitlik kanıtı değil; doğrudan fark +0,035 [−0,095, 0,145] eşitliği de farkı da dışlamıyor | Yanlış çıkarım kalıbı |
| S6 | Kadınlarda "sistematik fazla tahmin" | CITL −0,43 [−0,72, −0,12]; kadın − erkek CITL farkı −0,61 [−0,99, −0,20]. **Sinyal**: 18 olay, post hoc, model belirsizliği yok | Belirsizliğin abartılmaması |
| S7 | H2 "desteklendi" (LRT p = 0,081) | "H2 ile çelişen kanıt bulunmadı"; anlamsız test ek katkının yokluğunu kanıtlamaz | Kanıt yokluğu ≠ yokluk kanıtı |
| S8 | L2 "en iyi kalibrasyonu" sağladı | L2 iyi kalibre; Elastic-Net ve gradyan artırma benzer, RF daha zayıf | Tablo desteklemiyordu |
| S9 | Karar eğrisinde model "net fayda sağlar" | "Bu veride ve varsayımsal çerçevede daha yüksek net fayda gösterdi; klinik öneri değildir"; GA'ların model belirsizliğini içermediği ve eşikler arası düzeltme olmadığı belirtildi | Varsayımsal kararın abartılmaması |
| S10 | Aşama 3 analizleri planın parçasıymış gibi | **Protokol dışı, keşifsel** olarak beyan edildi | Şeffaflık |

Değişmeyen ana sonuçlar:
- CV AUC 0,854 / 0,900.
- L2'nin referans modele üstünlüğü (Holm p = 0,011 / < 0,001).
- Karmaşık modellerin ek yararının gösterilememesi.
- Merkezler arası heterojenlik ve yeniden kalibrasyon ihtiyacı.

## 2. Rapor tutarlılığı (görev 1)

- `scripts/audit_release.py`, temel sayıları (CV/test AUC'leri, AS4 farkı ve GA'sı, odds oranları,
  LRT p, transfer AUC'leri, spline farkı ve p'leri, alt grup CITL, eşik metrikleri, net fayda değerleri,
  yeniden kalibrasyon eğimi) doğrudan üretilen CSV/JSON tablolarından okuyup final rapor, README ve
  aşama raporlarında arar. Toplam 78 kontrol (65 sayı–belge eşleşmesi, 12 örneklem sayısı, 1 test
  sayısı); tamamı geçti.
- Örneklem tanımları (303/139, 242/111, 61/28) final raporda ve README'de tutarlı.
- Aşama 3 raporunun karar eğrisi tablosunda hızlı deneme koşusundan kalan 5 değer, Aşama 3 sonunda
  zaten düzeltilmişti; bu denetimde tablolarla yeniden doğrulandı.
- Aşama 1–3 raporlarındaki eski test sayıları (21, 33, 45) o aşamanın tarihsel durumudur. Güncel
  sayı (49) README'de ve final raporda.

## 3. Veri sızıntısı denetimi (görev 2)

| Adım | Uygulama | Kod | Sonuç |
|---|---|---|---|
| Önişleme (atama, gösterge, ölçekleme, one-hot) | Bütün modellerde `Pipeline` içinde; her eğitim katında (iç katlar dahil) yeniden fit | `modeling.py:38`, `audit_release.py` (14 model yapısal olarak doğrulandı), `test_preprocessor_fits_only_on_training_rows` | ✅ |
| Hiperparametre seçimi | İç içe CV; iç `GridSearchCV` yalnızca dış eğitim katında | `modeling.py:89`, `:185` | ✅ |
| Kilitli test | Son modeller geliştirme kümesinde ayarlandı, testte bir kez değerlendirildi | `run_phase2.py:127–128`, `run_phase3.py:199` | ✅ |
| Eşik seçimi | Eşik, eğitim katının kendi iç kat-dışı tahminlerinden; test katı görülmeden | `phase3.py:105–109` | ✅ (C eğitim katının tamamında seçildiği için eşik eğitim içinde hafif iyimser olabilir; test katına sızıntı yok) |
| Yeniden kalibrasyon | (a, b) hedef merkezin eğitim katında, değerlendirme dışarıda tutulan katta | `phase3.py:167` | ✅ |
| LOSO | Dışarıda bırakılan merkez eğitime ve hiperparametre aramasına girmez | `phase3.py:198` | ✅ |
| Karar eğrisi / alt grup / kalibrasyon grafikleri | Kat-dışı tahminler (10 tekrar ortalaması); hiçbir tahmin o kişiyi görmüş modelden gelmez | `modeling.py:200` | ✅ |

Beyan edilen (sızıntı değil, ama şeffaflık gerektiren) noktalar:
- Kilitli testteki 61 kişi, performans tahmini olmayan analizlerde bütün Cleveland verisinin
  parçasıydı: AS2 odds oranları, transfer ve LOSO modellerinin eğitimi, spline biçim grafiği.
- Aşama 1 EDA'sı 303 kişide yapıldı. `slope`'u nominal kodlama kararı EDA'dan etkilendi; sıralı
  kodlama duyarlılık analizinde AUC 0,849 vs 0,854.
- Aşama 2'nin hızlı duman testi kilitli test metriklerini bir kez daha hesapladı. Sonuçlar
  deterministik; hiçbir karar değişmedi.
- Merkezler arasında birebir aynı kayıt yok (`test_no_patient_overlap_between_sites`). Macaristan
  ve VA'da merkez içinde birer çift aynı kayıt var; merkez içi yeniden kalibrasyonu pratikte etkilemez.

## 4. Karar eğrisi incelemesi (görev 3)

- **Formül doğrulandı:**
  - NB = TP/n − FP/n · pt/(1 − pt)
  - herkesi sevk et = π − (1 − π) · pt/(1 − pt)
  - kimseyi sevk etme = 0

  Bilinen değer, "herkesi sevk et" özdeşliği ve mükemmel model (NB = π) için birim testleri var.
- **Belirsizlik:** 1000 basit bootstrap, kat-dışı tahminler sabit. Model yeniden eğitilmediği için
  GA'lar olduğundan dar olabilir. Beş eşik için çoklu karşılaştırma düzeltmesi yok. Bu artık
  `phase3.py` docstring'inde, Aşama 3 raporunda ve final raporda yazılı.
- **Klinik öneri izlenimi giderildi:** her yerde "varsayımsal", "yöntem gösterimi", "klinik öneri
  değildir" ifadeleri kullanılıyor. Ayrıca bütün hastaların zaten anjiyografi olduğu, yani "sevk
  etmeme"nin sonucunun gözlenmediği eklendi.

## 5. Alt grup (görev 4)

- Kadın alt grubu: n = 77, 18 olay. CITL GA'sı ve gruplar arası doğrudan fark GA'ları eklendi
  (`subgroup_differences.csv`, yeni `subgroup_difference()` fonksiyonu ve 2 test).
- "GA örtüşmesi = eşit performans" çıkarımı bütün belgelerden kaldırıldı (S5, S6).

## 6. Dış merkez ve yeniden kalibrasyon (görev 5)

- Cleveland transfer modeli hedef merkezlerden hiçbir veri görmez.
- Yeniden kalibrasyon merkez içi tekrarlı 5-kat CV ile yapıldı; parametreler yalnızca eğitim
  katından tahmin edildi.
- LOSO'da dışarıda bırakılan merkez eğitimde yok.
- Yeni bulgu: yeniden kalibrasyon tablosundaki `oof_auc` farkları (ör. İsviçre 0,758 → 0,708) bir
  ortalama artefaktıdır. Monoton yeniden kalibrasyon kat içinde sıralamayı değiştirmez; rapora
  açıklama eklendi.

## 7. Spline p-değeri (görev 6)

- Yöntem: aynı 50 dış katta eşleştirilmiş fark; Nadeau–Bengio düzeltmeli t testi
  (J = 50, n_test/n_train ≈ 48/194, sd = 49). Yaklaşık bir yöntemdir.
- Çoklu analiz: 4 spline karşılaştırması bir aile olarak Holm ile düzeltildi (yeni `p_holm`
  sütunu). Aşama 2 ailesiyle birlikte düzeltilmedi; bu beyan edildi.
- Yorum S4'e göre düzeltildi; spline analizinin önceden planlanmadığı belirtildi.

## 8. TRIPOD+AI (görev 7)

- 52 alt madde gerçek rapor bölümleriyle yeniden eşlendi. Atıf yapılan bütün final rapor
  bölümlerinin varlığı otomatik kontrol ediliyor.
- Önceki listede fazla iyimser işaretlenen maddeler düşürüldü:

  | Madde | Önceki | Şimdi |
  |---|---|---|
  | 2 | ✅ | ⚠️ |
  | 6c | ➖ | ⚠️ |
  | 7 | ✅ | ⚠️ |
  | 8a | ✅ | ⚠️ |
  | 17 | ➖ | ⚠️ |
  | 18c | ✅ | ⚠️ |
  | 18f | ✅ | ⚠️ |
  | 20b | ✅ | ⚠️ |

- Madde 3c'deki kaynaksız literatür iddiası kaldırıldı.
- Başlığa hedef popülasyon eklendi (madde 1).
- Projeyle giderilebilecek ⚠️'ler: 2, 7/20b, 20c, 22. 18f yayından sonra ✅ olur. Diğerleri
  1980'lerin veri kaynağında belgelenmemiş bilgilerden kaynaklanıyor.

## 9. Yeniden üretilebilirlik (görev 8)

- **Temiz ortam:** proje kaynak kodu (veri, çıktı ve `.venv` hariç) ayrı bir klasöre kopyalandı.
  Yeni Python 3.14.4 sanal ortamına `pip install -r requirements.txt` yapıldı. UCI arşivi yeniden
  indirildi; SHA-256 değerleri eşleşti. Ardından Aşama 1–3 ve testler çalıştırıldı.
- **Karşılaştırma:** bütün tablolar, 18 grafik, ara veri, ham veri ve veri sözlüğü (93 dosya)
  proje çıktılarıyla **bayt düzeyinde aynı**. Yalnızca `provenance.json` (indirme zaman damgası)
  ve log dosyaları (saatler) doğal olarak farklı.
- **Bağımlılıklar:** `requirements.txt` (doğrudan bağımlılıklar, sabit sürüm), yeni
  `requirements-lock.txt` (temiz ortamın tam `pip freeze` çıktısı, 23 paket), `pyproject.toml`
  (gerçek alt sınırlar).
- **Kritik bulgu:** `pyproject.toml` daha önce `scikit-learn>=1.3` diyordu. Ama kod
  `LogisticRegression(l1_ratio=...)` kullanıyor; scikit-learn 1.8'den eski sürümlerde bu parametre
  `penalty='elasticnet'` olmadan yok sayılır. Yani Elastic-Net modeli **sessizce L2'ye dönerdi**.
  Alt sınır `>=1.8` yapıldı. Ayrıca `matplotlib>=3.10` (`boxplot(orientation=)`) ve
  `requires-python>=3.11`.
- **Denetim sırasında bulunup düzeltilen hatalar:**
  - `run_phase3.py`'ye bu aşamada eklenen satırda sözdizimi hatası.
  - `subgroup_difference` bootstrap'ında tekil matris hatası: CITL artık yalnızca kesişimle
    hesaplanıyor.
  - Kabuk zincirindeki `set -e` hataları yakalamadı ve "ok" yazdı; çıktılar bu yüzden dosya
    düzeyinde doğrulandı.
- Süre (12 çekirdek): toplam yaklaşık 25 dakika. Aşama 2 ve 3'ün her biri yaklaşık 5–10 dakika.

## 10. Lisans, üçüncü taraf içerik, gizlilik, boyut (görev 10)

**Veri lisansı.** UCI Heart Disease, CC BY 4.0. Atıf koşuluyla yeniden dağıtıma izin verir.
README ve final rapor, veri setini, Detrano 1989 makalesini ve veri sahiplerinin istediği dört
sorumlu araştırmacıyı anıyor.

**Üçüncü taraf içerikler**

| İçerik | Lisans / durum | Öneri |
|---|---|---|
| `data/raw/` (UCI arşivi, `.names`, `WARNING`, `costs/` vb.) | CC BY 4.0 | Depoya eklemek serbest (atıf var). Ya da `.gitignore`'daki satırları açıp indirme betiğine bırakın; SHA-256 doğrulaması var |
| TRIPOD+AI madde özetleri | Kaynak makale CC BY 4.0; Türkçe özet olarak, atıfla | Sorun yok |
| Detrano 1989 bulguları | Yalnızca atıfla özetlendi; metin kopyalanmadı | Sorun yok |
| Python paketleri | Depoya dahil değil (yalnızca sürüm listesi) | Sorun yok |

**Gizlilik**
- `.venv` hariç bütün dosyalar tarandı: mutlak kullanıcı yolu, kullanıcı adı/ev dizini (PNG'ler
  dahil bayt düzeyinde), e-posta ve anahtar kalıpları.
- Bulgu yok. Tek e-posta, UCI belgesindeki kamuya açık donör adresi (`aha@ics.uci.edu`); bu
  bilinçli olarak izin listesinde.
- Sizin adınız, e-postanız veya bilgisayar yolunuz hiçbir dosyada yok.
- Veride hasta kimliği yok; UCI, isim ve kimlik numaralarını kaynağında kaldırmış.

**Boyut**
- Toplam 2,96 MB.
- En büyük dosya 1 MB'ın altında; ham veri 0,8 MB.
- Git LFS gerekmez.

**Lisans önerisi (karar sizin — `LICENSE` dosyası oluşturulmadı)**

| Seçenek | Kod | Raporlar, şekiller | Not |
|---|---|---|---|
| **A (önerilen)** | MIT | CC BY 4.0 | Portföy için en yaygın ve en sade. Raporlar veriyle aynı lisans ailesinde |
| B | Apache-2.0 | CC BY 4.0 | Açık patent hükmü; biraz daha uzun |
| C | MIT (tümü) | MIT | Tek lisans; ancak metin/şekil için CC daha uygun |

Hangi seçenek olursa olsun, UCI verisi CC BY 4.0 olarak kalır; README'deki not bunu belirtiyor.

## 11. Yapılan dosya değişiklikleri (Aşama 4)

- **Kod**
  - `scripts/run_phase2.py`: Holm sütunu.
  - `scripts/run_phase3.py`: Holm sütunu, alt grup farkları, sözdizimi düzeltmesi.
  - `src/mrml/phase3.py`: `subgroup_difference`, CITL GA'sı, sağlam CITL, net fayda docstring'i.
  - `src/mrml/modeling.py` ve `config.py`: Aşama 3'ten.
  - `scripts/run_phase1.py`: bütün merkez dosyaları provenance'a eklendi.
  - `pyproject.toml`: sürüm ve alt sınırlar.
- **Yeni:**
  - `scripts/audit_release.py`
  - `requirements-lock.txt`
  - `.gitignore`
  - `reports/release_audit.md`
  - bu rapor
- **Testler:** 4 yeni (alt grup farkı ×2, diğer merkez SHA-256, merkezler arası kayıt çakışması).
  Toplam 49.
- **Belgeler:**
  - `README.md`: profesyonel İngilizce, baştan yazıldı.
  - `reports/final_report.md`, `reports/phase2_report.md`, `reports/phase3_report.md`:
    düzeltme notları ve §1'deki yorum düzeltmeleri.
  - `docs/tripod_ai_checklist.md`: yeniden eşlendi.
- **Yeniden üretilen:** `reports/tables/**`, `reports/figures/**`, `data/metadata/provenance.json`,
  `data/interim/**`, `reports/phase*_run.log`.

## 12. Yayın öncesi sizin kararınız gerekenler

1. **Lisans:** A, B veya C (§10). Seçince `LICENSE` dosyası ve README'deki lisans bölümü
   güncellenir.
2. **Ham veri depoya girsin mi?** Evet (varsayılan) ya da hayır (`.gitignore` satırları açılır).
3. **Depo adı, açıklama, yazar/atıf adı:** README'de yazar adı yok. Bir `CITATION.cff` isterseniz
   hangi adın görüneceğini sizin belirtmeniz gerekir.

İsteğe bağlı iyileştirmeler (bilimsel sonucu etkilemez):
- GitHub Actions ile `pytest` + `audit_release.py` CI'si.
- TRIPOD+AI for Abstracts 13 maddelik karşılaştırması.
- Cinsiyete göre özellik tablosu (madde 7/20b).

## 13. Ek — Yayın kararlarının uygulanması (2026-11-21)

Kararlar: kod MIT; özgün raporlar ve grafikler CC BY 4.0 (© 2026 Seyhan Anıl Kaya); ham UCI verisi
depoya girmez; depo adı `medical-risk-modeling-lab`; yazar Seyhan Anıl Kaya; `CITATION.cff` (DOI yok).

| Dosya | İçerik |
|---|---|
| `LICENSE`, `LICENSES/MIT.txt` | Standart MIT metni, "Copyright (c) 2026 Seyhan Anıl Kaya" (GitHub lisans algılaması için yalın metin) |
| `LICENSES/CC-BY-4.0.txt` | creativecommons.org'dan indirilen resmî, değiştirilmemiş tam metin (18 657 bayt) |
| `LICENSING.md` | Dosya/klasör bazında lisans kapsamı: kod → MIT; özgün raporlar/grafikler → CC BY 4.0; uyarlanmış içerik ve türetilmiş tablolar → CC BY 4.0 + üçüncü taraf atfı |
| `THIRD_PARTY_NOTICES.md` | UCI verisi (CC BY 4.0, atıf, yapılan değişiklikler, donörlerin istediği dört araştırmacı), TRIPOD+AI uyarlaması (CC BY 4.0), CC lisans metni, bağımlılık lisansları (kurulu paket metadatasından okundu) |
| `CITATION.cff` | CFF 1.2.0; başlık, yazar, sürüm 1.0.0, lisanslar, veri/makale referansları (yalnızca gerçek DOI'ler). `cffconvert --validate` ile **geçerli**. Proje için DOI, yayın tarihi ve depo URL'si bilinçli olarak eklenmedi |
| `.gitignore` | `data/raw/` ve `data/interim/cleveland_typed.csv` dışlandı |
| `pyproject.toml`, `src/mrml/__init__.py` | Sürüm 1.0.0, yazar, `license = "MIT"`, lisans dosyaları |
| `README.md` | Yazar/sürüm/lisans satırı, "ham veri depoda değil" açıklaması, lisans tablosu, `CITATION.cff` atfı, klon + kilit dosyasıyla kurulum, adım sırası |
| `reports/final_report.md` | Yazar, sürüm ve lisans satırı; veri erişimi beyanı güncellendi |

**Doğrulamalar**
- `.gitignore`, Git'in eşleştirme kurallarını uygulayan `pathspec` 1.1.1 ile proje dışında
  denetlendi. Git kullanılmadı.
  - Proje 14 029 dosya içeriyor (`.venv` dahil).
  - **`data/raw/` altındaki 23 dosyanın tamamı** ve `cleveland_typed.csv` dışlanıyor.
  - Depoya girecek: 112 dosya, 2,19 MB; `.venv` ve önbellekler dahil değil.
  - Depoda kalan veri dosyaları yalnızca `data/interim/split_phase2.csv` (satır numarası + ayrım
    etiketi) ve `data/metadata/provenance.json`.
- **Yeni klon simülasyonu:** ham veri olmadan `pytest` çalıştırıldı ve **bir hata bulundu**.
  Aşama 4'te eklenen `test_other_site_checksums_recorded_and_match`, veri yokken atlanmak yerine
  çöküyordu. Test, veri fixture'ına bağlandı. Sonuç: 45 geçti, 10 atlandı, 0 hata.
- **Testler:** 6 yeni yayın testi eklendi (`tests/test_release_files.py`): MIT metni ve sahibi,
  CC BY 4.0 bütünlüğü, lisans kapsamları, CFF ↔ `pyproject` ↔ `__version__` sürüm tutarlılığı ve
  uydurma DOI olmaması, `.gitignore` kuralları, README atıfları ve göreli bağlantılar.
  **Toplam 55 / 55 geçti.**
- **`audit_release.py`:** 111 / 111 kontrol geçti.
- **Gizlilik:** yazar adı yalnızca 8 beklenen dosyada geçiyor (LICENSE, LICENSES/MIT.txt,
  LICENSING.md, CITATION.cff, pyproject.toml, README.md, final_report.md, yayın testi).
  E-posta veya yerel yol yok.

**Bilginize — depoda kalan satır düzeyi içerik**
- `reports/tables/rows_with_missing.csv`, eksik değeri olan 6 Cleveland kaydını tam olarak içeriyor
  (veri denetimi çıktısı).
- `reports/tables/phase3/oof_predictions_*.csv` ve `phase2/locked_test_predictions.csv`, satır
  numarasıyla birlikte gözlenen sonucu içeriyor.

Bunlar ham veri dosyası değil, analiz çıktısı; CC BY 4.0 atıfla buna izin veriyor. Ancak "ham veri
yok" ilkesini katı uygulamak isterseniz bu dosyalar da `.gitignore`'a eklenebilir. Hepsi boru hattı
tarafından yeniden üretilir.

**Yapılmayanlar:** ## 15. Yerel Git deposu

Kullanıcı onayıyla yerel bir Git deposu (`main` dalı) başlatıldı ve ilk commit yapıldı. Push, GitHub deposu veya deployment yok.

- **Satır sonu sorunu bulundu ve düzeltildi.** Bu bilgisayarda `core.autocrlf=true`; 64 dosya diskte CRLF olduğu için Git'te LF olarak saklanacak, klonlarda SHA-256 değerleri envanterden sapacaktı. `.gitattributes` (`* -text`) eklendi; dosyalar bayt bayt saklanıyor.
- `scripts/release_manifest.py` artık `.git/` klasörünü yayın içeriği saymıyor; `.gitattributes` kod/yapılandırma olarak (MIT) sınıflandırıldı. Envanter 108 dosya.
- Commit'teki dosya listesi envanterle birebir aynı (+ `RELEASE_MANIFEST.csv`); `data/raw/` ve `data/private/` altından dosya yok.
- Commit'ten yapılan bir `git clone` içinde `release_manifest.py --check` temiz geçti (bütün SHA-256 değerleri eşleşti).

## 14. Ek — Kişi düzeyi çıktıların yayından çıkarılması (2026-11-21)

**Karar:** satır düzeyinde hasta kaydı içeren hiçbir analiz çıktısı yayımlanmaz. Toplulaştırılmış
istatistikler, model performans tabloları, grafikler, raporlar ve kod yayımlanır.

### 14.1 Tespit edilen kişi düzeyi çıktılar ve yapılanlar

Yayın kümesindeki bütün CSV/JSON dosyaları başlık ve içerik bakımından tarandı.

| Dosya (eski konum) | İçerik | Yapılan |
|---|---|---|
| `reports/tables/rows_with_missing.csv` | 6 hastanın bütün klinik değerleri | → `data/private/phase1/` (yayın dışı) |
| `reports/tables/consistency_issues.csv` | satır no + ölçülen değer | → `data/private/phase1/`; yerine toplulaştırılmış `reports/tables/consistency_summary.csv` |
| `reports/tables/phase2/locked_test_predictions.csv` | satır + gözlenen sonuç + kişi bazlı tahmin | → `data/private/phase2/` |
| `reports/tables/phase3/oof_predictions_{pre_angio,full}.csv` | satır + gözlenen sonuç + kişi bazlı tahmin | → `data/private/phase3/` |
| `data/interim/split_phase2.csv` | satır no → test/geliştirme | → `data/private/` |
| `data/interim/cleveland_typed.csv` | 303 kaydın tam kopyası | → `data/private/` |
| `reports/tables/missing_summary.csv` | toplamlar + **hangi satırda eksik olduğu** (`row_indices`) | `row_indices` sütunu kaldırıldı; yalnızca toplamlar |
| `reports/figures/02_missingness.png` | kayıt başına eksiklik deseni, satır numarası etiketli | Değişken başına toplam eksik sayısı grafiğine çevrildi |

Kişi düzeyi çıktılar artık yalnızca `data/private/` klasörüne yazılıyor
(`config.PRIVATE_DIR`). `.gitignore` bu klasörü bütünüyle dışlıyor. Böylece ileride eklenecek
yeni bir kişi düzeyi çıktı da yanlışlıkla yayına giremez. Eski konumlardaki kopyalar,
`data/private/` altındaki yeniden üretilmiş kopyalarla bayt düzeyinde aynı oldukları
doğrulandıktan sonra silindi.

Gözden geçirilip yayında bırakılanlar (kişi düzeyi kayıt içermiyor):
- **Kat başına skor tabloları:** `cv_fold_scores_*`, `threshold_folds_*`, `permutation_*`. Satırlar
  kişiler değil, CV katları.
- **Spline eğrileri** (`spline_shapes.csv`): değişken ızgarası üzerinde model eğrileri.
- **Grafiklerdeki uç değer noktaları ve spline grafiğindeki çizgi işaretleri:** tek değişkenli
  marjinal dağılımlar. Değişkenler arasında kayıt bağlantısı olmadığından bir hasta kaydı yeniden
  kurulamaz.
- **Raporlardaki tekil uç değer anmaları** (ör. "`chol` = 564, 1 kayıt"): bağlamsız tek
  değerler.

### 14.2 Yayın envanteri

- `RELEASE_MANIFEST.csv`: depoya girecek her dosya için yol, boyut, SHA-256, kategori ve lisans.
- `scripts/release_manifest.py`: envanteri üretir. `--check` seçeneğiyle şunları doğrular:
  - envanter güncel mi
  - her dosyanın lisans kapsamı var mı
  - yayın kümesinde kişi düzeyi veri belirtisi (`row`, `y`, `id` sütunları, `*_indices`
    listeleri) var mı
  - `data/raw/` ve `data/private/` dışarıda mı
- Araç Git ya da ek paket gerektirmez. `.gitignore` eşleştiricisi, Git'in kurallarını uygulayan
  `pathspec` 1.1.1 ile projedeki 14 038 dosyanın tamamında çapraz doğrulandı: 0 uyuşmazlık.

| Kategori | Lisans | Dosya | Boyut | Konum |
|---|---|---|---|---|
| Kod | MIT | 27 | 170 kB | `src/mrml` (11), `scripts` (5), `tests` (6), kök (5: `pyproject.toml`, `requirements*.txt`, `.gitignore`, `.gitattributes`) |
| Özgün içerik | CC BY 4.0 | 12 | 112 kB | kök (4: README, LICENSING, THIRD_PARTY_NOTICES, CITATION.cff), `reports/*.md` (6), `docs` (2) |
| Uyarlanmış içerik | CC BY 4.0 (uyarlama) | 2 | 13 kB | `docs/data_dictionary.md`, `docs/tripod_ai_checklist.md` |
| Toplulaştırılmış tablolar | CC BY 4.0 (UCI'dan türetilmiş) | 46 | 303 kB | `reports/tables` (11 + 16 + 18), `data/metadata/provenance.json` |
| Grafikler | CC BY 4.0 | 18 | 1 548 kB | `reports/figures` |
| Lisans metinleri | MIT / CC BY 4.0 resmî metni | 3 | 21 kB | `LICENSE`, `LICENSES/` |
| **Toplam** | | **108 + envanterin kendisi** | **2,18 MB** | |

**Yayın dışı (yeniden üretilir):**
- `data/raw/`: 23 dosya; `run_phase1.py` indirir ve SHA-256 ile doğrular.
- `data/private/`: 7 dosya; `run_phase1–3.py` üretir.
- `reports/*_run.log`: zaman damgalı koşu logları.
- `.venv/`, önbellekler.

### 14.3 Doğrulama sonuçları

| Kontrol | Sonuç |
|---|---|
| **Lisans ve atıf** | `CITATION.cff` CFF 1.2.0'a göre geçerli (`cffconvert`). `LICENSE` = `LICENSES/MIT.txt`. CC BY 4.0 metni resmî ve değiştirilmemiş (SHA-256 `9ba9550a…`). Lisans dosyalarının altısı da yayın kümesinde. Her yayın dosyasının bir lisans kapsamı var |
| **Proje ortamı** | 58 / 58 test · `release_manifest.py --check` temiz · `audit_release.py` **134 / 134** (yeni "6-envanter" grubu 23 / 23 dahil) |
| **Yeni klon simülasyonu** | Proje dışında boş bir klasöre **yalnızca envanterdeki dosyalar** kopyalandı. Yeni Python 3.14.4 ortamına `pip install -r requirements-lock.txt` yapıldı |
| — veri indirilmeden | 48 geçti, 10 atlandı, 0 hata |
| — Aşama 1–3 | Üçü de ilk denemede hatasız tamamlandı (yaklaşık 19 dakika) |
| — testler | 58 / 58 |
| — envanter (`--check`) | Temiz: yeniden üretilen bütün yayın dosyaları kayıtlı SHA-256'larla aynı |
| — yayın denetimi | 134 / 134 |
| **Dışlanan çıktıların yeniden üretilebilirliği** | Yeni klonda üretilen 7 `data/private/` dosyası ve 23 `data/raw/` dosyası, projedeki kopyalarla bayt düzeyinde aynı |

### 14.4 Süreçte bulunan ve giderilen sorunlar

- **Proje içindeki ilk Aşama 3 koşusu yarıda kaldı.** Bir joblib işçi süreci işletim sistemi
  tarafından sonlandırıldı (`TerminatedWorkerError`, eşik metrikleri adımı). Kod hatası değildi:
  aynı kod yeniden çalıştırıldığında ve yeni klonda ilk denemede hatasız tamamlandı. Çıktılar
  önceki koşuyla bayt düzeyinde aynı. Çok çekirdekli uzun koşularda nadiren görülebilir; tekrar
  çalıştırmak yeterli.
- **Yeni klon testinde 1 test ve 2 denetim kontrolü başarısız oldu.** Neden, test düzeneğinin
  koşu loglarını klonun kök klasörüne yazmasıydı: envanter bunları lisanssız, beklenmeyen dosyalar
  olarak doğru biçimde yakaladı. Loglar klon dışına taşınınca hepsi geçti. Bu, envanter
  kontrolünün beklenmeyen dosyaları gerçekten yakaladığını da gösteriyor.

### 14.5 Kritik hata durumu

**Kritik hata yok.** Bilimsel sonuçlar değişmedi. Yayımlanan bütün sayısal tablolar ve
grafikler, kişi düzeyi çıktıların taşınmasından önceki koşuyla aynı. Yalnızca şu yayın dosyaları
tasarım gereği değişti:
- `missing_summary.csv` (`row_indices` sütunu kaldırıldı)
- `02_missingness.png` (toplulaştırılmış grafik)
- yeni `consistency_summary.csv`

## 15. Yerel Git deposu

Kullanıcı onayıyla yerel bir Git deposu (`main` dalı) başlatıldı ve ilk commit yapıldı. Push, GitHub deposu veya deployment yok.

- **Satır sonu sorunu bulundu ve düzeltildi.** Bu bilgisayarda `core.autocrlf=true`; 64 dosya diskte CRLF olduğu için Git'te LF olarak saklanacak, klonlarda SHA-256 değerleri envanterden sapacaktı. `.gitattributes` (`* -text`) eklendi; dosyalar bayt bayt saklanıyor.
- `scripts/release_manifest.py` artık `.git/` klasörünü yayın içeriği saymıyor; `.gitattributes` kod/yapılandırma olarak (MIT) sınıflandırıldı. Envanter 108 dosya.
- Commit'teki dosya listesi envanterle birebir aynı (+ `RELEASE_MANIFEST.csv`); `data/raw/` ve `data/private/` altından dosya yok.
- Commit'ten yapılan bir `git clone` içinde `release_manifest.py --check` temiz geçti (bütün SHA-256 değerleri eşleşti).
