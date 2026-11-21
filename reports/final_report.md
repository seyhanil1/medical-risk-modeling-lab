# Koroner Anjiyografiye Sevk Edilen Hastalarda Anjiyografik Koroner Arter Hastalığı Tanısının Klinik Değişkenlerle Öngörüsü: UCI Heart Disease (Cleveland) Verisiyle Çok Değişkenli Bir Tahmin Modelinin Geliştirilmesi ve İç–Dış Değerlendirmesi

**Medical Risk Modeling Lab — Birleşik Son Rapor (Aşama 1–3, Aşama 4 denetimiyle güncellendi)** · 2026-11-18

Yazar: Seyhan Anıl Kaya · Sürüm 1.0.0 · Rapor lisansı: CC BY 4.0 (kod: MIT; bkz. `LICENSING.md`)

> **Aşama 4 düzeltme notu.** Son bilimsel denetimde (i) çoklu karşılaştırma için Holm düzeltmeli
> p-değerleri eklendi ve bazı anlamlılık yorumları değişti (AS4: nominal p = 0,009, p_Holm = 0,080);
> (ii) alt grup farkları için doğrudan bootstrap GA'ları eklendi; (iii) karar eğrisinin varsayımsal
> niteliği ve GA'larının sınırlılığı açıklandı; (iv) Aşama 3 analizlerinin protokolde önceden
> belirtilmediği beyan edildi. Ayrıntı: `reports/release_readiness.md`.

> **Kapsam uyarısı.** Bu bir araştırma ve yöntem çalışmasıdır. Model, gerçek hastalarda teşhis,
> tedavi önerisi veya klinik karar desteği için **kullanılmamalıdır**. Veri 1980'lerden, küçük,
> sevk edilmiş hastalardan oluşan bir örneklemdir. Öngörülen sonuç, *kayıtlı anjiyografik tanıdır*;
> gelecekte hastalık gelişme veya ölüm riski değildir. Raporlama TRIPOD+AI'a göre yapılandırılmıştır
> (`docs/tripod_ai_checklist.md`).

## 0. Yapılandırılmış özet

**Amaç.** Koroner anjiyografiye sevk edilen hastalarda, rutin klinik ve egzersiz testi
değişkenleriyle anjiyografik koroner arter hastalığı (herhangi bir ana damarda > %50 daralma)
varlığını öngören bir modeli geliştirmek, iç ve merkezler arası performansını değerlendirmek.

**Yöntem.** Geliştirme: Cleveland Clinic (n = 303, 139 olay). %20 kilitli test (n = 61), kalan
242 kişide 5 kat × 10 tekrarlı iç içe çapraz doğrulama. İki önceden belirlenmiş özellik seti
(anjiyografi öncesi: 11 değişken; tam: + floroskopi `ca` ve talyum `thal`). Önceden belirlenmiş
birincil model L2 lojistik regresyon; karşılaştırma: yaş+cinsiyet referansı, Elastic-Net, Random
Forest, gradyan artırma, spline'lı lojistik. Ölçütler: ROC AUC, Brier, kalibrasyon eğimi/kesişimi,
karar eğrisi. Dış değerlendirme: Macaristan (n = 294), İsviçre (n = 123), Long Beach VA (n = 200);
yeniden kalibrasyon ve merkez-dışı-bırak analizi.

**Sonuçlar.** CV'de L2 modeli: ön-anjiyo AUC **0,854** (SD 0,056), tam set **0,900** (0,039);
referans modelden +0,14 ve +0,18 daha iyi; iç kalibrasyon iyi (kat-dışı eğim 1,04–1,08). Ağaç
tabanlı modellerin ve spline modelinin L2'den daha iyi olduğuna dair kanıt bulunmadı (spline
ön-anjiyo AUC farkı −0,027; nominal p = 0,011, aile içi Holm p = 0,043). `ca`/`thal` AUC'yi +0,045
[0,012, 0,079] artırdı (nominal p = 0,009; 18 karşılaştırmalık ailede Holm p = 0,080). Varsayımsal
bir sevk kararı için yapılan karar eğrisinde model, eşik ≈ 0,2–0,5 aralığında "herkesi sevk et" ve
"kimseyi sevk etme" stratejilerinden daha yüksek net fayda gösterdi; bu bir klinik eşik önerisi
değildir. Kadınlarda öngörülen risk gözlenenden yüksekti (kalibrasyon-genelde −0,43), ancak yalnızca
18 olay olduğundan bu tahmin çok belirsizdir. Dış merkezlerde AUC Macaristan 0,878, İsviçre 0,758,
VA 0,737; kalibrasyon merkezden merkeze bozuldu ve yeniden kalibrasyon gerektirdi.

