# OTIF Analitiği — zamanında teslimat KPI'ınız ne kadar dürüst?

![Python](https://img.shields.io/badge/python-3.10+-blue) ![License](https://img.shields.io/badge/license-MIT-green)

🇬🇧 English version: [README.md](README.md)

> Yönetim sunumundaki teslimat KPI'ı **%98,0** diyor.
> Müşterinin gerçekte yaşadığı şekilde ölçüldüğünde aynı siparişler **%59,1** alıyor.
> Bu proje, aradaki **~39 puanlık farkın** tam olarak nerede saklandığını adım adım gösteriyor — ve kendi sipariş verinizde aynı denetimi yapabilmeniz için bir Streamlit aracıyla geliyor.

Çoğu şirketin hem teslimat hem ölçüm sorunu yoktur — teslimat sorununu gizleyen bir ölçüm sorunu vardır. Bu çalışmayı, "zamanında" rakamlarını sessizce şişiren dört tanım tercihinin etrafında tasarladım: hangi tarihi esas aldığınız, ne kadar tolerans tanıdığınız, eksik sevkiyatların sayılıp sayılmadığı ve iptal edilen siparişlere ne olduğu.

## Metrik merdiveni

Aynı 4.000 sipariş. Sunumdaki tanımdan müşterinin hissettiğine, beş tanım:

![Metrik merdiveni](charts/metric_ladder.svg)

| # | Tanım | Sonuç | Ne değişti |
|---|-------|-------|------------|
| 1 | Söz verilen tarih, +3 gün tolerans | **%98,0** | Rapor edilen KPI |
| 2 | Söz verilen tarih, tolerans yok | **%78,0** | Tolerans penceresi kalktı: −20,0 puan |
| 3 | *İstenen* tarih, tolerans yok | **%64,3** | Satış vaadindeki dolgu ortaya çıktı (söz verilen tarihler, müşterinin istediğinden ortalama +0,7 gün): −13,7 puan |
| 4 | **OTIF** — istenen tarih + eksiksiz sipariş | **%59,1** | Eksik sevkiyatlar sayıldı: −5,2 puan |
| 5 | İptaller dahil OTIF | **%57,4** | İptal edilen siparişler saklanmayı bıraktı: −1,7 puan |

Her basamak teknik bir ayrıntı değil, bir *politika tercihidir*. Sözleşmeniz OTIF diyorsa ve panonuz 1. basamağı gösteriyorsa, o fark eninde sonunda ortaya çıkar — genellikle bir müşteri değerlendirme toplantısında, en kötü anda.

## Aynı verinin gösterdiği diğer şeyler

**İki hikaye, ay ay.** Rapor edilen çizgi ile OTIF çizgisi hiç kesişmiyor — fark mevsimsel değil, yapısal:

![Aylık trend](charts/monthly_trend.svg)

**Taşıyıcı seçimi OTIF'i 15,8 puan oynatıyor.** Bir taşıyıcı tüm ağı aşağı çekiyor — toleranslı metrikte görünmez, OTIF'te apaçık:

![Taşıyıcıya göre OTIF](charts/carrier_otif.svg)

**Ortalama, kuyruğu gizler.** Ortalama gecikme 0,0 gün — kulağa mükemmel geliyor. Ama siparişlerin %4,3'ü 4+ gün gecikiyor ve müşterilerin hatırladığı da onlar:

![Gecikme dağılımı](charts/lateness_distribution.svg)

**Her tolerans günü bedava KPI puanı satın alır.** "Zamanında" tanımlarının yıllar içinde neden hep yukarı süründüğünün eğrisi:

![Tolerans duyarlılığı](charts/tolerance_sensitivity.svg)

## Kendi verinizde çalıştırın

```bash
pip install -r requirements.txt
python generate_data.py     # 4.000 siparişlik veri setini yeniden üretir (seed'li)
python analysis.py          # tüm metrikleri ve grafikleri yeniden hesaplar
streamlit run app.py        # etkileşimli araç
```

Streamlit aracı kendi CSV'nizi kabul eder. Beklenen sütunlar:

| Sütun | Tip | Not |
|-------|-----|-----|
| `order_id` | metin | benzersiz |
| `requested_delivery_date` | tarih | müşterinin istediği |
| `promised_delivery_date` | tarih | teyit edilen |
| `actual_delivery_date` | tarih | iptalse boş |
| `lines_total` | tamsayı | sipariş kalemleri |
| `lines_delivered_complete` | tamsayı | eksiksiz teslim edilen kalemler |
| `status` | metin | `delivered` / `cancelled` |
| `carrier` | metin | opsiyonel — taşıyıcı tablosunu açar |

## Veri hakkında

**Tamamen sentetik.** Hiçbir yerde gerçek şirket verisi kullanılmamıştır. Üreteç (`generate_data.py`, tekrarlanabilirlik için seed'li), kurgusal orta ölçekli bir dağıtıcının bir yıllık sipariş defterini kurar ve gerçek operasyonlarda tekrar tekrar gördüğüm arıza desenlerini enjekte eder: satış vaatlerindeki tarih dolgusu, sistematik olarak zayıf bir taşıyıcı (kurgusal "Carrier B"), ay sonu sevkiyat sıkışıklığı ve tek ürün ailesinde yoğunlaşan eksik sevkiyatlar. Repoyla birlikte 300 satırlık örneklem gelir; tam dosya saniyeler içinde yeniden üretilir.

## Yöntem notları

- **Dürüst çıpa, istenen tarihtir.** Müşteri, sipariş masanızın teyit ettiğine göre değil, kendi istediğine göre plan yapar. Vaadi doldurmak metriği oynatır, deneyimi değil.
- **Eksiksizlik sipariş düzeyinde ölçülür.** 10 kalemin 9'unun gelmesi "%90 zamanında" değildir — müşterinin hattı hâlâ durmaktadır. Kalem bazlı dolum oranı ayrı ve tamamlayıcı bir metriktir.
- **Tolerans penceresi pano varsayılanı değil, sözleşme maddesi olmalıdır.** Kullanmak zorundaysanız, rakamın yanında yayınlayın.
- **İptalleri OTIF'in yanında raporlayın.** Paydadan sessizce kaybolan siparişler metriği pohpohlar.

## Yol haritası

- [ ] Kök neden Pareto'su: kategori / bölge / ay bazında gecikme nedenleri
- [ ] Gecikme maliyeti tahmincisi (ceza maddeleri, ekspres navlun)
- [ ] Aynı metrik merdiveni için Power BI şablonu

## Hakkında

**[Eren Gülmez](https://www.linkedin.com/in/erengulmez)** tarafından tasarlandı ve geliştirildi — endüstri mühendisi, İstanbul. *Ölçüm dürüstlüğü* serimin ilk parçası: metrikler gerçeği anlatmalı, slaytları süslememeli. Önce ölçüm sistemini tasarlarım, sonra modern araçları yöneterek hayata geçiririm; yukarıdaki metrik tanımları ve iş yorumu asıl üründür — kod, taşıyıcıdır.

Açık endüstri mühendisliği araç setinin parçası → **[awesome-industrial-engineering](https://github.com/gulmezeren2-byte/awesome-industrial-engineering)**

## Lisans

[MIT](LICENSE)
