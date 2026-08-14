import os
import sys
import time
import queue
import threading
from datetime import datetime
from typing import Optional, Callable
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from DrissionPage import ChromiumPage, ChromiumOptions

import shutil
import subprocess

# Set visual theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def find_browser_path() -> Optional[str]:
    """Finds an installed Chromium browser (Chrome, Edge, Brave, Chromium) across Windows, Linux, and macOS."""
    # 1. Check system PATH
    for binary in ["chrome", "google-chrome", "google-chrome-stable", "msedge", "brave", "brave-browser", "chromium", "chromium-browser"]:
        found = shutil.which(binary)
        if found and os.path.isfile(found):
            return found

    # 2. Check Windows Registry
    if sys.platform.startswith("win"):
        try:
            import winreg
            reg_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\brave.exe"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\brave.exe"),
            ]
            for root_key, sub_key in reg_paths:
                try:
                    with winreg.OpenKey(root_key, sub_key) as key:
                        val, _ = winreg.QueryValueEx(key, "")
                        if val and os.path.isfile(val):
                            return val
                except OSError:
                    pass
        except Exception:
            pass

    # 3. Known common file paths across platforms
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local_app_data = os.environ.get("LOCALAPPDATA", "")

    candidates = [
        # Windows - Chrome
        os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(program_files_x86, "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(local_app_data, "Google", "Chrome", "Application", "chrome.exe"),
        # Windows - Edge
        os.path.join(program_files_x86, "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(program_files, "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(local_app_data, "Microsoft", "Edge", "Application", "msedge.exe"),
        # Windows - Brave
        os.path.join(program_files, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
        os.path.join(program_files_x86, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
        os.path.join(local_app_data, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
        # Linux
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/brave-browser",
        "/snap/bin/chromium",
        # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ]

    for path in candidates:
        if path and os.path.isfile(path):
            return path

    return None


class LinkExtractorEngine:
    def __init__(
        self,
        log_callback: Optional[Callable[[str, str], None]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        link_found_callback: Optional[Callable[[str, str], None]] = None,
    ):
        self.log_callback = log_callback or (lambda lvl, msg: None)
        self.progress_callback = progress_callback or (lambda cur, tot, url: None)
        self.link_found_callback = link_found_callback or (lambda orig, dl: None)
        self.is_running = False
        self.was_stopped = False
        self.page: Optional[ChromiumPage] = None

    def log(self, level: str, msg: str):
        self.log_callback(level, msg)

    def stop(self):
        self.was_stopped = True
        self.is_running = False
        if self.page:
            try:
                self.page.quit()
            except Exception:
                pass
            self.page = None

    def extract_links(self, clean_links: list[str], output_file: str = "download_links.txt"):
        self.is_running = True
        self.was_stopped = False

        if not clean_links:
            self.log("ERROR", "No valid URLs found in input!")
            return

        browser_path = find_browser_path()
        if not browser_path:
            self.log("ERROR", "Could not locate Google Chrome or Edge on this system!")
            return

        self.log("INFO", f"Launching browser engine ({os.path.basename(browser_path)})...")
        options = ChromiumOptions()
        options.set_browser_path(browser_path)

        try:
            self.page = ChromiumPage(options)
        except Exception as e:
            self.log("ERROR", f"Failed to start browser: {e}")
            return

        total = len(clean_links)
        self.log("INFO", f"Starting extraction for {total} link(s)...")

        for idx, link in enumerate(clean_links, start=1):
            if not self.is_running:
                self.log("WARN", "Process stopped by user.")
                break

            self.progress_callback(idx, total, link)
            self.log("INFO", f"[{idx}/{total}] Navigating to: {link}")

            try:
                self.page.get(link)
            except Exception as e:
                self.log("ERROR", f"Failed to load page: {e}")
                continue

            # Check for download button (indicates page loaded / challenge passed)
            btn = self.page.ele("text:DOWNLOAD", timeout=15)
            if not btn:
                self.log("ERROR", f"[{idx}/{total}] Download button not found.")
                continue

            # Wait for Turnstile to clear (button becomes active/opaque)
            active = False
            for _ in range(30):
                if not self.is_running:
                    break
                try:
                    style = btn.attr("style")
                    if not style or ("opacity" not in style and "0.5" not in style):
                        active = True
                        break
                except Exception:
                    pass
                time.sleep(0.5)

            if not self.is_running:
                break

            if not active:
                self.log("WARN", f"[{idx}/{total}] Turnstile challenge was not resolved in time.")
                continue

            # Extract via XHR without triggering browser downloads
            file_id = link.split("/")[-1].split("#")[0]
            js = f"""
                var xhr = new XMLHttpRequest();
                xhr.open('POST', '/f/{file_id}/go', false);
                xhr.setRequestHeader('HX-Request', 'true');
                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                xhr.send('cf-turnstile-response=' + encodeURIComponent(window.turnstileToken || ''));
                return xhr.getResponseHeader('hx-redirect');
            """

            download_url = None
            try:
                download_url = self.page.run_js(js)
            except Exception as e:
                self.log("WARN", f"[{idx}/{total}] XHR failed: {e}")

            if not download_url:
                self.log("ERROR", f"[{idx}/{total}] Download URL not found.")
                continue

            self.log("SUCCESS", f"[{idx}/{total}] Extracted: {download_url}")
            self.link_found_callback(link, download_url)

            # Append to download_links.txt immediately
            try:
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(download_url + "\n")
            except Exception as e:
                self.log("WARN", f"Could not write to {output_file}: {e}")

        if self.page:
            try:
                self.page.quit()
            except Exception:
                pass
            self.page = None

        if not self.was_stopped:
            self.log("SUCCESS", f"All done! Extracted links saved to {output_file}")
        self.is_running = False


class FastLinkApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FitGirl FastLink Extractor")
        self.geometry("980x740")
        self.minsize(850, 600)

        # Threading and Queue
        self.msg_queue = queue.Queue()
        self.extractor: Optional[LinkExtractorEngine] = None
        self.worker_thread: Optional[threading.Thread] = None

        # Build UI
        self.build_ui()
        self.load_initial_input()

        # Start queue processor
        self.after(100, self.process_queue)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ---------------- HEADER ----------------
        header_frame = ctk.CTkFrame(self, corner_radius=12, fg_color=("#1f1f2e", "#181824"))
        header_frame.grid(row=0, column=0, padx=16, pady=(16, 10), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        title_label = ctk.CTkLabel(
            header_frame,
            text="FitGirl Link Extractor",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=("#ec4899", "#f43f5e"),
        )
        title_label.grid(row=0, column=0, padx=16, pady=(12, 2), sticky="w")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Automated Cloudflare Turnstile bypass & direct link generator for fuckingfast.co",
            font=ctk.CTkFont(size=12),
            text_color=("gray70", "gray60"),
        )
        subtitle_label.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

        self.status_badge = ctk.CTkLabel(
            header_frame,
            text="READY",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#10b981", "#059669"),
            text_color="white",
            corner_radius=8,
            padx=14,
            pady=4,
        )
        self.status_badge.grid(row=0, column=2, rowspan=2, padx=16, pady=12, sticky="e")

        # ---------------- MAIN CONTENT (SPLIT VIEW) ----------------
        main_paned = ctk.CTkFrame(self, fg_color="transparent")
        main_paned.grid(row=1, column=0, padx=16, pady=6, sticky="nsew")
        main_paned.grid_columnconfigure(0, weight=1)
        main_paned.grid_columnconfigure(1, weight=1)
        main_paned.grid_rowconfigure(0, weight=1)

        # ====== LEFT COLUMN: INPUT ======
        left_frame = ctk.CTkFrame(main_paned, corner_radius=12)
        left_frame.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(1, weight=1)

        input_header_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        input_header_frame.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="ew")
        input_header_frame.grid_columnconfigure(0, weight=1)

        input_title = ctk.CTkLabel(
            input_header_frame,
            text="📥 Input Links (input.txt)",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        input_title.grid(row=0, column=0, sticky="w")

        self.input_count_label = ctk.CTkLabel(
            input_header_frame,
            text="0 links",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
        )
        self.input_count_label.grid(row=0, column=1, sticky="e")

        self.input_textbox = ctk.CTkTextbox(
            left_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=8,
            wrap="none",
        )
        self.input_textbox.grid(row=1, column=0, padx=12, pady=6, sticky="nsew")
        self.input_textbox.bind("<KeyRelease>", self.update_input_count)

        # Input Quick Action Buttons
        input_btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        input_btn_frame.grid(row=2, column=0, padx=12, pady=(4, 12), sticky="ew")
        input_btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        paste_btn = ctk.CTkButton(
            input_btn_frame,
            text="📋 Paste",
            height=32,
            fg_color=("#374151", "#2d3748"),
            hover_color=("#4b5563", "#3b4252"),
            command=self.paste_input,
        )
        paste_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        load_btn = ctk.CTkButton(
            input_btn_frame,
            text="📂 Load File",
            height=32,
            fg_color=("#374151", "#2d3748"),
            hover_color=("#4b5563", "#3b4252"),
            command=self.load_input_dialog,
        )
        load_btn.grid(row=0, column=1, padx=4, sticky="ew")

        clear_input_btn = ctk.CTkButton(
            input_btn_frame,
            text="🗑️ Clear",
            height=32,
            fg_color=("#374151", "#2d3748"),
            hover_color=("#4b5563", "#3b4252"),
            command=self.clear_input,
        )
        clear_input_btn.grid(row=0, column=2, padx=(4, 0), sticky="ew")

        # ====== RIGHT COLUMN: OUTPUT & LOGS ======
        right_frame = ctk.CTkFrame(main_paned, corner_radius=12)
        right_frame.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_rowconfigure(3, weight=1)

        # Tab 1: Extracted Links Header
        out_header_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        out_header_frame.grid(row=0, column=0, padx=12, pady=(12, 4), sticky="ew")
        out_header_frame.grid_columnconfigure(0, weight=1)

        out_title = ctk.CTkLabel(
            out_header_frame,
            text="🚀 Extracted Direct Links",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        out_title.grid(row=0, column=0, sticky="w")

        self.out_count_label = ctk.CTkLabel(
            out_header_frame,
            text="0 extracted",
            font=ctk.CTkFont(size=12),
            text_color="#10b981",
        )
        self.out_count_label.grid(row=0, column=1, sticky="e")

        self.output_textbox = ctk.CTkTextbox(
            right_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=8,
            wrap="none",
        )
        self.output_textbox.grid(row=1, column=0, padx=12, pady=4, sticky="nsew")

        # Output Action Buttons
        out_btn_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        out_btn_frame.grid(row=2, column=0, padx=12, pady=4, sticky="ew")
        out_btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        copy_btn = ctk.CTkButton(
            out_btn_frame,
            text="📑 Copy All Links",
            height=30,
            fg_color=("#10b981", "#059669"),
            hover_color=("#059669", "#047857"),
            command=self.copy_output,
        )
        copy_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        open_file_btn = ctk.CTkButton(
            out_btn_frame,
            text="📄 Open Output File",
            height=30,
            fg_color=("#374151", "#2d3748"),
            hover_color=("#4b5563", "#3b4252"),
            command=self.open_output_file,
        )
        open_file_btn.grid(row=0, column=1, padx=4, sticky="ew")

        clear_out_btn = ctk.CTkButton(
            out_btn_frame,
            text="🗑️ Clear Output",
            height=30,
            fg_color=("#374151", "#2d3748"),
            hover_color=("#4b5563", "#3b4252"),
            command=self.clear_output,
        )
        clear_out_btn.grid(row=0, column=2, padx=(4, 0), sticky="ew")

        # Log Terminal Header
        log_header_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        log_header_frame.grid(row=3, column=0, padx=12, pady=(6, 2), sticky="ew")
        log_title = ctk.CTkLabel(
            log_header_frame,
            text="📟 Live Activity Console",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="gray70",
        )
        log_title.pack(side="left")

        # Log Text Box
        self.log_textbox = ctk.CTkTextbox(
            right_frame,
            font=ctk.CTkFont(family="Consolas", size=10),
            corner_radius=8,
            wrap="word",
            fg_color=("#111827", "#0f172a"),
        )
        self.log_textbox.grid(row=4, column=0, padx=12, pady=(2, 12), sticky="nsew")
        right_frame.grid_rowconfigure(4, weight=1)

        # ---------------- ACTION & PROGRESS FOOTER ----------------
        footer_frame = ctk.CTkFrame(self, corner_radius=12, fg_color=("#1f1f2e", "#181824"))
        footer_frame.grid(row=2, column=0, padx=16, pady=(6, 16), sticky="ew")
        footer_frame.grid_columnconfigure(1, weight=1)

        # Start / Stop Buttons
        self.start_btn = ctk.CTkButton(
            footer_frame,
            text="▶ Start Fetching Links",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            fg_color=("#e11d48", "#be123c"),
            hover_color=("#be123c", "#9f1239"),
            command=self.start_fetching,
        )
        self.start_btn.grid(row=0, column=0, rowspan=2, padx=16, pady=12, sticky="w")

        self.stop_btn = ctk.CTkButton(
            footer_frame,
            text="⏹ Stop",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            width=90,
            fg_color="#4b5563",
            hover_color="#374151",
            state="disabled",
            command=self.stop_fetching,
        )
        self.stop_btn.grid(row=0, column=1, rowspan=2, padx=(0, 16), pady=12, sticky="w")

        # Progress info
        self.progress_label = ctk.CTkLabel(
            footer_frame,
            text="Idle • Ready to process links",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
        )
        self.progress_label.grid(row=0, column=2, padx=16, pady=(8, 2), sticky="e")

        self.progress_bar = ctk.CTkProgressBar(
            footer_frame,
            height=10,
            progress_color="#e11d48",
        )
        self.progress_bar.grid(row=1, column=2, padx=16, pady=(0, 12), sticky="ew")
        self.progress_bar.set(0)

    # ---------------- LOGIC & EVENTS ----------------
    def update_input_count(self, event=None):
        text = self.input_textbox.get("1.0", "end-1c").strip()
        if not text:
            self.input_count_label.configure(text="0 links")
            return
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        links = [l for l in lines if "http://" in l or "https://" in l]
        self.input_count_label.configure(text=f"{len(links)} link(s)")

    def paste_input(self):
        try:
            clipboard = self.clipboard_get()
            self.input_textbox.insert("end", clipboard + "\n")
            self.update_input_count()
        except Exception:
            pass

    def clear_input(self):
        self.input_textbox.delete("1.0", "end")
        self.update_input_count()

    def load_initial_input(self):
        if os.path.exists("input.txt"):
            try:
                with open("input.txt", "r", encoding="utf-8") as f:
                    content = f.read()
                self.input_textbox.insert("1.0", content)
                self.update_input_count()
                self.log_message("INFO", "Loaded existing links from input.txt")
            except Exception as e:
                self.log_message("WARN", f"Could not read input.txt: {e}")

        # Load existing download_links.txt count if present
        if os.path.exists("download_links.txt"):
            try:
                with open("download_links.txt", "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f if l.strip()]
                if lines:
                    self.output_textbox.insert("1.0", "\n".join(lines) + "\n")
                    self.out_count_label.configure(text=f"{len(lines)} extracted")
            except Exception:
                pass

    def load_input_dialog(self):
        path = filedialog.askopenfilename(
            title="Select links text file",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.input_textbox.delete("1.0", "end")
                self.input_textbox.insert("1.0", content)
                self.update_input_count()
                self.log_message("INFO", f"Loaded links from {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")

    def copy_output(self):
        text = self.output_textbox.get("1.0", "end-1c").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "All direct links copied to clipboard!")
        else:
            messagebox.showwarning("Empty", "No extracted links to copy!")

    def open_output_file(self):
        if os.path.exists("download_links.txt"):
            try:
                if sys.platform.startswith("win"):
                    os.startfile("download_links.txt")
                elif sys.platform.startswith("darwin"):
                    subprocess.run(["open", "download_links.txt"])
                else:
                    subprocess.run(["xdg-open", "download_links.txt"])
            except Exception as e:
                messagebox.showwarning("Open File", f"Could not launch editor: {e}")
        else:
            messagebox.showinfo("Not Found", "download_links.txt has not been created yet.")

    def clear_output(self):
        self.output_textbox.delete("1.0", "end")
        self.out_count_label.configure(text="0 extracted")

    def log_message(self, level: str, text: str):
        self.msg_queue.put(("LOG", level, text))

    def on_progress(self, current: int, total: int, url: str):
        self.msg_queue.put(("PROGRESS", current, total, url))

    def on_link_found(self, original_url: str, direct_url: str):
        self.msg_queue.put(("LINK_FOUND", original_url, direct_url))

    def process_queue(self):
        """Processes messages from background thread to safely update UI."""
        try:
            while True:
                item = self.msg_queue.get_nowait()
                msg_type = item[0]

                if msg_type == "LOG":
                    _, level, text = item
                    ts = datetime.now().strftime("%H:%M:%S")
                    prefix = {
                        "INFO": "🔵 INFO",
                        "SUCCESS": "🟢 SUCC",
                        "WARN": "🟡 WARN",
                        "ERROR": "🔴 ERRR",
                    }.get(level, "⚪ LOG")
                    log_line = f"[{ts}] {prefix} • {text}\n"
                    self.log_textbox.insert("end", log_line)
                    self.log_textbox.see("end")

                elif msg_type == "PROGRESS":
                    _, current, total, url = item
                    fraction = current / max(total, 1)
                    self.progress_bar.set(fraction)
                    self.progress_label.configure(
                        text=f"Processing {current} of {total} ({int(fraction*100)}%)"
                    )

                elif msg_type == "LINK_FOUND":
                    _, orig, direct = item
                    self.output_textbox.insert("end", direct + "\n")
                    self.output_textbox.see("end")
                    lines = [
                        l
                        for l in self.output_textbox.get("1.0", "end-1c").splitlines()
                        if l.strip()
                    ]
                    self.out_count_label.configure(text=f"{len(lines)} extracted")

                elif msg_type == "FINISHED":
                    self.set_ui_state(running=False)
                    self.status_badge.configure(text="COMPLETED", fg_color="#10b981")
                    self.progress_label.configure(text="Finished extracting all links!")
                    self.progress_bar.set(1.0)
                    messagebox.showinfo(
                        "Extraction Complete",
                        "All links processed and saved to download_links.txt!",
                    )

                elif msg_type == "STOPPED":
                    self.set_ui_state(running=False)
                    self.status_badge.configure(text="STOPPED", fg_color="#f59e0b")
                    self.progress_label.configure(text="Process stopped by user.")

        except queue.Empty:
            pass

        self.after(100, self.process_queue)

    def set_ui_state(self, running: bool):
        if running:
            self.start_btn.configure(state="disabled", fg_color="#4b5563")
            self.stop_btn.configure(state="normal", fg_color="#dc2626")
            self.status_badge.configure(text="PROCESSING", fg_color="#3b82f6")
        else:
            self.start_btn.configure(state="normal", fg_color=("#e11d48", "#be123c"))
            self.stop_btn.configure(state="disabled", fg_color="#4b5563")

    def start_fetching(self):
        raw_text = self.input_textbox.get("1.0", "end-1c").strip()
        if not raw_text:
            messagebox.showwarning("No Input", "Please enter or paste some links first!")
            return

        clean_links = []
        for l in raw_text.splitlines():
            l = l.strip()
            if l.startswith("- "):
                l = l[2:].strip()
            if l.startswith("http://") or l.startswith("https://"):
                clean_links.append(l)

        if not clean_links:
            messagebox.showwarning(
                "Invalid Input", "No valid URLs starting with http:// or https:// found!"
            )
            return

        # Save to input.txt
        try:
            with open("input.txt", "w", encoding="utf-8") as f:
                f.write(raw_text + "\n")
            self.log_message("INFO", f"Saved {len(clean_links)} input links to input.txt")
        except Exception as e:
            self.log_message("WARN", f"Could not write input.txt: {e}")

        self.set_ui_state(running=True)
        self.progress_bar.set(0)
        self.progress_label.configure(text=f"Starting... 0 of {len(clean_links)}")

        self.extractor = LinkExtractorEngine(
            log_callback=self.log_message,
            progress_callback=self.on_progress,
            link_found_callback=self.on_link_found,
        )

        def worker():
            self.extractor.extract_links(clean_links, output_file="download_links.txt")
            if self.extractor.was_stopped:
                self.msg_queue.put(("STOPPED",))
            else:
                self.msg_queue.put(("FINISHED",))

        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()

    def stop_fetching(self):
        if self.extractor:
            self.log_message("WARN", "Stopping extractor...")
            self.extractor.stop()

    def on_closing(self):
        if self.extractor and self.extractor.is_running:
            if messagebox.askokcancel("Quit", "Extraction is running. Do you really want to quit?"):
                self.extractor.stop()
                self.destroy()
        else:
            self.destroy()


if __name__ == "__main__":
    app = FastLinkApp()
    app.mainloop()
