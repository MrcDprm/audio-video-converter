# Ses ve Video Dönüştürücü (Audio Video Converter)

[English](README.md) | **Türkçe**

Python ve Tkinter ile yazılmış bir masaüstü ses ve video dönüştürücü. Arka planda `ffmpeg`'i çalıştırır; onu hazır profilleri, kuyruğu ve gerçek ilerleme göstergesi olan, sürükle-bırakla kullanılan basit bir uygulamaya çevirir.

> 🚧 Geliştiriliyor. Bu README şimdilik proje planı; v1.0.0'da tamamlanacak.

## Plan

### MVP
- **Kuyruk:** Dosyalar sürükle-bırakla ya da dosya seçme penceresiyle eklenir, sırayla dönüştürülür.
- **Dosya bilgisi:** Süre, çözünürlük ve codec'ler `ffprobe` ile okunur.
- **Codec adı yerine hazır profiller:**
  - Video: MP4 (H.264 / AAC), MKV, WebM (VP9 / Opus), MOV.
  - Ses: MP3, M4A (AAC), WAV, FLAC, OGG (Opus). Videodan ses çıkarılabilir.
- **Seçenekler:** Kalite (düşük / orta / yüksek) ve dosya küçültmek için çözünürlük (orijinal / 1080p / 720p / 480p).
- **Hızlı mod:** Kaynağın codec'leri hedef formata zaten uyuyorsa yeniden kodlamadan kopyalanır. Örneğin MKV → MP4 dakikalar yerine saniyeler sürer.
- **Gerçek ilerleme:** Her dosya için yüzde ve kalan süre, iptal düğmesi, bitince "klasörü aç".
- **Güvenli çıktı:** Var olan dosyanın üzerine asla yazılmaz (otomatik yeniden adlandırma). Bozuk dosya, desteklenmeyen format ya da dolu disk gibi hatalar anlaşılır bir mesajla gösterilir.
- **Kullanım:** Çıktı klasörü seçimi, koyu ve açık tema, Türkçe ve İngilizce, hatırlanan ayarlar.
- **Masaüstü uygulaması:** İkon, sürüm, Hakkında penceresi, kullanıcı klasörüne kaydedilen ayarlar, `ffmpeg` dahil Windows kurulum dosyası (PyInstaller + Inno Setup).
- **Testler:** Komut oluşturma, ilerleme ayrıştırma, dosya adı çakışması ve ayarlar.

### Gelecek Planları
- Kırpma (başlangıç / bitiş zamanı).
- GIF çıktısı.
- Donanım hızlandırma (NVENC, Quick Sync).
- Altyazı gömme.
- Aynı anda birden fazla dosya dönüştürme.

## Kullanılan Teknolojiler
- Python 3, Tkinter
- [FFmpeg](https://ffmpeg.org) (`ffmpeg` ve `ffprobe`, `subprocess` ile çağrılır)
- Sürükle-bırak için [tkinterdnd2](https://github.com/Eliav2/tkinterdnd2)
- `unittest`
- PyInstaller, Inno Setup