**Sonuç.** Bu küçük veri setinde basit, cezalı lojistik regresyon daha karmaşık yöntemlerden geride
kalmadı ve iyi kalibre edildi; karmaşık yöntemlerin ek bir yararı gösterilemedi. Ancak performans merkezler arasında heterojendir;
model, yerel yeniden kalibrasyon ve güncel, prospektif dış doğrulama olmadan başka bir ortama
aktarılamaz.

## 1. Arka plan ve amaçlar (TRIPOD+AI 3–4)

- Bağlam: **tanısal** bir tahmin problemi — anjiyografi sonucunu, anjiyografiden önce elde edilen
  bilgilerle öngörmek. Önceki çalışma: Detrano ve ark. (1989), aynı veritabanlarında lojistik
  regresyon türevli bir diskriminant fonksiyonu (CDF) ve CADENZA'yı karşılaştırmış; merkezler
  arası aktarımda fazla tahmin bildirmiştir.
- Hedef popülasyon: göğüs ağrısı vb. nedenlerle **anjiyografiye sevk edilmiş** yetişkinler.
- Amaç kullanıcılar: yok — bu çalışma bir yöntem/öğrenme çalışmasıdır, klinik kullanım hedeflenmez.
- Araştırma soruları (`docs/research_plan.md`): AS1 tek değişkenli ilişkiler; AS2 çok değişkenli
  ilişkiler (odds oranları); AS3 anjiyografi öncesi bilgilerle öngörü; AS4 `ca`/`thal`'in artımsal
  değeri; AS5 merkezler arası genellenebilirlik.

## 2. Veri (TRIPOD+AI 5–9)

- Kaynak: UCI Machine Learning Repository, Heart Disease (DOI 10.24432/C52P4X, CC BY 4.0),
  `processed.*.data` dosyaları; SHA-256 özetleri `data/metadata/provenance.json`.
- Merkezler: Cleveland Clinic Foundation (geliştirme); Macaristan Kardiyoloji Enstitüsü (Budapeşte);
  Zürih ve Basel Üniversite Hastaneleri (İsviçre); V.A. Medical Center, Long Beach (değerlendirme).
- Tarihler: 1980'ler (UCI bağış tarihi 1988-06-30); kesin toplama tarihleri belgelenmemiş.
- Sonuç: `num` > 0 → `disease = 1` (`docs/decisions.md` K2). Kesitsel; zaman ufku yok.
- Öngörücüler: 13 değişken; tanımlar `docs/data_dictionary.md`. Ölçüm zamanı, değerlendirici
  nitelikleri ve körleme kaynakta belgelenmemiştir. Tedavi/ilaç bilgisi işlenmiş dosyalarda yoktur.
- Veri kalitesi (Aşama 1): Cleveland'da 6 eksik hücre (`ca` 4, `thal` 2), tekrar yok, kod dışı değer
  yok. Diğer merkezlerde `chol` = 0 ve `trestbps` = 0 eksik veri olarak işlendi.

## 3. Katılımcı akışı, örneklem büyüklüğü ve merkez özellikleri (TRIPOD+AI 10, 20–21)

| Analiz | n | Olay |
|---|---|---|
| Cleveland toplam | 303 | 139 |
| Geliştirme (iç içe CV, hiperparametre ayarı) | 242 | 111 |
| Kilitli test | 61 | 28 |
| AS2 odds oranı modeli (bütün Cleveland) | 303 | 139 |
| Dış: Macaristan / İsviçre / Long Beach VA | 294 / 123 / 200 | 106 / 115 / 149 |

