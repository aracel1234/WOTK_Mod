import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyautogui
import cv2
import pytesseract
import numpy as np
import json
import time
import threading
import os
from PIL import Image, ImageTk

class AutoWarSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Auto War Game System")
        self.root.geometry("800x600")
        
        # Konfigurasi Tesseract
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        self.tesseract_path = os.path.join(base_dir, "Tesseract-OCR")
        pytesseract.pytesseract.tesseract_cmd = os.path.join(self.tesseract_path, 'tesseract.exe')
        
        # Path konfigurasi
        self.config_path = r"C:\Users\Aracel Nestova\Downloads\ClashTK_AutoLogin\Auto_War\configuration_save"
        self.ocr_log_path = os.path.join(self.config_path, "ocr_log.txt")
        self.ensure_config_folders()
        
        # Variabel sistem
        self.static_coords = {}
        self.ocr_areas = {}
        self.city_lists = {}
        self.account_count = 1
        self.target_city_color = "merah"
        self.account_colors = []
        
        # Variabel kontrol looping
        self.is_running = False
        self.timer_thread = None
        
        # Setup GUI
        self.setup_gui()
        
        # Konfigurasi PyAutoGUI
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
    
    def ensure_config_folders(self):
        """Membuat folder konfigurasi jika belum ada"""
        folders = ['koordinat_statis', 'area_ocr', 'city_lists']
        for folder in folders:
            path = os.path.join(self.config_path, folder)
            if not os.path.exists(path):
                os.makedirs(path)
    
    def setup_gui(self):
        """Setup GUI utama"""
        # Notebook untuk tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab Konfigurasi Koordinat
        self.setup_coordinate_tab(notebook)
        
        # Tab Konfigurasi OCR
        self.setup_ocr_tab(notebook)
        
        # Tab Konfigurasi Akun dan Kota
        self.setup_account_tab(notebook)
        
        # Tab Testing
        self.setup_testing_tab(notebook)
        
        # Tab Eksekusi
        self.setup_execution_tab(notebook)
    
    def setup_coordinate_tab(self, notebook):
        """Setup tab konfigurasi koordinat"""
        coord_frame = ttk.Frame(notebook)
        notebook.add(coord_frame, text="Koordinat Statis")
        
        # Frame untuk kontrol
        control_frame = ttk.LabelFrame(coord_frame, text="Konfigurasi Koordinat", padding=10)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Nama user
        ttk.Label(control_frame, text="Nama User:").grid(row=0, column=0, sticky='w', pady=2)
        self.user_name_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.user_name_var, width=20).grid(row=0, column=1, pady=2)
        
        # Tombol untuk capture koordinat
        buttons = [
            ("Bendera Biru", "bendera_biru"),
            ("Search", "search"),
            ("Field Search", "field_search"),
            ("Konfirmasi Search", "konfirmasi_search"),
            ("Nama Kota", "nama_kota"),
            ("Fight", "fight"),
            ("Dispatch", "dispatch"),
            ("Minimize", "minimize"),
            ("Watch", "watch"),
            ("March", "march"),
            ("Back", "back"),
            ("Exit", "exit")
        ]
        
        row = 1
        for i, (text, key) in enumerate(buttons):
            if i % 3 == 0 and i > 0:
                row += 1
            
            btn = ttk.Button(control_frame, text=f"Capture {text}", 
                           command=lambda k=key: self.capture_coordinate(k))
            btn.grid(row=row, column=i%3, padx=5, pady=2, sticky='ew')
        
        # Frame untuk menampilkan koordinat
        display_frame = ttk.LabelFrame(coord_frame, text="Koordinat Tersimpan", padding=10)
        display_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.coord_text = tk.Text(display_frame, height=15, width=70)
        scrollbar = ttk.Scrollbar(display_frame, orient="vertical", command=self.coord_text.yview)
        self.coord_text.configure(yscrollcommand=scrollbar.set)
        self.coord_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Tombol save/load
        button_frame = ttk.Frame(coord_frame)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame, text="Save Koordinat", command=self.save_coordinates).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Load Koordinat", command=self.load_coordinates).pack(side='left', padx=5)
    
    def setup_ocr_tab(self, notebook):
        """Setup tab konfigurasi OCR"""
        ocr_frame = ttk.Frame(notebook)
        notebook.add(ocr_frame, text="Area OCR")
        
        control_frame = ttk.LabelFrame(ocr_frame, text="Konfigurasi Area OCR", padding=10)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Nama user
        ttk.Label(control_frame, text="Nama User:").grid(row=0, column=0, sticky='w', pady=2)
        self.ocr_user_name_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.ocr_user_name_var, width=20).grid(row=0, column=1, pady=2)
        
        # Tombol untuk capture area OCR
        ocr_areas = [
            ("Watch", "watch_area"),
            ("Defender", "defender_area"),
            ("Please Select City", "select_city_area")
        ]
        
        for i, (text, key) in enumerate(ocr_areas):
            btn = ttk.Button(control_frame, text=f"Capture Area {text}", 
                           command=lambda k=key: self.capture_ocr_area(k))
            btn.grid(row=i+1, column=0, columnspan=2, pady=2, sticky='ew')
        
        # Display area
        display_frame = ttk.LabelFrame(ocr_frame, text="Area OCR Tersimpan", padding=10)
        display_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.ocr_text = tk.Text(display_frame, height=15, width=70)
        scrollbar2 = ttk.Scrollbar(display_frame, orient="vertical", command=self.ocr_text.yview)
        self.ocr_text.configure(yscrollcommand=scrollbar2.set)
        self.ocr_text.pack(side='left', fill='both', expand=True)
        scrollbar2.pack(side='right', fill='y')
        
        # Tombol save/load
        button_frame2 = ttk.Frame(ocr_frame)
        button_frame2.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame2, text="Save Area OCR", command=self.save_ocr_areas).pack(side='left', padx=5)
        ttk.Button(button_frame2, text="Load Area OCR", command=self.load_ocr_areas).pack(side='left', padx=5)
    
    def setup_account_tab(self, notebook):
        """Setup tab konfigurasi akun dan kota"""
        account_frame = ttk.Frame(notebook)
        notebook.add(account_frame, text="Akun & Kota")
        
        # Konfigurasi jumlah akun
        account_config_frame = ttk.LabelFrame(account_frame, text="Konfigurasi Akun", padding=10)
        account_config_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(account_config_frame, text="Jumlah Akun:").grid(row=0, column=0, sticky='w', pady=2)
        self.account_count_var = tk.IntVar(value=1)
        account_spin = ttk.Spinbox(account_config_frame, from_=1, to=10, textvariable=self.account_count_var, width=10)
        account_spin.grid(row=0, column=1, pady=2)
        
        ttk.Label(account_config_frame, text="Warna Kota Target:").grid(row=1, column=0, sticky='w', pady=2)
        self.target_color_var = tk.StringVar(value="merah")
        color_combo = ttk.Combobox(account_config_frame, textvariable=self.target_color_var, 
                                  values=["merah", "hijau", "biru"], state="readonly", width=10)
        color_combo.grid(row=1, column=1, pady=2)
        
        ttk.Button(account_config_frame, text="Generate Form Akun", 
                  command=self.generate_account_forms).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Frame untuk form akun
        self.account_forms_frame = ttk.LabelFrame(account_frame, text="Warna Kota Per Akun", padding=10)
        self.account_forms_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # List kota
        city_frame = ttk.LabelFrame(account_frame, text="Daftar Kota", padding=10)
        city_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(city_frame, text="Masukkan daftar kota (satu per baris):").pack(anchor='w')
        self.city_list_text = tk.Text(city_frame, height=5, width=50)
        self.city_list_text.pack(fill='x', pady=5)
        
        # Default city list
        default_cities = "Dongxing\nMianzhu\nWeiXian"
        self.city_list_text.insert('1.0', default_cities)
        
        # Tombol save/load
        button_frame3 = ttk.Frame(account_frame)
        button_frame3.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame3, text="Save Konfigurasi", command=self.save_account_config).pack(side='left', padx=5)
        ttk.Button(button_frame3, text="Load Konfigurasi", command=self.load_account_config).pack(side='left', padx=5)
    
    def setup_testing_tab(self, notebook):
        """Setup tab testing"""
        test_frame = ttk.Frame(notebook)
        notebook.add(test_frame, text="Testing")
        
        # Testing koordinat
        coord_test_frame = ttk.LabelFrame(test_frame, text="Test Koordinat", padding=10)
        coord_test_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(coord_test_frame, text="Pilih koordinat untuk ditest:").pack(anchor='w')
        self.test_coord_var = tk.StringVar()
        self.test_coord_combo = ttk.Combobox(coord_test_frame, textvariable=self.test_coord_var, state="readonly")
        self.test_coord_combo.pack(fill='x', pady=5)
        
        ttk.Button(coord_test_frame, text="Test Click Koordinat", command=self.test_coordinate).pack(pady=5)
        
        # Testing OCR
        ocr_test_frame = ttk.LabelFrame(test_frame, text="Test OCR", padding=10)
        ocr_test_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(ocr_test_frame, text="Pilih area OCR untuk ditest:").pack(anchor='w')
        self.test_ocr_var = tk.StringVar()
        self.test_ocr_combo = ttk.Combobox(ocr_test_frame, textvariable=self.test_ocr_var, state="readonly")
        self.test_ocr_combo.pack(fill='x', pady=5)
        
        ttk.Button(ocr_test_frame, text="Test OCR Area", command=self.test_ocr).pack(pady=5)
        
        # Hasil test
        result_frame = ttk.LabelFrame(test_frame, text="Hasil Test", padding=10)
        result_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.test_result_text = tk.Text(result_frame, height=10, width=70)
        scrollbar3 = ttk.Scrollbar(result_frame, orient="vertical", command=self.test_result_text.yview)
        self.test_result_text.configure(yscrollcommand=scrollbar3.set)
        self.test_result_text.pack(side='left', fill='both', expand=True)
        scrollbar3.pack(side='right', fill='y')
    
    def setup_execution_tab(self, notebook):
        """Setup tab eksekusi"""
        exec_frame = ttk.Frame(notebook)
        notebook.add(exec_frame, text="Eksekusi")
        
        # Status frame
        status_frame = ttk.LabelFrame(exec_frame, text="Status Sistem", padding=10)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.status_var = tk.StringVar(value="Siap untuk dijalankan")
        ttk.Label(status_frame, textvariable=self.status_var, font=('Arial', 12)).pack()
        
        # Control buttons
        control_frame = ttk.Frame(exec_frame)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="START SYSTEM", command=self.start_system)
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="STOP SYSTEM", command=self.stop_system, state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(exec_frame, text="Log Sistem", padding=10)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=15, width=70)
        scrollbar4 = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar4.set)
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar4.pack(side='right', fill='y')
    
    def capture_coordinate(self, coord_name):
        """Capture koordinat dengan delay 3 detik"""
        self.log_message(f"Persiapan capture koordinat {coord_name}. Posisikan mouse dalam 3 detik...")
        
        def capture_after_delay():
            time.sleep(3)
            x, y = pyautogui.position()
            self.static_coords[coord_name] = (x, y)
            self.update_coordinate_display()
            self.log_message(f"Koordinat {coord_name} berhasil dicapture: ({x}, {y})")
        
        threading.Thread(target=capture_after_delay, daemon=True).start()
    
    def capture_ocr_area(self, area_name):
        """Capture area OCR dengan drag selection"""
        messagebox.showinfo("Capture Area OCR", 
                           f"Akan capture area {area_name}.\n\n"
                           "Instruksi:\n"
                           "1. Klik OK\n"
                           "2. Tunggu 3 detik\n"
                           "3. Drag mouse untuk select area\n"
                           "4. Area akan otomatis tersimpan")
        
        def capture_area():
            time.sleep(3)
            self.log_message(f"Mulai capture area {area_name}. Drag mouse untuk select area...")
            
            # Implementasi sederhana: user input koordinat manual untuk sekarang
            # Untuk implementasi drag yang kompleks, bisa ditambahkan kemudian
            x1 = pyautogui.position().x
            y1 = pyautogui.position().y
            
            messagebox.showinfo("Area Selection", "Klik OK lalu klik titik kedua untuk menentukan area")
            time.sleep(2)
            
            x2 = pyautogui.position().x
            y2 = pyautogui.position().y
            
            self.ocr_areas[area_name] = (min(x1,x2), min(y1,y2), abs(x2-x1), abs(y2-y1))
            self.update_ocr_display()
            self.log_message(f"Area {area_name} berhasil dicapture: ({min(x1,x2)}, {min(y1,y2)}, {abs(x2-x1)}, {abs(y2-y1)})")
        
        threading.Thread(target=capture_area, daemon=True).start()
    
    def update_coordinate_display(self):
        """Update display koordinat"""
        self.coord_text.delete('1.0', tk.END)
        for name, coord in self.static_coords.items():
            self.coord_text.insert(tk.END, f"{name}: {coord}\n")
        
        # Update combo box untuk testing
        self.test_coord_combo['values'] = list(self.static_coords.keys())
    
    def update_ocr_display(self):
        """Update display area OCR"""
        self.ocr_text.delete('1.0', tk.END)
        for name, area in self.ocr_areas.items():
            self.ocr_text.insert(tk.END, f"{name}: {area}\n")
        
        # Update combo box untuk testing
        self.test_ocr_combo['values'] = list(self.ocr_areas.keys())
    
    def generate_account_forms(self):
        """Generate form untuk setiap akun"""
        # Clear existing forms
        for widget in self.account_forms_frame.winfo_children():
            widget.destroy()
        
        self.account_color_vars = []
        account_count = self.account_count_var.get()
        target_color = self.target_color_var.get()
        
        # Available colors (exclude target color)
        all_colors = ["merah", "hijau", "biru"]
        available_colors = [c for c in all_colors if c != target_color]
        
        for i in range(account_count):
            frame = ttk.Frame(self.account_forms_frame)
            frame.pack(fill='x', pady=2)
            
            ttk.Label(frame, text=f"Akun {i+1}:").pack(side='left', padx=5)
            
            color_var = tk.StringVar(value=available_colors[0])
            color_combo = ttk.Combobox(frame, textvariable=color_var, 
                                     values=available_colors, state="readonly", width=10)
            color_combo.pack(side='left', padx=5)
            
            self.account_color_vars.append(color_var)
    
    def save_coordinates(self):
        """Save koordinat ke file"""
        user_name = self.user_name_var.get()
        if not user_name:
            messagebox.showerror("Error", "Masukkan nama user terlebih dahulu!")
            return
        
        filename = f"Koordinat_Statis_{user_name}.json"
        filepath = os.path.join(self.config_path, "koordinat_statis", filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.static_coords, f, indent=4)
            messagebox.showinfo("Sukses", f"Koordinat berhasil disimpan ke {filename}")
            self.log_message(f"Koordinat disimpan: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan koordinat: {str(e)}")
    
    def load_coordinates(self):
        """Load koordinat dari file"""
        filepath = filedialog.askopenfilename(
            initialdir=os.path.join(self.config_path, "koordinat_statis"),
            title="Pilih file koordinat",
            filetypes=[("JSON files", "*.json")]
        )
        
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    self.static_coords = json.load(f)
                self.update_coordinate_display()
                messagebox.showinfo("Sukses", "Koordinat berhasil dimuat!")
                self.log_message(f"Koordinat dimuat dari: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal memuat koordinat: {str(e)}")
    
    def save_ocr_areas(self):
        """Save area OCR ke file"""
        user_name = self.ocr_user_name_var.get()
        if not user_name:
            messagebox.showerror("Error", "Masukkan nama user terlebih dahulu!")
            return
        
        filename = f"Area_OCR_{user_name}.json"
        filepath = os.path.join(self.config_path, "area_ocr", filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.ocr_areas, f, indent=4)
            messagebox.showinfo("Sukses", f"Area OCR berhasil disimpan ke {filename}")
            self.log_message(f"Area OCR disimpan: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan area OCR: {str(e)}")
    
    def load_ocr_areas(self):
        """Load area OCR dari file"""
        filepath = filedialog.askopenfilename(
            initialdir=os.path.join(self.config_path, "area_ocr"),
            title="Pilih file area OCR",
            filetypes=[("JSON files", "*.json")]
        )
        
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    self.ocr_areas = json.load(f)
                self.update_ocr_display()
                messagebox.showinfo("Sukses", "Area OCR berhasil dimuat!")
                self.log_message(f"Area OCR dimuat dari: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal memuat area OCR: {str(e)}")
    
    def save_account_config(self):
        """Save konfigurasi akun dan kota"""
        if not hasattr(self, 'account_color_vars'):
            messagebox.showerror("Error", "Generate form akun terlebih dahulu!")
            return
        
        config = {
            'account_count': self.account_count_var.get(),
            'target_color': self.target_color_var.get(),
            'account_colors': [var.get() for var in self.account_color_vars],
            'city_list': self.city_list_text.get('1.0', tk.END).strip().split('\n')
        }
        
        filename = f"account_config_{int(time.time())}.json"
        filepath = os.path.join(self.config_path, "city_lists", filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=4)
            messagebox.showinfo("Sukses", f"Konfigurasi akun berhasil disimpan ke {filename}")
            self.log_message(f"Konfigurasi akun disimpan: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan konfigurasi akun: {str(e)}")
    
    def load_account_config(self):
        """Load konfigurasi akun dan kota"""
        filepath = filedialog.askopenfilename(
            initialdir=os.path.join(self.config_path, "city_lists"),
            title="Pilih file konfigurasi akun",
            filetypes=[("JSON files", "*.json")]
        )
        
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    config = json.load(f)
                
                self.account_count_var.set(config['account_count'])
                self.target_color_var.set(config['target_color'])
                
                # Load city list
                self.city_list_text.delete('1.0', tk.END)
                self.city_list_text.insert('1.0', '\n'.join(config['city_list']))
                
                # Generate forms and set colors
                self.generate_account_forms()
                for i, color in enumerate(config['account_colors']):
                    if i < len(self.account_color_vars):
                        self.account_color_vars[i].set(color)
                
                messagebox.showinfo("Sukses", "Konfigurasi akun berhasil dimuat!")
                self.log_message(f"Konfigurasi akun dimuat dari: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal memuat konfigurasi akun: {str(e)}")
    
    def test_coordinate(self):
        """Test klik koordinat"""
        coord_name = self.test_coord_var.get()
        if not coord_name or coord_name not in self.static_coords:
            messagebox.showerror("Error", "Pilih koordinat yang valid!")
            return
        
        x, y = self.static_coords[coord_name]
        self.log_message(f"Testing koordinat {coord_name}: ({x}, {y})")
        
        def test_click():
            time.sleep(2)  # Delay untuk persiapan
            pyautogui.click(x, y)
            self.log_message(f"Koordinat {coord_name} berhasil diklik!")
        
        threading.Thread(target=test_click, daemon=True).start()
    
    def test_ocr(self):
        """Test OCR area"""
        area_name = self.test_ocr_var.get()
        if not area_name or area_name not in self.ocr_areas:
            messagebox.showerror("Error", "Pilih area OCR yang valid!")
            return
        
        x, y, w, h = self.ocr_areas[area_name]
        self.log_message(f"Testing OCR area {area_name}: ({x}, {y}, {w}, {h})")
        
        try:
            # Screenshot area
            screenshot = pyautogui.screenshot(region=(x, y, w, h))

            # === SIMPAN PREVIEW ke OCR_Testing ===
            preview_dir = os.path.join(self.config_path, "OCR_Testing")
            os.makedirs(preview_dir, exist_ok=True)          # pastikan ada
            preview_path = os.path.join(preview_dir, f"{area_name}_{int(time.time())}.png")
            screenshot.save(preview_path)
            # ======================================
            
            # OCR
            text = pytesseract.image_to_string(screenshot, lang='eng')
            
            self.test_result_text.insert(tk.END, f"=== OCR Result for {area_name} ===\n")
            self.test_result_text.insert(tk.END, f"Text found: '{text.strip()}'\n")
            self.test_result_text.insert(tk.END, f"Region: ({x}, {y}, {w}, {h})\n\n")
            self.test_result_text.see(tk.END)
            
            self.log_message(f"OCR {area_name} selesai. Text: '{text.strip()}' (preview: {preview_path})")
            
        except Exception as e:
            error_msg = f"Error saat OCR {area_name}: {str(e)}"
            self.test_result_text.insert(tk.END, error_msg + "\n\n")
            self.test_result_text.see(tk.END)
            self.log_message(error_msg)
    
    def start_system(self):
        """Start sistem auto war"""
        # Validasi konfigurasi
        if not self.validate_configuration():
            return
        
        self.is_running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_var.set("Sistem sedang berjalan...")
        
        self.log_message("=== SISTEM AUTO WAR DIMULAI ===")
        
        # Start main system thread
        self.system_thread = threading.Thread(target=self.run_main_system, daemon=True)
        self.system_thread.start()
    
    def stop_system(self):
        """Stop sistem auto war"""
        self.is_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_var.set("Sistem dihentikan")
        
        self.log_message("=== SISTEM AUTO WAR DIHENTIKAN ===")
    
    def validate_configuration(self):
        """Validasi konfigurasi sebelum menjalankan sistem"""
        # Check koordinat statis
        required_coords = ['bendera_biru', 'search', 'field_search', 'konfirmasi_search', 
                          'nama_kota', 'fight', 'dispatch', 'minimize', 'watch', 'march', 'back', 'exit']
        
        missing_coords = [coord for coord in required_coords if coord not in self.static_coords]
        if missing_coords:
            messagebox.showerror("Error", f"Koordinat belum lengkap: {', '.join(missing_coords)}")
            return False
        
        # Check area OCR
        required_areas = ['watch_area', 'defender_area', 'select_city_area']
        missing_areas = [area for area in required_areas if area not in self.ocr_areas]
        if missing_areas:
            messagebox.showerror("Error", f"Area OCR belum lengkap: {', '.join(missing_areas)}")
            return False
        
        # Check account configuration
        if not hasattr(self, 'account_color_vars') or not self.account_color_vars:
            messagebox.showerror("Error", "Konfigurasi akun belum dibuat!")
            return False
        
        # Check city list
        city_list = self.city_list_text.get('1.0', tk.END).strip()
        if not city_list:
            messagebox.showerror("Error", "Daftar kota tidak boleh kosong!")
            return False
        
        target_color = self.target_color_var.get()
        # Pastikan warna akun tidak sama dgn target
        for idx, var in enumerate(self.account_color_vars, start=1):
            if var.get() == target_color:
                messagebox.showerror(
                    "Error",
                    f"Warna akun {idx} tidak boleh sama dengan warna target ({target_color})."
                )
                return False
        return True
    
    def run_main_system(self):
        try:
            account_count = self.account_count_var.get()

            # Ambil data dari GUI
            city_list = [city.strip() for city in self.city_list_text.get('1.0', tk.END).strip().split('\n') if city.strip()]
            account_colors = [var.get() for var in self.account_color_vars]
            target_color = self.target_color_var.get()

            # Mapping warna ke kota target
            color_to_city = {
                "merah": "Dongxing",
                "hijau": "Mianzhu",
                "biru": "WeiXian"
            }
            target_city = color_to_city.get(target_color, "Dongxing")

            while self.is_running:
                self.log_message("=== MULAI SIKLUS ===")

                # Step 8: Looping Perubahan Maps
                self.looping_perubahan_maps(account_count)
                if not self.is_running:
                    break

                # Step 9: P = 1 (Auto Fight satu kali)
                self.log_message("Menjalankan Auto Fight awal (P=1)...")

                # Step 10: Timer 31 menit dimulai (sebagai patokan)
                timer_end = time.time() + (31 * 60)
                self.log_message("Timer 31 menit dimulai...")

                # Step 11: Jalankan Auto Fight sekali
                self.looping_finding_kota(account_count, target_city)
                if not self.is_running:
                    break
                self.looping_auto_fight_akun(account_count)
                if not self.is_running:
                    break

                # Step 12–13: Langsung lanjut ke Check Kondisi (Q=1)
                self.log_message("Memulai Looping Check Kondisi...")

                while self.is_running and time.time() < timer_end:
                    self.looping_check_kondisi(account_count, city_list, account_colors, color_to_city)
                    time.sleep(2)  # jeda kecil agar CPU tidak full load

                self.log_message("Timer selesai. Kembali ke Looping Perubahan Maps.")

                # Jeda kecil sebelum siklus berikutnya
                time.sleep(5)

        except Exception as e:
            self.log_message(f"ERROR dalam sistem utama: {str(e)}")
            messagebox.showerror("Error", f"Terjadi error dalam sistem: {str(e)}")
        finally:
            self.stop_system()
    
    def looping_perubahan_maps(self, account_count):
        """Looping perubahan maps"""
        self.log_message("Memulai looping perubahan maps...")
        
        for n in range(account_count):
            if not self.is_running:
                break
                
            self.log_message(f"Perubahan maps akun {n+1}")
            
            # 1. Tekan tombol bendera biru
            self.click_coordinate('bendera_biru')
            time.sleep(1)
            
            # 2. Ctrl+Tab untuk berganti tab
            pyautogui.hotkey('ctrl', 'tab')
            time.sleep(2)
    
    def looping_finding_kota(self, account_count, target_city):
        """Looping finding kota"""
        self.log_message(f"Mencari kota {target_city} untuk semua akun...")
        
        for o in range(account_count):
            if not self.is_running:
                break
                
            self.log_message(f"Finding kota untuk akun {o+1}")
            
            # 1. Tekan tombol search
            self.click_coordinate('search')
            time.sleep(1)
            
            # 2. Clear field search (klik 3x + delete)
            self.click_coordinate('field_search')
            time.sleep(0.5)
            for _ in range(3):
                pyautogui.click()
                time.sleep(0.1)
            pyautogui.key('delete')
            time.sleep(0.5)
            
            # 3. Ketik nama kota target
            pyautogui.write(target_city)
            time.sleep(1)
            
            # 4. Tekan tombol konfirmasi search
            self.click_coordinate('konfirmasi_search')
            time.sleep(2)
            
            # 6. Ctrl+Tab untuk berganti akun
            pyautogui.hotkey('ctrl', 'tab')
            time.sleep(1)
    
    def looping_auto_fight_akun(self, account_count):
        """Auto fight untuk semua akun"""
        self.log_message("Memulai auto fight untuk semua akun...")
        
        for p in range(account_count):
            if not self.is_running:
                break
                
            self.log_message(f"Auto fight akun {p+1}")
            
            # 1. Tekan tombol nama kota
            self.click_coordinate('nama_kota')
            time.sleep(1)
            
            # 2. Tekan tombol fight
            self.click_coordinate('fight')
            time.sleep(1)
            
            # 3. Tekan tombol dispatch
            self.click_coordinate('dispatch')
            time.sleep(1)
            
            # 4. Tekan tombol minimize
            self.click_coordinate('minimize')
            time.sleep(1)
            
            # 5. Ctrl+Tab untuk berganti akun
            pyautogui.hotkey('ctrl', 'tab')
            time.sleep(1)
    
    def looping_check_kondisi(self, account_count, city_list, account_colors, color_to_city):
        """Looping check kondisi"""
        self.log_message("Memulai check kondisi...")
        
        Q = 1
        
        for account_idx in range(account_count):
            if not self.is_running:
                break
            
            self.log_message(f"Check kondisi akun {account_idx+1}")
            
            # Reset Q untuk setiap akun
            Q = 1
            account_color = account_colors[account_idx]
            account_city = color_to_city.get(account_color, "Dongxing")
            
            while Q <= len(city_list) and self.is_running:
                city_to_check = city_list[Q-1]  # Q dimulai dari 1
                
                self.log_message(f"Checking kota {city_to_check} (Q={Q})")
                
                # 1. Tekan tombol search
                self.click_coordinate('search')
                time.sleep(1)
                
                # 2. Clear field search
                self.click_coordinate('field_search')
                time.sleep(0.5)
                for _ in range(3):
                    pyautogui.click()
                    time.sleep(0.1)
                pyautogui.key('delete')
                time.sleep(0.5)
                
                # 3. Ketik nama kota sesuai urutan
                pyautogui.write(city_to_check)
                time.sleep(1)
                
                # 4. Tekan konfirmasi search
                self.click_coordinate('konfirmasi_search')
                time.sleep(2)
                
                # 5. Tekan nama kota
                self.click_coordinate('nama_kota')
                time.sleep(2)
                
                # 6. Check apakah ada tulisan "watch"
                has_watch = self.check_text_in_area('watch_area', 'watch')
                
                if has_watch:
                    self.log_message(f"Ditemukan 'watch' di kota {city_to_check}")
                    
                    # Tekan tombol watch
                    self.click_coordinate('watch')
                    time.sleep(1)
                    
                    # Auto March
                    self.auto_march(Q, city_list, account_city)
                    
                    Q += 1
                else:
                    self.log_message(f"Tidak ada 'watch' di kota {city_to_check}")
                    
                    # Check apakah ada "defender"
                    has_defender = self.check_text_in_area('defender_area', 'defender')
                    
                    if not has_defender:
                        self.log_message(f"Tidak ada 'defender' di kota {city_to_check}, menghapus dari list")
                        # Hapus kota dari list (implementasi sederhana: skip)
                    
                    # Reset Q dan pindah akun
                    Q = 1
                    
                    # Tekan tombol exit
                    self.click_coordinate('exit')
                    time.sleep(1)
                    
                    break  # Keluar dari loop kota untuk akun ini
            
            # Pindah ke akun berikutnya
            pyautogui.hotkey('ctrl', 'tab')
            time.sleep(1)
    
    def auto_march(self, Q, city_list, account_city):
        """Fungsi auto march"""
        self.log_message("Memulai auto march...")
        
        
        # Tekan tombol march
        self.click_coordinate('march')
        time.sleep(2)
        
        # Check apakah ada tulisan "Please Select the city you want to visit"
        has_select_text = self.check_text_in_area('select_city_area', 'Please Select the city you want to visit')
        
        if has_select_text:
            self.log_message("Ditemukan dialog 'Please Select the city you want to visit'")
            
            # Cari kota tujuan (Q + 1)
            target_index = Q + 1
            
            if target_index < len(city_list):
                target_city = city_list[target_index]
                self.log_message(f"March ke kota {target_city}")
                
                # Tekan search
                self.click_coordinate('search')
                time.sleep(1)
                
                # Clear field
                self.click_coordinate('field_search')
                time.sleep(0.5)
                for _ in range(3):
                    pyautogui.click()
                    time.sleep(0.1)
                pyautogui.key('delete')
                time.sleep(0.5)
                
                # Ketik nama kota tujuan
                pyautogui.write(target_city)
                time.sleep(1)
                
                # Konfirmasi search
                self.click_coordinate('konfirmasi_search')
                time.sleep(2)
                
                # Tekan nama kota
                self.click_coordinate('nama_kota')
                time.sleep(1)
            else:
                self.log_message("Index kota tujuan melebihi daftar kota")
        else:
            self.log_message("Tidak ada dialog select city, tekan back")
            self.click_coordinate('back')
            time.sleep(1)    
    
    def check_text_in_area(self, area_name, target_text):
        """Check apakah text tertentu ada di area OCR"""
        try:
            if area_name not in self.ocr_areas:
                self.log_message(f"Area OCR {area_name} tidak ditemukan")
                return False

            x, y, w, h = self.ocr_areas[area_name]
            screenshot = pyautogui.screenshot(region=(x, y, w, h))
            text = pytesseract.image_to_string(screenshot, lang='eng').lower().strip()
            target = target_text.lower().strip()
            result = target in text

            # --- LOG KE FILE ---
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(self.ocr_log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {area_name}: '{text}' | target='{target}' | match={result}\n")

            self.log_message(f"OCR {area_name}: '{text}' | Looking for: '{target}' | Found: {result}")
            return result
        except Exception as e:
            self.log_message(f"Error saat OCR {area_name}: {str(e)}")
            return False
    
    def click_coordinate(self, coord_name):
        """Click koordinat berdasarkan nama"""
        if coord_name in self.static_coords:
            x, y = self.static_coords[coord_name]
            pyautogui.click(x, y)
            self.log_message(f"Clicked {coord_name} at ({x}, {y})")
        else:
            self.log_message(f"Koordinat {coord_name} tidak ditemukan!")
    
    def log_message(self, message):
        """Log message ke text widget"""
        timestamp = time.strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        # Insert ke log text widget
        self.log_text.insert(tk.END, full_message)
        self.log_text.see(tk.END)
        
        # Update GUI
        self.root.update_idletasks()
        
        # Print ke console juga
        print(full_message.strip())
    
    def run(self):
        """Run aplikasi"""
        self.root.mainloop()

# Main execution
if __name__ == "__main__":
    app = AutoWarSystem()
    app.run()