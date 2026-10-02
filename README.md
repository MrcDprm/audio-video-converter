<p align="center">
  <img src="assets/icon.png" alt="Audio Video Converter icon" width="96">
</p>

<h1 align="center">Audio Video Converter</h1>

<p align="center">
  <b>English</b> | <a href="README.tr.md">Türkçe</a>
</p>

<p align="center">
  A desktop audio and video converter written in Python and Tkinter. It runs FFmpeg in the background<br>
  and turns it into a simple drag-and-drop app with presets, a queue and real progress.
</p>

<p align="center">
  <a href="https://github.com/MrcDprm/audio-video-converter/releases/latest"><b>⬇️ Download for Windows</b></a>
</p>

<p align="center">
  <img src="docs/demo.gif" alt="Animation showing a 4K video being converted to 720p MP4" width="720">
</p>

## Features

**Conversion**
- **Presets instead of codec names:** MP4, MKV, WebM and MOV for video; MP3, M4A, WAV, FLAC and OGG for audio
- **Audio from video:** pick an audio format and the soundtrack is extracted
- **Quality and size:** low / medium / high quality and 1080p, 720p or 480p to shrink files (videos are never upscaled)
- **Fast mode:** if the source codecs already fit the target format, streams are copied without re-encoding. A 1080p MKV becomes an MP4 in under a second instead of minutes
- **Plays everywhere:** H.264 + AAC with a compatible pixel format and `faststart`, so files open on phones, browsers and TVs

**Queue**
- Drag and drop files or whole folders onto the window, or use the file dialog
- Duration, resolution and codecs are read with `ffprobe` and shown for each file
- Files are converted one after another with percentage and time left; one button stops the queue
- Broken files, images and other non-media files are detected before converting

**Safety**
- Existing files are never overwritten: the output is named `video (1).mp4`, `video (2).mp4`…
- A stopped or failed conversion deletes its unfinished output
- Clear messages for full disks, missing permissions and impossible conversions (for example an MP3 to MP4)
- Closing the window during a conversion asks first and stops FFmpeg cleanly

**Interface**
- Output to the source folder or a folder of your choice
- Double-click a finished file to show it in Explorer
- Dark and light theme, Turkish and English interface, remembered settings

**Other**
- 37 tests, including real conversions with FFmpeg
- Setup wizard with FFmpeg included: nothing else to install

## Screenshots

**Converting a queue (dark, Turkish)**

<img src="docs/queue-dark.png" alt="Queue with one finished file, one converting at 39 percent and a rejected non-media file" width="720">

| Extracting audio (light, English) | Empty window |
|---|---|
| <img src="docs/audio-light-en.png" alt="Four files converted to MP3 in light theme" width="420"> | <img src="docs/empty-dark.png" alt="Empty window inviting to drop files" width="420"> |

## Installation

