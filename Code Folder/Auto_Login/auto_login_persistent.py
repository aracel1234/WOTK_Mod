import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess, json, os, time, threading
import pyautogui, pygetwindow as gw
from dataclasses import dataclass, asdict
from typing import List, Dict

# ─────────────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class AccountData:
    username: str
    password: str
    confirm_password: str | None = None
    action_type: str = "login"  # "login" | "register"
    server_number: str = "7"

    @classmethod
    def from_dict(cls, d: Dict):
        return cls(**{k: d.get(k) for k in cls.__annotations__})

# ─────────────────────────────────────────────────────────────────────────────
# Main Application Class
# ─────────────────────────────────────────────────────────────────────────────
class UCBrowserAutoManager:
    JSON_COORDS = "coordinates.json"
    JSON_ACCOUNTS = "accounts.json"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("UC Browser Auto Manager")
        self.root.geometry("900x800")

        # Runtime storages
        self.coordinates: Dict[str, Dict[str, int]] = {}
        self.entries: List[Dict] = []  # GUI entry widgets

        # UC Browser path
        self.uc_browser_path = r"C:\\Program Files (x86)\\UCBrowser\\Application\\UCBrowser.exe"

        # PyAutoGUI settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        self._build_gui()
        self._load_coordinates()

    # ─────────────────────────────────────────────────────────────────────
    # GUI BUILDING
    # ─────────────────────────────────────────────────────────────────────
    def _build_gui(self):
        title = tk.Label(self.root, text="🎮 UC Browser Auto Manager", font=("Arial", 16, "bold"))
        title.pack(pady=10)

        main = ttk.Frame(self.root, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        # Coordinate section
        coord_f = ttk.LabelFrame(main, text="Coordinate Configuration", padding=10)
        coord_f.pack(fill=tk.X, pady=5)
        ttk.Button(coord_f, text="🎯 Configure Coordinates", command=self._open_coordinate_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(coord_f, text="💾 Save Coordinates", command=self._save_coordinates).pack(side=tk.LEFT, padx=5)

        # Account config section
        acc_conf = ttk.LabelFrame(main, text="Account Configuration", padding=10)
        acc_conf.pack(fill=tk.X, pady=5)
        self.accounts_var = tk.StringVar(value="1")
        tk.Label(acc_conf, text="Number of Accounts:").pack(side=tk.LEFT)
        tk.Spinbox(acc_conf, from_=1, to=10, width=5, textvariable=self.accounts_var).pack(side=tk.LEFT, padx=10)
        ttk.Button(acc_conf, text="Generate Forms", command=self._generate_forms).pack(side=tk.LEFT)
        ttk.Button(acc_conf, text="💾 Save Accounts", command=self._save_accounts).pack(side=tk.LEFT, padx=5)
        ttk.Button(acc_conf, text="📂 Load Accounts", command=self._load_accounts).pack(side=tk.LEFT)

        # Scrollable account detail section
        self.detail_frame = ttk.LabelFrame(main, text="Account Details", padding=10)
        self.detail_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.canvas = tk.Canvas(self.detail_frame)
        self.scrollbar = ttk.Scrollbar(self.detail_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Action buttons
        act_f = ttk.LabelFrame(main, text="Actions", padding=10)
        act_f.pack(fill=tk.X, pady=5)
        self.start_btn = ttk.Button(act_f, text="🚀 Start Process", state="disabled", command=self._start_process)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(act_f, text="🔄 Clear All", command=self._clear_all).pack(side=tk.LEFT)

        # Progress & logs
        prog_f = ttk.LabelFrame(main, text="Progress & Status", padding=10)
        prog_f.pack(fill=tk.X, pady=5)
        self.progress = ttk.Progressbar(prog_f)
        self.progress.pack(fill=tk.X, pady=5)
        self.status_text = scrolledtext.ScrolledText(prog_f, height=8)
        self.status_text.pack(fill=tk.X)

        # Initial forms
        self._generate_forms()

    # ─────────────────────────────────────────────────────────────────────
    # Coordinate persistence
    # ─────────────────────────────────────────────────────────────────────
    def _load_coordinates(self):
        if os.path.exists(self.JSON_COORDS):
            with open(self.JSON_COORDS) as f:
                self.coordinates = json.load(f)
            self._log("📍 Coordinates loaded")
        else:
            # Empty template
            keys = [
                'login_username', 'login_password', 'login_button', 'signup_button',
                'reg_username', 'reg_password', 'reg_confirm', 'reg_button',
                'play_now', 'address_bar', 'id_button', 'logout_button'
            ]
            self.coordinates = {k: {'x': 0, 'y': 0} for k in keys}

    def _save_coordinates(self):
        with open(self.JSON_COORDS, 'w') as f:
            json.dump(self.coordinates, f, indent=2)
        self._log("💾 Coordinates saved")
        messagebox.showinfo("Success", "Coordinates saved successfully!")

    # ─────────────────────────────────────────────────────────────────────
    # Account persistence
    # ─────────────────────────────────────────────────────────────────────
    def _save_accounts(self):
        accounts = self._collect_accounts()
        if accounts is None:
            return
        with open(self.JSON_ACCOUNTS, 'w') as f:
            json.dump([asdict(acc) for acc in accounts], f, indent=2)
        self._log("💾 Accounts saved")
        messagebox.showinfo("Success", "Accounts saved successfully!")

    def _load_accounts(self):
        if not os.path.exists(self.JSON_ACCOUNTS):
            messagebox.showerror("Error", "No saved accounts file found")
            return
        with open(self.JSON_ACCOUNTS) as f:
            data = json.load(f)
        accounts = [AccountData.from_dict(d) for d in data]
        self.accounts_var.set(str(len(accounts)))
        self._generate_forms()
        for entry, acc in zip(self.entries, accounts):
            entry['action_var'].set(acc.action_type)
            entry['username_var'].set(acc.username)
            entry['password_var'].set(acc.password)
            entry['confirm_var'].set(acc.confirm_password or "")
            entry['server_var'].set(acc.server_number)
            # Ensure confirm field visibility
            if acc.action_type == "register":
                entry['confirm_frame'].pack(fill=tk.X, pady=2)
        self._log("📂 Accounts loaded")
        messagebox.showinfo("Success", "Accounts loaded successfully!")

    # ─────────────────────────────────────────────────────────────────────
    # Accounts form handling
    # ─────────────────────────────────────────────────────────────────────
    def _generate_forms(self):
        for w in self.scrollable_frame.winfo_children():
            w.destroy()
        self.entries.clear()

        for i in range(int(self.accounts_var.get())):
            frame = ttk.LabelFrame(self.scrollable_frame, text=f"Account {i+1}", padding=8)
            frame.pack(fill=tk.X, pady=3, padx=3)

            # First row: action & server
            row1 = ttk.Frame(frame)
            row1.pack(fill=tk.X, pady=2)
            tk.Label(row1, text="Action:").pack(side=tk.LEFT)
            action_var = tk.StringVar(value="login")
            action_cb = ttk.Combobox(row1, textvariable=action_var, values=["login", "register"], state="readonly", width=10)
            action_cb.pack(side=tk.LEFT)
            tk.Label(row1, text="Server:").pack(side=tk.LEFT, padx=(15, 0))
            server_var = tk.StringVar(value="7")
            ttk.Entry(row1, textvariable=server_var, width=8).pack(side=tk.LEFT)

            # Username row
            row2 = ttk.Frame(frame)
            row2.pack(fill=tk.X, pady=2)
            tk.Label(row2, text="Username:").pack(side=tk.LEFT)
            username_var = tk.StringVar()
            ttk.Entry(row2, textvariable=username_var, width=25).pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Password row
            row3 = ttk.Frame(frame)
            row3.pack(fill=tk.X, pady=2)
            tk.Label(row3, text="Password:").pack(side=tk.LEFT)
            password_var = tk.StringVar()
            ttk.Entry(row3, textvariable=password_var, show="*", width=25).pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Confirm row (initially hidden)
            row4 = ttk.Frame(frame)
            confirm_var = tk.StringVar()
            tk.Label(row4, text="Confirm:").pack(side=tk.LEFT)
            ttk.Entry(row4, textvariable=confirm_var, show="*", width=25).pack(side=tk.LEFT, fill=tk.X, expand=True)

            def toggle_confirm(event=None, rf=row4, cb=action_cb):
                rf.pack_forget() if cb.get() == "login" else rf.pack(fill=tk.X, pady=2)
            action_cb.bind('<<ComboboxSelected>>', toggle_confirm)
            toggle_confirm()

            self.entries.append({
                'action_var': action_var, 'username_var': username_var, 'password_var': password_var,
                'confirm_var': confirm_var, 'server_var': server_var, 'confirm_frame': row4
            })

        self._update_scroll()
        self.start_btn.config(state="normal")

    def _update_scroll(self):
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # ─────────────────────────────────────────────────────────────────────
    # Account data helpers
    # ─────────────────────────────────────────────────────────────────────
    def _collect_accounts(self) -> List[AccountData] | None:
        accounts = []
        for i, e in enumerate(self.entries, start=1):
            act, usr, pwd, conf, srv = (e[x].get().strip() for x in ('action_var', 'username_var', 'password_var', 'confirm_var', 'server_var'))
            if not usr or not pwd:
                messagebox.showerror("Error", f"Account {i}: Username and password required")
                return None
            if act == "register" and not conf:
                messagebox.showerror("Error", f"Account {i}: Confirm password required for registration")
                return None
            accounts.append(AccountData(usr, pwd, conf or None, act, srv))
        return accounts

    # ─────────────────────────────────────────────────────────────────────
    # Start process
    # ─────────────────────────────────────────────────────────────────────
    def _start_process(self):
        if all(c['x'] == 0 and c['y'] == 0 for c in self.coordinates.values()):
            messagebox.showerror("Error", "Please configure coordinates first!")
            return
        accounts = self._collect_accounts()
        if accounts is None:
            return
        self.start_btn.config(state="disabled")
        threading.Thread(target=self._run_automation, args=(accounts,), daemon=True).start()

    # ─────────────────────────────────────────────────────────────────────
    # Logging helper
    # ─────────────────────────────────────────────────────────────────────
    def _log(self, msg: str):
        self.status_text.insert(tk.END, msg + "\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()

    # ─────────────────────────────────────────────────────────────────────
    # Automation core (unchanged logic)
    # ─────────────────────────────────────────────────────────────────────
    # Helper wrappers -----------------------------------------------------
    def _open_uc_browser(self):
        self._log("🌐 Opening UC Browser…")
        try:
            subprocess.Popen([self.uc_browser_path])
            time.sleep(1)  # shortened to 1 second
            return True
        except Exception as e:
            self._log(f"❌ Failed to open UC Browser: {e}")
            return False

    def _focus_uc_browser(self):
        windows = gw.getWindowsWithTitle("UC") or gw.getWindowsWithTitle("Browser")
        if windows:
            window = windows[0]
            window.maximize()
            window.activate()
            time.sleep(1)
            return True
        return False

    def _click(self, name: str, wait: float = 0.2):
        if name in self.coordinates:
            coord = self.coordinates[name]
            pyautogui.click(coord['x'], coord['y'])
            time.sleep(wait)
            return True
        return False

    def _type(self, text: str, clear: bool = True):
        if clear: pyautogui.hotkey('ctrl', 'a'); time.sleep(0.1)
        pyautogui.write(text); time.sleep(0.2)

    # Action blocks -------------------------------------------------------
    def _perform_login(self, acc: AccountData):
        self._log("🔑 Login…")
        self._click('login_username')
        self._type(acc.username)
        self._click('login_password')
        self._type(acc.password)
        self._click('login_button')
        time.sleep(0.3)
        self._log("✅ Login done")

    def _perform_register(self, acc: AccountData):
        self._log("📝 Register…")
        self._click('signup_button')
        time.sleep(1)
        self._click('reg_username')
        self._type(acc.username)
        self._click('reg_password')
        self._type(acc.password)
        self._click('reg_confirm')
        self._type(acc.confirm_password)
        self._click('reg_button')
        self._click('play_now')
        self._log("✅ Register done")

    def _access_server(self, server: str):
        url = f"s{server}.cot.heyshell.com"
        self._log(f"🎮 Opening server {server}…")
        self._click('address_bar')
        self._type(url)
        pyautogui.press('enter')
        time.sleep(5)  # set to 5 seconds after opening server
        self._log(f"✅ Server {server} ready")

    # Main loop -----------------------------------------------------------
    def _run_automation(self, accounts: List[AccountData]):
        try:
            if not self._open_uc_browser():
                return
            self.progress['maximum'] = len(accounts)
            for i, acc in enumerate(accounts):
                self._log(f"\n📍 Processing Account {i+1}: {acc.username}")
                self._focus_uc_browser()
                if i > 0:
                    pyautogui.hotkey('ctrl', 't')
                    self._click('address_bar')
                    self._type("heyshell.com/cot/")
                    pyautogui.press('enter')
                    time.sleep(1)
                    self._click('id_button')
                    self._click('logout_button')
                if i == 0:
                    self._click('address_bar')
                    self._type("heyshell.com/cot/")
                    pyautogui.press('enter')
                    time.sleep(1)
                if acc.action_type == "register":
                    self._perform_register(acc)
                else:
                    self._perform_login(acc)
                self._access_server(acc.server_number)
                self.progress['value'] = i + 1
                self.root.update_idletasks()
            self._log("\n✅ All accounts processed!")
            messagebox.showinfo("Complete", "Process completed for all accounts!")
        finally:
            self.start_btn.config(state="normal")

    # ─────────────────────────────────────────────────────────────────────
    # Misc
    # ─────────────────────────────────────────────────────────────────────
    def _open_coordinate_config(self):
        CoordinateConfigWindow(self)

    def _clear_all(self):
        for e in self.entries:
            e['action_var'].set("login")
            e['username_var'].set(""); e['password_var'].set("")
            e['confirm_var'].set(""); e['server_var'].set("7")
            e['confirm_frame'].pack_forget()
        self.status_text.delete(1.0, tk.END); self.progress['value'] = 0

# ─────────────────────────────────────────────────────────────────────────────
# Coordinate Config Window (unchanged, minor refactor for brevity)
# ─────────────────────────────────────────────────────────────────────────────
class CoordinateConfigWindow:
    LABELS = {
        'login_username': 'Login Username Field',
        'login_password': 'Login Password Field',
        'login_button': 'Login Button',
        'signup_button': 'SignUp Button',
        'reg_username': 'Register Username Field',
        'reg_password': 'Register Password Field',
        'reg_confirm': 'Register Confirm Password Field',
        'reg_button': 'Register Button',
        'play_now': 'Play Now Button',
        'address_bar': 'Browser Address Bar',
        'id_button': 'ID Button',
        'logout_button': 'Logout Button',
    }

    def __init__(self, app: UCBrowserAutoManager):
        self.app = app
        self.win = tk.Toplevel(app.root)
        self.win.title("Coordinate Configuration"); self.win.geometry("600x700"); self.win.grab_set()
        self._build()

    def _build(self):
        tk.Label(self.win, text="Click 'Capture' then click on the element in UC Browser\nYou have 3 seconds after clicking to position your mouse", fg="blue", wraplength=550).pack(pady=10)
        canvas = tk.Canvas(self.win); scr = ttk.Scrollbar(self.win, orient="vertical", command=canvas.yview)
        frm = ttk.Frame(canvas); canvas.configure(yscrollcommand=scr.set)
        canvas.create_window((0,0), window=frm, anchor="nw"); canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self.coord_vars = {}
        for k, lab in self.LABELS.items():
            f = ttk.Frame(frm); f.pack(fill=tk.X, pady=2, padx=10)
            tk.Label(f, text=lab, width=25).pack(side=tk.LEFT)
            x_var, y_var = tk.StringVar(value=str(self.app.coordinates[k]['x'])), tk.StringVar(value=str(self.app.coordinates[k]['y']))
            ttk.Label(f, text="X:").pack(side=tk.LEFT); ttk.Entry(f, textvariable=x_var, width=8).pack(side=tk.LEFT, padx=5)
            ttk.Label(f, text="Y:").pack(side=tk.LEFT); ttk.Entry(f, textvariable=y_var, width=8).pack(side=tk.LEFT, padx=5)
            ttk.Button(f, text="Capture", command=lambda ck=k,xv=x_var,yv=y_var:self._capture(ck,xv,yv)).pack(side=tk.LEFT, padx=5)
            self.coord_vars[k] = {'x': x_var, 'y': y_var}
        canvas.pack(side="left", fill="both", expand=True); scr.pack(side="right", fill="y")
        bfr = ttk.Frame(self.win); bfr.pack(pady=10)
        ttk.Button(bfr, text="Save & Close", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(bfr, text="Cancel", command=self.win.destroy).pack(side=tk.LEFT)

    # Capture coord
    def _capture(self, key, xv, yv):
        messagebox.showinfo("Capture", f"Window will minimize. Click on '{key}' in UC Browser.")
        def on_click(x, y, button, pressed):
            if pressed:
                xv.set(str(x)); yv.set(str(y)); return False
        def worker():
            self.win.withdraw(); self.app.root.withdraw();
            from pynput import mouse
            with mouse.Listener(on_click=on_click) as listener: listener.join()
            self.app.root.deiconify(); self.win.deiconify(); self.win.lift()
        threading.Thread(target=worker, daemon=True).start()

    def _save(self):
        for k, var in self.coord_vars.items():
            try:
                self.app.coordinates[k] = {'x': int(var['x'].get()), 'y': int(var['y'].get())}
            except ValueError:
                messagebox.showerror("Error", f"Invalid coordinate for {k}"); return
        self.app._save_coordinates(); self.win.destroy()

# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk(); app = UCBrowserAutoManager(root)
    root.eval('tk::PlaceWindow . center'); root.mainloop()
