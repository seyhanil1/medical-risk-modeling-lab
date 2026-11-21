# Aşama 3 Raporu — Klinik Fayda, Eşikler, Yeniden Kalibrasyon, Heterojenlik, Doğrusal Olmama

Tarih: 2026-11-18 · Çalıştırma: `python scripts/run_phase3.py` (Aşama 2'nin kilitli test ayrımını
yeniden kullanır) · Tablolar: `reports/tables/phase3/` · Log: `reports/phase3_run.log`.

> Araştırma/eğitim amaçlıdır. Eşikler ve net fayda değerleri **varsayımsal bir sevk kararı**
> üzerinden hesaplanmıştır; klinik eşik önerisi değildir.

> **Aşama 4 düzeltme notu (2026-11-18).** (1) Bu aşamadaki analizler `docs/research_plan.md`'de
> önceden belirtilmemiştir; Aşama 2 sonuçlarından sonra eklendiler ve keşifseldir. (2) Spline
> karşılaştırmalarına Holm düzeltmesi eklendi (§6). (3) Alt gruplar için GA örtüşmesi yerine doğrudan
> fark GA'ları ve CITL GA'ları eklendi (§3). (4) Karar eğrisi GA'larının yöntemi ve sınırlılığı
> açıklandı (§1). (5) Yeniden kalibrasyon tablosundaki AUC değişimlerinin bir ortalama artefaktı
> olduğu belirtildi (§4).

## 1. Karar eğrisi analizi (AS: model karar açısından fayda sağlar mı?)

Yöntem: Vickers & Elkin (2006) net faydası, NB(pt) = TP/n − FP/n · pt/(1 − pt); karşılaştırma
stratejileri "herkesi sevk et" (NB = prevalans − (1 − prevalans) · pt/(1 − pt)) ve "kimseyi sevk
etme" (NB = 0). Tahminler geliştirme kümesinin kat-dışı olasılıklarıdır (n = 242; her kişi için
10 tekrarın ortalaması, yani hiçbir tahmin o kişiyi görmüş bir modelden gelmez). Varsayımsal karar:
"invazif anjiyografiye sevk et / etme". pt/(1 − pt), bir gereksiz sevkin zararının bir kaçırılan
hastalığın zararına oranını ifade eder. **Önemli:** bu hastaların hepsi zaten anjiyografi olmuştur;
"sevk etmeme"nin gerçek sonuçları gözlenmez ve eşik aralığı klinik paydaşlarla belirlenmemiştir.

| pt | Herkesi sevk | Referans | L2 ön-anjiyo | L2 tam |
|---|---|---|---|---|
| 0,10 | 0,399 | 0,403 | 0,407 | 0,408 |
| 0,20 | 0,323 | 0,349 | 0,364 | 0,375 |
| 0,30 | 0,227 | 0,239 | 0,302 | 0,331 |
| 0,40 | 0,098 | 0,163 | 0,267 | 0,317 |
| 0,50 | −0,083 | 0,120 | 0,231 | 0,298 |

(Tam değerler `decision_curve.csv`.) Bootstrap %95 GA'lı farklar (`net_benefit_differences.csv`;
1000 basit bootstrap örneği, kat-dışı tahminler **sabit** tutularak — model yeniden eğitilmediği için
GA'lar model kurma belirsizliğini içermez ve olduğundan dar olabilir; beş eşik için çoklu
karşılaştırma düzeltmesi yapılmadı):
- **L2 ön-anjiyo − herkesi sevk et:** pt = 0,10'da +0,008 [−0,002, 0,016] (fark yok);
  pt = 0,20'de +0,040 [0,016, 0,062]; 0,30'da +0,075 [0,029, 0,116]; 0,50'de +0,314 [0,223, 0,397].
- **L2 tam − L2 ön-anjiyo:** pt ≤ 0,30'da GA sıfırı kapsar; pt = 0,40'ta +0,050 [0,008, 0,088].

Yorum: Çok düşük eşiklerde (kaçırılan hastalık çok pahalı sayıldığında) model "herkesi sevk et"
stratejisinden ayırt edilemez; pt ≈ 0,2–0,5 aralığında bu veride ve bu varsayımsal çerçevede daha
yüksek net fayda gösterir. `ca`/`thal`'in ek faydasının GA'sı yalnızca pt ≥ 0,4'te sıfırın
üstündedir. Bu bir **yöntem gösterimidir**, sevk kararı için bir öneri değildir; sonuçlar %46'lık
sevk-popülasyonu prevalansına özgüdür.

## 2. Eşik-bağımlı metrikler (eşik yalnızca eğitim katında seçildi)