1. Download `AudioVideoConverter-x.y.z-Setup.exe` from the [Releases](https://github.com/MrcDprm/audio-video-converter/releases/latest) page.
2. Run it and follow the setup steps. No administrator rights are needed. FFmpeg is included.
3. Find the app in the Start menu as **Ses ve Video Dönüştürücü**. The interface opens in Turkish; the language button at the top right switches it to English.

> **Windows "protected your PC" warning:** The app is not digitally signed, so Windows SmartScreen may show a warning on first launch. Continue with **More info → Run anyway**. The full source code is open in this repository.

**Uninstall:** Settings → Apps → Installed apps → Ses ve Video Dönüştürücü → Uninstall.
Settings are kept in `%USERPROFILE%\.audio-video-converter` and are not deleted on uninstall.

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Ctrl+O` | Add files |
| `Delete` | Remove the selected files |
| `Ctrl+Enter` | Start or stop converting |

## Tech Stack

- **Python 3.12** and **Tkinter / ttk**: user interface
- **[FFmpeg](https://ffmpeg.org)** (`ffmpeg` and `ffprobe`): conversion and file info, run with `subprocess`
- **[tkinterdnd2](https://github.com/Eliav2/tkinterdnd2)**: drag and drop
- **threading, queue**: probing and converting in the background
- **unittest**: tests
- **PyInstaller** and **Inno Setup**: Windows installer

## Project Structure

```
audio-video-converter/
├── main.py         # Entry point, drag-and-drop window
├── gui.py          # Tkinter interface: queue, options, progress
├── presets.py      # Output formats, qualities and resolutions
├── probe.py        # Reads file info with ffprobe
├── command.py      # Builds the ffmpeg command, fast mode, output names
├── progress.py     # Parses ffmpeg progress, time left
├── runner.py       # Runs ffmpeg, cancels, classifies errors
├── settings.py     # Remembered options
├── i18n.py         # Turkish and English texts
├── storage.py      # Saves JSON files to the user folder
├── app_info.py     # App name, version, FFmpeg lookup
├── scripts/        # Downloads a verified FFmpeg build for packaging
├── assets/         # App icon
├── docs/           # README images
├── installer/      # Inno Setup script
└── tests/          # Tests
```

## Running from Source

Requires Python 3.12 or newer and FFmpeg on the `PATH` (for example `winget install Gyan.FFmpeg`).

```bash
python -m pip install tkinterdnd2
python main.py           # run the app
python -m unittest -v    # run the tests (FFmpeg tests are skipped if FFmpeg is missing)
```

### Building the installer

Requires [PyInstaller](https://pyinstaller.org) and [Inno Setup 6](https://jrsoftware.org/isinfo.php).

```bash
python scripts/fetch_ffmpeg.py    # downloads FFmpeg into vendor/ and checks its SHA-256
python -m PyInstaller --noconfirm AudioVideoConverter.spec
ISCC installer/audio-video-converter.iss
```

The installer is created in the `installer/Output/` folder.

**When releasing a new version:** update the version number in both `app_info.py` (`VERSION`) and `installer/audio-video-converter.iss` (`AppVersion`), run the tests, run the build commands and upload the installer to a new GitHub Release.

## What I Learned

- **Running another program safely.** I learned to start FFmpeg with `subprocess`, passing the command as a list instead of a single string so a file name can never be treated as a command, and to hide the console window on Windows.
- **Containers and codecs are different things.** An `.mkv` or `.mp4` is only a box; the video and audio inside are compressed with codecs such as H.264 and AAC. Understanding this made fast mode possible: when the codecs already fit, I only change the box and the conversion takes seconds instead of minutes.
- **Reading a program's output while it runs.** I parsed FFmpeg's `-progress` output line by line to show a real percentage and time left. I also learned the hard way that if one output pipe is not read, its buffer fills up and the program freezes, so errors are read in a second thread.
- **Background work in a desktop app.** Probing and converting run in threads and send their results through a `queue`; only the main thread touches the window. This keeps the interface responsive even with a 4K video.
- **Not trusting input files.** File extensions lie, so every file is checked with `ffprobe` and every value it returns is validated. Broken files, images and empty files get a clear message instead of a crash.
- **Protecting the user's files.** Outputs never overwrite existing files, unfinished files are deleted when a conversion stops, and closing the app stops FFmpeg cleanly.
- **Shipping a third-party tool.** I bundled FFmpeg with the installer, verified the download with a SHA-256 hash, and included FFmpeg's GPL license and source link, while my own code stays MIT because FFmpeg runs as a separate program.
- **Testing with the real tool.** Besides unit tests, I generate small test videos with FFmpeg itself and convert them for real, including cancelling in the middle.

## Future Plans

- Trimming (start and end time)
- GIF output
- Hardware acceleration (NVIDIA NVENC, Intel Quick Sync)
- Embedding subtitles
- Packages for macOS and Linux

## License

[MIT](LICENSE) © 2026 Miraç Deprem

The installer includes [FFmpeg](https://ffmpeg.org) (a static build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)), which is licensed under the GPL v3. Its license text and a link to its source code are installed next to it in the `vendor` folder.