Örneklem büyüklüğü veriyle sabittir (hesaplanmadı). Geliştirme kümesinde ~111 olay ve one-hot
sonrası ~18 parametre ≈ 6 olay/parametre: aşırı uyum riski yüksektir; bu nedenle cezalı modeller
ve iç içe CV kullanıldı ve küçük ızgaralar seçildi.

| Merkez | n | Prevalans | Erkek | Yaş medyanı | cp = 4 (asemptomatik) | `thalach` medyanı | `oldpeak` medyanı |
|---|---|---|---|---|---|---|---|
| Cleveland | 303 | %45,9 | %68,0 | 56 | %47,5 | 153 | 0,8 |
| Macaristan | 294 | %36,1 | %72,4 | 49 | %41,8 | 140 | 0,0 |
| İsviçre | 123 | %93,5 | %91,9 | 56 | %79,7 | 121 | 0,3 |
| Long Beach VA | 200 | %74,5 | %97,0 | 60 | %65,5 | 120 | 1,5 |

Merkezler vaka karışımı, prevalans ve cinsiyet bileşimi bakımından çok farklıdır (TRIPOD+AI 16, 20c).

## 4. Yöntem (TRIPOD+AI 11–15)

- **Önişleme** scikit-learn `Pipeline` içinde, her eğitim katında yeniden fit: sayısal → medyan
  atama + eksiklik göstergesi + standartlaştırma; ikili → en sık değer; `cp`, `restecg`, `slope`,
  `thal` → en sık değer + one-hot. Sızıntısızlık testle doğrulandı.
- **Doğrulama:** %20 tabakalı kilitli test; geliştirmede 5 kat × 10 tekrar dış döngü, iç döngüde
  5 kat `GridSearchCV` (log-loss). Modeller aynı dış katları paylaşır; karşılaştırmalar
  Nadeau–Bengio düzeltmeli t testiyle yapıldı.
- **Modeller:** referans yaş+cinsiyet (cezasız LR); **L2 LR (birincil)**; Elastic-Net LR; Random
  Forest; HistGradientBoosting; kübik B-spline + L2 LR.
- **Ölçütler:** ROC AUC, PR AUC, Brier, log-loss, kalibrasyon eğimi ve kalibrasyon-genelde (CITL);
  karar eğrisi (net fayda); eşik metrikleri (eşikler yalnızca eğitim katında seçildi).
- **AS2:** cezasız lojistik regresyon, Wald %95 GA; ek değişkenler için olabilirlik oranı testi.
- **Dış değerlendirme:** Cleveland modelinin doğrudan uygulanması; merkez içi CV ile kesişim ve
  lojistik yeniden kalibrasyon; merkez-dışı-bırak (göstergesiz atama).
- Sınıf dengesizliği yöntemi kullanılmadı (%46 olay). Model çıktısı olasılıktır.
- **Çoklu karşılaştırma:** p-değerleri nominal ve aile içi Holm düzeltmeli olarak raporlandı
  (Aşama 2: 18 model karşılaştırması tek aile; Aşama 3: 4 spline karşılaştırması tek aile). Karar
  eğrisi eşikleri arasında düzeltme yapılmadı.
- **Kilitli testin diğer kullanımları:** öngörü performansı tahmini olmayan analizlerde (AS2 odds
  oranları, transfer/LOSO modellerinin eğitimi, spline biçim grafiği) bütün 303 kişi kullanıldı.
  Aşama 1 EDA'sı da 303 kişide yapıldı; `slope` kodlama kararı bu EDA'dan etkilendi.
- **Protokolden sapmalar:** `docs/research_plan.md` Aşama 1'de, modellemeden önce yazıldı. Aşama 2
  bu plana uyar. Aşama 3 analizleri (karar eğrisi, eşik metrikleri, alt grup farkları, yeniden
  kalibrasyon, LOSO, spline) Aşama 2 sonuçları görüldükten **sonra** eklendi; keşifsel olarak
  okunmalıdır.

## 5. Bulgular — iç performans (TRIPOD+AI 22–23a)

