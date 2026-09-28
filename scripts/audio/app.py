"""Yomineko Audio control app: start / stop the TTS generator, watch progress. Single file, tkinter.

The generator runs as a separate process in the TTS venv, so closing this window does NOT stop it;
Stop writes <store>/STOP and the generator exits after the batch in flight (seconds). Progress comes
from <store>/status.json, which the generator rewrites after every batch.
"""
from __future__ import annotations

import ctypes
import datetime as dt
import json
import os
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import ttk

HERE = Path(__file__).resolve().parent
AUDIO_ROOT = Path(os.environ.get("YOMINEKO_AUDIO_ROOT", Path.home() / "yomineko-audio"))
STORE = Path(os.environ.get("YOMINEKO_AUDIO_STORE", AUDIO_ROOT / "store"))
SCRIPTS = HERE if (HERE / "generate.py").exists() else Path(
    os.environ.get("YOMINEKO_SCRIPTS", r"C:\Users\WiseWolf\IdeaProjects\code\yomineko-research\scripts\audio"))
PYTHON = AUDIO_ROOT / ".venv" / "Scripts" / "python.exe"
TIERS = ("n5", "n4", "speak", "n3")


def pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    h = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = ctypes.c_ulong()
    ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
    ctypes.windll.kernel32.CloseHandle(h)
    return code.value == 259  # STILL_ACTIVE


def read_status() -> dict:
    try:
        return json.loads((STORE / "status.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def fmt_eta(s) -> str:
    if s is None:
        return "-"
    return str(dt.timedelta(seconds=int(s)))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Yomineko Audio")
        self.geometry("720x480")
        ico = HERE / "yomineko_audio.ico"
        if ico.exists():
            self.iconbitmap(str(ico))
        self.child: subprocess.Popen | None = None
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="Tier:").pack(side="left")
        self.tier = tk.StringVar(value="n5")
        ttk.Combobox(top, textvariable=self.tier, values=TIERS, width=8, state="readonly").pack(side="left", padx=6)
        self.start_btn = ttk.Button(top, text="Start", command=self.start)
        self.start_btn.pack(side="left", padx=6)
        self.stop_btn = ttk.Button(top, text="Stop", command=self.stop)
        self.stop_btn.pack(side="left")
        self.state_lbl = ttk.Label(top, text="", width=40)
        self.state_lbl.pack(side="left", padx=12)
        mid = ttk.Frame(self, padding=(10, 0))
        mid.pack(fill="x")
        self.bar = ttk.Progressbar(mid, maximum=1, length=680)
        self.bar.pack(fill="x", pady=4)
        self.counts = ttk.Label(mid, text="", font=("Segoe UI", 11))
        self.counts.pack(anchor="w")
        self.logbox = tk.Text(self, height=18, wrap="none", font=("Consolas", 9))
        self.logbox.pack(fill="both", expand=True, padx=10, pady=8)
        self.after(200, self.poll)

    def running(self, st: dict) -> bool:
        if self.child is not None and self.child.poll() is None:
            return True
        return st.get("state") == "running" and pid_alive(st.get("pid"))

    def start(self):
        if self.running(read_status()):
            return
        (STORE / "STOP").unlink(missing_ok=True)
        (AUDIO_ROOT / "logs").mkdir(exist_ok=True)
        out = open(AUDIO_ROOT / "logs" / "generate_stdout.log", "a", encoding="utf-8")
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        self.child = subprocess.Popen([str(PYTHON), str(SCRIPTS / "generate.py"), "--tier", self.tier.get()],
                                      cwd=str(AUDIO_ROOT), stdout=out, stderr=subprocess.STDOUT, creationflags=flags,
                                      env=env)

    def stop(self):
        STORE.mkdir(parents=True, exist_ok=True)
        (STORE / "STOP").write_text("stop requested from the app\n", encoding="utf-8")

    def poll(self):
        st = read_status()
        run = self.running(st)
        stopping = run and (STORE / "STOP").exists()
        self.start_btn.state(["disabled"] if run else ["!disabled"])
        self.stop_btn.state(["!disabled"] if run and not stopping else ["disabled"])
        state = "stopping (finishing the current batch)" if stopping else ("running" if run else st.get("state", "idle"))
        self.state_lbl.config(text=f"State: {state}  tier {st.get('tier', '-')}")
        total, done, failed = st.get("total", 0), st.get("done", 0), st.get("failed", 0)
        self.bar.config(maximum=max(total, 1), value=done + failed)
        self.counts.config(text=f"done {done} / {total}    failed {failed}    pending {st.get('pending', '-')}    "
                                f"rate {st.get('rate_units_per_min', '-')}/min    ETA {fmt_eta(st.get('eta_s')) if run else '-'}")
        lines = st.get("last") or []
        self.logbox.delete("1.0", "end")
        self.logbox.insert("end", "\n".join(lines))
        self.logbox.see("end")
        self.after(2000, self.poll)


if __name__ == "__main__":
    App().mainloop()
