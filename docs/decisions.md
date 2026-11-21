# Veri ve Hedef Değişken Kararları (Aşama 1)

## K1 — Analiz dosyası: `processed.cleveland.data`

- Arşivdeki `WARNING` dosyası ham `cleveland.data` dosyasının bozulduğunu, `processed.cleveland.data`
  dosyasının ise 14 öznitelik için kullanılabilir olduğunu belirtir. Bu nedenle yalnızca işlenmiş
  dosya kullanılır.
- Bu dosyada hasta kimliği, tarih ve diğer 62 ham öznitelik yoktur.

## K2 — Hedef değişken `num` (0–4) ve ikili dönüşüm

**Belgede yazan** (`heart-disease.names`):
- Öznitelik 58 `num`: "diagnosis of heart disease (angiographic disease status)";
  değer 0 = herhangi bir ana damarda **< %50 çap daralması**, değer 1 = **> %50 çap daralması**.
- Bölüm 4: alan "0 (no presence) ile 4 arasında tamsayıdır"; Cleveland deneyleri
  **var (1, 2, 3, 4)** ile **yok (0)** ayrımına odaklanmıştır.

**Belgede yazmayan**: 2, 3 ve 4 değerlerinin ne anlama geldiği. Yaygın yorum "ciddiyet" ya da
"daralmalı damar sayısı" olsa da UCI belgeleri bunu tanımlamaz; bu projede **bu yorum varsayılmaz**.

**Karar**: `disease = 1 if num ≥ 1 else 0`.
- Gerekçe: (i) belgedeki tek açık tanım 0 ile ">%50 daralma" ayrımıdır; (ii) önceki literatürle
  karşılaştırılabilirlik; (iii) 4. sınıfta yalnızca 13 gözlem vardır, 5 sınıflı model için yetersizdir.
- Sonuç: 164 (54,1 %) yok / 139 (45,9 %) var. Sınıflar yaklaşık dengelidir; yeniden örnekleme gerekmez.
- Ham `num` sütunu veride korunur; çok sınıflı / sıralı analiz yapılmaz, yalnızca betimsel tutulur.

**Yorum sınırı**: `disease`, kayıtlı anjiyografi sonucudur. Gelecek olay riski, mortalite
veya genel popülasyonda hastalık olasılığı değildir.

## K3 — Eksik değerler

- Dosyada `?` ile kodlanmış 6 eksik hücre vardır: `ca` 4, `thal` 2 (6 farklı satır; satır başına
  en çok bir eksik). UCI web sayfasındaki değişken tablosu "missing values: no" gösterir; bu, dosya
  ile uyuşmaz ve not edilmiştir.
- Aşama 1'de **hiçbir değer doldurulmaz veya silinmez**. Tek değişkenli testler, değişken bazında
  tam vakalarla yapılmıştır. Aşama 2 kararı: [research_plan.md](research_plan.md) §4.

## K4 — Değişken türleri

- `cp`, `restecg`, `thal`: nominal (sayı kodları sıra bildirmez; `thal` kodları 3/6/7'dir).
- `slope`, `ca`: sıralı olarak sınıflandırıldı. Not: `slope` için hastalık oranı monoton değildir
  (düz %65 > aşağı eğimli %57), bu yüzden Aşama 2'de nominal (one-hot) kodlama da denenmelidir.
- `oldpeak` ondalıklıdır (UCI web tablosundaki "Integer" etiketi hatalıdır).

## K5 — Aykırı değerler

Klinik olarak mümkün aralık dışında değer bulunmadı. İncelenmesi önerilen uç değerler
(silinmedi): `chol` = 564 mg/dl (1 kayıt), `oldpeak` = 6,2; `thalach` = 71. Yaşa göre tahmini
maksimum kalp hızını (220 − yaş) 20'den fazla aşan 4 kayıt yalnızca bilgi amaçlı işaretlendi.