| Model | Ön-anjiyo CV AUC | Tam CV AUC | Not |
|---|---|---|---|
| Referans yaş+cinsiyet | 0,716 | 0,716 | |
| **L2 lojistik** | **0,854 ± 0,056** | **0,900 ± 0,039** | kat-dışı eğim 1,04 / 1,08 |
| Elastic-Net | 0,854 | 0,898 | L2 ile fark ≈ 0 |
| Random Forest | 0,833 | 0,892 | eğim 1,3–1,6 (aşırı temkinli) |
| Gradyan artırma | 0,833 | 0,875 | tam sette L2'den düşük (nominal p = 0,046; Holm p = 0,27) |
| Spline + L2 | 0,828 | 0,887 | ön-anjiyo'da L2'den düşük (nominal p = 0,011; Holm p = 0,043) |

- **Kilitli test (n = 61):** L2 AUC 0,950 [0,887, 0,994] (ön-anjiyo), 0,948 [0,881, 0,992] (tam).
  CV tahmininden yüksek; küçük ve rastlantısal olarak "kolay" bir test kümesiyle uyumlu. Birincil
  tahmin CV'dir.
- **AS4:** `ca`/`thal` eklenmesi CV AUC'yi +0,045 [0,012, 0,079] artırdı (nominal p = 0,009;
  Holm p = 0,080; yön dört modelde de aynı); net fayda farkının GA'sı yalnızca pt ≥ 0,4'te sıfırın
  üstünde. Bu testler anjiyografiye yakın olduğundan "tam" model tarama senaryosu değildir.
- **Karar eğrisi (varsayımsal sevk kararı; klinik öneri değildir):** net fayda
  NB = TP/n − FP/n · pt/(1 − pt), kat-dışı tahminlerle; karşılaştırma stratejileri "herkesi sevk et"
  ve "kimseyi sevk etme". pt ≈ 0,1'de model "herkesi sevk et"ten ayırt edilemez; pt = 0,2–0,5
  aralığında L2 − herkesi sevk et farkı +0,04 ile +0,31 arasında. GA'lar sabit tahminler üzerinde
  bootstrap ile elde edildi (model yeniden eğitilmedi), bu yüzden olduğundan dar olabilir ve
  eşikler arasında çoklu karşılaştırma düzeltmesi yoktur. Bu hastalar zaten anjiyografi olmuştur;
  "sevk etmeme" kararının gerçek sonuçları bu veride gözlenmez.
- **Eşikler:** duyarlılık ≥ 0,90 hedefiyle (eşik ≈ 0,24) test katlarında duyarlılık 0,91,
  özgüllük 0,56 (ön-anjiyo); Youden eşiğiyle (≈ 0,48) 0,71 / 0,79.
- **Alt gruplar:** AUC kadınlarda 0,86, erkeklerde 0,83; doğrudan fark +0,035 [−0,095, 0,145].
  GA'ların örtüşmesi eşit performansın kanıtı değildir; bu GA, anlamlı bir farkı da eşitliği de
  dışlamaya yetmez (Aşama 3 raporu §3). Kadınlarda öngörülen risk
  gözlenenden yüksek (gözlenen %23 vs öngörülen %29; CITL −0,43), ancak kadın alt grubunda yalnızca
  77 kişi ve 18 olay vardır; bu tahmin çok belirsizdir ve ne bir farkı ne de farkın yokluğunu
  güvenle gösterir.
- **Model belirtimi (22):** standartlaştırılmış katsayılar
  `reports/tables/phase2/final_logreg_l2_coefficients.csv`. Bilinçli olarak bireysel risk
  hesaplayıcısı veya formül arayüzü sunulmadı.

**AS2 — çok değişkenli ilişkiler** (n = 303; ilişki, nedensellik değil): erkek cinsiyet OR 5,92
[2,75, 12,75]; asemptomatik göğüs ağrısı (tipik anjinaya göre) 8,83 [2,73, 28,59]; `oldpeak`
(1 mm) 1,88 [1,29, 2,73]; egzersiz anjinası 2,16 [1,03, 4,49]; düz ST eğimi 2,22 [1,02, 4,82];
yaş (10 yıl) 1,46 [0,99, 2,17]; `thalach` (10 atım/dk) 0,87 [0,73, 1,05]. `trestbps`, `chol`,
`fbs` eklenmesi: LRT p = 0,081.

## 6. Bulgular — merkezler arası performans ve güncelleme (TRIPOD+AI 12d, 23b, 24)

