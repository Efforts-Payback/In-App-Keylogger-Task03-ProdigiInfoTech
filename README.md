# 🔎 In-App Key Logger  
### Internship Project — Prodigi Info Tech (Task 03)

---

## Overview
This is an **ethical, in-app key logging tool** developed with **Python (Tkinter)** for controlled testing, debugging, and usability research. The app logs keystrokes **only while the user starts logging** and the app window is focused. It includes visible safeguards (blinking indicator, topmost window), consent receipts, an Emergency Stop, and export options.

> **Important:** This project does **not** implement system-wide/global key capture. Do **not** attempt to use it for covert or unauthorized monitoring. Always obtain informed consent.

---

## Features
- ✅ Records keystrokes only while **logging is ON** and the **app is focused**  
- ✅ Visible status indicator (small circle) in the header — **blinks red while recording**  
- ✅ Window becomes **topmost** during recording (so the recording indicator is always visible)  
- ✅ **Consent dialog** before logging starts; consent saved to a receipt file (`consent_YYYYMMDD_HHMMSS.txt`)  
- ✅ **Emergency Stop (Ctrl+Shift+E)** — immediately stops logging and can clear in-memory logs  
- ✅ Auto-save (append mode), manual **Save As (TXT)**, **Export CSV**, **Copy to clipboard**  
- ✅ **Anonymize display** option — masks the on-screen display while still saving real keystrokes locally  
- ✅ Session stats: `Start`, `Stop`, `Total Keys`, `Printable Characters`  
- ✅ Robust file I/O with error handling; single-file app (no external GUI libraries required)

---

## Why this is ethical
This application is built for legitimate workflows where transparency and consent matter. Key ethical points:
- The user must explicitly agree to log keystrokes.  
- A visible indicator + topmost window ensures recording cannot be hidden.  
- A stored consent receipt documents the user’s informed consent.  
- All logs remain local to the machine running the app.  

**Do not use** for recording others without their express consent.

---

## Quick demo / Usage

### Requirements
- Python 3.8 or newer (tested on 3.8+)
- No external dependencies required (uses Python standard library)
- `tkinter` (bundled with most Python installers)

### Run
1. Clone or download this repository:
git clone https://github.com/yourusername/In-App-Keylogger-Task03-ProdigiInfoTech.git
cd In-App-Keylogger-Task03-ProdigiInfoTech

### How to use

--> Click Start Logging. Read the consent dialog and click Yes to proceed. A consent_YYYYMMDD_HHMMSS.txt file will be saved in the current folder.
--> Type inside the application window (or the provided entry field). The small circle in the header will blink red and the status will show the consent timestamp.
--> Click Stop Logging to end the session.
--> Use Save As (TXT) or Export CSV to save the recorded session.
--> If you need to quickly stop and clear unsaved memory logs, press Ctrl+Shift+E (Emergency Stop).

**Files produced by the app**

--> consent_YYYYMMDD_HHMMSS.txt — consent receipt for each session
--> keystrokes_log.txt (default) — appended session logs if auto-save enabled
--> session_YYYYMMDD_HHMMSS.txt or .csv — exported session files as chosen by the user

### Security & Privacy Recommendations

• Only run this application on machines where you have permission to collect data.
• Store logs securely and delete them when no longer needed.
• When using the tool for research, require participants to sign a consent form and archive consent receipts.
• Consider encrypting stored logs for extra security if logs contain sensitive test data.

### Development notes

• The app uses bind_all("<Key>") to capture key events while focused; it checks focus and a logging flag before recording.
• Anonymize mode masks the display for demos or public presentations; underlying saved files remain unchanged unless the user chooses to redact.
• Emergency Stop clears in-memory logs (does not delete previously saved files) to protect users who need an immediate wipe of unsaved data.

### License

Use for educational and legitimate testing purposes. Do not use this software to record others without consent.
