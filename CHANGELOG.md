# Boomusic - Değişiklik Günlüğü

Bu dosya her sürümde neyin değiştiğini anlatır. Kurulumdan sonra bu dosyanın
bir kopyası `~/.local/share/boomusic/CHANGELOG.md` yolunda, yani
`boomusic.log` ile TAM OLARAK AYNI klasörde durur.

---

## v1.7.3 — Playlist context menüsü düzeltmeleri + Just Icon dönüş fix + bağımlılık hardening

### Düzeltilen hatalar
- **"Şu playliste ekle" alt menüsü boş kalıyordu.** Sağ tık menüsündeki
  "Add to playlist" öğesinin alt menüsünde playlist isimleri hiç
  görünmüyordu (panel tamamen boş). Kök neden: `buildContextMenuDOM`
  içinde `onSubmenuCreated` parametre olarak aranıyordu ama JS köprüsü
  bunu item'ın üzerine (`it.onSubmenuCreated`) koyuyordu ve
  `openContextMenu` parametreyi geçirmediği için callback hiç
  tetiklenmiyordu → panel boş, kullanıcı "playlist gözükmüyor" diyordu.
- **Playlist kapak boyutları bozuktu.** Sidebar'daki playlist kapakları
  28×28 olması gerekirken 80px+ görünüyor, playlist isimleri sığmıyordu;
  playlist başlığındaki büyük kapağın placeholder'ı ise sol-üst köşede
  duruyordu. Kök neden: `applyCoverToEl` sidebar cover elementine `.pl-cover`
  class'ı eklemiyordu (28×28 kuralı bu class'a bağlı); `setCoverImg`
  başlık kapağının placeholder'ını `<div class="placeholder">` yerine
  `<span class="center-cover-placeholder">` ile değiştiriyor ama flex-center
  CSS'i sadece eski seçicide vardı.
- **Just Icon'dan GUI'ye dönüş iki tray ikonu bırakıyordu.** Just Icon
  menüsünden "Boomusic'i Göster" tıklanınca yeni GUI başlıyor ama Just
  Icon süreci çalışmaya devam ediyordu → tepside iki Boomusic ikonu.
  Artık Just Icon süreci SIGTERM ile kendini düzgünce kapatır (lock
  dosyası silinir, sadece tek GUI süreci + tek tray ikonu kalır).

### Bağımlılık hardening
- **yt-dlp artık her sistemde çalışır.** Önceden sadece sistem paketi
  olarak kuruluysa çalışıyordu; minimal Fedora/Ubuntu kurulumlarında
  depoda yoksa YouTube özelliği sessizce çalışmıyordu. Artık pip ile
  de kuruluyor ve venv/bin/yt-dlp, ~/.local/bin/yt-dlp olarak
  symlink'leniyor — `shutil.which("yt-dlp")` her zaman bulur.
- **Kullanılmayan `python-xlib` bağımlılığı kaldırıldı.** Pip listesinden
  çıkarıldı (kodda hiçbir import yoktu, sadece gereksiz sürüm çakışması
  riski yaratıyordu).

### Teknik
- `__version__` = "1.7.3"
- Build: `boomusic_1.7.3.tar.gz`

---

## v1.7.2 — Bug fixes & i18n, splash screen, keyboard shortcuts, songs filter

- **i18n (dil desteği) eklendi.** İngilizce (varsayılan) ve Türkçe
  arasında Ayarlar'dan geçiş yapılabilir.
- **Yazı tipi seçimi eklendi.** Ayarlar'dan DM Sans veya Anthropic Serif
  arasında geçiş yapılabilir.
- **Splash / yüklenme ekranı eklendi.** Beyaz flash'ı engellemek için
  açılışta Boomusic logolu mor splash gösterilir.
- **Klavye kısayolları:** Space → oynat/duraklat, K → şimdi çalan paneli,
  ←/→ → önceki/sonraki şarkı.
