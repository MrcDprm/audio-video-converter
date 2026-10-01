# Audio Video Converter

**English** | [Türkçe](README.tr.md)

A desktop audio and video converter written in Python and Tkinter. It drives `ffmpeg` in the background and turns it into a simple drag-and-drop app with presets, a queue and real progress.

> 🚧 Work in progress. This README is the project plan and will be completed at v1.0.0.

## Plan

### MVP
- **Queue:** add files with drag and drop or a file dialog, then convert them one after another.
- **File info:** duration, resolution and codecs, read with `ffprobe`.
- **Presets instead of codec names:**
  - Video: MP4 (H.264 / AAC), MKV, WebM (VP9 / Opus), MOV.
  - Audio: MP3, M4A (AAC), WAV, FLAC, OGG (Opus). Audio can be extracted from video.
- **Options:** quality (low / medium / high) and resolution (original / 1080p / 720p / 480p) to shrink files.
- **Fast mode:** if the source codecs already fit the target format, streams are copied without re-encoding. For example, MKV → MP4 takes seconds instead of minutes.
- **Real progress:** percentage and time left for each file, a cancel button, "open folder" when done.
- **Safe output:** existing files are never overwritten (automatic renaming). Errors such as a broken file, an unsupported format or a full disk get a clear message.
- **Usability:** output folder choice, dark and light theme, Turkish and English, remembered settings.
- **Desktop app:** icon, version, About window, settings saved in the user's folder, Windows installer with `ffmpeg` included (PyInstaller + Inno Setup).
- **Tests:** command building, progress parsing, file name conflicts and settings.

### Future Plans
- Trimming (start / end time).
- GIF output.
- Hardware acceleration (NVENC, Quick Sync).
- Embedding subtitles.
- Converting several files at the same time.

## Tech Stack
- Python 3, Tkinter
- [FFmpeg](https://ffmpeg.org) (`ffmpeg` and `ffprobe`, called with `subprocess`)
- [tkinterdnd2](https://github.com/Eliav2/tkinterdnd2) for drag and drop
- `unittest`
- PyInstaller, Inno Setup
