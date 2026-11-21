# Aşama 2 Raporu — Doğrulama Protokolü ve Temel Modeller

Tarih: 2026-11-18 · Veri: UCI Heart Disease, Cleveland (n = 303, 139 olay) · Çalıştırma:
`python scripts/run_phase2.py` (log: `reports/phase2_run.log`, tablolar: `reports/tables/phase2/`).

> **Aşama 4 düzeltme notu (2026-11-18).** Bu rapor son bilimsel denetimde güncellendi:
> (1) eşleştirilmiş karşılaştırmalara Holm düzeltmeli p-değerleri eklendi (18 karşılaştırma tek
> aile); bu, bazı karşılaştırmaların yorumunu değiştirdi (§2, §3); (2) anlamsız testler "etki yok"
> olarak yorumlanmaz (§5 H2); (3) kilitli test kümesinin hangi analizlerde kullanıldığı açıkça
> belirtildi (§1). Ayrıntı: `reports/release_readiness.md`.

> Bu sonuçlar bir araştırma örneğine aittir. Hiçbir model bireysel hasta için risk hesaplamada
> kullanılmamalıdır. Hedef, *kayıtlı anjiyografik tanıdır*; gelecekteki olay veya ölüm riski değildir.

## 1. Protokol (önceden belirlendi, `docs/research_plan.md`)

| Öğe | Uygulama |
|---|---|
| Kilitli test | Tabakalı %20: **n = 61 (28 olay)**; geliştirme **n = 242 (111 olay)**; tohum 42; `data/private/split_phase2.csv` (satır anahtarlı, yayımlanmaz; tohumdan yeniden üretilir) |
| Dış döngü | Tekrarlı tabakalı 5 kat × 10 tekrar = 50 kat (bütün modeller aynı katlar → eşleştirilmiş karşılaştırma) |
| İç döngü | 5 kat `GridSearchCV`, skor: log-loss (uygun skor; kalibrasyonu da ödüllendirir) |
| Önişleme | `Pipeline` içinde: sayısal → medyan + eksiklik göstergesi + ölçekleme; ikili → en sık; `cp`, `restecg`, `slope`, `thal` → en sık + one-hot. Her katta yeniden fit edilir (sızıntı yok, testle doğrulandı) |
| Özellik setleri | **Anjiyografi öncesi** (11 değişken) · **Tam** (+ `ca`, `thal`) |
| Modeller | Referans yaş+cinsiyet (cezasız LR) · **L2 LR (birincil, önceden belirlenmiş)** · Elastic-Net LR · Random Forest · HistGradientBoosting |
| Karşılaştırma | Nadeau–Bengio düzeltmeli tekrarlı-örnekleme t testi (katlar bağımsız olmadığı için) |

Kilitli test kümesi model, özellik, hiperparametre veya eşik seçimi için **hiç kullanılmadı**;
seçim yalnızca önceden belirlenmiş birincil model ve CV sonuçlarına dayanır. Kilitli testteki 61
kişi, öngörü performansı tahmini olmayan şu analizlerde bütün Cleveland verisinin parçası olarak
kullanıldı: AS2 odds oranı modeli (§5), transfer modelinin eğitimi ve "Cleveland iç CV" referans
satırı (§8). Aşama 1 EDA'sı da 303 kişinin tamamında yapıldı; `slope`'un nominal kodlanması
kararı EDA'daki monoton olmayan örüntüye dayandığından, bu küçük bir model belirtimi bilgisi
taşır (sıralı kodlama duyarlılık analizinde sonuç değişmedi, §6). (Not: hızlı duman testi sırasında test metrikleri bir kez
daha hesaplandı; sonuçlar deterministiktir ve hiçbir karar bu değerlere göre değiştirilmedi.)

## 2. İç içe CV sonuçları (geliştirme kümesi; birincil performans tahmini)

ROC AUC, 50 dış katın ortalaması ± SD; Brier ve kalibrasyon eğimi kat ortalaması.