- **Sadece şarkılar filtresi.** ♪ düğmesi ile sadece ses dosyaları
  (mp3/flac/ogg/wav/m4a/wma/opus/aac) gösterilir.
- **`t is not a function` hatası düzeltildi.** `var t = tracks[i]` hoist
  sorunu giderildi.
- **Config'e font + dil eklendi.** `font_family` ve `language` alanları,
  `set_font()`/`set_language()` API'ları.

---

## v1.7.2 — Şimdi çalan paneli, bildirimler kaldırıldı, track list genişletildi

- **Şimdi Çalan Paneli eklendi** (sağ taraf). Şarkı çalarken sağda fixed
  overlay olarak belirir: 200×200 playlist kapağı, çizgi, şarkı adı,
  yapımcı (boşsa gizlenir), süre. Opaklık 0.5, `pointer-events: none`,
  transparan arka plan — playlistlerin "arkasındaymış" hissi.
- **Ayarlardan açılıp kapatılabiliyor** (Şimdi Çalan Paneli toggle'ı).
  Panel genişliği `min(300px, 24vw)` ile pencere boyutuna uyarlanır.
- **Cover sınıf çakışması düzeltildi.** `.np-cover` bottom bar ile
  çakıştığı için paneldeki cover 44×44 görünüp yanlış yerde çıkıyordu;
  `.np-panel-cover` olarak rename'lendi.
- **Bildirimler kaldırıldı.** `notifier.notify()` çağrıları, bildirim
  toggle'ı UI'dan ve API'dan tamamen temizlendi.
- **Ayarlar butonu sağ üste taşındı** (alt bardan `.search-area`'ya,
  absolute pozisyonla).
- **Track list genişletildi.** Satır padding'i 7→10px, font 13→14px,
  grid sütunları 28→32px, gap 8→12px. Playlist header cover 120→140px,
  başlık 24→28px.
- **Varsayılan bildirim durumu kapalı** (`notifications_enabled: bool = False`).
- **Varsayılan ses %10'da kalıyor** (önceki sürümlerden devam).
- `__version__` = "1.7.2"

---

## v1.7.gd-1 — Bug fixes: ikon, animasyon, cover boyutu, sidebar resize

- **Pencere ikonu düzeltildi.** Artık GTK üzerinden `assets/icon.png` pencere
  ikonu olarak atanıyor (önceden hiç atanmıyordu).
- **Arama animasyonu tekrarı durduruldu.** `renderSearchResults()` her
  600ms'de yeniden çağrıldığı için `stagger` animasyonu sürekli oynuyordu.
  Artık sonuçlar değişmediği sürece DOM yeniden oluşturulmuyor.
- **Playlist cover boyutu düzeltildi.** Cover resmi olan playlistlerde
  dış `<span>`'e `pl-cover` class'ı eklenmediği için 28×28 sınırlaması
  çalışmıyor, resim büyük görünüyordu.
- **Sidebar artık fareyle genişletilebiliyor.** Sağ kenarda 4px'lik
  resize handle eklendi; sürükleyerek 140–400px arasında ayarlanabiliyor.
- Build: `boomusic_1.7.gd-1.tar.gz`

---

## v1.7.gd — Premium/minimalist UI tasarımı (YENİ TASARIM)

- **gui.html baştan yazıldı (sıfırdan yeniden tasarım).** Eski arayüzün
  tamamı atıldı; yerine premium, koyu temalı, glassmorphism efektli,
  gradient geçişli, akıcı animasyonlu yepyeni bir arayüz geldi.
- **Izgara (grid) tabanlı düzen:** Kartlar, listeler ve paneller artık
  esnek grid yapısıyla yerleşiyor; pencere boyutuna duyarlı şekilde
  akıcı olarak yeniden konumlanıyor.
- **CSS değişkenleriyle ölçeklendirme:** `--scale` değişkeni viewport
  boyutuna göre 0.75×–1.8× aralığında dinamik ayarlanıyor; yeniden
  boyutlandırmada `resize` dinleyicisiyle anında güncelleniyor.
- **Sidebar'da "1.7.gd" rozeti** — bu deneysel tasarım sürümünü
  işaretlemek için eklendi.
- Bu sürüm kod mantığına dokunmaz; sadece görsel katman değiştirilmiştir.
- `__version__` = "1.7.gd"
- Build: `boomusic_1.7.gd.tar.gz` (134K)

---

## v1.7.1 — Kod incelemesi düzeltmeleri + duyarlı pencere boyutu

### Ses motoru
- **Hata:** `vlc.Instance()`'e geçirilen `--pulse-audio-name=Boomusic`
  argümanı, VLC 3.0.23'te tanınmıyordu. VLC instance oluşturulamayınca
  `'NoneType' object has no attribute 'media_player_new'` hatası alınıyor
  ve uygulama sessiz modda (ses olmadan) çalışıyordu.
- **Düzeltme:** `--pulse-audio-name` kaldırıldı; bu işlev `PULSE_PROP_application.name`
  ortam değişkeniyle `__main__.py`'de zaten yapılıyordu.
- **Ek koruma:** `vlc.Instance()` `None` döndürürse artık açıkça `RuntimeError`
  fırlatılıp loglanıyor, sessizce geçiştirilmiyor.

### Kritik hata düzeltmeleri
- **İndirme progress modal'ı çalışmıyordu.** `get_active_downloads()` liste
  döndürmesine rağmen JS tarafında `count > 0` ile kontrol ediliyordu;
  JS'de `[...] > 0` her zaman `false` olduğu için modal hiç açılmıyordu.
- **`get_download_progress()` argümansız çağrılıyordu.** JS'den anahtar
  parametresi olmadan çağrı yapılıyordu; Python'da TypeError fırlatıyordu.
  Artık `get_active_downloads()`'den alınan ilk indirmenin anahtarıyla
  düzgün çağrılıyor.
- **XSS açığı kapatıldı.** Kullanıcı/YouTube/yarasa dosyalarından gelen
  şarkı adları, sanatçı, YouTube başlıkları, playlist adları ve
  açıklamaları — dış kaynaklı tüm metin verileri — `innerHTML`'e
  yazılmadan önce HTML-kaçışından geçiriliyor (`escapeHtml()`).
  Etkilenen tüm noktalar: arama sonuçları, ana sayfa kartları, şarkı
  listesi, alt çubuk, ayarlar paneli.

### Thread güvenliği
- **`_download_progress` sözlüğüne senkronizasyon eklendi.** Birden çok
  indirme thread'i aynı sözlüğe yazabiliyordu; artık tüm okuma/yazmalar
  `_download_lock` ile korunuyor. Daha temiz bir arayüz için
  `_update_dl_progress()` yardımcı metodu eklendi.

### Güvenlik
- **`rename_playlist()` path traversal koruması.** Çalma listesi adında
  `..`, `/`, `\\` karakterleri engelleniyor; geçersiz adlar `ValueError`
  fırlatıyor.

### Duyarlı (Responsive) Pencere
- **Pencere boyutu artık ekran çözünürlüğüne göre ayarlanıyor.** Eski sabit
  980×640 px yerine, GTK üzerinden ekran boyutu tespit edilip pencere genişliği
  ekranın %70'i, yüksekliği %78'i olacak şekilde hesaplanıyor (en az 980×640).
  Yüksek DPI/çözünürlüklü ekranlarda pencere aşırı küçük kalmıyor.
- **`--scale` CSS değişkeni dinamik hale geldi.** Pencere boyutuna göre
  (taban: 980×640) otomatik ölçekleniyor (0.75× – 1.8× aralığında).
  Kenar çubuğu genişliği de `--scale` ile orantılı büyüyor.
- Pencere yeniden boyutlandırıldığında (`resize` olayı) `--scale` yeniden
  hesaplanıyor.

### Performans & Mimari
- **`played_at` sıralaması kaldırıldı.** `Track`/`TrackEntry`'de `played_at`
  alanı bulunmuyordu; "Son Çalınanlar" bölümündeki anlamsız sıralama,
  `play_count`'e göre azalan sıralama ile değiştirildi.
- **Ölü kod temizliği:** `Settings.youtube_enabled`, `toggle_youtube()`,
  `_do_toggle_youtube()`, `youtube_enabled()` kaldırıldı (bu ayar hiçbir
  UI öğesinden toggle edilmiyordu; tüm UI `youtube_mix_with_local` kullanıyor).
- **`import re` modül seviyesine taşındı** (`youtube.py`).

### Teknik
- `__version__` = "1.7.1"

---

## v1.7.0 — YouTube Music entegrasyonu (yt-dlp) + Birleşik Arama + MP3 İndirme

**Yeni özellik: YouTube Music entegrasyonu.** yt-dlp kullanarak
YouTube Music'ten şarkı ve podcast aranabilir, doğrudan çalınabilir
ve MP3 olarak indirilebilir.

### Yeni Özellikler
- **Birleşik arama çubuğu**: Sidebar'daki ayrı YouTube arama kutusu
  kaldırıldı; üst center'da yerel kütüphane + YouTube'u birlikte tarayan
  tek bir arama çubuğu eklendi. Sonuçlar "Yerel" ve "YT" etiketleriyle
  aynı listede gösterilir.
- **YouTube Music araması**: `ymsearch` kullanılır (sonuç yoksa `ytsearch`'e
  düşer); sadece müzik içerikleri gelir, videolar/klipler/reklamlar hariç
  tutulur.
- **Süre filtresi**: 30 saniyeden kısa videolar otomatik olarak elenir.
- **Reklamsız**: yt-dlp zaten reklam göstermez.
- **Stream URL cache**: Çalınan şarkılar 30 dakika cache'lenir. Arama
  sonuçlarının ilk 2 videosunun stream URL'i önceden cache'e ısıtılır
  (prewarm).
- **YouTube MP3 indirme**: Herhangi bir YouTube videosu (veya URL'si)
  MP3'e dönüştürülüp doğrudan müzik klasörü altındaki
  "YouTube İndirilenler" klasörüne indirilebilir. İndirme ilerlemesi
  arayüzde yüzde olarak gösterilir. İndirme bitince kütüphane otomatik
  yeniden taranır.
- **YouTube + yerel karışık mod**: Toggle ile açılıp kapatılabilir.
- **Tepsi menüsüne YouTube toggle'ı eklendi**, metin "İnternete Bağlı" /
  "İnternet Kapalı" olarak gösterilir.
- **Çalma listesi yönetimi**: Uygulama içinden yeni çalma listesi
  oluşturma, yeniden adlandırma, açıklama ekleme desteği
  (`create_playlist()`, `rename_playlist()`, `playlist_meta()`).
- **Pano okuma**: URL yapıştırmayı kolaylaştırmak için `wl-paste` /
  `xclip` / `xsel` ile pano okuma desteği eklendi.

### Performans
- **Stats batch save**: `record_play` artık her çağrıda değil, 2 saniye
  debounce ile toplu yazma yapar. Sürekli çalma durumunda disk yazma
  sayısı büyük ölçüde azalır.

### Teknik Detaylar
- `youtube.py` **(yeni dosya, 373 satır)**: Tüm YouTube mantığı
  (arama, stream URL, cache, video bilgisi, MP3 indirme, progress takibi)
- `config.py`: `youtube_enabled`, `youtube_mix_with_local`,
  `youtube_search_limit` ayarları eklendi
- `library.py`: Track'e `source`, `thumbnail_url`, `youtube_video_id`
  alanları; `is_youtube` property; `create_playlist()`, `rename_playlist()`,
  `playlist_meta()`, `set_playlist_meta()` metotları; `PLAYLIST_META_FILENAME`
- `player.py`: `set_current_path()` eklendi (YouTube stream URL'leri için)
- `app.py`: `search_youtube()`, `search_all()`, `play_youtube()`,
  `play_youtube_in_mix()`, `toggle_youtube()`, `toggle_youtube_mix()`,
  `download_youtube()`, `download_youtube_url()`, `get_download_progress()`,
  `get_active_downloads()`, `create_playlist()`, `edit_playlist()` metotları;
  `playback_state()` artık `youtube_enabled`/`youtube_mix_enabled` alanlarını
  içerir
- `gui.py`: JS köprüsüne `search_youtube`, `search_all`, `play_youtube`,
  `play_youtube_in_mix`, `toggle_youtube_mix`, `clear_youtube_search`,
  `download_youtube`, `download_youtube_url`, `get_download_progress`,
  `get_active_downloads`, `read_clipboard`, `create_playlist`,
  `edit_playlist` metotları; `get_state()` YouTube alanları
- `tray.py`: YouTube toggle menü metni "İnternete Bağlı" / "İnternet Kapalı"
  olarak güncellendi
- `stats.py`: Batch save (2s debounce) optimizasyonu
- `shuffle.py`: `add_track()` ile YouTube şarkılarını torbaya ekleme
- `install.sh`: yt-dlp bağımlılık olarak eklendi

### Gereksinimler
- `yt-dlp` kurulu olmalı (install.sh otomatik kurar)
- İnternet bağlantısı gereklidir

---

## v1.6.1 — Renkli ilerleme/ses çubuğu + hover titremesi düzeltmesi

- **İlerleme (seek) ve ses çubuklarının DOLU kısmı artık mor** (dinlenen/
  ayarlanan kısım ile geri kalanı net şekilde ayrılıyor).
- **Ses çubuğu artık sürüklerken CANLI değişiyor** (bırakmayı beklemeden);
  IPC köprüsünü boğmamak için ~80ms'de bir gönderiliyor ama görsel dolgu
  her zaman anlık güncelleniyor. Bırakınca son değer kesin olarak uygulanır.
- **Şarkı listesindeki "git-gel" (hover titremesi) düzeltildi.** Kök
  neden: arayüz her ~600ms'de TÜM şarkı listesini ve çalma listesi
  panelini koşulsuz yeniden oluşturuyordu; imlecin altındaki eleman
  sürekli yok edilip yeniden yaratıldığı için hover efekti titriyordu.
  Artık ilgili veri (hangi şarkı çalıyor, hangi liste seçili, vb.)
  GERÇEKTEN değişmediyse o bölüm hiç dokunulmadan bırakılıyor; sadece
  konum/süre gibi her an değişen küçük şeyler güncelleniyor. Bu, gerçek
  bir tarayıcı DOM'u (jsdom) üzerinde otomatik testlerle doğrulandı:
  aynı state ile ve sadece oynatma konumu ilerlerken şarkı satırlarının
  DOM elemanı aynı kalıyor; sadece çalan şarkı gerçekten değişince
  yeniden oluşturuluyor.

---

## v1.6.0 — KRİTİK: kapanma sorunu + kurulum düzeltmeleri

**Sorun 1 (kritik): Uygulama "Çıkış"tan kapanmıyordu**, `killall python3`
gerekiyordu. Kök neden: v1.4.1'de tray ve pencere aynı GTK döngüsünü
paylaşmaya başladı (bkz. o sürümün notu), ama "Çıkış" hâlâ sadece
`icon.stop()` çağırıyordu -- bu, döngünün asıl sahibi olan pencereyi
KAPATMIYORDU, yani paylaşılan döngü hiç sonlanmıyordu.

**Düzeltme:**
- "Çıkış" artık önce pencereyi GERÇEKTEN kapatıyor (`gui.quit()` ->
  `window.destroy()`), bu da paylaşılan döngünün sona ermesini sağlıyor.
- **Güvenlik ağı eklendi**: "Çıkış"a basıldıktan (ya da bir kapatma
  sinyali alındıktan) 4 saniye sonra, her ihtimale karşı süreç KOŞULSUZ
  sonlandırılıyor. Artık hiçbir durumda elle `kill` yapmak gerekmemeli.
- Ayarlar paneline de bir "Boomusic'ten Çık" düğmesi eklendi (tepsiye
  ek, alternatif bir çıkış yolu).

**Sorun 2 (kritik): Yeniden kurulumda eski sürüm çakışması.**
`install.sh` artık İLK ADIM olarak (paket kurulumundan önce) hâlâ çalışan
bir Boomusic örneği olup olmadığını (kilit dosyasından) kontrol ediyor;
varsa önce düzgünce (SIGTERM, 5sn bekleme), olmuyorsa zorla (SIGKILL)
kapatıp öyle devam ediyor. Böylece eski, takılı kalmış bir sürüm varken
bile güncelleme sorunsuz çalışır.

**Küçük düzeltme:** Alt bardaki "şimdi çalan" ikonu artık çalan şarkının
ait olduğu çalma listesinin kapak resmini gösteriyor (kapak yoksa eski
sabit nota ikonuna düşüyor).

**Not:** Kullanıcıdan gelen diğer istekler (açıklama alanı, center
düzeni, "Boomin's Shuffle" adı + yeni shuffle modları, ses karıştırıcı
ismi/ikonu, kurulum ekranı sadeleştirme, tray↔pencere senkron hızı,
otomatik klasör izleme) sıraya alındı, kritik olanlardan sonra tek tek
işlenecek.

---

## v1.5.0 — Çalma listesi kapak resmi (1/9 adım)

Kullanıcının istek listesindeki 9 maddeden **1. adım**: çalma listesi
kapak resimleri.

- Her çalma listesinin (ve kök/"Genel" listenin) bir kapak resmi olabilir.
- Pencerede, seçili listenin başlığındaki büyük kapağa tıklayınca (üzerine
  gelince görünen kalem ikonuyla) native bir dosya seçici açılıyor;
  seçilen resim otomatik olarak küçültülüp JPEG'e çevrilip kaydediliyor.
- Kenar çubuğunda her listenin yanında küçük bir kapak önizlemesi var.
- **Kapaklar müzik klasörünün İÇİNDE saklanıyor** (her çalma listesi alt
  klasörünün kendi `cover.jpg` dosyası olarak; "Genel" için müzik
  klasörünün kökünde). Ayrı bir veritabanı YOK — bu sayede uygulama
  silinip yeniden kurulsa, hatta klasör başka bir bilgisayara taşınsa
  bile kapaklar şarkılarla birlikte kalır. Bu, kullanıcının 5. isteğindeki
  "veriler müzik klasöründe saklansın, yeniden kurulumda okunabilsin"
  ihtiyacının bir kısmını da baştan karşılıyor.
- `cover.jpg` dosyaları şarkı taramasında (uzantı filtresi sayesinde)
  asla şarkı olarak algılanmıyor.

**Sırada (kullanıcıdan gelen sıraya göre, her adım sonrası geri bildirim
bekleniyor):** 2) ses karıştırıcıda "VLC" yerine Boomusic adı/ikonu,
3) daha gösterişli/az-gürültülü kurulum çıktısı, 4) ilerleme çubuğunda
dinlenen kısmın mor renkte gösterilmesi, 5) playlist'i uygulama içinden
oluşturma + açıklama alanı, 6) şarkı ekleme dahil her şeyin arayüzden
yapılabilmesi, 7) pencere ikonunun düzeltilmesi, 8) tray↔pencere
senkronizasyonunun hızlandırılması, 9) otomatik klasör izleme (elle
"yeniden tara"ya gerek kalmaması).

