"""Arayüz: dosya kuyruğu, sürükle-bırak, format seçenekleri, ilerleme ve iptal.

Dosya okuma (probe) ve dönüştürme (runner) arka plan iş parçacıklarında çalışır. Onlar sonuçlarını
self.events kuyruğuna koyar; pencereye sadece ana iş parçacığı dokunur (poll_events).
"""
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
import traceback
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from app_info import REPOSITORY_URL, VERSION, find_tool, resource_path
from command import CommandError, build_command, output_path
from i18n import media_summary, translate
from presets import FORMATS, INPUT_EXTENSIONS, QUALITIES, RESOLUTIONS
from probe import ProbeError, probe
from progress import format_duration
from runner import Conversion
from settings import load_settings, save_settings

try:
    from tkinterdnd2 import DND_FILES
except ImportError:  # sürükle-bırak olmadan da çalışır
    DND_FILES = None

FONT = "Segoe UI"
POLL_MS = 100
MAX_QUEUE = 500
RETRY_STATES = ("ready", "cancelled", "failed")  # "Dönüştür"e basınca sıraya girenler

THEMES = {
    "dark": {
        "background": "#202020", "panel": "#2b2b2b", "field": "#1c1c1c", "text": "#ffffff",
        "muted": "#9d9d9d", "accent": "#4cc2ff", "accent_text": "#000000", "hover": "#383838",
        "error": "#ff99a4", "success": "#6ccb5f", "line": "#3d3d3d",
    },
    "light": {
        "background": "#f3f3f3", "panel": "#ffffff", "field": "#fbfbfb", "text": "#1a1a1a",
        "muted": "#5f5f5f", "accent": "#005fb8", "accent_text": "#ffffff", "hover": "#e5e5e5",
        "error": "#c42b1c", "success": "#0f7b0f", "line": "#d4d4d4",
    },
}


