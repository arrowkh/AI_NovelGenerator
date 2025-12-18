# ui/hover_tooltip.py
# -*- coding: utf-8 -*-

from __future__ import annotations

import tkinter as tk


class HoverTooltip:
    """轻量级悬停提示。

    - 使用 Toplevel + overrideredirect 实现
    - 绑定 <Enter>/<Leave> 显示/隐藏
    """

    def __init__(self, widget: tk.Widget, text: str, wraplength: int = 360, delay_ms: int = 350):
        self.widget = widget
        self.text = text
        self.wraplength = wraplength
        self.delay_ms = delay_ms

        self._tooltip_window: tk.Toplevel | None = None
        self._after_id: str | None = None

        self.widget.bind("<Enter>", self._on_enter, add=True)
        self.widget.bind("<Leave>", self._on_leave, add=True)
        self.widget.bind("<ButtonPress>", self._on_leave, add=True)

    def _on_enter(self, _event=None):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

        self._after_id = self.widget.after(self.delay_ms, self.show)

    def _on_leave(self, _event=None):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

        self.hide()

    def show(self):
        if self._tooltip_window is not None or not self.text:
            return

        try:
            x = self.widget.winfo_rootx() + 18
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        except Exception:
            return

        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        try:
            tw.attributes("-topmost", True)
        except Exception:
            pass

        frame = tk.Frame(tw, bg="#111", bd=1, relief="solid")
        frame.pack(fill="both", expand=True)

        label = tk.Label(
            frame,
            text=self.text,
            justify="left",
            bg="#111",
            fg="#fff",
            padx=10,
            pady=8,
            wraplength=self.wraplength,
            font=("Microsoft YaHei", 10),
        )
        label.pack(fill="both", expand=True)

        self._tooltip_window = tw

    def hide(self):
        if self._tooltip_window is None:
            return

        try:
            self._tooltip_window.destroy()
        except Exception:
            pass
        finally:
            self._tooltip_window = None


def attach_hover_tooltip(widget: tk.Widget, text: str, wraplength: int = 360, delay_ms: int = 350) -> HoverTooltip:
    return HoverTooltip(widget=widget, text=text, wraplength=wraplength, delay_ms=delay_ms)