---

## v1.4.1 — GTK çakışması düzeltmesi + tanılama iyileştirmeleri

**Sorun:** Bazı sistemlerde pencere hiç açılmıyordu; `boomusic.log`
"başlatıldı" yazıp hiçbir hata vermeden sessizce takılıp kalıyordu.

**Kök neden:** Tepsi simgesi (pystray/AppIndicator) ve pencere
(pywebview/GTK) ikisi de GTK tabanlı; ikisini de AYRI thread'lerde kendi
ana döngüleriyle (mainloop) çalıştırmak GTK'nın thread modeliyle güvenli
değil ve kilitlenmeye yol açabiliyordu.

**Düzeltme:**
- Pencere VE tray birlikte kullanılabiliyorsa, tray artık kendi döngüsünü
  BAŞLATMIYOR (`icon.run()` değil); `icon.run_detached()` ile sadece
  KAYDEDİLİYOR. Gerçek, PAYLAŞILAN GTK döngüsünü pencere (`webview.start`)
  başlatıyor ve bu tek döngü hem pencereyi hem tepsiyi birlikte işletiyor.
  (Bu, pystray'in kaynak koduna bakılarak doğrulandı: `run_detached()`
  gerçekten kendi döngüsünü başlatmıyor, sadece kurulum yapıp ortak
  döngünün gelmesini bekliyor.)