Her dış katta eşik, eğitim katının kendi iç kat-dışı tahminlerinden seçildi; test katı eşik
seçimine hiç katılmadı. 50 katın ortalaması (± SD):

| Set | Kural | Eşik | Duyarlılık | Özgüllük | PPV | NPV |
|---|---|---|---|---|---|---|
| Ön-anjiyo | Duyarlılık ≥ 0,90 | 0,24 | 0,91 ± 0,08 | 0,56 ± 0,10 | 0,64 | 0,88 |
| Ön-anjiyo | Youden | 0,48 | 0,71 ± 0,14 | 0,79 ± 0,10 | 0,75 | 0,78 |
| Tam | Duyarlılık ≥ 0,90 | 0,26 | 0,90 ± 0,08 | 0,64 ± 0,09 | 0,68 | 0,89 |
| Tam | Youden | 0,51 | 0,76 ± 0,09 | 0,89 ± 0,07 | 0,86 | 0,81 |

Eğitimde hedeflenen %90 duyarlılık test katlarında ortalama korunuyor ama katlar arası SD ~0,08:
küçük örneklemde bir eşiğin davranışı belirsizdir. PPV/NPV prevalansa bağlıdır, aktarılamaz.

## 3. Alt grup performansı (TRIPOD+AI madde 14, 23a)

L2, kat-dışı tahminler (geliştirme kümesi):

| Set | Grup | n (olay) | AUC [%95 GA] | Gözlenen | Ort. öngörü | CITL |
|---|---|---|---|---|---|---|
| Ön-anjiyo | Kadın | 77 (18) | 0,861 [0,756, 0,946] | %23,4 | %29,3 | −0,43 |
| Ön-anjiyo | Erkek | 165 (93) | 0,826 [0,763, 0,886] | %56,4 | %53,4 | +0,18 |
| Ön-anjiyo | Yaş < 55 | 115 (37) | 0,869 [0,794, 0,932] | %32,2 | %34,8 | −0,18 |
| Ön-anjiyo | Yaş ≥ 55 | 127 (74) | 0,815 [0,730, 0,882] | %58,3 | %55,6 | +0,16 |
| Tam | Kadın | 77 (18) | 0,893 [0,795, 0,968] | %23,4 | %28,0 | −0,42 |
| Tam | Erkek | 165 (93) | 0,877 [0,824, 0,929] | %56,4 | %54,1 | +0,16 |

CITL %95 bootstrap GA'ları (`subgroup_performance.csv`): ön-anjiyo kadın −0,43 [−0,72, −0,12],
erkek +0,18 [−0,04, 0,40]; tam set kadın −0,42 [−0,92, −0,00], erkek +0,16 [−0,12, 0,41].

**Gruplar arası doğrudan farklar** (`subgroup_differences.csv`; her grup kendi içinde tabakalı
bootstrap, 2000 örnek; tahminler sabit):

| Set | Karşılaştırma | AUC farkı [%95 GA] | CITL farkı [%95 GA] |
|---|---|---|---|
| Ön-anjiyo | Kadın − Erkek | +0,035 [−0,095, 0,145] | −0,61 [−0,99, −0,20] |
| Ön-anjiyo | Yaş < 55 − Yaş ≥ 55 | +0,053 [−0,051, 0,158] | −0,34 [−0,71, 0,04] |
| Tam | Kadın − Erkek | +0,015 [−0,084, 0,113] | −0,58 [−1,13, −0,07] |
| Tam | Yaş < 55 − Yaş ≥ 55 | +0,046 [−0,040, 0,131] | −0,33 [−0,78, 0,11] |

- **GA örtüşmesi eşit performansın kanıtı değildir.** Kadın − erkek AUC farkının GA'sı yaklaşık
  ±0,12 genişliğindedir; veri, ayrıştırmanın eşit olduğunu da, farklı olduğunu da göstermeye yetmez.
- Kadın − erkek CITL farkının GA'sı sıfırı dışlar (≈ −0,6). Bu, kadınlarda göreli fazla tahmin
  yönünde bir **sinyaldir**; ancak (i) 18 olaya dayanır, (ii) GA'lar model yeniden eğitimini içermez,
  (iii) analiz önceden planlanmamıştır ve çoklu karşılaştırma düzeltmesi yoktur.
- **Kalibrasyon:** Kadınlarda öngörülen risk gözlenenden yüksek (CITL −0,43). Ancak kadın alt grubunda
  yalnızca 77 kişi ve **18 olay** vardır; GA geniştir ve bootstrap yalnızca örneklem değişkenliğini
  yansıtır. Bu bulgu bir sinyal olarak raporlanır, kanıtlanmış bir yanlılık olarak değil. Olası
  açıklama: L2 cezası cinsiyet katsayısını sıfıra doğru çeker (düşük prevalanslı grupta fazla tahmin).