| Model | Ön-anjiyo AUC | Brier | Kal. eğimi | Tam AUC | Brier | Kal. eğimi |
|---|---|---|---|---|---|---|
| Referans yaş+cinsiyet | 0,716 ± 0,070 | 0,215 | 1,05 | 0,716 ± 0,070 | 0,215 | 1,05 |
| **L2 lojistik (birincil)** | **0,854 ± 0,056** | 0,157 | 1,14 | **0,900 ± 0,039** | 0,126 | 1,20 |
| Elastic-Net lojistik | 0,854 ± 0,056 | 0,157 | 1,08 | 0,898 ± 0,039 | 0,129 | 1,18 |
| Random Forest | 0,833 ± 0,058 | 0,167 | 1,30 | 0,892 ± 0,039 | 0,136 | 1,56 |
| Gradyan artırma | 0,833 ± 0,056 | 0,169 | 0,90 | 0,875 ± 0,044 | 0,147 | 0,93 |

Kat-dışı (10 tekrar ortalaması) olasılıklarla L2 modeli: ön-anjiyo AUC 0,854, kalibrasyon eğimi
1,04, CITL 0,01; tam set AUC 0,898, eğim 1,08, CITL 0,01 → **iç kalibrasyon iyi**.

**Eşleştirilmiş karşılaştırmalar** (AUC farkı, %95 GA; p = Nadeau–Bengio düzeltmeli
tekrarlı-örnekleme t testi, nominal; p_Holm = tablodaki 18 karşılaştırma için Holm düzeltmesi;
`cv_paired_comparisons.csv`):
- L2 − referans: ön-anjiyo **+0,139** [0,060, 0,217], p = 0,0009, p_Holm = 0,011; tam **+0,184**
  [0,110, 0,258], p < 0,001, p_Holm < 0,001.
- RF / gradyan artırma − referans (ön-anjiyo): +0,117 / +0,118, nominal p = 0,008 / 0,005, ancak
  p_Holm = 0,080 / 0,059.
- Elastic-Net − L2: ≈ 0 (her iki sette p > 0,5).
- Random Forest − L2: −0,022 [−0,051, 0,007] (ön-anjiyo), −0,008 [−0,026, 0,010] (tam); anlamlı
  fark saptanmadı.
- Gradyan artırma − L2: −0,021 (ön-anjiyo, p = 0,20); −0,025 [−0,050, −0,001] (tam, nominal
  p = 0,046, **p_Holm = 0,27**).
- Sonuç: Karmaşık modellerin basit L2 lojistik regresyondan **daha iyi olduğuna dair kanıt
  bulunmadı**; bu, eşdeğer olduklarının kanıtı da değildir. RF'nin kalibrasyon eğimi (1,3–1,6;
  aşırı temkinli olasılıklar) daha zayıftır. Tekrarlı CV'de katlar bağımsız olmadığından
  düzeltilmiş t testi de yaklaşık bir yöntemdir.

## 3. AS4 — `ca` ve `thal` eklenmesinin artımsal değeri

CV'de L2 için tam − ön-anjiyo: **+0,045** [0,012, 0,079], nominal p = 0,009; 18 karşılaştırmalık
aile için Holm düzeltmesiyle **p_Holm = 0,080**. Bu karşılaştırma önceden belirlenmiş birincil
hipotezdir (H3), bu yüzden nominal p de raporlanır; ancak tutucu düzeltme altında istatistiksel
olarak anlamlı değildir. Artışın yönü dört modelin hepsinde aynıdır (+0,04–0,06; RF için
p_Holm = 0,012).
Kilitli testte fark −0,002 [−0,075, 0,069] — 61 kişilik testin bu büyüklükte bir farkı ayırt
edecek gücü yoktur. Yorum: floroskopi ve talyum bulguları ayrıştırmayı artırır; ancak bunlar
anjiyografiye yakın ileri testlerdir, bu yüzden "tam" model bir tarama senaryosunu temsil etmez.

## 4. Kilitli test (tek seferlik, n = 61)

| Set | Model | AUC [%95 bootstrap GA] | Brier | Kal. eğimi |
|---|---|---|---|---|
| Ön-anjiyo | **L2 (birincil)** | **0,950 [0,887, 0,994]** | 0,098 | 2,07 |
| Tam | **L2 (birincil)** | **0,948 [0,881, 0,992]** | 0,095 | 1,34 |
| Ön-anjiyo / Tam | Referans | 0,680 [0,531, 0,809] | 0,226 | 0,71 |

