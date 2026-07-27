import tkinter as _tk

_root = None


def _get_root():
    global _root
    if _root is None:
        _root = _tk.Tk()
        _root.withdraw()
    return _root


def clipboard_get():
    try:
        return _get_root().clipboard_get()
    except _tk.TclError:
        return ""


def clipboard_set(text):
    r = _get_root()
    r.clipboard_clear()
    r.clipboard_append(text)