- Düzeltici bir adalet yöntemi uygulanmadı; bulgu raporlandı. Bu analiz önceden planlanmamıştır.

## 4. Diğer merkezlerde yeniden kalibrasyon (TRIPOD+AI 12f, 24)

Aşama 2'nin Cleveland transfer modeli; her hedef merkezde **merkez içi tekrarlı 5-kat CV** ile
yeniden kalibrasyon parametreleri merkezin bir kısmında öğrenildi, kalan kısımda değerlendirildi.

| Merkez (n, olay) | Yöntem | a | b | Brier | CITL | Kal. eğimi |
|---|---|---|---|---|---|---|
| Macaristan (294, 106) | Özgün | 0 | 1 | 0,133 | −0,49 | 0,91 |
| | Kesişim | −0,50 | 1 | **0,126** | 0,00 | 0,91 |
| | Lojistik | −0,49 | 0,92 | 0,127 | 0,00 | 0,98 |
| İsviçre (123, 115) | Özgün | 0 | 1 | 0,160 | +2,60 | 0,59 |
| | Kesişim | +2,60 | 1 | 0,059 | 0,03 | 0,56 |
| | Lojistik | +2,42 | 0,59 | **0,058** | −0,01 | 0,81 |
| Long Beach VA (200, 149) | Özgün | 0 | 1 | 0,174 | +0,30 | 0,57 |
| | Kesişim | +0,30 | 1 | 0,169 | 0,01 | 0,56 |
| | Lojistik | +0,53 | 0,57 | **0,165** | 0,00 | 0,93 |

- Kesişim güncellemesi her merkezde kalibrasyon-genelde hatasını giderir; Macaristan için yeterlidir.
- İsviçre ve VA'da eğim de düzeltilmelidir (lojistik yeniden kalibrasyon: eğim 0,57 → 0,93 VA).
- Yeniden kalibrasyon (b > 0) her kat içinde sıralamayı değiştirmez; **ayrıştırma (AUC) iyileşmez**
  (İsviçre 0,76, VA 0,74). Tablodaki `oof_auc` sütununda yöntemler arasında görülen küçük AUC
  düşüşleri (ör. İsviçre lojistik 0,71), farklı katlarda farklı parametrelerle yeniden kalibre
  edilmiş tahminlerin tekrarlar üzerinden ortalanmasından kaynaklanan bir artefakttır; gerçek bir
  bozulma değildir. Bu merkezlerde gereken şey yeni öngörücüler veya merkeze özgü yeniden geliştirmedir.
- **Sızıntı kontrolü:** yeniden kalibrasyon parametreleri (a, b) her katta yalnızca o merkezin
  eğitim katında tahmin edildi ve yalnızca dışarıda tutulan katta değerlendirildi. Cleveland modeli
  hedef merkezden hiçbir veri görmedi. Macaristan ve VA'da birer çift birebir aynı kayıt vardır; bir
  çiftin eğitim ve test katlarına bölünmesi iki parametreli yeniden kalibrasyonu pratikte etkilemez.
- İsviçre'deki büyük Brier düşüşü esas olarak %94'lük prevalansın yakalanmasından gelir.

## 5. Merkez-dışı-bırak (LOSO) doğrulama (TRIPOD+AI 12d, 23b)

Özellik seti: `age, sex, cp, trestbps, restecg, thalach, exang, oldpeak` (`chol`, `fbs` İsviçre'de
sistematik eksik olduğu için çıkarıldı). Eksiklik göstergesi kullanılmadı (merkezi kodlamasın diye).
Eksiklik: VA'da `trestbps`, `thalach`, `exang`, `oldpeak` %27–29; diğerlerinde ≤ %5.

| Dışarıda bırakılan | Eğitim | AUC [%95 GA] | Gözlenen | Ort. öngörü | Kal. eğimi |
|---|---|---|---|---|---|
| Cleveland | diğer 3 (n = 617) | 0,867 [0,825, 0,906] | %45,9 | %53,3 | 1,02 |
| Macaristan | diğer 3 (n = 626) | 0,884 [0,841, 0,921] | %36,1 | %49,2 | 1,11 |
| İsviçre | diğer 3 (n = 797) | 0,726 [0,512, 0,909] | %93,5 | %64,8 | 0,72 |
| Long Beach VA | diğer 3 (n = 720) | 0,746 [0,667, 0,821] | %74,5 | %72,5 | 0,59 |
| Macaristan | yalnız Cleveland | 0,873 [0,825, 0,913] | %36,1 | %40,7 | 0,93 |
| İsviçre | yalnız Cleveland | 0,753 [0,601, 0,896] | %93,5 | %67,9 | 0,58 |
| Long Beach VA | yalnız Cleveland | 0,733 [0,656, 0,806] | %74,5 | %69,5 | 0,57 |