Diğer modeller 0,938–0,963 arasında; GA'lar tamamen örtüşür (`locked_test_results.csv`).
**Önemli uyarı:** Test AUC'si CV tahmininden belirgin yüksektir (0,95 vs 0,85). Bu, 61 kişilik
kümenin rastlantısal olarak "kolay" düşmesiyle uyumludur; GA geniştir ve kalibrasyon eğimi
tahminleri (1,3–2,1) bu n'de güvenilmezdir. **Raporlanacak birincil performans tahmini CV
sonucudur** (ön-anjiyo ≈ 0,85, tam ≈ 0,90); test sonucu yalnızca "belirgin bozulma yok"
kontrolü olarak okunmalıdır.

Seçilen hiperparametre (geliştirme kümesinin tamamında iç CV ile): L2 C = 0,316 (her iki set).

## 5. AS2 — Çok değişkenli ilişki (cezasız lojistik regresyon, n = 303, 139 olay, 10 parametre)

Bu analiz öngörü değil ilişki sorusudur; bu yüzden bütün Cleveland verisi kullanıldı.

| Terim | OR [%95 GA] | p |
|---|---|---|
| Yaş (10 yıl başına) | 1,46 [0,99, 2,17] | 0,058 |
| Erkek cinsiyet | **5,92 [2,75, 12,75]** | < 0,001 |
| cp = 4 asemptomatik (ref: tipik anjina) | **8,83 [2,73, 28,59]** | < 0,001 |
| cp = 2 / cp = 3 | 2,13 [0,55, 8,30] / 1,18 [0,35, 3,89] | 0,27 / 0,79 |
| thalach (10 atım/dk başına) | 0,87 [0,73, 1,05] | 0,15 |
| Egzersiz anjinası | **2,16 [1,03, 4,49]** | 0,040 |
| oldpeak (1 mm başına) | **1,88 [1,29, 2,73]** | 0,001 |
| slope = 2 düz (ref: yukarı) | **2,22 [1,02, 4,82]** | 0,044 |
| slope = 3 aşağı | 0,79 [0,16, 3,92] | 0,77 |

- **H1 kısmen desteklendi:** yaş ve cinsiyet ayarından sonra `oldpeak`, `exang` ve `cp = 4` ile
  ilişki sürüyor. `thalach` ise diğer egzersiz bulgularıyla birlikte modele girdiğinde istatistiksel
  olarak anlamlı değil (bu, ilişkinin olmadığı anlamına gelmez) (tek değişkenli ilişkisi güçlüydü; `oldpeak`, `slope`, `age` ile korelasyon).
- **H2 ile çelişen kanıt bulunmadı:** `trestbps`, `chol`, `fbs` eklenince olabilirlik oranı
  testi χ² = 6,73, sd = 3, **p = 0,081**; ek katkı istatistiksel olarak gösterilemedi. Anlamsız bir
  test ek katkının *olmadığını* kanıtlamaz (n = 303; `trestbps` OR 1,21 [1,00, 1,47] sınırda).
  Permütasyon öneminde de bu üç değişkenin katkısı ≈ 0.
- Referans grubu tipik anjina (n = 23) küçük olduğundan `cp` OR'larının GA'ları geniştir.
- `cp = 4`'ün en yüksek OR'a sahip olması klinik sezgiye aykırıdır ve sevk edilmiş hasta
  örnekleminin (spektrum yanlılığı) bir sonucu olabilir. Bu OR'lar **nedensel etki değildir**.

## 6. Duyarlılık analizleri (L2, CV AUC)

| Set | Birincil | Tam vaka | `slope` sıralı sayısal |
|---|---|---|---|
| Ön-anjiyo | 0,854 (n = 242) | 0,854 (eksik yok) | 0,849 |
| Tam | 0,900 (n = 242) | 0,902 (n = 240) | 0,899 |

Sonuçlar eksik veri yöntemine ve `slope` kodlamasına karşı sağlamdır. (Ön-anjiyo setinde eksik
veri olmadığından "tam vaka" satırı birincil analizle aynıdır.)

## 7. Permütasyon önemi (L2, 50 dış kat)

Ön-anjiyo: `cp` > `sex` > `oldpeak` > `thalach` > `slope`; `age`, `trestbps`, `chol`, `fbs` ≈ 0.
Tam set: `ca` > `thal` > `cp` > `sex`; `oldpeak`'in önemi `ca`/`thal` varken ≈ 0'a düşer (bilgi
örtüşmesi). Önem, model içi öngörü katkısıdır; nedensel önem değildir.

