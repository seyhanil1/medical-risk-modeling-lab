# Araştırma Soruları ve Aşama 2 Analiz Planı

## 1. Araştırma soruları

Bütün sorular **ilişkisel/öngörüseldir**; gözlemsel, kesitsel bir veriden nedensel sonuç çıkarılmaz.

- **AS1 (betimsel).** Cleveland örnekleminde hangi klinik ve test değişkenleri kayıtlı anjiyografik
  kalp hastalığı ile tek değişkenli olarak en güçlü ilişkiyi gösteriyor? *(Aşama 1'de yanıtlandı.)*
- **AS2 (çok değişkenli ilişki).** Yaş ve cinsiyet ayarlandığında egzersiz testi bulguları
  (`thalach`, `oldpeak`, `exang`, `slope`) ve göğüs ağrısı tipi (`cp`) ile ilişki sürüyor mu?
  (Lojistik regresyon, odds oranı + %95 GA; yorum: ilişki, nedensellik değil.)
- **AS3 (öngörü).** Yalnızca **invazif olmayan / anjiyografi öncesi** bilgilerle (demografi,
  semptom, dinlenme ölçümleri, egzersiz EKG) iyi kalibre edilmiş bir sınıflandırıcı hangi
  ayrıştırma (ROC AUC) ve kalibrasyonu sağlar?
- **AS4 (artımsal değer).** `ca` (floroskopi) ve `thal` (talyum) eklenmesi AS3 modelinin
  performansını ne kadar artırıyor? Bu değişkenler tanı sürecinin ileri aşamasına ait olduğundan
  ayrı raporlanmalıdır (olası hedef sızıntısı / kullanım zamanı uyumsuzluğu).
- **AS5 (dış geçerlilik, keşifsel).** Cleveland'da geliştirilen model Macaristan, İsviçre ve
  Long Beach VA alt kümelerinde nasıl performans gösteriyor? (Bu alt kümelerde `ca`/`thal`
  büyük ölçüde eksik olduğundan yalnızca AS3 modeli için uygundur.)

## 2. Hipotezler (önceden kayıt niteliğinde, keşifsel)

- H1: `thalach` daha düşük, `oldpeak` daha yüksek, `exang = 1` ve `cp = 4` (asemptomatik) olanlarda
  kayıtlı hastalık oranı yaş ve cinsiyet ayarından sonra da daha yüksektir.
- H2: `chol`, `trestbps` ve `fbs`, çok değişkenli modelde anlamlı ek ayrıştırma sağlamaz
  (Aşama 1'de tek değişkenli ilişkileri zayıf/Holm sonrası anlamsız).
- H3: `ca` ve `thal` eklenmesi AUC'yi artırır; ancak bu artış klinik kullanım zamanlaması
  bakımından ayrı yorumlanmalıdır.

## 3. Aşama 2 analiz planı

1. **Veri bölme / doğrulama.** n = 303 için tek bir test ayrımı yüksek varyanslıdır. Birincil
   protokol: **tekrarlı katmanlı 5-kat çapraz doğrulama (10 tekrar)**; hiperparametre seçimi için
   **iç içe (nested) CV**. Ek olarak sabit tohumlu (%20) bir *kilitli* test kümesi yalnızca son
   raporda bir kez kullanılır. `RANDOM_SEED = 42`.
2. **Önişleme (scikit-learn `Pipeline` / `ColumnTransformer` içinde, sızıntısız).**
   Sürekli: standartlaştırma. Nominal (`cp`, `restecg`, `thal`, ayrıca `slope` duyarlılık analizi):
   one-hot. `ca`: sıralı sayısal + one-hot karşılaştırması.
3. **Eksik veri.** Birincil: kat içi en sık değer ile basit atama + eksiklik göstergesi
   (6 hücre, %0,14). Duyarlılık: tam vaka analizi (n = 297). Sonuçlar farklılaşırsa raporlanır.
4. **Modeller (karmaşıklık sırasıyla).** (a) Sadece yaş+cinsiyet referans modeli; (b) L2
   lojistik regresyon; (c) L1/Elastic-Net lojistik regresyon; (d) Random Forest ve
   gradyan artırma (yalnızca karşılaştırma için). n küçük olduğundan basit, yorumlanabilir
   modeller önceliklidir.
5. **Değerlendirme.** Birincil: ROC AUC (CV ortalama ± SD, bootstrap %95 GA). İkincil: Brier
   skoru, kalibrasyon eğrisi / eğim / kesişim, duyarlılık, özgüllük, PR AUC. Eşik seçimi yalnızca
   eğitim katlarında yapılır. Modeller arası karşılaştırma için katlar arası eşleştirilmiş farklar.
6. **Yorumlanabilirlik.** Lojistik katsayılar / odds oranları (%95 GA), permütasyon önemi
   (CV içinde). SHAP vb. gerekirse; nedensel yorum yapılmaz.
7. **Raporlama.** TRIPOD+AI kontrol listesine uygun yapı; sınırlılıklar bölümü zorunlu.
8. **Testler.** Pipeline'ın sızıntısızlığı (atama/ölçekleme yalnızca eğitim katında fit edilir),
   tekrarlanabilirlik (aynı tohum → aynı skorlar), çıktı şekilleri.

## 4. Aşama 2'de yapılmayacaklar

- Bireysel hasta için risk hesaplama arayüzü, deployment, klinik kullanım iddiası.
- Ham `num` (0–4) için çok sınıflı model (belgelenmemiş kodlama, 4. sınıfta n = 13).
