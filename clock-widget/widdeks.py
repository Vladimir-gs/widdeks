import asyncio
import ctypes
import glob
import io
import json
import os
import shutil
import subprocess
import sys
import threading
import traceback
from ctypes import wintypes
from datetime import datetime

import tkinter as tk
from tkinter import colorchooser

import pystray
from PIL import Image, ImageChops, ImageDraw, ImageFont

try:
    from pycaw.pycaw import AudioUtilities
except Exception:
    AudioUtilities = None

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

APP_NAME = "Widdeks"


def resource_dir():
    """Carpeta de recursos de solo lectura (fuentes, iconos)."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    return os.path.dirname(os.path.abspath(__file__))


def data_dir():
    """Carpeta escribible de configuración y logs del usuario."""
    base = os.environ.get("LOCALAPPDATA") or os.path.join(
        os.path.expanduser("~"), "AppData", "Local"
    )
    path = os.path.join(base, APP_NAME)
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        return resource_dir()
    return path


BASE = resource_dir()
DATA = data_dir()
CLOCK_CFG = os.path.join(DATA, "clock_config.json")
PANEL_CFG = os.path.join(DATA, "panel_config.json")
FONT_DIR = os.path.join(BASE, "fonts")
LOG_PATH = os.path.join(DATA, "widget_error.log")


def migrate_config(name):
    """Copia configuraciones de instalaciones anteriores si aún no existen."""
    dest = os.path.join(DATA, name)
    if os.path.exists(dest):
        return
    local = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), name),
        os.path.join(local, "Programs", "Widdeks", name),
        os.path.join(local, "Programs", "RelojWidget", name),
    ]
    for src in candidates:
        try:
            if os.path.isfile(src) and os.path.abspath(src) != os.path.abspath(dest):
                shutil.copyfile(src, dest)
                return
        except Exception:
            pass

ULW_ALPHA = 0x2
BI_RGB = 0
DIB_RGB_COLORS = 0
WS_EX_LAYERED = 0x00080000
GWL_EXSTYLE = -20
SWP_NOSIZE = 0x1
SWP_NOMOVE = 0x2
SWP_NOZORDER = 0x4
SWP_NOACTIVATE = 0x10
SWP_FRAMECHANGED = 0x20

CREATE_NO_WINDOW = 0x08000000
VK_MEDIA_NEXT = 0xB0
VK_MEDIA_PREV = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_VOL_UP = 0xAF
VK_VOL_DOWN = 0xAE

WEIGHTS = ("Light", "Regular", "Medium", "SemiBold", "Bold")
WEEKDAYS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
MONTHS = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")

TEXT = (243, 243, 249, 255)
TEXT_DIM = (236, 236, 246, 165)
ACCENT = (128, 226, 150, 255)

PW = 300
PAD = 14
GAP = 10
CARD_W = PW - PAD * 2
TILE = 62
TILE_GAP = 8
GRID_H = TILE * 2 + TILE_GAP

_MUTEX = None


def acquire_single_instance():
    global _MUTEX
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    _MUTEX = kernel32.CreateMutexW(None, False, "Local\\WiddeksApp")
    return kernel32.GetLastError() != 183


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_ubyte),
        ("BlendFlags", ctypes.c_ubyte),
        ("SourceConstantAlpha", ctypes.c_ubyte),
        ("AlphaFormat", ctypes.c_ubyte),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class SIZE(ctypes.Structure):
    _fields_ = [("cx", wintypes.LONG), ("cy", wintypes.LONG)]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class SPS(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", ctypes.c_byte),
        ("BatteryFlag", ctypes.c_byte),
        ("BatteryLifePercent", ctypes.c_byte),
        ("Reserved1", ctypes.c_byte),
        ("BatteryLifeTime", ctypes.c_ulong),
        ("BatteryFullLifeTime", ctypes.c_ulong),
    ]


class SHFILEINFOW(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HICON),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.WCHAR * 260),
        ("szTypeName", wintypes.WCHAR * 80),
    ]


def log_error():
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(traceback.format_exc() + "\n")
    except Exception:
        pass


def win32():
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

    user32.GetParent.restype = ctypes.c_void_p
    user32.GetParent.argtypes = [ctypes.c_void_p]
    user32.GetWindow.restype = ctypes.c_void_p
    user32.FindWindowW.restype = ctypes.c_void_p
    user32.FindWindowExW.restype = ctypes.c_void_p
    user32.GetDC.restype = ctypes.c_void_p
    user32.GetDC.argtypes = [ctypes.c_void_p]
    user32.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.c_uint,
    ]
    user32.UpdateLayeredWindow.restype = wintypes.BOOL
    user32.UpdateLayeredWindow.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p,
        ctypes.POINTER(POINT), ctypes.POINTER(SIZE),
        ctypes.c_void_p, ctypes.POINTER(POINT), wintypes.DWORD,
        ctypes.POINTER(BLENDFUNCTION), wintypes.DWORD,
    ]
    for name in ("GetWindowLongPtrW", "SetWindowLongPtrW"):
        if hasattr(user32, name):
            getattr(user32, name).restype = ctypes.c_ssize_t

    gdi32.CreateCompatibleDC.restype = ctypes.c_void_p
    gdi32.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
    gdi32.CreateDIBSection.restype = ctypes.c_void_p
    gdi32.CreateDIBSection.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(BITMAPINFOHEADER), wintypes.UINT,
        ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p, wintypes.DWORD,
    ]
    gdi32.SelectObject.restype = ctypes.c_void_p
    gdi32.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
    gdi32.DeleteDC.argtypes = [ctypes.c_void_p]
    return user32, gdi32


def extract_icon(path, size=32):
    if not path or not os.path.isfile(path):
        return None
    shell32 = ctypes.windll.shell32
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    shfi = SHFILEINFOW()
    shell32.SHGetFileInfoW.restype = ctypes.c_void_p
    ok = shell32.SHGetFileInfoW(
        ctypes.c_wchar_p(path), 0, ctypes.byref(shfi), ctypes.sizeof(shfi), 0x100,
    )
    if not ok or not shfi.hIcon:
        return None
    hdc = user32.GetDC(None)
    mdc = gdi32.CreateCompatibleDC(hdc)
    hbmp = None
    try:
        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = size
        bmi.biHeight = -size
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = BI_RGB
        bits = ctypes.c_void_p()
        hbmp = gdi32.CreateDIBSection(mdc, ctypes.byref(bmi), DIB_RGB_COLORS, ctypes.byref(bits), None, 0)
        if not hbmp:
            return None
        old = gdi32.SelectObject(mdc, hbmp)
        user32.DrawIconEx(mdc, 0, 0, shfi.hIcon, size, size, 0, None, 3)
        buf = ctypes.string_at(bits, size * size * 4)
        gdi32.SelectObject(mdc, old)
        img = Image.frombuffer("RGBA", (size, size), buf, "raw", "BGRA", 0, 1).copy()
        if img.getchannel("A").getextrema()[1] == 0:
            return None
        return img
    finally:
        if hbmp:
            gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(mdc)
        user32.ReleaseDC(None, hdc)
        user32.DestroyIcon(shfi.hIcon)


def press_vk(vk):
    ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk, 0, 2, 0)


def glyph(size, draw_fn, color=TEXT, ss=4):
    big = Image.new("L", (size * ss, size * ss), 0)
    draw_fn(ImageDraw.Draw(big), size * ss)
    mask = big.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(Image.new("RGBA", (size, size), color), (0, 0), mask)
    return out


def icon_play(size=16):
    def f(d, s):
        d.polygon([(s * 0.30, s * 0.16), (s * 0.84, s * 0.5), (s * 0.30, s * 0.84)], fill=255)
    return glyph(size, f)


def icon_pause(size=16):
    def f(d, s):
        d.rectangle([s * 0.28, s * 0.18, s * 0.44, s * 0.82], fill=255)
        d.rectangle([s * 0.56, s * 0.18, s * 0.72, s * 0.82], fill=255)
    return glyph(size, f)


def icon_next(size=16):
    def f(d, s):
        d.polygon([(s * 0.18, s * 0.18), (s * 0.62, s * 0.5), (s * 0.18, s * 0.82)], fill=255)
        d.rectangle([s * 0.68, s * 0.18, s * 0.80, s * 0.82], fill=255)
    return glyph(size, f)


def icon_prev(size=16):
    def f(d, s):
        d.polygon([(s * 0.82, s * 0.18), (s * 0.38, s * 0.5), (s * 0.82, s * 0.82)], fill=255)
        d.rectangle([s * 0.20, s * 0.18, s * 0.32, s * 0.82], fill=255)
    return glyph(size, f)


def icon_volume(size=18):
    def f(d, s):
        d.polygon([(s * 0.12, s * 0.38), (s * 0.30, s * 0.38), (s * 0.50, s * 0.20),
                   (s * 0.50, s * 0.80), (s * 0.30, s * 0.62), (s * 0.12, s * 0.62)], fill=255)
        d.arc([s * 0.40, s * 0.28, s * 0.72, s * 0.72], start=-55, end=55, fill=255, width=max(1, int(s * 0.055)))
        d.arc([s * 0.40, s * 0.14, s * 0.92, s * 0.86], start=-55, end=55, fill=255, width=max(1, int(s * 0.055)))
    return glyph(size, f)


def icon_sun(size=18):
    def f(d, s):
        d.ellipse([s * 0.35, s * 0.35, s * 0.65, s * 0.65], fill=255)
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0), (-0.7, -0.7), (0.7, -0.7), (-0.7, 0.7), (0.7, 0.7)):
            x0 = s * 0.5 + dx * s * 0.36
            y0 = s * 0.5 + dy * s * 0.36
            x1 = s * 0.5 + dx * s * 0.47
            y1 = s * 0.5 + dy * s * 0.47
            d.line([x0, y0, x1, y1], fill=255, width=max(1, int(s * 0.07)))
    return glyph(size, f)


def icon_battery(size=20):
    def f(d, s):
        d.rounded_rectangle([s * 0.08, s * 0.28, s * 0.80, s * 0.72], radius=s * 0.10,
                            outline=255, width=max(1, int(s * 0.08)))
        d.rectangle([s * 0.82, s * 0.40, s * 0.90, s * 0.60], fill=255)
        d.rectangle([s * 0.16, s * 0.36, s * 0.52, s * 0.64], fill=255)
    return glyph(size, f)


def icon_note(size=20):
    def f(d, s):
        d.ellipse([s * 0.18, s * 0.62, s * 0.46, s * 0.88], fill=255)
        d.rectangle([s * 0.40, s * 0.18, s * 0.48, s * 0.76], fill=255)
        d.polygon([(s * 0.40, s * 0.18), (s * 0.80, s * 0.10), (s * 0.80, s * 0.30), (s * 0.40, s * 0.38)], fill=255)
    return glyph(size, f)


ICONS = {
    "play": icon_play(),
    "pause": icon_pause(),
    "next": icon_next(),
    "prev": icon_prev(),
    "volume": icon_volume(),
    "sun": icon_sun(),
    "battery": icon_battery(),
    "note": icon_note(),
}


def default_shortcuts():
    la = os.environ.get("LOCALAPPDATA", "")
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    discord = sorted(glob.glob(os.path.join(la, "Discord", "app-*", "Discord.exe")))
    items = [
        ("Chrome", os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe")),
        ("VS Code", os.path.join(la, "Programs", "Microsoft VS Code", "Code.exe")),
        ("Discord", discord[-1] if discord else ""),
        ("Explorador", r"C:\Windows\explorer.exe"),
        ("Terminal", os.path.join(la, "Microsoft", "WindowsApps", "wt.exe")),
        ("Ajustes", r"C:\Windows\ImmersiveControlPanel\SystemSettings.exe"),
        ("Calculadora", r"C:\Windows\System32\calc.exe"),
        ("Notas", r"C:\Windows\System32\notepad.exe"),
    ]
    out = []
    for name, target in items:
        if target:
            out.append({"name": name, "target": target, "icon": target})
    return out


CLOCK_DEFAULTS = {
    "x": None,
    "y": None,
    "size": 150,
    "weight": "Medium",
    "hour24": True,
    "seconds": False,
    "vertical": True,
    "color": "#ffffff",
}

PANEL_DEFAULTS = {
    "x": None,
    "y": 20,
    "shortcuts": None,
}


def load_config(path, defaults):
    cfg = dict(defaults)
    try:
        with open(path, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_config(path, cfg):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class MediaWatcher(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.lock = threading.Lock()
        self.state = {"title": "", "artist": "", "playing": False, "art": None, "app": ""}
        self._loop = None
        self._manager = None
        self._key = None

    def has_session(self):
        with self.lock:
            return bool(self.state.get("app"))

    def snapshot(self):
        with self.lock:
            return dict(self.state)

    def action(self, what):
        loop = self._loop
        if loop is None:
            return False
        asyncio.run_coroutine_threadsafe(self._run_action(what), loop)
        return True

    async def _run_action(self, what):
        try:
            session = self._manager.get_current_session()
            handled = False
            if session is not None:
                controls = session.get_playback_info().controls
                if what == "playpause":
                    handled = await session.try_toggle_play_pause_async()
                elif what == "next":
                    handled = controls.is_next_enabled and await session.try_skip_next_async()
                elif what == "prev":
                    handled = controls.is_previous_enabled and await session.try_skip_previous_async()
            if not handled:
                press_vk({
                    "playpause": VK_MEDIA_PLAY_PAUSE,
                    "next": VK_MEDIA_NEXT,
                    "prev": VK_MEDIA_PREV,
                }[what])
        except Exception:
            log_error()

    def run(self):
        try:
            asyncio.run(self._main())
        except Exception:
            log_error()

    async def _main(self):
        from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as Manager
        from winrt.windows.storage.streams import DataReader

        self._loop = asyncio.get_running_loop()
        self._manager = await Manager.request_async()

        while True:
            try:
                session = self._manager.get_current_session()
                if not session:
                    with self.lock:
                        self.state = {"title": "", "artist": "", "playing": False, "art": None, "app": ""}
                    self._key = None
                else:
                    info = await session.try_get_media_properties_async()
                    status = session.get_playback_info().playback_status
                    app = session.source_app_user_model_id or ""
                    key = (app, info.title, info.artist, info.album_title)
                    art = None
                    if key != self._key:
                        self._key = key
                        ref = info.thumbnail
                        if ref:
                            try:
                                stream = await ref.open_read_async()
                                size = stream.size
                                reader = DataReader(stream)
                                await reader.load_async(size)
                                buf = bytearray(size)
                                reader.read_bytes(buf)
                                art = Image.open(io.BytesIO(bytes(buf))).convert("RGBA")
                            except Exception:
                                art = None
                    else:
                        with self.lock:
                            art = self.state.get("art")
                    with self.lock:
                        self.state = {
                            "title": info.title or "",
                            "artist": info.artist or "",
                            "playing": status == 4,
                            "art": art,
                            "app": app,
                        }
            except Exception:
                log_error()
            await asyncio.sleep(1.0)


class Surface:
    def __init__(self, app, win, cfg_path, defaults):
        self.app = app
        self.win = win
        self.cfg_path = cfg_path
        self.cfg = load_config(cfg_path, defaults)
        self.defaults = defaults
        win.overrideredirect(True)
        win.configure(bg="#000000")
        win.attributes("-topmost", False)
        self._hwnd_val = None
        self._sw = None
        self.visible = True

    def save(self):
        save_config(self.cfg_path, self.cfg)

    def hwnd(self):
        if self._hwnd_val is None:
            wid = self.win.winfo_id()
            parent = self.app.user32.GetParent(ctypes.c_void_p(wid))
            self._hwnd_val = parent or wid
        return self._hwnd_val

    def make_layered(self):
        hwnd = ctypes.c_void_p(self.hwnd())
        get_ptr = getattr(self.app.user32, "GetWindowLongPtrW", None)
        set_ptr = getattr(self.app.user32, "SetWindowLongPtrW", None)
        if get_ptr and set_ptr:
            ex = get_ptr(hwnd, GWL_EXSTYLE)
            set_ptr(hwnd, GWL_EXSTYLE, ex | WS_EX_LAYERED)
        else:
            ex = self.app.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            self.app.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex | WS_EX_LAYERED)
        self.app.user32.SetWindowPos(
            hwnd, None, 0, 0, 0, 0,
            SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED,
        )

    def attach(self):
        user32 = self.app.user32
        progman = user32.FindWindowW("Progman", None)
        if not progman:
            return False
        if not user32.FindWindowExW(progman, None, "SHELLDLL_DefView", None):
            return False
        hwnd = ctypes.c_void_p(self.hwnd())
        WS_EX_TOPMOST = 0x8
        WS_EX_NOACTIVATE = 0x08000000
        get_ptr = getattr(user32, "GetWindowLongPtrW", None)
        set_ptr = getattr(user32, "SetWindowLongPtrW", None)
        if get_ptr and set_ptr:
            ex = get_ptr(hwnd, GWL_EXSTYLE)
            set_ptr(hwnd, GWL_EXSTYLE, (ex | WS_EX_NOACTIVATE) & ~WS_EX_TOPMOST)
        else:
            ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, (ex | WS_EX_NOACTIVATE) & ~WS_EX_TOPMOST)
        user32.SetWindowPos(hwnd, progman, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
        if user32.GetWindow(hwnd, 2) == progman:
            self._sw = (user32, hwnd, progman, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
            return True
        return False

    def assert_z(self):
        if self._sw:
            user32, hwnd, progman, flags = self._sw
            user32.SetWindowPos(hwnd, progman, 0, 0, 0, 0, flags)

    def paint(self, img):
        w, h = img.size
        a = img.getchannel("A")
        r, g, b = img.convert("RGB").split()
        premul = Image.merge("RGBA", (
            ImageChops.multiply(r, a),
            ImageChops.multiply(g, a),
            ImageChops.multiply(b, a),
            a,
        ))
        data = premul.tobytes("raw", "BGRA")
        hwnd = ctypes.c_void_p(self.hwnd())
        hdc_screen = self.app.user32.GetDC(None)
        hdc_mem = self.app.gdi32.CreateCompatibleDC(hdc_screen)
        hbmp = None
        try:
            bmi = BITMAPINFOHEADER()
            bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.biWidth = w
            bmi.biHeight = -h
            bmi.biPlanes = 1
            bmi.biBitCount = 32
            bmi.biCompression = BI_RGB
            bits = ctypes.c_void_p()
            hbmp = self.app.gdi32.CreateDIBSection(
                hdc_mem, ctypes.byref(bmi), DIB_RGB_COLORS, ctypes.byref(bits), None, 0,
            )
            if not hbmp:
                raise OSError("CreateDIBSection failed")
            ctypes.memmove(bits, data, len(data))
            old = self.app.gdi32.SelectObject(hdc_mem, hbmp)
            size_ = SIZE(w, h)
            src = POINT(0, 0)
            blend = BLENDFUNCTION(0, 0, 255, 1)
            ok = self.app.user32.UpdateLayeredWindow(
                hwnd, None, None, ctypes.byref(size_),
                hdc_mem, ctypes.byref(src), 0, ctypes.byref(blend), ULW_ALPHA,
            )
            self.app.gdi32.SelectObject(hdc_mem, old)
            if not ok:
                raise OSError(f"UpdateLayeredWindow failed: {ctypes.get_last_error()}")
        finally:
            if hbmp:
                self.app.gdi32.DeleteObject(hbmp)
            self.app.gdi32.DeleteDC(hdc_mem)
            self.app.user32.ReleaseDC(None, hdc_screen)

    def show(self):
        self.visible = True
        self.win.deiconify()
        self.assert_z()
        self.render(force=True)

    def hide(self):
        self.visible = False
        self.win.withdraw()

    def _menu_label(self, popup, text, cmd=None, header=False):
        lbl = tk.Label(
            popup, text=text, bg="#111111", fg="#8a8a8a" if header else "#e6e6e6",
            font=("Segoe UI", 10 if not header else 9), anchor="w",
            padx=16, pady=5, cursor=("" if (header or cmd is None) else "hand2"),
        )
        lbl.pack(fill="x")
        if header or cmd is None:
            return lbl

        def on_click(_e):
            try:
                cmd()
            finally:
                self.app.root.after(0, self.close_menu)

        lbl.bind("<Enter>", lambda _e: lbl.configure(bg="#2b2b2b"))
        lbl.bind("<Leave>", lambda _e: lbl.configure(bg="#111111"))
        lbl.bind("<Button-1>", on_click)
        return lbl

    def open_menu(self, event, items):
        self.close_menu()
        popup = tk.Toplevel(self.win)
        self._menu = popup
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg="#111111")
        popup.withdraw()
        for kind, payload in items:
            if kind == "sep":
                tk.Frame(popup, bg="#333333", height=1).pack(fill="x", padx=8, pady=4)
            elif kind == "header":
                self._menu_label(popup, payload, header=True)
            else:
                text, cmd, checked = payload
                prefix = "✓  " if checked else "   "
                self._menu_label(popup, prefix + text, cmd)
        popup.update_idletasks()
        w = popup.winfo_reqwidth()
        h = popup.winfo_reqheight()
        sw = popup.winfo_screenwidth()
        sh = popup.winfo_screenheight()
        x = max(0, min(event.x_root, sw - w - 4))
        y = max(0, min(event.y_root, sh - h - 4))
        popup.geometry(f"+{x}+{y}")
        popup.deiconify()
        popup.bind("<Escape>", lambda _e: self.close_menu())
        popup.bind("<FocusOut>", lambda _e: popup.after(80, self._check_focus, popup))
        popup.after(30, lambda: popup.focus_force())

    def _check_focus(self, popup):
        try:
            if getattr(self, "_menu", None) is popup and not popup.focus_get():
                self.close_menu()
        except Exception:
            pass

    def close_menu(self):
        m = getattr(self, "_menu", None)
        if m is not None:
            self._menu = None
            try:
                m.destroy()
            except Exception:
                pass


class ClockSurface(Surface):
    PAD_X = 48
    PAD_Y = 36
    GRIP = 28

    def __init__(self, app, win):
        super().__init__(app, win, CLOCK_CFG, CLOCK_DEFAULTS)
        self._drag = None
        self._resize = None
        self._pil_fonts = {}
        self._sig = None

        self.grip = tk.Label(self.win, bg="#000000", cursor="size_nw_se")
        self.grip.place(relx=1.0, rely=1.0, anchor="se", width=self.GRIP, height=self.GRIP)

        self.win.bind("<ButtonPress-1>", self._on_press)
        self.win.bind("<B1-Motion>", self._on_drag)
        self.grip.bind("<ButtonPress-1>", self._on_grip_press)
        self.grip.bind("<B1-Motion>", self._on_grip_drag)
        self.grip.bind("<ButtonRelease-1>", self._on_release)
        self.win.bind("<ButtonRelease-1>", self._on_release)
        self.win.bind("<Button-3>", self._on_menu)
        self.grip.bind("<Button-3>", self._on_menu)
        self.win.bind("<Control-MouseWheel>", self._on_wheel)
        self.grip.bind("<Control-MouseWheel>", self._on_wheel)

        self._place_window()
        self.win.update_idletasks()
        self.make_layered()
        self.attach()
        self.render()

    def _place_window(self):
        sw = self.win.winfo_screenwidth()
        x = self.cfg["x"] if self.cfg["x"] is not None else sw - 420
        y = self.cfg["y"] if self.cfg["y"] is not None else 120
        self.win.geometry(f"+{x}+{y}")

    def _time_strings(self):
        now = datetime.now()
        if self.cfg["hour24"]:
            return now.strftime("%H"), now.strftime("%M"), now.strftime("%S"), ""
        return now.strftime("%I").lstrip("0"), now.strftime("%M"), now.strftime("%S"), now.strftime("%p")

    def _pil_font(self, px):
        key = (self.cfg["weight"], px)
        f = self._pil_fonts.get(key)
        if f is None:
            path = os.path.join(FONT_DIR, f"Poppins-{self.cfg['weight']}.ttf")
            f = ImageFont.truetype(path, px)
            self._pil_fonts[key] = f
        return f

    def _compose(self):
        cfg = self.cfg
        size = max(10, int(cfg["size"]))
        hh, mm, ss, ampm = self._time_strings()
        color = cfg["color"]
        f = self._pil_font(size)
        sub = ss if cfg["seconds"] else ""
        if ampm:
            sub = f"{sub} {ampm}".strip()
        fs = max(10, int(size * 0.22))
        f_s = self._pil_font(fs) if sub else None

        def ink_w(font, text):
            b = font.getbbox(text)
            return b[2] - b[0]

        def draw_line(d, text, font, top, total_w):
            b = font.getbbox(text)
            tw = b[2] - b[0]
            th = b[3] - b[1]
            d.text(((total_w - tw) / 2, top), text, font=font, fill=color, anchor="lt")
            return th

        if cfg["vertical"]:
            gap = max(4, int(size * 0.04))
            pad = max(10, int(size * 0.09))
            b_h = f.getbbox(hh)
            b_m = f.getbbox(mm)
            hh_h = b_h[3] - b_h[1]
            mm_h = b_m[3] - b_m[1]
            sub_h = 0
            if sub:
                b_s = f_s.getbbox(sub)
                sub_h = b_s[3] - b_s[1]
            w = max(ink_w(f, hh), ink_w(f, mm)) + self.PAD_X * 2
            if sub:
                w = max(w, ink_w(f_s, sub) + self.PAD_X * 2)
            total_h = pad + hh_h + gap + mm_h + pad
            if sub:
                total_h += max(4, int(fs * 0.5)) + sub_h
            img = Image.new("RGBA", (int(w), int(total_h)), (0, 0, 0, 1))
            d = ImageDraw.Draw(img)
            y = pad
            y += draw_line(d, hh, f, y, w) + gap
            y += draw_line(d, mm, f, y, w)
            if sub:
                y += max(4, int(fs * 0.5))
                draw_line(d, sub, f_s, y, w)
        else:
            text = f"{hh}:{mm}"
            b = f.getbbox(text)
            tw = b[2] - b[0]
            th = b[3] - b[1]
            sub_gap = max(4, int(fs * 0.35))
            sub_h = 0
            w = tw + self.PAD_X * 2
            if sub:
                b_s = f_s.getbbox(sub)
                sub_h = b_s[3] - b_s[1]
                w = max(w, (b_s[2] - b_s[0]) + self.PAD_X * 2)
            total_h = th + self.PAD_Y * 2 + (sub_gap + sub_h if sub else 0)
            img = Image.new("RGBA", (int(w), int(total_h)), (0, 0, 0, 1))
            d = ImageDraw.Draw(img)
            d.text(((w - tw) / 2, self.PAD_Y), text, font=f, fill=color, anchor="lt")
            if sub:
                draw_line(d, sub, f_s, self.PAD_Y + th + sub_gap, w)
        return img

    def _sig_value(self):
        cfg = self.cfg
        hh, mm, ss, ampm = self._time_strings()
        if not cfg["seconds"]:
            ss = ""
        return (hh, mm, ss, ampm, cfg["size"], cfg["weight"], cfg["color"],
                cfg["vertical"], cfg["seconds"], cfg["hour24"])

    def render(self, force=False):
        if not self.visible:
            return
        sig = self._sig_value()
        if not force and sig == self._sig:
            self.assert_z()
            return
        try:
            img = self._compose()
            w, h = img.size
            self.win.geometry(f"{w}x{h}")
            self.win.update_idletasks()
            self.paint(img)
            self._sig = sig
        except Exception:
            log_error()
        self.assert_z()

    def _on_press(self, event):
        self.close_menu()
        self._drag = (event.x_root - self.win.winfo_x(), event.y_root - self.win.winfo_y())

    def _on_drag(self, event):
        if self._drag:
            self.win.geometry(f"+{event.x_root - self._drag[0]}+{event.y_root - self._drag[1]}")

    def _on_grip_press(self, event):
        self._resize = (event.y_root, self.cfg["size"])

    def _on_grip_drag(self, event):
        if self._resize:
            start_y, start_size = self._resize
            new = max(24, min(400, start_size + (event.y_root - start_y)))
            if new != self.cfg["size"]:
                self.cfg["size"] = new
                self.render()

    def _on_release(self, _event):
        if self._drag or self._resize:
            self.cfg["x"] = self.win.winfo_x()
            self.cfg["y"] = self.win.winfo_y()
            self.save()
        self._drag = None
        self._resize = None

    def _on_wheel(self, event):
        delta = 1 if event.delta > 0 else -1
        new = max(24, min(400, self.cfg["size"] + delta * 6))
        if new != self.cfg["size"]:
            self._set(size=new)

    def _on_menu(self, event):
        cfg = self.cfg
        items = [
            ("header", "Formato"),
            ("item", ("24 horas", lambda: self._set(hour24=True), cfg["hour24"])),
            ("item", ("12 horas", lambda: self._set(hour24=False), not cfg["hour24"])),
            ("sep", None),
            ("item", ("Vertical (apilado)", lambda: self._set(vertical=True), cfg["vertical"])),
            ("item", ("Horizontal", lambda: self._set(vertical=False), not cfg["vertical"])),
            ("sep", None),
            ("item", ("Segundos", lambda: self._set(seconds=not cfg["seconds"]), cfg["seconds"])),
            ("item", ("Color del texto…", self._pick_color, False)),
            ("sep", None),
            ("header", "Grosor de fuente"),
        ]
        for weight in WEIGHTS:
            items.append(("item", (weight, lambda w=weight: self._set(weight=w), cfg["weight"] == weight)))
        items += [
            ("sep", None),
            ("item", ("Agrandar  +", lambda: self._resize_by(12), False)),
            ("item", ("Reducir  −", lambda: self._resize_by(-12), False)),
            ("item", ("Tamaño normal", lambda: self._set(size=150), False)),
            ("sep", None),
            ("item", ("Ocultar reloj", self.hide, False)),
            ("item", ("Salir", self.app.quit, False)),
        ]
        try:
            self.open_menu(event, items)
        except Exception:
            log_error()
            self.close_menu()

    def _pick_color(self):
        self.close_menu()
        try:
            _rgb, hexval = colorchooser.askcolor(
                color=self.cfg["color"], title="Color del texto", parent=self.win,
            )
        except Exception:
            log_error()
            return
        if hexval:
            self.cfg["color"] = hexval
            self.save()
            self.render()

    def _set(self, **kwargs):
        self.cfg.update(kwargs)
        self.cfg["x"] = self.win.winfo_x()
        self.cfg["y"] = self.win.winfo_y()
        self.save()
        self.render()

    def _resize_by(self, delta):
        new = max(24, min(400, self.cfg["size"] + delta))
        self._set(size=new)


class PanelSurface(Surface):
    def __init__(self, app, win):
        super().__init__(app, win, PANEL_CFG, PANEL_DEFAULTS)
        self._menu = None
        self._drag = None
        self._press = None
        self._hover = None
        self._masks = {}
        self._bg = None
        self._fonts = {}
        self._app_icons = {}
        self._vol_ep = None
        self._vol = None
        self._brightness = None
        self._bright_busy = False
        self._bright_poll_busy = False
        self._ticks = 0
        self._hit = []
        self._sig = None

        if not self.cfg.get("shortcuts"):
            self.cfg["shortcuts"] = default_shortcuts()
            self.save()

        self._build_geometry()
        self._build_background()
        self._place_window()
        self._init_volume()

        self.win.bind("<ButtonPress-1>", self._on_press)
        self.win.bind("<B1-Motion>", self._on_motion_drag)
        self.win.bind("<ButtonRelease-1>", self._on_release)
        self.win.bind("<Motion>", self._on_hover)
        self.win.bind("<Button-3>", self._on_menu)
        self.win.bind("<Leave>", self._on_leave)

        self.win.update_idletasks()
        self.make_layered()
        self.attach()
        self.win.geometry(f"{PW}x{self.H}")
        self.render()
        threading.Thread(target=self._read_brightness, daemon=True).start()

    def _init_volume(self):
        try:
            if AudioUtilities:
                self._vol_ep = AudioUtilities.GetSpeakers().EndpointVolume
                self._vol = round(self._vol_ep.GetMasterVolumeLevelScalar() * 100)
        except Exception:
            self._vol_ep = None

    def _build_geometry(self):
        y = PAD
        self.tiles = []
        for row in range(2):
            for col in range(4):
                x = PAD + col * (TILE + TILE_GAP)
                ty = y + row * (TILE + TILE_GAP)
                self.tiles.append((x, ty, x + TILE, ty + TILE))
        y += GRID_H + GAP
        self.clock_box = (PAD, y, PAD + CARD_W, y + 112)
        y += 112 + GAP
        self.media_box = (PAD, y, PAD + CARD_W, y + 100)
        y += 100 + GAP
        self.vb_box = (PAD, y, PAD + CARD_W, y + 116)
        y += 116 + GAP
        self.bat_box = (PAD, y, PAD + CARD_W, y + 92)
        y += 92 + PAD
        self.H = y

        mx0, my0, mx1, my1 = self.media_box
        by = my0 + 60
        self.media_buttons = []
        for i, ident in enumerate(("prev", "play", "next")):
            bx = mx0 + 92 + i * 30
            self.media_buttons.append((bx, by, bx + 24, by + 24, ident))

        vx0, vy0, vx1, vy1 = self.vb_box
        self.vb_buttons = []
        for row in range(2):
            ry = vy0 + 12 + row * 50
            minus = (vx1 - 14 - 28 - 28 - 6, ry + 7, vx1 - 14 - 28 - 6, ry + 35)
            plus = (vx1 - 14 - 28, ry + 7, vx1 - 14, ry + 35)
            prefix = "vol" if row == 0 else "br"
            self.vb_buttons.append((minus[0], minus[1], minus[2], minus[3], prefix + "-"))
            self.vb_buttons.append((plus[0], plus[1], plus[2], plus[3], prefix + "+"))

    def _build_background(self):
        img = Image.new("RGBA", (PW, self.H), (0, 0, 0, 1))
        for box in (self.clock_box, self.media_box, self.vb_box, self.bat_box):
            self._paste_round(img, box, (14, 14, 20, 118), 20)
            self._paste_outline(img, box, (255, 255, 255, 26), 20)
        for box in self.tiles:
            self._paste_round(img, box, (255, 255, 255, 30), 16)
            self._paste_outline(img, box, (255, 255, 255, 22), 16)
        self._bg = img

    def _round_mask(self, w, h, r):
        key = ("m", w, h, r)
        m = self._masks.get(key)
        if m is None:
            ss = 4
            big = Image.new("L", (w * ss, h * ss), 0)
            ImageDraw.Draw(big).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=r * ss, fill=255)
            m = big.resize((w, h), Image.LANCZOS)
            self._masks[key] = m
        return m

    def _outline_mask(self, w, h, r):
        key = ("o", w, h, r)
        m = self._masks.get(key)
        if m is None:
            ss = 4
            big = Image.new("L", (w * ss, h * ss), 0)
            ImageDraw.Draw(big).rounded_rectangle(
                [0, 0, w * ss - 1, h * ss - 1], radius=r * ss, outline=255, width=ss,
            )
            m = big.resize((w, h), Image.LANCZOS)
            self._masks[key] = m
        return m

    def _paste_round(self, img, box, fill, r):
        x0, y0, x1, y1 = box
        w, h = x1 - x0, y1 - y0
        img.paste(Image.new("RGBA", (w, h), fill), (x0, y0), self._round_mask(w, h, r))

    def _paste_outline(self, img, box, color, r):
        x0, y0, x1, y1 = box
        w, h = x1 - x0, y1 - y0
        img.paste(Image.new("RGBA", (w, h), color), (x0, y0), self._outline_mask(w, h, r))

    def _font(self, name, px):
        key = (name, px)
        f = self._fonts.get(key)
        if f is None:
            f = ImageFont.truetype(os.path.join(FONT_DIR, f"Poppins-{name}.ttf"), px)
            self._fonts[key] = f
        return f

    def _ellipsize(self, text, font, maxw):
        if font.getlength(text) <= maxw:
            return text
        while text and font.getlength(text + "…") > maxw:
            text = text[:-1]
        return text + "…"

    def _app_icon(self, sc):
        key = sc.get("icon") or sc.get("target")
        if key in self._app_icons:
            return self._app_icons[key]
        img = extract_icon(sc.get("icon") or sc.get("target"))
        self._app_icons[key] = img
        return img

    def _battery(self):
        s = SPS()
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s)):
            return None, None
        pct = None if s.BatteryLifePercent == 255 else s.BatteryLifePercent
        return pct, s.ACLineStatus

    def _compose(self):
        hit = []
        now = datetime.now()
        img = self._bg.copy()
        d = ImageDraw.Draw(img)

        for i, box in enumerate(self.tiles):
            if self._hover == f"tile:{i}":
                self._paste_round(img, box, (255, 255, 255, 52), 16)
                d = ImageDraw.Draw(img)
            sc = self.cfg["shortcuts"][i] if i < len(self.cfg["shortcuts"]) else None
            if not sc:
                continue
            icon = self._app_icon(sc)
            cx = (box[0] + box[2]) // 2
            cy = (box[1] + box[3]) // 2
            if icon is not None:
                icon = icon.resize((32, 32), Image.LANCZOS)
                img.alpha_composite(icon, (cx - 16, cy - 16))
            else:
                f = self._font("SemiBold", 20)
                letter = (sc.get("name") or "?")[:1].upper()
                d.text((cx, cy), letter, font=f, fill=TEXT, anchor="mm")
            hit.append((*box, f"tile:{i}", "shortcut"))

        x0, y0, x1, y1 = self.clock_box
        f_time = self._font("SemiBold", 40)
        f_date = self._font("Regular", 12)
        d.text((x0 + 18, y0 + 20), now.strftime("%H:%M"), font=f_time, fill=TEXT, anchor="lt")
        date = f"{WEEKDAYS[now.weekday()]}, {now.day} {MONTHS[now.month - 1]}"
        d.text((x0 + 18, y0 + 78), date, font=f_date, fill=TEXT_DIM, anchor="lt")

        x0, y0, x1, y1 = self.media_box
        state = self.app.media.snapshot()
        art_box = (x0 + 14, y0 + 14, x0 + 78, y0 + 78)
        if state["art"] is not None:
            art = state["art"].resize((64, 64), Image.LANCZOS)
            mask = self._round_mask(64, 64, 14)
            img.paste(art, (art_box[0], art_box[1]), mask)
        else:
            self._paste_round(img, art_box, (255, 255, 255, 18), 14)
            img.alpha_composite(ICONS["note"], (art_box[0] + 22, art_box[1] + 22))
            d = ImageDraw.Draw(img)
        f_title = self._font("Medium", 12)
        f_sub = self._font("Regular", 10)
        title = self._ellipsize(state["title"] or "Sin reproducción", f_title, 150)
        sub = self._ellipsize(state["artist"] or ("Control multimedia" if not state["app"] else ""), f_sub, 150)
        d.text((x0 + 92, y0 + 20), title, font=f_title, fill=TEXT, anchor="lt")
        if sub:
            d.text((x0 + 92, y0 + 40), sub, font=f_sub, fill=TEXT_DIM, anchor="lt")

        for bx0, by0, bx1, by1, ident in self.media_buttons:
            is_play = ident == "play"
            key = "pause" if (is_play and state["playing"]) else ("play" if is_play else ident)
            hovered = self._hover == f"mb:{ident}"
            if hovered:
                self._paste_round(img, (bx0, by0, bx1, by1), (255, 255, 255, 38), 10)
                d = ImageDraw.Draw(img)
            img.alpha_composite(ICONS[key], (bx0 + 4, by0 + 4))
            d = ImageDraw.Draw(img)
            hit.append((bx0, by0, bx1, by1, f"mb:{ident}", "media"))

        x0, y0, x1, y1 = self.vb_box
        f_lbl = self._font("Medium", 11)
        f_val = self._font("Regular", 10)
        rows = (("volume", "Volumen", self._vol), ("sun", "Brillo", self._brightness))
        for row, (icon_key, label, value) in enumerate(rows):
            ry = y0 + 12 + row * 50
            img.alpha_composite(ICONS[icon_key], (x0 + 16, ry + 12))
            d = ImageDraw.Draw(img)
            d.text((x0 + 44, ry + 8), label, font=f_lbl, fill=TEXT, anchor="lt")
            val = "--" if value is None else f"{value}%"
            d.text((x0 + 44, ry + 24), val, font=f_val, fill=TEXT_DIM, anchor="lt")

        f_btn = self._font("Medium", 15)
        for bx0, by0, bx1, by1, ident in self.vb_buttons:
            hovered = self._hover == f"vb:{ident}"
            self._paste_round(img, (bx0, by0, bx1, by1), (255, 255, 255, 40 if hovered else 24), 9)
            d = ImageDraw.Draw(img)
            d.text(((bx0 + bx1) / 2, (by0 + by1) / 2), "−" if ident.endswith("-") else "+",
                   font=f_btn, fill=TEXT, anchor="mm")
            hit.append((bx0, by0, bx1, by1, f"vb:{ident}", "vb"))

        x0, y0, x1, y1 = self.bat_box
        pct, ac = self._battery()
        img.alpha_composite(ICONS["battery"], (x0 + 16, y0 + 22))
        d = ImageDraw.Draw(img)
        f_lbl = self._font("Medium", 11)
        f_sub = self._font("Regular", 10)
        f_pct = self._font("SemiBold", 26)
        d.text((x0 + 44, y0 + 22), "Batería", font=f_lbl, fill=TEXT, anchor="lt")
        if pct is None:
            status = "Sin batería"
        elif ac == 1:
            status = "Cargando" if pct < 100 else "Conectado"
        else:
            status = "En batería"
        d.text((x0 + 44, y0 + 40), status, font=f_sub, fill=TEXT_DIM, anchor="lt")
        pct_txt = "--" if pct is None else f"{pct}%"
        d.text((x1 - 16, (y0 + y1) // 2), pct_txt, font=f_pct, fill=ACCENT, anchor="rm")
        return img, hit

    def _sig_value(self):
        now = datetime.now()
        st = self.app.media.snapshot()
        pct, ac = self._battery()
        return (now.strftime("%H:%M"), now.year, now.month, now.day,
                st["title"], st["artist"], st["playing"], st["app"], id(st["art"]),
                self._vol, self._brightness, pct, ac, self._hover,
                len(self.cfg["shortcuts"]))

    def render(self, force=False):
        if not self.visible:
            return
        sig = self._sig_value()
        if not force and sig == self._sig:
            self.assert_z()
            return
        try:
            img, hit = self._compose()
            self._hit = hit
            self.paint(img)
            self._sig = sig
        except Exception:
            log_error()
        self.assert_z()

    def tick(self):
        self._refresh_volume()
        self._ticks += 1
        if self._ticks % 10 == 0 and not self._bright_poll_busy:
            self._bright_poll_busy = True

            def poll():
                try:
                    self._read_brightness()
                finally:
                    self._bright_poll_busy = False

            threading.Thread(target=poll, daemon=True).start()
        self.render()

    def _refresh_volume(self):
        if self._vol_ep is None:
            return
        try:
            value = round(self._vol_ep.GetMasterVolumeLevelScalar() * 100)
            if value != self._vol:
                self._vol = value
        except Exception:
            self._vol_ep = None

    def _hit_at(self, x, y):
        for hx0, hy0, hx1, hy1, ident, kind in reversed(self._hit):
            if hx0 <= x <= hx1 and hy0 <= y <= hy1:
                return ident, kind
        return None

    def _on_press(self, event):
        self.close_menu()
        hit = self._hit_at(event.x, event.y)
        self._press = None
        self._drag = None
        if hit:
            self._press = (hit[0], hit[1], event.x, event.y)
        else:
            self._drag = (event.x_root - self.win.winfo_x(), event.y_root - self.win.winfo_y())

    def _on_motion_drag(self, event):
        if self._drag:
            self.win.geometry(f"+{event.x_root - self._drag[0]}+{event.y_root - self._drag[1]}")

    def _on_release(self, event):
        if self._press:
            ident, kind, px, py = self._press
            cur = self._hit_at(event.x, event.y)
            if cur and cur[0] == ident and abs(event.x - px) < 6 and abs(event.y - py) < 6:
                self._do(ident, kind)
            self._press = None
        if self._drag:
            self.cfg["x"] = self.win.winfo_x()
            self.cfg["y"] = self.win.winfo_y()
            self.save()
            self._drag = None

    def _do(self, ident, kind):
        try:
            if kind == "shortcut":
                self._act_shortcut(int(ident.split(":")[1]))
            elif kind == "media":
                what = ident.split(":")[1]
                self._act_media("playpause" if what == "play" else what)
            elif kind == "vb":
                code = ident.split(":")[1]
                prefix, sign = code[:-1], code[-1]
                delta = 5 if sign == "+" else -5
                if prefix == "vol":
                    self._act_vol(delta)
                else:
                    self._act_bright(delta)
        except Exception:
            log_error()

    def _act_shortcut(self, index):
        shortcuts = self.cfg.get("shortcuts") or []
        if index >= len(shortcuts):
            return
        sc = shortcuts[index]
        target = sc.get("target") or ""
        args = sc.get("args") or []
        if isinstance(args, str):
            args = [args]
        if target.lower().endswith(".exe") and os.path.isfile(target):
            subprocess.Popen([target, *args], close_fds=True)
        else:
            os.startfile(target)

    def _act_media(self, what):
        if not self.app.media.action(what):
            press_vk({"playpause": VK_MEDIA_PLAY_PAUSE, "next": VK_MEDIA_NEXT, "prev": VK_MEDIA_PREV}[what])

    def _act_vol(self, delta):
        if self._vol_ep is not None:
            cur = self._vol_ep.GetMasterVolumeLevelScalar()
            self._vol_ep.SetMasterVolumeLevelScalar(max(0.0, min(1.0, cur + delta / 100.0)), None)
            self._vol = round(self._vol_ep.GetMasterVolumeLevelScalar() * 100)
            self.render()
        else:
            press_vk(VK_VOL_UP if delta > 0 else VK_VOL_DOWN)

    def _ps(self, script):
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, text=True, timeout=15, creationflags=CREATE_NO_WINDOW,
        )
        if result.returncode != 0 or result.stderr.strip():
            raise RuntimeError(result.stderr.strip()[:400] or f"exit {result.returncode}")
        return result.stdout

    def _read_brightness(self):
        try:
            out = self._ps("(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness")
            value = int(out.strip().splitlines()[0])
            self._brightness = max(0, min(100, value))
        except Exception:
            pass

    def _act_bright(self, delta):
        if self._bright_busy:
            return
        base = self._brightness if self._brightness is not None else 50
        target = max(0, min(100, base + delta))
        self._bright_busy = True

        def worker():
            try:
                script = ("$m=Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods;"
                          f"$m.WmiSetBrightness(1,[byte]{target})")
                self._ps(script)
                self._brightness = target
            except Exception:
                log_error()
            finally:
                self._bright_busy = False

        threading.Thread(target=worker, daemon=True).start()

    def _on_hover(self, event):
        hit = self._hit_at(event.x, event.y)
        ident = hit[0] if hit else None
        if ident != self._hover:
            self._hover = ident
            try:
                self.win.configure(cursor="hand2" if hit else "")
            except Exception:
                pass
            self.render()

    def _on_leave(self, _event):
        if self._hover is not None:
            self._hover = None
            self.render()

    def _place_window(self):
        sw = self.win.winfo_screenwidth()
        x = self.cfg["x"] if self.cfg["x"] is not None else sw - PW - 20
        y = self.cfg["y"] if self.cfg["y"] is not None else 20
        self.win.geometry(f"+{x}+{y}")

    def _on_menu(self, event):
        items = [
            ("item", ("Ocultar panel", self.hide, False)),
            ("item", ("Salir", self.app.quit, False)),
        ]
        try:
            self.open_menu(event, items)
        except Exception:
            log_error()
            self.close_menu()


class WiddeksApp:
    def __init__(self):
        self.user32, self.gdi32 = win32()
        self.root = tk.Tk()
        self.root.withdraw()
        self._icon = None
        self.media = MediaWatcher()
        self.media.start()

        self.clock = ClockSurface(self, tk.Toplevel(self.root))
        self.panel = PanelSurface(self, tk.Toplevel(self.root))

        self._start_tray()
        self._clock_tick()
        self._panel_tick()

    def _start_tray(self):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([5, 5, 59, 59], radius=14, fill=(34, 34, 40, 255),
                            outline=(255, 255, 255, 190), width=2)
        d.ellipse([16, 16, 34, 34], fill=(230, 230, 236, 255))
        d.ellipse([20, 20, 30, 30], fill=(34, 34, 40, 255))
        d.rounded_rectangle([38, 42, 48, 52], radius=2, fill=(230, 230, 236, 255))
        menu = pystray.Menu(
            pystray.MenuItem("Mostrar/Ocultar reloj", self._tray_clock, default=True),
            pystray.MenuItem("Mostrar/Ocultar panel", self._tray_panel),
            pystray.MenuItem("Salir", self._tray_quit),
        )
        self._icon = pystray.Icon("Widdeks", img, "Widdeks", menu)
        threading.Thread(target=self._icon.run, daemon=True).start()

    def _tray_clock(self, icon=None, item=None):
        self.root.after(0, self._toggle_clock)

    def _tray_panel(self, icon=None, item=None):
        self.root.after(0, self._toggle_panel)

    def _tray_quit(self, icon=None, item=None):
        self.root.after(0, self.quit)

    def _toggle_clock(self):
        if self.clock.visible:
            self.clock.hide()
        else:
            self.clock.show()

    def _toggle_panel(self):
        if self.panel.visible:
            self.panel.hide()
        else:
            self.panel.show()

    def _clock_tick(self):
        try:
            self.clock.render()
        except Exception:
            log_error()
        self.root.after(200 if self.clock.cfg["seconds"] else 1000, self._clock_tick)

    def _panel_tick(self):
        try:
            self.panel.tick()
        except Exception:
            log_error()
        self.root.after(1000, self._panel_tick)

    def quit(self):
        for surface in (self.clock, self.panel):
            surface.cfg["x"] = surface.win.winfo_x()
            surface.cfg["y"] = surface.win.winfo_y()
            surface.save()
        if self._icon:
            self._icon.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    if not acquire_single_instance():
        sys.exit(0)
    migrate_config("clock_config.json")
    migrate_config("panel_config.json")
    WiddeksApp().run()