## 8. AS5 — Keşifsel transfer (diğer UCI merkezleri)

Model: tüm Cleveland (n = 303) ile eğitilmiş L2, **transfer seti** (`slope`, `ca`, `thal` hariç; diğer
merkezlerde büyük ölçüde eksik). Eksikler Cleveland medyan/en sık değerleriyle atandı.

| Merkez | n | Prevalans | Ort. öngörü | AUC [%95 GA] | Kal. eğimi |
|---|---|---|---|---|---|
| Cleveland (iç CV) | 303 | %45,9 | %45,8 | 0,876 | 1,05 |
| Macaristan | 294 | %36,1 | %42,2 | **0,878 [0,832, 0,917]** | 0,91 |
| İsviçre | 123 | %93,5 | %69,2 | 0,758 [0,612, 0,895] | 0,59 |
| Long Beach VA | 200 | %74,5 | %70,4 | 0,737 [0,656, 0,812] | 0,57 |

- Ayrıştırma Macaristan'da korunuyor, İsviçre ve VA'da belirgin düşüyor.
- Kalibrasyon merkezden merkeze bozuluyor: Macaristan'da **fazla tahmin**, İsviçre'de güçlü
  **eksik tahmin**; eğim 0,6 civarında (aşırı uç tahminler). Bu, Detrano ve ark. (1989)'un
  Macaristan ve Long Beach'te fazla tahmin bulgusuyla nitel olarak uyumludur.
- Ciddi sınırlılık: İsviçre'de `chol` %100, VA'da `thalach`/`exang`/`oldpeak` ~%27 eksik ve
  atandı; tam vaka analizleri (Macaristan n = 261: AUC 0,871; VA n = 97: 0,762) benzer.
- Sonuç: **Model başka bir ortama yeniden kalibrasyon olmadan aktarılamaz.**

## 9. Test sonuçları

`python -m pytest -q` → **33 passed** (Aşama 1'den 21 + yeni 12): önişleyici yalnızca eğitim
satırlarından istatistik öğreniyor (sızıntı yok); görülmemiş kategori/eksik değerde çalışıyor;
ön-anjiyo setinde `ca`/`thal` yok; Newton lojistik regresyon sklearn ile aynı katsayıları veriyor;
kalibrasyon eğimi ideal (≈ 1) ve aşırı kendinden emin (≈ 0,5) durumda doğru; düzeltilmiş t testi
olağan t testinden daha temkinli; iç içe CV tekrarlanabilir (aynı tohum → aynı skorlar) ve sinyali
yakalıyor; OR referans kodlaması ve LRT doğru.

## 10. Sınırlılıklar (Aşama 1'e ek)

- Kilitli test (n = 61) yalnızca kaba bir kontroldür; kalibrasyon ve model farkları için güçsüzdür.
- İç içe CV performans tahminidir, dış geçerlilik değildir; transfer analizi ağır eksik veri ve
  farklı vaka karışımı yüzünden keşifseldir.
- Hiperparametre ızgaraları küçük tutuldu (n'ye uygun); ağaç modelleri daha geniş ayarla bir miktar
  iyileşebilir ama mevcut kanıt L2'yi geçeceklerini göstermiyor.
- Odds oranları ölçülmemiş karıştırıcılara (ilaç, sigara, etnik köken vb.) ve seçim yanlılığına açıktır.
- `ca`/`thal` modelleri olası hedef sızıntısı / kullanım zamanı uyumsuzluğu içerir.

## 11. Önerilen sonraki adımlar (Aşama 3 için öneri — onay gerekir)

1. Karar eğrisi analizi (net fayda) ve eşik-bağımlı metriklerin (duyarlılık/özgüllük) yalnızca
   eğitim katlarında belirlenen eşiklerle raporlanması.
2. Transfer için yeniden kalibrasyon deneyi (kesişim güncelleme / lojistik yeniden kalibrasyon) ve
   merkez-dışı-bırak (leave-one-site-out) analizi, transfer özellik setiyle.
3. Doğrusal olmayan ilişkiler için kısıtlı kübik spline'lı lojistik model (age, oldpeak, thalach).
4. TRIPOD+AI kontrol listesinin doldurulması ve bulguların tek bir son rapora birleştirilmesi.
