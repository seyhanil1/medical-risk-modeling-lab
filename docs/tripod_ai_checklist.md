# TRIPOD+AI Kontrol Listesi — Medical Risk Modeling Lab

Kaynak: Collins GS, Moons KGM, Dhiman P, ve ark. *TRIPOD+AI statement: updated guidance for reporting
clinical prediction models that use regression or machine learning methods.* BMJ 2024;385:e078378
(CC BY 4.0), Tablo 2. Madde metinleri resmî çeviri değil, Türkçe özetlerdir. D = geliştirme,
E = değerlendirme; çalışma ikisini de içerdiğinden 52 alt maddenin hepsi geçerlidir.

Kısaltmalar: **FR** = `reports/final_report.md` · **P1/P2/P3** = aşama raporları
(`reports/phase*_report.md`) · **DEC** = `docs/decisions.md` · **DD** = `docs/data_dictionary.md`.

Durum: ✅ raporda karşılandı · ⚠️ kısmen karşılandı (eksik olan "Not" sütununda) · ➖ uygulanamaz
(gerekçe "Not" sütununda). Aşama 4 denetiminde (2026-11-18) her satır gerçek bölüme göre yeniden
kontrol edildi; veri kaynağının belgelemediği bilgiler ✅ olarak işaretlenmedi.