| Merkez | AUC (Cleveland modeli) | Gözlenen / öngörülen | Gereken güncelleme |
|---|---|---|---|
| Macaristan | 0,878 [0,832, 0,917] | %36 / %42 | kesişim (Brier 0,133 → 0,126) |
| İsviçre | 0,758 [0,612, 0,895] | %94 / %69 | kesişim + eğim (eğim 0,59 → 0,81) |
| Long Beach VA | 0,737 [0,656, 0,812] | %75 / %70 | kesişim + eğim (eğim 0,57 → 0,93) |

- Yeniden kalibrasyon kalibrasyonu düzeltir ama ayrıştırmayı iyileştirmez.
- Merkez-dışı-bırak: üç merkezle eğitim, yalnız Cleveland'la eğitime göre ayrıştırmayı artırmadı
  (dışarıda bırakılan merkezde AUC 0,73–0,88). Heterojenlik veri havuzlamayla giderilemiyor.
- Bu dış analizler ağır eksik veriyle (İsviçre `chol` %100; VA egzersiz değişkenleri ~%27) ve
  farklı vaka karışımıyla sınırlıdır; keşifsel niteliktedir.

## 7. Yorum (TRIPOD+AI 25)

1. Anjiyografi öncesi bilgilerle yapılan öngörüde en çok katkıyı göğüs ağrısı tipi, cinsiyet ve
   egzersiz testi bulguları (`oldpeak`, `exang`, `slope`, `thalach`) sağlar; kolesterol, dinlenme kan
   basıncı ve açlık kan şekerinin bu sevk edilmiş popülasyonda ek katkısı küçüktür. Bu, sevk
   sürecinde risk faktörlerine göre zaten seçilmiş bir popülasyonla tutarlıdır ve klasik risk
   faktörlerinin önemsiz olduğu anlamına gelmez.
2. "Asemptomatik" göğüs ağrısının en güçlü öngörücü olması sezgiye aykırıdır; anjiyografiye başka
   gerekçelerle (ör. pozitif egzersiz testi) sevk edilmiş hastaların seçilim etkisini yansıtıyor
   olabilir.
3. n ≈ 300'lük bir veri setinde ağaç modelleri, Elastic-Net ve spline genişletmesinin L2 lojistik
   regresyondan daha iyi olduğuna dair kanıt bulunmadı; L2 iyi kalibre edildi (Elastic-Net ve
   gradyan artırmanın kalibrasyonu benzer, RF'ninki daha zayıftı). Bu, küçük tablo verisinde
   karmaşık modellerin çoğu zaman avantaj sağlamadığı gözlemiyle uyumludur; eşdeğerlik testi yapılmadı.
4. Detrano ve ark. (1989) ile nitel olarak uyumlu biçimde, Cleveland'da geliştirilen model
   Macaristan'da fazla tahmin etti; ayrıca İsviçre ve VA'da hem prevalans hem ayrıştırma bakımından
   belirgin bozulma görüldü.
5. Adalet: kadınlarda gözlenen fazla tahmin, kadınların küçük ve düşük prevalanslı bir alt grup
   olmasıyla ve L2 cezasının cinsiyet katsayısını küçültmesiyle ilişkili olabilir. Yalnızca 18 olay
   olduğundan bulgu belirsizdir; doğrulanırsa böyle bir model kadınlarda gereksiz sevke yol
   açabilirdi. Veri yalnızca yaş ve cinsiyet içerdiğinden diğer sosyodemografik gruplar (etnik köken,
   sosyoekonomik durum) incelenemedi.

## 8. Sınırlılıklar (TRIPOD+AI 26, 27a)

- **Temsil:** sevk edilmiş, tek merkezli, %68 erkek, 1980'ler; günümüz tanı yollarını (BT
  anjiyografi, yüksek duyarlıklı troponin, fonksiyonel görüntüleme) ve risk profillerini yansıtmaz.
- **Örneklem büyüklüğü ve aşırı uyum:** ön-anjiyo setinde ~6, tam sette ~5 olay/parametre;
  kilitli test (61 kişi) güçsüz; kadın alt grubunda 18 olay.
