"""Uygulamanın giriş noktası."""
import ctypes
import tkinter as tk

from gui import ConverterApp


def create_root():
    """Sürükle-bırak destekli pencere; tkinterdnd2 yoksa ya da yüklenemezse normal pencere."""
    try:
        from tkinterdnd2 import TkinterDnD
        return TkinterDnD.Tk()
    except (ImportError, RuntimeError, tk.TclError):
        return tk.Tk()


def main():
    # Yüksek çözünürlüklü ekranlarda yazılar bulanık olmasın (sadece Windows)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    root = create_root()
    ConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()