- Birden çok merkezle eğitmek, yalnız Cleveland'la eğitmeye göre ayrıştırmayı **iyileştirmedi**.
- Kalibrasyon-genelde hatası merkezler arası prevalans farkını izliyor (Macaristan'da havuzlu
  model daha çok fazla tahmin ediyor, çünkü eğitim havuzu yüksek prevalanslı VA/İsviçre içeriyor).
- Merkez heterojenliği büyük: AUC 0,73–0,88. Tek bir "evrensel" model bu veriyle desteklenmiyor.
- Sızıntı kontrolü: dışarıda bırakılan merkez ne eğitimde ne hiperparametre seçiminde kullanıldı
  (iç CV yalnızca eğitim havuzunda, merkez gruplaması gözetilmeden); merkezler arasında birebir aynı
  kayıt yoktur (`tests/test_data.py`).

## 6. Doğrusal olmayan ilişkiler: spline'lı lojistik model

Kübik B-spline (4 nicelik düğümü, kuyruklarda doğrusal dış değerleme; sklearn'de "restricted
cubic spline" yoktur, bu benzer bir kısıttır) + L2, aynı iç içe CV katlarında:

| Set | Spline − doğrusal AUC [%95 GA]; p; p_Holm | Spline − doğrusal Brier [%95 GA]; p; p_Holm |
|---|---|---|
| Ön-anjiyo | **−0,027 [−0,047, −0,007]**; p = 0,011; p_Holm = 0,043 | +0,013 [0,003, 0,022]; p = 0,012; p_Holm = 0,043 |
| Tam | −0,013 [−0,033, 0,008]; p = 0,218; p_Holm = 0,218 | +0,012 [0,001, 0,023]; p = 0,028; p_Holm = 0,056 |

**p-değerinin hesaplanması:** aynı 50 dış katta (5 kat × 10 tekrar) spline ve doğrusal modelin
kat-içi AUC (veya Brier) farkları alındı; Nadeau & Bengio (2003) düzeltmeli tekrarlı-örnekleme t
testi uygulandı: t = d̄ / √((1/J + n_test/n_train) · s²), J = 50, n_test/n_train ≈ 48/194, sd = 49.
Bu düzeltme katların bağımlılığını yaklaşık olarak hesaba katar; kesin bir test değildir.
**Çoklu analiz bağlamı:** bu dört karşılaştırma tek aile kabul edilip Holm ile düzeltildi; Aşama 2'nin
18 karşılaştırmasıyla birlikte düzeltme yapılmadı. Spline analizi önceden planlanmamıştı.

- Spline modelinin doğrusal modelden **daha iyi olduğuna dair kanıt yok**; ön-anjiyo setinde AUC ve
  Brier bakımından daha düşük performans yönünde bir sinyal var (Holm p = 0,043), tam sette AUC
  farkı anlamlı değil. Olası neden: n = 242'de fazladan esneklik varyans ekliyor.
- İlişki biçimleri (`p3_04_spline_shapes.png`): `oldpeak` ve `thalach` için spline eğrisi doğrusala
  yakın ve doğrusal çizgi bootstrap bandı içinde. `age` ve `chol` için dalgalı biçimler var ama
  bantlar çok geniş; doğrusal olmama için güvenilir kanıt yok.
- Karar: **Doğrusal L2 lojistik regresyon birincil model olarak kalır.**
- Kilitli test (bilgi amaçlı): spline ön-anjiyo AUC 0,967 [0,916, 0,998] — Aşama 2'de belirtilen
  "kolay test kümesi" etkisi; karar CV'ye dayanır.

## 7. Test sonuçları

`python -m pytest -q` → **45 passed** (Aşama 1: 21, Aşama 2: 12, Aşama 3: 12). Aşama 4 denetimiyle
toplam 49 teste çıktı (`reports/release_readiness.md`). Yeni testler: net
fayda bilinen değer, herkesi-sevk ve mükemmel model özdeşlikleri; eşik kuralları; sınıflandırma
metrikleri; yeniden kalibrasyonun bilinen kaymayı/eğimi geri bulması ve CV'de Brier'i düzeltmesi;
LOSO'nun her merkezi bir kez dışarıda bırakması ve eksiklik göstergesi içermemesi; spline baz
sayısı ve merkezleme; alt grup tablosu.

## 8. Grafikler

`p3_01_decision_curve.png`, `p3_02_recalibration.png`, `p3_03_loso.png`,
`p3_04_spline_shapes.png`, `p3_05_subgroups.png`.