- **Çoklu analiz:** çok sayıda model, özellik seti, eşik ve alt grup karşılaştırıldı; Holm düzeltmesi
  aile içinde uygulandı, aileler arası düzeltme yapılmadı. Aşama 3 analizleri protokol sonrası
  eklendiğinden keşifseldir.
- **Veri tekrarları:** Macaristan ve Long Beach VA'da birer çift birebir aynı kayıt vardır (merkezler
  arasında ortak kayıt yok); merkez içi yeniden kalibrasyon CV'sinde etkileri ihmal edilebilir.
- **Sonuç tanımı:** > %50 daralma eşiği bir tanı uzlaşısıdır; `num` 2–4 belgelenmemiştir;
  değerlendirici ve körleme bilgisi yok (doğrulama yanlılığı olasılığı).
- **Öngörücüler:** birimler/ölçüm koşulları kısmen belirsiz; `ca` ve `thal` kullanım zamanı
  bakımından sorunlu; ilaç, sigara, diyabet, etnik köken gibi değişkenler yok.
- **Eksik veri:** Cleveland'da önemsiz; dış merkezlerde ağır ve büyük olasılıkla rastgele değil.
  Uygulamada eksik girdiler (ör. egzersiz testi yapılamaması) modeli doğrudan geçersiz kılar;
  medyan ataması bu durumda güvenilir değildir.
- **Nedensellik:** bütün odds oranları ve önem ölçüleri ilişkiseldir; ölçülmemiş karıştırıcılar
  ve seçilim yanlılığı mümkündür.
- **Genellenebilirlik:** merkezler arası heterojenlik büyüktür; tek bir modelin taşınabilirliği
  bu veriyle desteklenmez.

## 9. Sonraki adımlar (TRIPOD+AI 27c)

Bu veriyle yapılabilecek ek analizlerin beklenen kazancı sınırlıdır. Anlamlı ilerleme için:
1. Güncel, prospektif, çok merkezli bir veri kaynağı (ör. modern göğüs ağrısı kohortları) ve
   önceden kaydedilmiş bir protokol.
2. Klinik paydaşlarla gerçek karar eşiklerinin belirlenmesi ve karar eğrisinin bu eşiklerde
   yeniden değerlendirilmesi.
3. Kadınlarda kalibrasyonun daha büyük örneklemde incelenmesi; gerekiyorsa gruba özgü güncelleme.
4. Merkez heterojenliği için çok düzeyli (karma etkili) modeller ve TRIPOD-Cluster uyumlu raporlama.
5. PROBAST(+AI) ile yanlılık riski değerlendirmesi.

## 10. Beyanlar (TRIPOD+AI 17–19)

- Etik: kamuya açık, kimliksizleştirilmiş ikincil veri; yeni etik kurul onayı alınmadı.
- Finansman: yok. Çıkar çatışması: yok.
- Protokol: `docs/research_plan.md` (modellemeden önce yazıldı; Aşama 3 analizleri protokol
  dışıdır, bkz. §4); kayıt yapılmadı.
- Veri: UCI, DOI 10.24432/C52P4X (CC BY 4.0). Ham veri depoya eklenmez; `scripts/run_phase1.py`
  indirir ve SHA-256 ile doğrular. Kod: `src/`, `scripts/`, `tests/` (MIT); bu rapor yazıldığında
  herkese açık bir depoda **henüz yayımlanmamıştı**. Atıf: `CITATION.cff` (DOI atanmadı).
- Hasta/halk katılımı: yok.
- Atıf isteği: Andras Janosi, M.D.; William Steinbrunn, M.D.; Matthias Pfisterer, M.D.;
  Robert Detrano, M.D., Ph.D.

## Ek: Yeniden üretim

```bash
python scripts/run_phase1.py   # veri indirme, doğrulama, EDA
python scripts/run_phase2.py   # iç içe CV, kilitli test, OR, transfer (~10 dk)
python scripts/run_phase3.py   # karar eğrisi, eşikler, yeniden kalibrasyon, LOSO, spline (~10 dk)
python -m pytest -q            # 58 test
python scripts/audit_release.py  # tutarlılık / gizlilik / yapı denetimi
```

Aşama raporları: `reports/phase1_report.md`, `reports/phase2_report.md`, `reports/phase3_report.md`.