class ConverterApp:
    def __init__(self, root):
        self.root = root
        root.report_callback_exception = self.on_unexpected_error
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.set_icon()

        self.settings = load_settings()
        self.colors = THEMES[self.settings["theme"]]
        self.ffmpeg, self.ffprobe = find_tool("ffmpeg"), find_tool("ffprobe")
        self.items = {}  # kimlik → {"path", "info", "state", "code", "percent", "remaining", "target"}
        self.next_id = 0
        self.events = queue.Queue()
        self.probe_jobs = queue.Queue()
        self.running = False  # kullanıcı "Dönüştür"e bastı, kuyruk işleniyor
        self.current = None  # (kimlik, Conversion)
        self.run_done = self.run_failed = 0
        self.last_target = None
        self.closing = False

        self.style = ttk.Style(root)
        self.style.theme_use("clam")
        self.build_header()
        self.build_queue()
        self.build_options()
        self.build_footer()
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self.bind_keys()
        self.enable_drop()

        self.apply_theme()
        self.render_texts()
        self.fit_window()
        threading.Thread(target=self.probe_worker, daemon=True).start()
        self.root.after(POLL_MS, self.poll_events)
        if not self.ffmpeg or not self.ffprobe:
            self.root.after(300, lambda: messagebox.showerror(self.t("app_name"), self.t("ffmpeg_missing_text")))

    # ---------- Kurulum ----------

    def build_header(self):
        self.header = tk.Frame(self.root, padx=20, pady=12)
        self.header.grid(row=0, column=0, sticky="ew")
        self.title_label = tk.Label(self.header, font=(FONT, 16, "bold"), anchor="w")
        self.title_label.pack(side="left")
        self.about_button = self.small_button(self.header, self.show_about)
        self.language_button = self.small_button(self.header, self.toggle_language)
        self.theme_button = self.small_button(self.header, self.toggle_theme)

    def small_button(self, parent, command, side="right"):
        button = tk.Button(parent, font=(FONT, 10), relief="flat", bd=0, padx=12, pady=5, cursor="hand2",
                           command=command)
        button.pack(side=side, padx=(6, 0))
        return button

    def build_queue(self):
        self.queue_frame = tk.Frame(self.root, padx=20)
        self.queue_frame.grid(row=1, column=0, sticky="nsew")
        self.queue_frame.grid_columnconfigure(0, weight=1)
        self.queue_frame.grid_rowconfigure(1, weight=1)

        self.toolbar = tk.Frame(self.queue_frame)
        self.toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.add_button = tk.Button(self.toolbar, font=(FONT, 10, "bold"), relief="flat", bd=0, padx=14, pady=6,
                                    cursor="hand2", command=self.choose_files)
        self.add_button.pack(side="left")
        self.remove_button = self.small_button(self.toolbar, self.remove_selected, side="left")
        self.clear_button = self.small_button(self.toolbar, self.clear_queue, side="left")

        self.table = ttk.Treeview(self.queue_frame, columns=("file", "info", "status"), show="headings",
                                  selectmode="extended")
        self.table.column("file", width=320, anchor="w")
        self.table.column("info", width=260, anchor="w")
        self.table.column("status", width=200, anchor="w")
        self.table.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.queue_frame, orient="vertical", command=self.table.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.bind("<Double-1>", self.on_double_click)

        # Liste boşken ortada görünen ipucu
        self.hint = tk.Frame(self.queue_frame)
        self.hint_icon = tk.Label(self.hint, text="⇣", font=(FONT, 30))
        self.hint_icon.pack()
        self.hint_label = tk.Label(self.hint, font=(FONT, 12, "bold"))
        self.hint_label.pack()
        self.hint_sub = tk.Label(self.hint, font=(FONT, 9))
        self.hint_sub.pack(pady=(4, 0))
        for widget in (self.hint, self.hint_icon, self.hint_label, self.hint_sub):
            widget.bind("<Button-1>", lambda event: self.choose_files())
            widget.configure(cursor="hand2")

    def build_options(self):
        self.options = tk.Frame(self.root, padx=20, pady=12)
        self.options.grid(row=3, column=0, sticky="ew")
        for column in (1, 3, 5):
            self.options.grid_columnconfigure(column, weight=1)

        self.format_label = tk.Label(self.options, font=(FONT, 10), anchor="w")
        self.format_label.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.format_combo = ttk.Combobox(self.options, state="readonly", font=(FONT, 10), width=18)
        self.format_combo.grid(row=0, column=1, sticky="ew", padx=(0, 18))
        self.quality_label = tk.Label(self.options, font=(FONT, 10), anchor="w")
        self.quality_label.grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.quality_combo = ttk.Combobox(self.options, state="readonly", font=(FONT, 10), width=18)
        self.quality_combo.grid(row=0, column=3, sticky="ew", padx=(0, 18))
        self.resolution_label = tk.Label(self.options, font=(FONT, 10), anchor="w")
        self.resolution_label.grid(row=0, column=4, sticky="w", padx=(0, 8))
        self.resolution_combo = ttk.Combobox(self.options, state="readonly", font=(FONT, 10), width=12)
        self.resolution_combo.grid(row=0, column=5, sticky="ew")
        for combo in (self.format_combo, self.quality_combo, self.resolution_combo):
            combo.bind("<<ComboboxSelected>>", lambda event: self.on_option_changed())

        self.fast_var = tk.BooleanVar(value=self.settings["fast"])
        self.fast_check = tk.Checkbutton(self.options, variable=self.fast_var, font=(FONT, 10), anchor="w",
                                         bd=0, highlightthickness=0, command=self.on_option_changed)
        self.fast_check.grid(row=1, column=0, columnspan=6, sticky="w", pady=(10, 0))

        self.folder_row = tk.Frame(self.options)
        self.folder_row.grid(row=2, column=0, columnspan=6, sticky="ew", pady=(10, 0))
        self.folder_label = tk.Label(self.folder_row, font=(FONT, 10), anchor="w")
        self.folder_label.pack(side="left", padx=(0, 8))
        self.folder_value = tk.Label(self.folder_row, font=(FONT, 10), anchor="w")
        self.folder_value.pack(side="left")
        self.source_button = self.small_button(self.folder_row, self.use_source_folder)
        self.change_button = self.small_button(self.folder_row, self.choose_folder)

    def build_footer(self):
        self.footer = tk.Frame(self.root, padx=20, pady=14)
        self.footer.grid(row=4, column=0, sticky="ew")
        self.footer.grid_columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(self.footer, maximum=100)
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 14))
        self.summary_label = tk.Label(self.footer, font=(FONT, 10), anchor="e")
        self.summary_label.grid(row=0, column=1, sticky="e", padx=(0, 10))
        self.open_button = tk.Button(self.footer, font=(FONT, 10), relief="flat", bd=0, padx=12, pady=8,
                                     cursor="hand2", command=self.open_last_folder)
        self.open_button.grid(row=0, column=2, padx=(0, 8))
        self.convert_button = tk.Button(self.footer, font=(FONT, 11, "bold"), relief="flat", bd=0, padx=26, pady=8,
                                        cursor="hand2", command=self.toggle_conversion)
        self.convert_button.grid(row=0, column=3)

    def bind_keys(self):
        self.root.bind("<Control-o>", lambda event: self.choose_files())
        self.root.bind("<Delete>", lambda event: self.remove_selected())
        self.root.bind("<Control-Return>", lambda event: self.toggle_conversion())

    def enable_drop(self):
        """tkinterdnd2 yüklüyse dosyalar pencereye sürüklenip bırakılabilir."""
        if DND_FILES is None or not hasattr(self.root, "drop_target_register"):
            return
        for widget in (self.root, self.table, self.hint, self.hint_icon, self.hint_label, self.hint_sub):
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self.on_drop)

    def set_icon(self):
        try:
            self.root.iconbitmap(default=resource_path("assets/icon.ico"))
        except tk.TclError:
            pass

    def fit_window(self):
        """Pencere boyutu ekran ölçeğine göre ayarlanır: %150 ölçekte yazılar büyür, pencere de büyümeli."""
        self.root.update_idletasks()
        scale = self.root.winfo_fpixels("1i") / 96
        needed_width, needed_height = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        width = min(max(int(1000 * scale), needed_width), self.root.winfo_screenwidth() - 40)
        height = min(max(int(640 * scale), needed_height), self.root.winfo_screenheight() - 80)
        left = (self.root.winfo_screenwidth() - width) // 2
        top = max(0, (self.root.winfo_screenheight() - height) // 2 - 20)
        self.root.geometry(f"{width}x{height}+{left}+{top}")
        self.root.minsize(min(needed_width, width), min(needed_height, height))

    # ---------- Metinler ve tema ----------

    def t(self, key, **params):
        return translate(self.settings["lang"], key, **params)

    def render_texts(self):
        self.root.title(self.t("app_name"))
        self.title_label.config(text=self.t("app_name"))
        self.theme_button.config(text=("☀  " if self.settings["theme"] == "dark" else "☾  ") + self.t("theme"))
        self.language_button.config(text="🌐  " + self.t("language"))
        self.about_button.config(text="ⓘ  " + self.t("about"))
        self.add_button.config(text=self.t("add_files"))
        self.remove_button.config(text=self.t("remove"))
        self.clear_button.config(text=self.t("clear"))
        self.hint_label.config(text=self.t("drop_hint"))
        self.hint_sub.config(text=self.t("drop_hint_sub"))
        for column in ("file", "info", "status"):
            self.table.heading(column, text=self.t(f"col_{column}"))
        self.format_label.config(text=self.t("format"))
        self.quality_label.config(text=self.t("quality"))
        self.resolution_label.config(text=self.t("resolution"))
        self.fast_check.config(text=self.t("fast_mode"))
        self.folder_label.config(text=self.t("output_folder") + ":")
        self.change_button.config(text=self.t("change"))
        self.source_button.config(text=self.t("use_source"))
        self.open_button.config(text=self.t("open_folder"))
        self.render_options()
        self.render_folder()
        for item_id in self.items:
            self.render_row(item_id)
        self.render_state()

    def apply_theme(self):
        c = self.colors
        for frame in (self.root, self.header, self.queue_frame, self.toolbar, self.options, self.folder_row,
                      self.footer):
            frame.config(bg=c["background"])
        self.hint.config(bg=c["field"])
        self.title_label.config(bg=c["background"], fg=c["text"])
        self.hint_label.config(bg=c["field"], fg=c["text"])
        for label in (self.hint_icon, self.hint_sub):
            label.config(bg=c["field"], fg=c["muted"])
        for label in (self.format_label, self.quality_label, self.resolution_label,
                      self.folder_label, self.folder_value):
            label.config(bg=c["background"], fg=c["text"])
        self.summary_label.config(bg=c["background"], fg=c["muted"])
        for button in (self.theme_button, self.language_button, self.about_button):
            button.config(bg=c["background"], fg=c["text"], activebackground=c["hover"], activeforeground=c["text"])
        for button in (self.remove_button, self.clear_button, self.change_button, self.source_button,
                       self.open_button):
            button.config(bg=c["panel"], fg=c["text"], activebackground=c["hover"], activeforeground=c["text"],
                          disabledforeground=c["muted"])
        for button in (self.add_button, self.convert_button):
            button.config(bg=c["accent"], fg=c["accent_text"], activebackground=c["accent"],
                          activeforeground=c["accent_text"], disabledforeground=c["accent_text"])
        self.fast_check.config(bg=c["background"], fg=c["text"], activebackground=c["background"],
                               activeforeground=c["text"], selectcolor=c["field"])

        self.style.configure("TCombobox", fieldbackground=c["field"], background=c["panel"], foreground=c["text"],
                             arrowcolor=c["text"], bordercolor=c["line"], lightcolor=c["field"], darkcolor=c["field"])
        self.style.map("TCombobox",
                       fieldbackground=[("readonly", c["field"]), ("disabled", c["background"])],
                       foreground=[("disabled", c["muted"]), ("readonly", c["text"])],
                       selectbackground=[("readonly", c["field"])], selectforeground=[("readonly", c["text"])])
        self.style.configure("Treeview", background=c["field"], fieldbackground=c["field"], foreground=c["text"],
                             bordercolor=c["line"], lightcolor=c["line"], darkcolor=c["line"], rowheight=28,
                             font=(FONT, 10))
        self.style.map("Treeview", background=[("selected", c["hover"])], foreground=[("selected", c["text"])])
        self.style.configure("Treeview.Heading", background=c["panel"], foreground=c["muted"], relief="flat",
                             font=(FONT, 9, "bold"))
        self.style.map("Treeview.Heading", background=[("active", c["hover"])])
        self.style.configure("Vertical.TScrollbar", background=c["hover"], troughcolor=c["field"],
                             bordercolor=c["field"], arrowcolor=c["muted"], lightcolor=c["hover"],
                             darkcolor=c["hover"], gripcount=0)
        self.style.map("Vertical.TScrollbar", background=[("active", c["line"])])
        self.style.configure("Horizontal.TProgressbar", background=c["accent"], troughcolor=c["panel"],
                             bordercolor=c["panel"], lightcolor=c["accent"], darkcolor=c["accent"])
        self.table.tag_configure("error", foreground=c["error"])
        self.table.tag_configure("done", foreground=c["success"])
        self.table.tag_configure("muted", foreground=c["muted"])
        self.root.option_add("*TCombobox*Listbox.background", c["panel"])
        self.root.option_add("*TCombobox*Listbox.foreground", c["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", c["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", c["accent_text"])
        for combo in (self.format_combo, self.quality_combo, self.resolution_combo):
            try:
                popdown = combo.tk.eval(f"ttk::combobox::PopdownWindow {combo}")
                combo.tk.call(f"{popdown}.f.l", "configure", "-background", c["panel"], "-foreground", c["text"],
                              "-selectbackground", c["accent"], "-selectforeground", c["accent_text"])
            except tk.TclError:
                pass

    def toggle_theme(self):
        self.settings["theme"] = "light" if self.settings["theme"] == "dark" else "dark"
        self.colors = THEMES[self.settings["theme"]]
        save_settings(self.settings)
        self.apply_theme()
        self.render_texts()

    def toggle_language(self):
        self.settings["lang"] = "en" if self.settings["lang"] == "tr" else "tr"
        save_settings(self.settings)
        self.render_texts()

    # ---------- Seçenekler ----------

    def render_options(self):
        """Seçenek listeleri dile göre doldurulur; seçim anahtar listesindeki sırayla eşleşir."""
        self.format_keys = list(FORMATS)
        self.quality_keys = list(QUALITIES)
        self.resolution_keys = list(RESOLUTIONS)
        self.format_combo.config(values=[
            ("🎬  " if FORMATS[key]["kind"] == "video" else "🎵  ") + FORMATS[key]["label"] for key in self.format_keys
        ])
        self.quality_combo.config(values=[self.t(f"quality_{key}") for key in self.quality_keys])
        self.resolution_combo.config(values=[
            self.t("resolution_original") if key == "original" else key for key in self.resolution_keys
        ])
        self.format_combo.current(self.format_keys.index(self.settings["format"]))
        self.quality_combo.current(self.quality_keys.index(self.settings["quality"]))
        self.resolution_combo.current(self.resolution_keys.index(self.settings["resolution"]))

    def on_option_changed(self):
        self.settings["format"] = self.format_keys[self.format_combo.current()]
        self.settings["quality"] = self.quality_keys[self.quality_combo.current()]
        self.settings["resolution"] = self.resolution_keys[self.resolution_combo.current()]
        self.settings["fast"] = self.fast_var.get()
        save_settings(self.settings)
        self.render_state()

    def render_folder(self):
        folder = self.settings["output_dir"]
        if not folder:
            self.folder_value.config(text=self.t("same_folder"))
        else:
            self.folder_value.config(text=folder if len(folder) <= 60 else "…" + folder[-59:])

    def choose_folder(self):
        folder = filedialog.askdirectory(parent=self.root, title=self.t("select_folder"),
                                         initialdir=self.settings["output_dir"] or Path.home())
        if folder:
            self.settings["output_dir"] = str(Path(folder))
            save_settings(self.settings)
            self.render_folder()

    def use_source_folder(self):
        self.settings["output_dir"] = None
        save_settings(self.settings)
        self.render_folder()

    # ---------- Kuyruk ----------

    def choose_files(self):
        patterns = " ".join(f"*{extension}" for extension in INPUT_EXTENSIONS)
        paths = filedialog.askopenfilenames(parent=self.root, title=self.t("select_files"),
                                            filetypes=[(self.t("filter_media"), patterns), (self.t("filter_all"), "*.*")])
        self.add_paths(paths)

    def on_drop(self, event):
        # Boşluk içeren yollar {süslü parantez} içinde gelir; splitlist bunları doğru ayırır
        self.add_paths(self.root.tk.splitlist(event.data))
        return event.action

    def add_paths(self, paths):
        known = {item["path"] for item in self.items.values()}
        for raw in paths:
            path = Path(raw)
            # Bırakılan klasördeki medya dosyaları da eklenir (alt klasörlere inilmez)
            try:
                files = [path] if not path.is_dir() else sorted(
                    child for child in path.iterdir() if child.suffix.lower() in INPUT_EXTENSIONS
                )
            except OSError:  # izin verilmeyen klasör
                continue
            for file in files:
                if len(self.items) >= MAX_QUEUE:
                    return
                if not file.is_file() or file in known:
                    continue
                known.add(file)
                self.add_item(file)
        self.render_state()

    def add_item(self, path):
        item_id = str(self.next_id)
        self.next_id += 1
        self.items[item_id] = {"path": path, "info": None, "state": "probing", "code": None,
                               "percent": 0, "remaining": None, "target": None}
        self.table.insert("", "end", iid=item_id, values=(path.name, "", ""))
        self.render_row(item_id)
        if self.ffprobe:
            self.probe_jobs.put((item_id, path))
        else:
            self.set_state(item_id, "error", "ffmpeg_missing")

    def render_row(self, item_id):
        item = self.items[item_id]
        state = item["state"]
        info = media_summary(item["info"]) if item["info"] else ""
        if state == "converting":
            percent = int(item["percent"])
            status = (self.t("status_remaining", percent=percent, time=format_duration(item["remaining"]))
                      if (item["remaining"] or 0) >= 1 else self.t("status_converting", percent=percent))
        elif state in ("error", "failed"):
            status = self.t(f"error_{item['code']}")
        else:
            status = self.t(f"status_{state}")
        tag = {"error": "error", "failed": "error", "done": "done", "probing": "muted", "cancelled": "muted"}.get(state, "")
        self.table.item(item_id, values=(item["path"].name, info, status), tags=(tag,))

    def set_state(self, item_id, state, code=None):
        item = self.items.get(item_id)
        if item is None:
            return
        item["state"], item["code"] = state, code
        self.render_row(item_id)

    def remove_selected(self):
        for item_id in self.table.selection():
            if self.current and self.current[0] == item_id:
                continue  # dönüştürülen dosya kaldırılamaz; önce durdurulmalı
            self.table.delete(item_id)
            del self.items[item_id]
        self.render_state()

    def clear_queue(self):
        self.table.selection_set(list(self.items))
        self.remove_selected()

    def on_double_click(self, event):
        item = self.items.get(self.table.identify_row(event.y))
        if item and item["state"] == "done":
            self.reveal(item["target"])

    # ---------- Arka plan işleri ----------

    def probe_worker(self):
        while True:
            item_id, path = self.probe_jobs.get()
            try:
                self.events.put(("probed", item_id, probe(self.ffprobe, path), None))
            except ProbeError as error:
                self.events.put(("probed", item_id, None, error.code))

    def poll_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                handler = getattr(self, f"on_{event[0]}")
                handler(*event[1:])
        except queue.Empty:
            pass
        self.root.after(POLL_MS, self.poll_events)

    def on_probed(self, item_id, info, code):
        if item_id not in self.items:
            return  # okunurken listeden kaldırıldı
        if info is None:
            self.set_state(item_id, "error", code)
        else:
            self.items[item_id]["info"] = info
            self.set_state(item_id, "ready")
        self.render_state()
        if self.running and not self.current:
            self.start_next()

    def on_progress(self, item_id, percent, remaining):
        item = self.items.get(item_id)
        if item is None or item["state"] != "converting":
            return
        item["percent"], item["remaining"] = percent, remaining
        self.render_row(item_id)
        self.progress.config(value=percent)

    def on_finished(self, item_id, result):
        self.current = None
        if result == "done":
            self.run_done += 1
            self.last_target = self.items[item_id]["target"] if item_id in self.items else self.last_target
            self.set_state(item_id, "done")
        elif result == "cancelled":
            self.set_state(item_id, "cancelled")
        else:
            self.run_failed += 1
            self.set_state(item_id, "failed", result)
        if self.closing:
            self.close_window()
            return
        if self.running:
            self.start_next()
        self.render_state()

    # ---------- Dönüştürme ----------

    def toggle_conversion(self):
        if self.running:
            self.stop()
            return
        retry = [item_id for item_id, item in self.items.items() if item["state"] in RETRY_STATES]
        if not retry:
            return
        for item_id in retry:
            self.set_state(item_id, "ready")
        self.running = True
        self.run_done = self.run_failed = 0
        self.start_next()
        self.render_state()

    def start_next(self):
        ready = [item_id for item_id, item in self.items.items() if item["state"] == "ready"]
        if not ready:
            # Okunmayı bekleyen dosya varsa onları bekle; yoksa iş bitti
            if not any(item["state"] == "probing" for item in self.items.values()):
                self.running = False
                self.progress.config(value=100 if self.run_done else 0)
                if self.run_done:
                    self.root.bell()
            self.render_state()
            return
        item_id = ready[0]
        item = self.items[item_id]
        folder = self.settings["output_dir"]
        if folder and not Path(folder).is_dir():
            self.run_failed += 1
            self.set_state(item_id, "failed", "output_missing")
            self.start_next()
            return
        try:
            target = output_path(item["path"], self.settings["format"], folder)
            command = build_command(self.ffmpeg, item["path"], target, item["info"], self.settings["format"],
                                    self.settings["quality"], self.settings["resolution"], self.settings["fast"])
        except CommandError as error:
            self.run_failed += 1
            self.set_state(item_id, "failed", error.code)
            self.start_next()
            return

        item.update(target=target, percent=0, remaining=None)
        self.set_state(item_id, "converting")
        self.progress.config(value=0)
        conversion = Conversion(command, target, item["info"]["duration"],
                                lambda percent, remaining: self.events.put(("progress", item_id, percent, remaining)))
        self.current = (item_id, conversion)
        threading.Thread(target=lambda: self.events.put(("finished", item_id, conversion.run())), daemon=True).start()
        self.render_state()

    def stop(self):
        self.running = False
        if self.current:
            self.current[1].cancel()
        self.render_state()

    def render_state(self):
        """Düğmeler, özet yazısı ve boş liste ipucu."""
        has_items = bool(self.items)
        if has_items:
            self.hint.place_forget()
        else:
            self.hint.place(in_=self.table, relx=0.5, rely=0.5, anchor="center")
        can_start = any(item["state"] in RETRY_STATES for item in self.items.values())
        self.convert_button.config(text=self.t("cancel") if self.running else self.t("convert"),
                                   state="normal" if self.running or can_start else "disabled")
        self.remove_button.config(state="normal" if has_items else "disabled")
        self.clear_button.config(state="normal" if has_items else "disabled")
        self.open_button.config(state="normal" if self.last_target else "disabled")
        is_audio = FORMATS[self.settings["format"]]["kind"] == "audio"
        self.resolution_combo.config(state="disabled" if is_audio else "readonly")
        for widget in (self.format_combo, self.quality_combo):
            widget.config(state="disabled" if self.running else "readonly")
        if self.running:
            self.resolution_combo.config(state="disabled")
        self.fast_check.config(state="disabled" if self.running else "normal")

        if self.running:
            waiting = sum(item["state"] in ("ready", "probing") for item in self.items.values())
            finished = self.run_done + self.run_failed
            total = finished + waiting + (1 if self.current else 0)
            text = self.t("summary_running", current=min(finished + 1, total), total=total)
        elif self.run_done or self.run_failed:
            parts = [self.t("summary_done", count=self.run_done)] if self.run_done else []
            if self.run_failed:
                parts.append(self.t("summary_failed", count=self.run_failed))
            text = " · ".join(parts)
        elif any(item["state"] == "cancelled" for item in self.items.values()):
            text = self.t("summary_stopped")
        else:
            text = ""
        self.summary_label.config(text=text)

    # ---------- Diğer ----------

    def reveal(self, path):
        """Dosyayı Gezgin'de seçili olarak gösterir; dosya artık yoksa klasörünü açar."""
        if path and Path(path).exists():
            subprocess.Popen(["explorer", "/select,", str(path)])
        elif path and Path(path).parent.is_dir():
            os.startfile(Path(path).parent)

    def open_last_folder(self):
        self.reveal(self.last_target)

    def show_about(self):
        c = self.colors
        window = tk.Toplevel(self.root, bg=c["background"], padx=28, pady=22)
        window.title(self.t("about"))
        window.resizable(False, False)
        window.transient(self.root)
        window.geometry(f"+{self.root.winfo_rootx() + 80}+{self.root.winfo_rooty() + 80}")
        for text, font in (
            (self.t("app_name"), (FONT, 16, "bold")),
            (self.t("version", version=VERSION), (FONT, 11)),
            (self.t("about_text"), (FONT, 10)),
            (self.t("ffmpeg_credit"), (FONT, 9)),
            ("© 2026 Miraç Deprem", (FONT, 9)),
        ):
            tk.Label(window, text=text, font=font, wraplength=340, justify="center", bg=c["background"],
                     fg=c["text"]).pack(pady=2)
        link = tk.Label(window, text=self.t("view_on_github"), font=(FONT, 10, "underline"), cursor="hand2",
                        bg=c["background"], fg=c["accent"])
        link.pack(pady=(10, 0))
        link.bind("<Button-1>", lambda event: webbrowser.open(REPOSITORY_URL))
        window.bind("<Escape>", lambda event: window.destroy())
        window.grab_set()
        window.focus_set()

    def on_close(self):
        if not self.current:
            self.root.destroy()
            return
        if messagebox.askyesno(self.t("app_name"), self.t("quit_text"), parent=self.root):
            # Önce ffmpeg durdurulur ve yarım dosya silinir; pencere "finished" olayında kapanır
            self.closing = True
            self.stop()
            self.root.after(5000, self.close_window)  # her ihtimale karşı

    def close_window(self):
        try:
            self.root.destroy()
        except tk.TclError:  # zaten kapandı
            pass

    def on_unexpected_error(self, exc_type, exc_value, exc_traceback):
        # Ayrıntı kullanıcıya değil konsola yazılır; kullanıcı sade bir mesaj görür ve uygulama çalışmaya devam eder
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
        messagebox.showerror(self.t("app_name"), self.t("unexpected_error"), parent=self.root)