| # | Konu (D/E) | Madde özeti | Durum | Nerede | Not |
|---|---|---|---|---|---|
| 1 | Başlık (D;E) | Geliştirme/değerlendirme, hedef popülasyon ve öngörülen sonuç başlıkta | ✅ | FR başlık | "anjiyografiye sevk edilen hastalar", "anjiyografik KAH tanısı" |
| 2 | Özet (D;E) | TRIPOD+AI for Abstracts (13 madde) | ⚠️ | FR §0 | Yapılandırılmış özet var; 13 maddelik özet listesiyle madde madde karşılaştırılmadı |
| 3a | Arka plan (D;E) | Bağlam (tanısal/prognostik), gerekçe, mevcut modeller | ✅ | FR §1 | Tanısal; Detrano 1989 (CDF, CADENZA) |
| 3b | (D;E) | Hedef popülasyon, bakım yolundaki amaç, kullanıcılar | ✅ | FR §1, uyarı kutusu | Klinik kullanıcı hedeflenmediği açıkça belirtildi |
| 3c | (D;E) | Sosyodemografik gruplar arası bilinen eşitsizlikler | ⚠️ | FR §7(5), §8 | Literatür taraması yapılmadı; veride yalnızca yaş/cinsiyet var |
| 4 | Amaçlar (D;E) | Geliştirme ve/veya doğrulama amaçları | ✅ | FR §1 | AS1–AS5 |
| 5a | Veri (D;E) | Geliştirme/değerlendirme veri kaynakları, gerekçe, temsil | ✅ | FR §2, §3; P1 §1 | Temsil sınırlılığı FR §8 |
| 5b | (D;E) | Katılımcı verisinin tarihleri | ⚠️ | FR §2 | Yalnızca "1980'ler"; kesin başlangıç/bitiş kaynakta yok |
| 6a | Katılımcılar (D;E) | Ortam, merkez sayısı ve yeri | ✅ | FR §2 | 4 merkez; sevk edilmiş hastalar |
| 6b | (D;E) | Uygunluk kriterleri | ⚠️ | FR §1, §2 | Yalnızca "anjiyografiye sevk"; ayrıntılı kriterler kaynakta yok |
| 6c | (D;E) | Alınan tedaviler ve ele alınışı | ⚠️ | FR §2, §8 | İşlenmiş veride tedavi değişkeni yok; yalnızca bu eksiklik beyan edildi |
| 7 | Veri hazırlama (D;E) | Önişleme, kalite kontrol, gruplar arası benzerlik | ⚠️ | FR §2, §4; P1 §2–3; DEC | Kalite kontrolü yapıldı; gruplar arası (cinsiyete göre) ayrı kalite kontrolü yapılmadı |
| 8a | Sonuç (D;E) | Sonuç tanımı, zaman ufku, nasıl/ne zaman, gerekçe, gruplar arası tutarlılık | ⚠️ | FR §2; DEC K2 | Tanım ve gerekçe var; değerlendirme zamanı ve gruplar arası tutarlılık kaynakta yok |
| 8b | (D;E) | Öznel yorumda değerlendirici nitelikleri | ⚠️ | FR §8 | Anjiyografi yorumu öznel; bilgi kaynakta yok, beyan edildi |
| 8c | (D;E) | Sonuç değerlendirmesinde körleme | ⚠️ | FR §2, §8 | Kaynakta yok, beyan edildi |
| 9a | Öngörücüler (D) | Başlangıç öngörücüleri ve ön-seçim | ✅ | FR §2, §4; P2 §1 | 14 öznitelik kaynakça seçilmiş; özellik setleri klinik zamanlamaya göre önceden belirlendi |
| 9b | (D;E) | Öngörücü tanımları, ölçüm zamanı, körleme | ⚠️ | DD; FR §2 | Tanımlar var; ölçüm zamanı/körleme kaynakta yok |
| 9c | (D;E) | Öznel ölçümde değerlendirici nitelikleri | ⚠️ | FR §8 | `cp`, `thal`, `ca`, EKG; bilgi yok |
| 10 | Örneklem büyüklüğü (D;E) | Büyüklüğün gerekçesi ve yeterliliği | ✅ | FR §3, §8 | Sabit veri; olay/parametre oranı tartışıldı, hesap yapılmadı (beyan edildi) |
| 11 | Eksik veri (D;E) | Eksik verinin ele alınışı | ✅ | FR §2, §4; P1 §3; P2 §6 | Atama + gösterge; tam vaka duyarlılığı; LOSO'da göstergesiz |
| 12a | Analiz (D) | Verinin kullanımı, bölme | ✅ | FR §3, §4 | Kilitli test + iç içe CV; kilitli testin diğer kullanımları FR §4 |
| 12b | (D) | Öngörücülerin işlenmesi (biçim, ölçekleme) | ✅ | FR §4; P3 §6 | Doğrusal + spline duyarlılığı |
| 12c | (D) | Model türü, gerekçe, adımlar, hiperparametre, iç doğrulama | ✅ | FR §4; P2 §1 | |
| 12d | (D;E) | Kümeler (merkezler) arası heterojenlik | ✅ | FR §6; P3 §5 | LOSO; çok düzeyli model yok |
| 12e | (D;E) | Ölçütler, grafikler, model karşılaştırma | ✅ | FR §4 | Holm düzeltmesi dahil |
| 12f | (E) | Model güncelleme | ✅ | FR §4, §6; P3 §4 | Kesişim / lojistik yeniden kalibrasyon |
| 12g | (E) | Değerlendirmede tahminlerin nasıl hesaplandığı | ✅ | FR Ek; `scripts/` | Python kodu |
| 13 | Sınıf dengesizliği (D;E) | Kullanıldıysa neden/nasıl | ➖ | FR §4 | Kullanılmadı (%46 olay), beyan edildi |
| 14 | Adalet (D;E) | Adalete yönelik yaklaşımlar | ⚠️ | FR §5, §7(5); P3 §3 | Alt grup performansı ve farkları raporlandı; düzeltici yöntem yok |
| 15 | Model çıktısı (D) | Çıktı türü, eşiklerin belirlenmesi | ✅ | FR §4, §5; P3 §2 | Olasılık; eşikler yalnızca eğitim katında |
| 16 | Eğitim vs değerlendirme (D;E) | Ortam/kriter/sonuç/öngörücü farkları | ✅ | FR §3, §6 | Prevalans, bileşim, eksiklik |
| 17 | Etik onay (D;E) | Etik kurul ve onam | ⚠️ | FR §10 | Yeni onay alınmadı (kamuya açık ikincil veri); özgün çalışmanın etik onayı kaynakta bilinmiyor |
| 18a | Finansman (D;E) | Finansman | ✅ | FR §10 | Yok |
| 18b | Çıkar çatışması (D;E) | Çıkar çatışması | ✅ | FR §10 | Yok |
| 18c | Protokol (D;E) | Protokole erişim | ⚠️ | FR §4, §10; `docs/research_plan.md` | Protokol var; Aşama 3 analizleri protokol dışıdır |
| 18d | Kayıt (D;E) | Kayıt bilgisi | ✅ | FR §10 | Kayıt yapılmadığı beyan edildi |
| 18e | Veri paylaşımı (D;E) | Veri erişilebilirliği | ✅ | FR §2, §10 | UCI DOI, CC BY 4.0 |
| 18f | Kod paylaşımı (D;E) | Analiz kodunun erişilebilirliği | ⚠️ | FR §10 | Kod tam; **henüz herkese açık depoda değil** (yayın sonrası ✅) |
| 19 | Hasta/halk katılımı (D;E) | Katılım | ✅ | FR §10 | Katılım olmadığı beyan edildi |
| 20a | Katılımcı akışı (D;E) | Akış, sonuçlu/sonuçsuz sayılar | ✅ | FR §3 | Tablo; akış diyagramı yok |
| 20b | (D;E) | Kaynak başına özellikler, eksik veri, gruplar arası farklar | ⚠️ | FR §3; P1 §4; `tables/phase3/loso_missing_by_site.csv` | Cinsiyete göre ayrıntılı özellik tablosu yok |
| 20c | (E) | Değerlendirme verisinde öngörücü dağılımlarının geliştirmeyle karşılaştırılması | ⚠️ | FR §3 | Seçili değişkenler; tam dağılım tablosu yok |
| 21 | Model geliştirme (D;E) | Her analizde katılımcı ve olay sayısı | ✅ | FR §3 | |
| 22 | Model belirtimi (D) | Tam model (formül/kod) | ⚠️ | FR §5; `tables/phase2/final_logreg_l2_coefficients.csv`; kod | Katsayılar ve kod var; ölçekleme parametreleri ayrı yayımlanmadı; bilinçli olarak risk hesaplayıcı yok |
| 23a | Performans (D;E) | GA'lı performans, alt gruplar dahil | ✅ | FR §5; P2; P3 §3 | |
| 23b | (D;E) | Kümeler arası heterojenlik sonuçları | ✅ | FR §6; P3 §5 | |
| 24 | Model güncelleme (E) | Güncellenmiş model ve performansı | ✅ | FR §6; P3 §4 | |
| 25 | Yorum (D;E) | Genel yorum, adalet, önceki çalışmalar | ✅ | FR §7 | |
| 26 | Sınırlılıklar (D;E) | Temsil, örneklem, aşırı uyum, eksik veri, genellenebilirlik | ✅ | FR §8 | |
| 27a | Kullanılabilirlik (D) | Kalitesiz/eksik girdinin uygulamada ele alınması | ➖ | FR §8 | Uygulama amaçlanmıyor; eksik girdinin geçersizleştirici etkisi tartışıldı |
| 27b | (D) | Kullanıcı etkileşimi ve uzmanlık | ➖ | FR uyarı kutusu | Uygulama amaçlanmıyor |
| 27c | (D;E) | Gelecek araştırma adımları | ✅ | FR §9 | |

**Özet:** 52 alt madde · ✅ 31 · ⚠️ 18 · ➖ 3. ⚠️ maddelerin çoğu (5b, 6b, 6c, 8a–c, 9b–c, 17),
1980'lerin ikincil veri kaynağında belgelenmemiş bilgilerden kaynaklanır ve bu projede
giderilemez. Projeyle giderilebilecek olanlar: 2 (özet kontrolü), 7 ve 20b (cinsiyete göre tablo),
20c (tam dağılım tablosu), 22 (ölçekleme parametrelerinin yayımı) ve 18f (yayın sonrası).