- Pencere hiç kullanılamıyorsa (örn. webkit2gtk kurulu değilse), tray
  eskisi gibi kendi (tek başına, güvenli) arka plan thread'inde çalışıyor.
- `boomusic.log`'a HER AŞAMA için ayrı satırlar eklendi: kilit alındı mı,
  App/GUI/Tray oluşturuldu mu, hangi modda (paylaşılan döngü / kendi
  thread'i) başlatıldı, GUI mainloop'u ne zaman girildi/çıktı, vb. Artık
  bir şey takılırsa/çökerse TAM OLARAK hangi adımda olduğu görülebiliyor.

**Diğer:**
- `install.sh` artık gerekli sistem paketlerini (python-gobject, gtk3,
  appindicator, webkit2gtk-4.1, vlc, zenity) SORMADAN direkt kuruyor
  (bunlar olmadan uygulama zaten çalışmıyor, sormanın anlamı yoktu).
- Bu CHANGELOG dosyası eklendi ve kurulumda `boomusic.log` ile aynı
  klasöre kopyalanıyor.

---

## v1.4.0 — Masaüstü penceresi ve VLC ses motoru

- **Yeni masaüstü penceresi** (pywebview): sol tarafta çalma listeleri,
  ortada seçili listenin şarkıları, altta şimdi çalan + kontroller +
  gerçek zamanlı ilerleme çubuğu (seek bar), sağ üstte ayarlar.
- **Çalma listeleri = alt klasörler**: `BooPlaylist` altına açılan her
  alt klasör otomatik olarak ayrı bir çalma listesi olarak görünüyor.
  Ayrı bir playlist yönetim sistemi kurulmadı; zaten var olan klasör
  tarama mantığı kullanıldı.
- **Ses motoru pygame-ce'den libVLC'ye taşındı.** Sebep: pencerede
  istenen "istediğin saniyeye sar" özelliği için MP3'lerde GÜVENİLİR,
  mutlak seek gerekiyordu; SDL_mixer/pygame bunu MP3'te sadece göreceli
  ve VBR kodlamada hatalı yapabiliyordu. libVLC formattan bağımsız doğru
  seek sağlıyor. Fade in/out artık libVLC üzerinde elle (adım adım ses
  değiştirerek) uygulanıyor (VLC'de pygame'deki gibi hazır bir "fade_ms"
  yok).
- Pencere kapatma (X) uygulamayı kapatmıyor, sadece gizliyor (Discord/
  Slack gibi); tepsi menüsüne "Pencereyi Göster" eklendi.
- Ayarlar paneli: müzik klasörünü değiştirme (native klasör seçici),
  yeniden tarama, bildirim aç/kapa.
- Mimari: Tepsi ayrı thread'de, GUI ana thread'de çalışacak şekilde
  tasarlandı (bu sürümde henüz GTK çakışması fark edilmemişti — bkz.
  v1.4.1'deki düzeltme).

## v1.3.0 — İkon yenileme ve küçük ayarlar

- Tepsi/uygulama ikonu yeniden tasarlandı: önceki "daire + dikdörtgen"
  (nota) görünümü yerine tek tip yuvarlatılmış çubuklardan oluşan daha
  pürüzsüz, minimalist bir "equalizer" motifi.
- Varsayılan ses seviyesi %80'den %10'a düşürüldü.

## v1.2.0 — Fade in/out, shuffle aç/kapa, kolay açılış, güvenilirlik

- **Fade in/out**: her şarkı 2 saniyede yükselerek başlıyor, 2 saniyede
  sönerek bitiyor (elle geçişte de, doğal bitişte de — süre bilgisi
  mutagen ile okunup buna göre proaktif tetikleniyor).
- **Ses kontrolü**: tepsi menüsünde tek tıkla %0-100 ön-ayarlar eklendi;
  `zenity` kuruluysa gerçek, sürüklenebilir bir kaydırıcı penceresi de
  açılabiliyor.
- **"Şarkı Seç"** menüsü: playlist'teki her şarkıyı listeleyip doğrudan
  seçebilme (▶ çalan / ✓ bu tur dinlenmiş / ‣ dinlenmemiş işaretleriyle).
- **Smart Shuffle aç/kapa**: kapatılırsa kütüphane sırayla çalıyor.
- **Kolay açılış**: uygulama artık sistem uygulama menüsüne (KDE/GNOME/
  rofi/wofi) ekleniyor; isteğe bağlı masaüstü simgesi.
- Ses karıştırıcıda (pavucontrol vb.) artık "python3" değil "Boomusic"
  görünüyor (PulseAudio'nun `PULSE_PROP_application.name` mekanizması).
- Belgeler klasörü artık sistemin diline göre (`xdg-user-dir` ile)
  bulunuyor; sabit "Documents" varsayılmıyor.
- **Güvenilirlik düzeltmesi**: shuffle aç/kapa ve kütüphane yeniden
  tarama gibi durum-değiştiren TÜM işlemler artık tek bir arka plan
  kuyruğundan geçiyor; böylece "tam shuffle kapatılırken otomatik şarkı
  geçişi de olursa ne olur" gibi yarış durumları yapısal olarak imkânsız
  hale getirildi (15 rastgele komutluk bir stres testiyle doğrulandı).
- Mimari: tray, ana thread'i ileride bir GUI'ye ayırmak için ayrı bir
  arka plan thread'ine taşındı (bu, v1.4.0'da gerçek bir GUI eklenmesini
  mümkün kıldı).

## v1.1.0 — pygame mixer düzeltmesi

- Resmi `pygame` paketinin, bazı (özellikle çok yeni) Python
  sürümlerinde `mixer` alt modülünü düzgün paketlemediği bir sorun
  tespit edildi ("mixer module not available" hatası). `pygame` yerine
  aynı arayüze sahip, daha güncel wheel'leri olan topluluk sürümü
  `pygame-ce` kuruldu.

## v1.0.0 — İlk sürüm

- CachyOS/Arch için tepsi (tray) simgesinden yönetilen yerel müzik çalar.
- Varsayılan müzik klasörü (`~/Documents/BooPlaylist`), mp3/ogg/wav/flac
  desteği, alt klasör taraması.
- **Smart Shuffle**: bir şarkı, diğer tüm şarkılar çalınmadan tekrar
  çalınmaz ("torba karıştırma" / bag shuffle algoritması).
- Sonraki/önceki, duraklat/devam et, ses ayarı.
- Dinleme istatistikleri (`stats.json`) — hangi şarkı kaç kere çalındı.
- `install.sh` / `uninstall.sh`: sanal ortam kurulumu, isteğe bağlı
  otomatik başlatma, müzik dosyalarına asla dokunmayan güvenli kaldırma.
