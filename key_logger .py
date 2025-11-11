import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import csv
import os
import platform
import threading

LOG_FILENAME_DEFAULT = "keystrokes_log.txt"
CSV_FILENAME_DEFAULT = "keystrokes_log.csv"

# ---------------------- Utility helpers ----------------------
def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
\
def ensure_file_exists(path):
    if not os.path.exists(path):
        open(path, "w", encoding="utf-8").close()

# ---------------------- Main App ----------------------
class InAppKeyLoggerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("In-App Key Logger — Prodigi Info Tech (Ethical)")
        self.geometry("820x560")
        self.minsize(780, 520)
        self.configure(bg="#f5f7fb")

        # Internal state
        self.logging = False
        self.log_lines = []
        self.start_time = None
        self.stop_time = None
        self.total_keys = 0
        self.printable_chars = 0
        self.auto_save = tk.BooleanVar(value=False)
        self.append_mode = tk.BooleanVar(value=True)
        self.anonymize_display = tk.BooleanVar(value=False)
        self.log_path_txt = LOG_FILENAME_DEFAULT
        self.log_path_csv = CSV_FILENAME_DEFAULT
        ensure_file_exists(self.log_path_txt)

        # Indicator/blink control variables (new features)
        self._blink_on = False
        self._blink_job = None
        self._reminder_job = None

        self._build_ui()
        self.bind_all("<Key>", self._on_key_event)  # will use logging flag and focus checks

        # Emergency stop binding: Ctrl+Shift+E
        self.bind_all("<Control-Shift-E>", lambda e: self._emergency_stop())

    # ---------------------- UI ----------------------
    def _build_ui(self):
        # Top header (same as before; we only add a small indicator in this header)
        header = tk.Frame(self, bg="#ffffff", bd=0, relief="flat")
        header.pack(fill="x", padx=14, pady=(12,6))
        title = tk.Label(header, text="🔎 In-App Key Logger", font=("Segoe UI Semibold", 18), bg="#ffffff", fg="#111")
        title.pack(side="left")
        subtitle = tk.Label(header, text="(Consent required • Logs only while active)", bg="#ffffff", fg="#555", font=("Segoe UI", 10))
        subtitle.pack(side="left", padx=(12,0))

        # ------------------ NEW: Visible Indicator (non-intrusive) ------------------
        # Small circular indicator + label placed on the header (right side).
        # This is intentionally minimal and does not change existing layout except adding this small control.
        self.indicator_frame = tk.Frame(header, bg="#ffffff")
        self.indicator_frame.pack(side="right", padx=8)

        self.indicator_canvas = tk.Canvas(self.indicator_frame, width=18, height=18, bg="#ffffff", highlightthickness=0)
        self.indicator_canvas.grid(row=0, column=0, padx=(0,6))
        self.indicator_circle = self.indicator_canvas.create_oval(2,2,16,16, fill="#9aa0a6", outline="")

        self.indicator_label = tk.Label(self.indicator_frame, text="Status: OFF", font=("Segoe UI", 9), bg="#ffffff", fg="#444")
        self.indicator_label.grid(row=0, column=1)
        # ---------------------------------------------------------------------------

        # Main frame
        main = tk.Frame(self, bg="#f5f7fb")
        main.pack(fill="both", expand=True, padx=14, pady=(0,12))

        # Left column - controls & stats
        left = tk.Frame(main, bg="#f5f7fb")
        left.pack(side="left", fill="y", padx=(0,10))

        # Controls card
        controls_card = ttk.Frame(left, padding=12)
        controls_card.pack(fill="x", pady=(0,10))

        ttk.Style().configure("TButton", padding=6)
        self.start_btn = ttk.Button(controls_card, text="Start Logging", command=self.start_logging)
        self.start_btn.grid(row=0, column=0, sticky="ew")
        self.stop_btn = ttk.Button(controls_card, text="Stop Logging", command=self.stop_logging, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=(8,0), sticky="ew")

        # Options row
        opts = ttk.Frame(controls_card)
        opts.grid(row=1, column=0, columnspan=2, pady=(10,0), sticky="ew")

        ttk.Checkbutton(opts, text="Auto-save (append)", variable=self.auto_save).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(opts, text="Anonymize display", variable=self.anonymize_display).grid(row=0, column=1, padx=(12,0), sticky="w")

        # Save / Export buttons
        save_frame = ttk.Frame(controls_card)
        save_frame.grid(row=2, column=0, columnspan=2, pady=(12,0), sticky="ew")

        ttk.Button(save_frame, text="Save As (TXT)", command=self.save_as_txt).grid(row=0, column=0, sticky="ew")
        ttk.Button(save_frame, text="Export CSV", command=self.export_csv).grid(row=0, column=1, padx=(8,0), sticky="ew")
        ttk.Button(save_frame, text="Clear Display", command=self.clear_display).grid(row=0, column=2, padx=(8,0), sticky="ew")

        # Session stats card
        stats_card = ttk.Frame(left, padding=12)
        stats_card.pack(fill="x", pady=(8,0))
        ttk.Label(stats_card, text="Session Stats", font=("Segoe UI Semibold", 11)).grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(stats_card, text="Status:").grid(row=1, column=0, sticky="w", pady=(8,0))
        self.status_var = tk.StringVar(value="Logging: OFF")
        ttk.Label(stats_card, textvariable=self.status_var).grid(row=1, column=1, sticky="w", pady=(8,0))

        ttk.Label(stats_card, text="Start:").grid(row=2, column=0, sticky="w", pady=(6,0))
        self.start_var = tk.StringVar(value="-")
        ttk.Label(stats_card, textvariable=self.start_var).grid(row=2, column=1, sticky="w", pady=(6,0))

        ttk.Label(stats_card, text="Stop:").grid(row=3, column=0, sticky="w", pady=(6,0))
        self.stop_var = tk.StringVar(value="-")
        ttk.Label(stats_card, textvariable=self.stop_var).grid(row=3, column=1, sticky="w", pady=(6,0))

        ttk.Label(stats_card, text="Total Keys:").grid(row=4, column=0, sticky="w", pady=(6,0))
        self.total_keys_var = tk.StringVar(value="0")
        ttk.Label(stats_card, textvariable=self.total_keys_var).grid(row=4, column=1, sticky="w", pady=(6,0))

        ttk.Label(stats_card, text="Printable Chars:").grid(row=5, column=0, sticky="w", pady=(6,0))
        self.printable_var = tk.StringVar(value="0")
        ttk.Label(stats_card, textvariable=self.printable_var).grid(row=5, column=1, sticky="w", pady=(6,0))

        # Right column - log display
        right = tk.Frame(main, bg="#f5f7fb")
        right.pack(side="right", fill="both", expand=True)

        # Search / filter row
        search_row = ttk.Frame(right)
        search_row.pack(fill="x", pady=(0,8))
        ttk.Label(search_row, text="Filter:").pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(search_row, textvariable=self.filter_var, width=28)
        self.filter_entry.pack(side="left", padx=(8,8))
        ttk.Button(search_row, text="Apply", command=self.apply_filter).pack(side="left")
        ttk.Button(search_row, text="Clear Filter", command=self.clear_filter).pack(side="left", padx=(8,0))

        # Log display (scrolled)
        log_frame = tk.Frame(right, bg="#ffffff", bd=1, relief="solid")
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(log_frame, bg="#fcfcfd", wrap="none", state="disabled",
                                font=("Consolas", 10), padx=6, pady=6)
        self.log_text.pack(side="left", fill="both", expand=True)

        # Scrollbars
        yscroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        yscroll.pack(side="right", fill="y")
        self.log_text['yscrollcommand'] = yscroll.set

        xscroll = ttk.Scrollbar(right, orient="horizontal", command=self.log_text.xview)
        xscroll.pack(fill="x")
        self.log_text['xscrollcommand'] = xscroll.set

        # Bottom action row
        bottom = tk.Frame(self, bg="#f5f7fb")
        bottom.pack(fill="x", padx=14, pady=(6,12))
        ttk.Button(bottom, text="Copy Display to Clipboard", command=self.copy_to_clipboard).pack(side="left")
        ttk.Button(bottom, text="Open Log Folder", command=self.open_log_folder).pack(side="left", padx=(8,0))
        ttk.Button(bottom, text="About / Ethical Notes", command=self.show_about).pack(side="right")

    # ---------------------- Actions ----------------------
    def start_logging(self):
        if self.logging:
            return
        # Consent dialog
        consent_text = (
            "You are about to start logging keystrokes inside this application.\n\n"
            "Logs are stored locally on this machine.\n"
            "Do you give informed consent to record keystrokes for this session?"
        )
        consent = messagebox.askyesno("Consent required", consent_text)
        if not consent:
            return

        # Save consent receipt (new feature)
        try:
            receipt_name = f"consent_{datetime.now().strftime('%Y%m%d_%H%M%S  ')}.txt"
            with open(receipt_name, "w", encoding="utf-8") as rfile:
                rfile.write("Consent Receipt\n")
                rfile.write(f"Timestamp: {timestamp()}\n")
                rfile.write("Action: User consented to in-app keystroke logging for this session.\n")
                rfile.write("Notes: Logs stored locally. Do not use without informed consent.\n")
        except Exception:
            # Non-fatal; continue
            pass

        self.logging = True
        self.start_time = datetime.now()
        self.total_keys = 0
        self.printable_chars = 0
        self.log_lines.append(("SESSION_START", timestamp(), "", ""))
        self.status_var.set("Logging: ON")
        self.start_var.set(self.start_time.strftime("%Y-%m-%d %H:%M:%S  "))
        self.stop_var.set("-")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        # Make window topmost and start blinking indicator (new features)
        self._start_indicator_mode()

        # Auto-append header if auto_save and append_mode
        if self.auto_save.get() and self.append_mode.get():
            try:
                with open(self.log_path_txt, "a", encoding="utf-8") as f:
                    f.write(f"\n--- SESSION START {timestamp()} ---\n")
            except Exception as e:
                messagebox.showerror("File Error", f"Could not write header to log file:\n{e}")

        # Start periodic reminder (visible) to show recording duration (new)
        self._schedule_reminder()

    def stop_logging(self):
        if not self.logging:
            return
        self.logging = False
        self.stop_time = datetime.now()
        self.log_lines.append(("SESSION_STOP", timestamp(), "", ""))
        self.status_var.set("Logging: OFF")
        self.stop_var.set(self.stop_time.strftime("%Y-%m-%d %H:%M:%S"))
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

        # Stop indicator + restore topmost (new)
        self._stop_indicator_mode()

        # Cancel reminder
        if self._reminder_job:
            try:
                self.after_cancel(self._reminder_job)
            except Exception:
                pass
            self._reminder_job = None

        # Auto-save session if requested
        if self.auto_save.get():
            try:
                self._append_session_to_file(self.log_path_txt)
            except Exception as e:
                messagebox.showerror("Auto-save Error", f"Failed to auto-save:\n{e}")

    def clear_display(self):
        confirm = messagebox.askyesno("Clear display", "Clear the on-screen log display? (This will NOT delete saved files.)")
        if not confirm:
            return
        self.log_lines.clear()
        self._refresh_display()
        self.total_keys = 0
        self.printable_chars = 0
        self.total_keys_var.set(str(self.total_keys))
        self.printable_var.set(str(self.printable_chars))

    # ---------------------- Key handling ----------------------
    def _on_key_event(self, event):
        # Only log when logging is enabled and the app has focus
        if not self.logging:
            return
        if not self.focus_displayof():
            return  # app not focused

        keysym = event.keysym
        char = event.char
        ts = timestamp()

        # Represent printable or named key
        if char and char.isprintable():
            repr_text = char
            self.printable_chars += 1
        else:
            # Use readable names for special keys
            repr_text = f"<{keysym}>"

        self.total_keys += 1
        self.total_keys_var.set(str(self.total_keys))
        self.printable_var.set(str(self.printable_chars))

        # Record tuple
        self.log_lines.append((ts, repr_text, keysym, char))

        # Update display (respect anonymize option)
        display_text = repr_text if not self.anonymize_display.get() else "*" * len(repr_text)
        line = f"{ts}    {display_text}\n"
        self._append_to_display(line)

        # Also append to file immediately if auto-save is on and append_mode true
        if self.auto_save.get() and self.append_mode.get():
            try:
                with open(self.log_path_txt, "a", encoding="utf-8") as f:
                    f.write(f"{ts}    {repr_text}\n")
            except Exception:
                pass  # Non-blocking: don't spam user with errors during typing

    # ---------------------- Display / Filter ----------------------
    def _append_to_display(self, text):
        self.log_text.config(state="normal")
        self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _refresh_display(self, filtered=None):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        lines_to_show = filtered if filtered is not None else self.log_lines
        for entry in lines_to_show:
            if entry[0] in ("SESSION_START", "SESSION_STOP"):
                # show markers
                marker = f"--- {entry[0]} {entry[1]} ---\n"
                self.log_text.insert("end", marker)
            else:
                display_text = entry[1] if not self.anonymize_display.get() else "*" * len(entry[1])
                self.log_text.insert("end", f"{entry[0]}    {display_text}\n")
        self.log_text.config(state="disabled")

    def apply_filter(self):
        query = self.filter_var.get().strip()
        if not query:
            return
        filtered = [e for e in self.log_lines if query in (e[1] or "") or query in (e[2] or "")]
        self._refresh_display(filtered)

    def clear_filter(self):
        self.filter_var.set("")
        self._refresh_display()

    # ---------------------- Save / Export ----------------------
    def save_as_txt(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                                            initialfile=LOG_FILENAME_DEFAULT)
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                for e in self.log_lines:
                    if e[0] in ("SESSION_START", "SESSION_STOP"):
                        f.write(f"--- {e[0]} {e[1]} ---\n")
                    else:
                        f.write(f"{e[0]}    {e[1]}\n")
            messagebox.showinfo("Saved", f"Log saved to: {path}")
        except Exception as exc:
            messagebox.showerror("Save Error", f"Could not save file:\n{exc}")

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                                            initialfile=CSV_FILENAME_DEFAULT)
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["timestamp", "display", "keysym", "char"])
                for e in self.log_lines:
                    if e[0] in ("SESSION_START", "SESSION_STOP"):
                        writer.writerow([e[1], e[0], "", ""])
                    else:
                        writer.writerow([e[0], e[1], e[2], e[3]])
            messagebox.showinfo("Exported", f"CSV exported to: {path}")
        except Exception as exc:
            messagebox.showerror("Export Error", f"Could not export CSV:\n{exc}")

    def _append_session_to_file(self, path):
        # Append entire session to a file (TXT)
        with open(path, "a", encoding="utf-8") as f:
            for e in self.log_lines:
                if e[0] in ("SESSION_START", "SESSION_STOP"):
                    f.write(f"--- {e[0]} {e[1]} ---\n")
                else:
                    f.write(f"{e[0]}    {e[1]}\n")

    # ---------------------- Indicator & Reminder (NEW features) ----------------------
    def _set_indicator(self, color, text):
        """Set indicator color and label immediately (non-blinking)."""
        try:
            self.indicator_canvas.itemconfig(self.indicator_circle, fill=color)
            self.indicator_label.config(text=text)
        except Exception:
            pass

    def _blink_indicator(self, colors=("red", "#ffc8c8"), interval=500):
        """Blink the indicator between two colors while recording."""
        self._blink_on = not self._blink_on
        color = colors[int(self._blink_on)]
        label = "Recording..." if self.logging else "Status: ON"
        try:
            self.indicator_canvas.itemconfig(self.indicator_circle, fill=color)
            self.indicator_label.config(text=label)
        except Exception:
            pass
        # schedule next blink while still logging
        if self.logging:
            self._blink_job = self.after(interval, lambda: self._blink_indicator(colors, interval))
        else:
            self._blink_job = None

    def _start_indicator_mode(self):
        """Make UI unmistakably show Recorder is active: topmost + blinking + consent timestamp."""
        # Make window stay on top while logging so user cannot miss it
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass
        # Start blinking red
        if self._blink_job:
            try:
                self.after_cancel(self._blink_job)
            except Exception:
                pass
        self._blink_indicator(colors=("red", "#ff6b6b"), interval=600)
        # show consent timestamp in status_var (adds clarity)
        try:
            consent_info = f"Logging: ON (consent at {timestamp()})"
            self.status_var.set(consent_info)
        except Exception:
            pass

    def _stop_indicator_mode(self):
        """Turn off recording indicator and restore UI state."""
        # Cancel blinking job
        if self._blink_job:
            try:
                self.after_cancel(self._blink_job)
            except Exception:
                pass
            self._blink_job = None
        # Reset indicator and label
        self._set_indicator("#9aa0a6", "Status: OFF")
        # allow window to return to normal stacking
        try:
            self.attributes("-topmost", False)
        except Exception:
            pass
        # restore normal status label
        self.status_var.set("Logging: OFF")

    def _schedule_reminder(self, interval_ms=300000):
        """Schedule a visible, non-modal reminder update every interval_ms (default 5 minutes)."""
        # Update a subtle reminder appended to the status_var text (so it remains visible)
        def _reminder():
            if not self.logging:
                return
            # compute duration
            dur = datetime.now() - self.start_time if self.start_time else timedelta(0)
            mins = int(dur.total_seconds() // 60)
            secs = int(dur.total_seconds() % 60)
            reminder_text = f"Logging: ON • Duration {mins}m {secs}s (Press Ctrl+Shift+E to Emergency Stop)"
            self.status_var.set(reminder_text)
            self._reminder_job = self.after(interval_ms, _reminder)
        # schedule first call
        if self._reminder_job:
            try:
                self.after_cancel(self._reminder_job)
            except Exception:
                pass
        self._reminder_job = self.after(1000, _reminder)  # first update in 1s

    # ---------------------- Emergency stop (NEW) ----------------------
    def _emergency_stop(self):
        """Immediate stop and optional deletion of unsaved log from memory (keyboard shortcut)."""
        if not self.logging:
            # if not logging just clear in-memory logs as quick 'erase' if user asks
            confirm = messagebox.askyesno("Emergency Clear?", "Not currently logging. Clear in-memory logs now?")
            if confirm:
                self.log_lines.clear()
                self._refresh_display()
            return

        confirm = messagebox.askyesno("Emergency Stop", "Emergency stop will immediately end logging and clear unsaved in-memory logs. Continue?")
        if not confirm:
            return
        # Stop logging, clear in-memory logs (but do not touch already saved files), update UI
        self.logging = False
        self.stop_time = datetime.now()
        self.log_lines.clear()
        self._refresh_display()
        self.status_var.set("Logging: EMERGENCY STOPPED (memory cleared)")
        # stop indicator + reminder
        self._stop_indicator_mode()
        if self._reminder_job:
            try:
                self.after_cancel(self._reminder_job)
            except Exception:
                pass
            self._reminder_job = None
        # reset buttons
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        messagebox.showinfo("Emergency Stop", "Logging stopped and in-memory logs cleared. Any previously saved files are not deleted.")

    # ---------------------- Utilities ----------------------
    def copy_to_clipboard(self):
        try:
            txt = self.log_text.get("1.0", "end").strip()
            self.clipboard_clear()
            self.clipboard_append(txt)
            messagebox.showinfo("Copied", "Displayed log copied to clipboard.")
        except Exception as e:
            messagebox.showerror("Clipboard Error", str(e))

    def open_log_folder(self):
        folder = os.getcwd()
        try:
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                os.system(f"open '{folder}'")
            else:
                os.system(f'xdg-open "{folder}"')
        except Exception:
            messagebox.showinfo("Folder", f"Open folder: {folder}")

    def show_about(self):
        about = (
            "In-App Key Logger — Ethical Example\n\n"
            "• Logs keystrokes only while logging is ON and the app window is focused.\n"
            "• Intended for testing, debugging, or usability research with informed consent.\n"
            "• Do NOT use to record people without permission.\n\n"
            "New safety features: visible recording indicator, blinking while active, topmost during recording,\n"
            "consent receipt file, periodic visible reminder, and Emergency Stop (Ctrl+Shift+E).\n\n"
            "Developed for internship tasks at Prodigy Info Tech."
        )
        messagebox.showinfo("About / Ethics", about)

# ---------------------- Run ----------------------
if __name__ == "__main__":
    app = InAppKeyLoggerGUI()
    app.mainloop()
