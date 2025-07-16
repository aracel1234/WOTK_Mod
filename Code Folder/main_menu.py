import tkinter as tk
from tkinter import ttk, messagebox
import subprocess, os, sys

# Base folder: lokasi fisik Bot_Clash_of_TK.exe berada
BASE_DIR = os.path.dirname(sys.executable)

# Map label tombol → path .exe (relatif thd lokasi launcher .exe)
APPS = {
    "Auto Login":             os.path.join(BASE_DIR, "Auto_Login",          "Auto_Login_Persistent.exe"),
    "Auto Quest Mysteriland": os.path.join(BASE_DIR, "Auto_Quest_Mysteriland", "Auto_Quest_Mysteriland.exe"),
    "Auto Quest Supremacy":   os.path.join(BASE_DIR, "Auto_Quest_Supremacy",   "Auto_Quest_Supremacy.exe"),
    "Auto Quest Individual":  os.path.join(BASE_DIR, "Auto_Quest_Individual",  "Auto_Quest_Individual.exe"),
    "Auto War":               os.path.join(BASE_DIR, "Auto_War",              "Auto_War.exe"),
}

def launch_app(app_name):
    path = APPS[app_name]
    if not os.path.exists(path):
        messagebox.showerror("File Not Found", f"Tidak menemukan file:\n{path}")
        return
    try:
        subprocess.Popen([path])
    except Exception as e:
        messagebox.showerror("Launch Error", f"Gagal membuka {app_name}:\n{str(e)}")

# GUI
root = tk.Tk()
root.title("Clash of Three Kingdom Bot")
root.geometry("500x400")
root.configure(bg="#1e1e1e")

tk.Label(root, text="Clash of Three Kingdom Bot",
         font=("Helvetica", 18, "bold"),
         fg="white", bg="#1e1e1e").pack(pady=30)

style = ttk.Style()
style.configure("TButton", font=("Segoe UI", 12), padding=10)
frame = ttk.Frame(root)
frame.pack()

for app in APPS:
    ttk.Button(frame, text=app, width=35, command=lambda a=app: launch_app(a)).pack(pady=6)

root.mainloop()
