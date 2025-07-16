import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import glob
from tkinter import simpledialog, filedialog
import pyautogui
import time
import json
import os
import threading
from datetime import datetime
from dataclasses import dataclass
from pynput import mouse

@dataclass
class BotConfig:
    max_loops: int = 10
    initial_phase_loops: int = 6
    total_heroes: int = 8
    max_hero_usage: int = 6
    selected_challenge: int = 1 

class ClashOfThreeKingdomsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🏛️ Clash of Three Kingdoms - Auto Quest Bot")
        self.root.geometry("1000x800")
        
        # Bot configuration
        self.config = BotConfig()
        self.config_file = "clash_coordinates_config.json"
        self.coordinates = {}
        self.hero_usage = {f"Hero_{i}": 0 for i in range(1, 9)}
        self.hero_usage.update({f"Hero_{i}_secondary": 0 for i in range(1, 5)})
        
        # Bot state
        self.loop_count = 0
        self.successful_loops = 0
        self.phase = "initial"
        self.heroes_selected_for_battle = []
        self.is_running = False
        
        # PyAutoGUI setup
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # Optimized delays for speed
        self.delays = {
            "Challenge_Setup": 1.5, "Crusade": 1.5, "Challenge_Loop": 1.5,
            "Hero_Selection": 1.5, "Confirm": 1.5, "Fight": 1.5,
            "Quick_Combat": 1.5, "OK": 1.5, "Claim": 1.5, "Start": 1.5,
            "OK_After_Start": 1.5, 
            **{f"Hero_{i}": 0.5 for i in range(1, 9)},
            **{f"Challenge_Battle_{i}": 1 for i in range(1, 7)}
        }    
        
        
        self.challenge_names = [
            "Yellow Rebellion", "Battle of D. Zhuo", "Lords of J.Dong", 
            "Xiao Hu Gui Tian", "Battle of Guan Du", "San Gu Mao Lu",
            "Battle Of Chi Bi", "He Fei Cin Cheng", "War Of Tong Guan", 
            "Burning Fire", "Six Expeditions", "Conquer The North"
    ]
        # Sequences
        self.initial_sequence = ["Challenge_Setup", "Crusade"]
        self.phase1_sequence = ["Challenge_Loop", "Confirm", "Fight", "Quick_Combat", "OK", "Claim"]
        self.phase2_sequence = ["Challenge_Loop", "Hero_Selection", "Confirm", "Fight", "Quick_Combat", "OK", "Claim"]
        self.initial_sequence = ["Challenge_Setup", "Crusade", "Challenge_Battle", "Start", "OK_After_Start"]
        
        # Setup GUI
        self.setup_gui()
        self.load_coordinates()
    
    def setup_gui(self):
        """Setup main GUI interface"""
        # Title
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title = tk.Label(title_frame, text="🏛️ Clash of Three Kingdoms - Auto Quest Bot", 
                        font=("Arial", 18, "bold"), fg="white", bg="#2c3e50")
        title.pack(expand=True)
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configuration Section
        self.setup_config_section(main_frame)
        
        # Control Section
        self.setup_control_section(main_frame)
        
        # Status Section
        self.setup_status_section(main_frame)
    
    def setup_config_section(self, parent):
        config_frame = ttk.LabelFrame(parent, text="⚙️ Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=5)
    
        # File operations frame
        file_frame = ttk.Frame(config_frame)
        file_frame.pack(fill=tk.X, pady=5)
    
        ttk.Button(file_frame, text="💾 Save Config", 
                  command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="📂 Load Config", 
                  command=self.load_config).pack(side=tk.LEFT, padx=5)
    
        # Coordinate configuration
        coord_frame = ttk.Frame(config_frame)
        coord_frame.pack(fill=tk.X, pady=5)
    
        ttk.Button(coord_frame, text="🎯 Setup Coordinates", 
                  command=self.open_coordinate_setup).pack(side=tk.LEFT, padx=5)
        ttk.Button(coord_frame, text="🧪 Test Coordinates", 
                  command=self.test_coordinates).pack(side=tk.LEFT, padx=5)
    
        # Challenge selection frame
        challenge_frame = ttk.Frame(config_frame)
        challenge_frame.pack(fill=tk.X, pady=10)
    
        tk.Label(challenge_frame, text="Challenge Type:").pack(side=tk.LEFT)
        self.challenge_var = tk.StringVar(value=self.challenge_names[0])
        challenge_combo = ttk.Combobox(challenge_frame, textvariable=self.challenge_var, 
                                      values=self.challenge_names, state="readonly", width=20)
        challenge_combo.pack(side=tk.LEFT, padx=(5, 15))

        # Battle configuration
        battle_frame = ttk.Frame(config_frame)
        battle_frame.pack(fill=tk.X, pady=10)
    
        tk.Label(battle_frame, text="Max Loops:").pack(side=tk.LEFT)
        self.loops_var = tk.StringVar(value=str(self.config.max_loops))
        loops_spin = tk.Spinbox(battle_frame, from_=1, to=50, width=5, textvariable=self.loops_var)
        loops_spin.pack(side=tk.LEFT, padx=(5, 15))
    
        tk.Label(battle_frame, text="Phase 1 Loops:").pack(side=tk.LEFT)
        self.phase1_var = tk.StringVar(value=str(self.config.initial_phase_loops))
        phase1_spin = tk.Spinbox(battle_frame, from_=1, to=20, width=5, textvariable=self.phase1_var)
        phase1_spin.pack(side=tk.LEFT, padx=(5, 15))
    
        # Quick action buttons
        quick_frame = ttk.Frame(config_frame)
        quick_frame.pack(fill=tk.X, pady=5)
    
        ttk.Button(quick_frame, text="⚡ Quick Battle (5x)", 
                  command=lambda: self.set_quick_config(5)).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="🔥 Extended Battle (20x)", 
                  command=lambda: self.set_quick_config(20)).pack(side=tk.LEFT, padx=5)
    
    # Tambahan method untuk save/load configuration
    def save_config(self):
        config_name = simpledialog.askstring("Save Configuration", "Enter configuration name:")
        if not config_name:
            return
    
        try:
            config_data = {
                'coordinates': {k: list(v) if isinstance(v, tuple) else v 
                              for k, v in self.coordinates.items()},
                'max_loops': int(self.loops_var.get()),
                'initial_phase_loops': int(self.phase1_var.get()),
                'selected_challenge': self.challenge_names.index(self.challenge_var.get()) + 1,
                'hero_usage': self.hero_usage.copy()
            }
        
            filename = f"config_{config_name}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)

            self.log_message(f"💾 Configuration '{config_name}' saved successfully!")
            messagebox.showinfo("Success", f"Configuration '{config_name}' saved!")
        except Exception as e:
            self.log_message(f"❌ Error saving configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")

    def load_config(self):
        config_files = glob.glob("config_*.json")
        if not config_files:
            messagebox.showinfo("Info", "No saved configurations found!")
            return
    
        config_names = [f.replace("config_", "").replace(".json", "") for f in config_files]

        # Create selection window
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Load Configuration")
        selection_window.geometry("300x200")
        selection_window.grab_set()
    
        tk.Label(selection_window, text="Select configuration to load:").pack(pady=10)
    
        listbox = tk.Listbox(selection_window)
        for name in config_names:
            listbox.insert(tk.END, name)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
        def load_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a configuration!")
                return

            config_name = config_names[selection[0]]
            filename = f"config_{config_name}.json"

            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                # Load coordinates
                self.coordinates = {k: tuple(v) if isinstance(v, list) else v 
                                   for k, v in config_data['coordinates'].items()}
            
                # Update GUI
                self.loops_var.set(str(config_data['max_loops']))
                self.phase1_var.set(str(config_data['initial_phase_loops']))
                challenge_index = config_data.get('selected_challenge', 1) - 1
                self.challenge_var.set(self.challenge_names[challenge_index])

                if 'hero_usage' in config_data:
                    self.hero_usage = config_data['hero_usage']

                self.log_message(f"📂 Configuration '{config_name}' loaded successfully!")
            
                if self.is_coordinates_ready():
                    self.start_btn.config(state="normal")
                    self.coord_status.config(text="Coordinates: Ready", fg="#27ae60")
            
                selection_window.destroy()
                messagebox.showinfo("Success", f"Configuration '{config_name}' loaded!")
            
            except Exception as e:
                self.log_message(f"❌ Error loading configuration: {e}")
                messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
        button_frame = ttk.Frame(selection_window)
        button_frame.pack(fill=tk.X, pady=10)
    
        ttk.Button(button_frame, text="Load", command=load_selected).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=selection_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def setup_control_section(self, parent):
        """Setup control section"""
        control_frame = ttk.LabelFrame(parent, text="🎮 Controls", padding="10")
        control_frame.pack(fill=tk.X, pady=5)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(btn_frame, text="🚀 Start Automation", 
                                   command=self.start_automation, state="disabled")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="🛑 Stop", 
                                  command=self.stop_automation, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="🔄 Reset Hero Usage", 
                  command=self.reset_hero_usage).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="📊 Show Hero Status", 
                  command=self.show_hero_status).pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(control_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(10, 0))
    
    def setup_status_section(self, parent):
        """Setup status section"""
        status_frame = ttk.LabelFrame(parent, text="📋 Status & Logs", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Status info
        info_frame = ttk.Frame(status_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = tk.Label(info_frame, text="Status: Ready", 
                                    font=("Arial", 10, "bold"), fg="#27ae60")
        self.status_label.pack(side=tk.LEFT)
        
        self.coord_status = tk.Label(info_frame, text="Coordinates: Not Loaded", 
                                    font=("Arial", 10), fg="#e74c3c")
        self.coord_status.pack(side=tk.RIGHT)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(status_frame, height=15, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Clear logs button
        ttk.Button(status_frame, text="🗑️ Clear Logs", 
                  command=lambda: self.log_text.delete(1.0, tk.END)).pack(pady=5)
    
    def load_coordinates(self):
        """Load coordinates from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_coords = json.load(f)
                
                self.coordinates = {k: tuple(v) if isinstance(v, list) else v 
                                  for k, v in saved_coords.items()}
                
                self.log_message("✅ Coordinates loaded successfully")
                self.coord_status.config(text=f"Coordinates: {len(self.coordinates)} loaded", fg="#27ae60")
                
                if self.is_coordinates_ready():
                    self.start_btn.config(state="normal")
            else:
                self.log_message("⚠️ No coordinate file found. Please setup coordinates first.")
        except Exception as e:
            self.log_message(f"❌ Error loading coordinates: {e}")
    
    def save_coordinates(self):
        """Save coordinates to file"""
        try:
            coords_to_save = {k: list(v) if isinstance(v, tuple) else v 
                             for k, v in self.coordinates.items()}
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(coords_to_save, f, indent=4, ensure_ascii=False)
            
            self.log_message("💾 Coordinates saved successfully!")
            messagebox.showinfo("Success", "Coordinates saved successfully!")
        except Exception as e:
            self.log_message(f"❌ Error saving coordinates: {e}")
            messagebox.showerror("Error", f"Failed to save coordinates: {e}")
    
    def open_coordinate_setup(self):
        """Open coordinate setup window"""
        CoordinateSetupWindow(self)
    
    def test_coordinates(self):
        """Test all coordinates"""
        if not self.coordinates:
            messagebox.showwarning("Warning", "No coordinates to test!")
            return
        
        def test_all():
            self.log_message("🧪 Testing all coordinates...")
            for name, (x, y) in self.coordinates.items():
                if isinstance(self.coordinates[name], tuple):
                    self.log_message(f"Testing {name} at ({x}, {y})")
                    pyautogui.click(x, y)
                    time.sleep(1)
            self.log_message("✅ Coordinate testing completed!")
        
        if messagebox.askyesno("Test Coordinates", "This will click all saved coordinates. Continue?"):
            threading.Thread(target=test_all, daemon=True).start()
    
    def set_quick_config(self, loops):
        """Set quick configuration"""
        self.loops_var.set(str(loops))
        self.log_message(f"⚡ Quick config set: {loops} loops")
    
    def is_coordinates_ready(self):
        required = ["Challenge_Setup", "Crusade", "Challenge_Loop", "Confirm", 
                   "Fight", "Quick_Combat", "OK", "Claim", "Start", "OK_After_Start"] + \
                    [f"Hero_{i}" for i in range(1, 9)] + \
                    [f"Challenge_Battle_{i}" for i in range(1, 7)]
        return all(coord in self.coordinates for coord in required)
    
    def start_automation(self):
        if not self.is_coordinates_ready():
            messagebox.showerror("Error", "Please setup coordinates first!")
            return
    
        # Update config from GUI
        self.config.max_loops = int(self.loops_var.get())
        self.config.initial_phase_loops = int(self.phase1_var.get())
        self.config.selected_challenge = self.challenge_names.index(self.challenge_var.get()) + 1

        # Reset counters
        self.loop_count = 0
        self.successful_loops = 0
        self.is_running = True
    
        # Update UI
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress['maximum'] = self.config.max_loops
        self.progress['value'] = 0
        self.status_label.config(text="Status: Running", fg="#f39c12")
    
        threading.Thread(target=self.run_automation, daemon=True).start()
        self.root.iconify()  # Minimize main window

    
    def stop_automation(self):
        """Stop the automation process"""
        self.is_running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Status: Stopped", fg="#e74c3c")
        self.log_message("🛑 Automation stopped by user")
    
    def run_automation(self):
        """Main automation logic"""
        try:
            self.log_message(f"🚀 Starting automation: {self.config.max_loops} loops")
            self.log_message(f"Phase 1: {self.config.initial_phase_loops} loops (direct challenge)")
            self.log_message(f"Phase 2: {self.config.max_loops - self.config.initial_phase_loops} loops (hero selection)")
            
            start_time = time.time()
            
            # Initial setup
            if not self.execute_initial_setup():
                return
            
            # Battle loops
            for loop in range(self.config.max_loops):
                if not self.is_running:
                    break
                
                self.loop_count = loop
                self.determine_phase()
                
                if loop == self.config.initial_phase_loops:
                    self.reset_secondary_phase_usage()
                
                if self.execute_battle_loop():
                    self.successful_loops += 1
                    self.progress['value'] = loop + 1
                    self.log_message(f"✅ Loop {loop + 1} completed successfully!")
                else:
                    self.log_message(f"❌ Loop {loop + 1} failed!")
                
                self.root.update_idletasks()
                time.sleep(1)
            
            # Summary
            duration = time.time() - start_time
            self.print_summary(duration)
            
        except Exception as e:
            self.log_message(f"💥 Critical error: {e}")
        finally:
            self.is_running = False
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.status_label.config(text="Status: Completed", fg="#27ae60")
    
    def execute_initial_setup(self):
        self.log_message("🚀 Executing initial setup...")
        for step in self.initial_sequence:
            if not self.is_running:
                return False

            if step == "Challenge_Battle":
                if not self.select_challenge_battle():
                    return False
            else:
                if not self.click_button(step):
                    return False
        return True
    
    def select_challenge_battle(self):
        try:
            challenge_index = self.challenge_names.index(self.challenge_var.get()) + 1
            self.log_message(f"🎯 Selecting challenge: {self.challenge_var.get()} (#{challenge_index})")

            # Jika challenge 7-12, scroll down dulu
            if challenge_index > 6:
                self.log_message("📜 Scrolling down for challenge 7-12...")
                for _ in range(3):
                    pyautogui.scroll(-3)  # Scroll down
                    time.sleep(0.2)
            
                # Gunakan koordinat challenge 1-6 untuk challenge 7-12
                actual_challenge = challenge_index - 6
            else:
                actual_challenge = challenge_index

            # Click challenge battle
            challenge_coord_key = f"Challenge_Battle_{actual_challenge}"
            if challenge_coord_key not in self.coordinates:
                self.log_message(f"❌ Challenge battle {actual_challenge} coordinates not found!")
                return False

            x, y = self.coordinates[challenge_coord_key]
            pyautogui.click(x, y)
            time.sleep(0.8)

            return True

        except Exception as e:
            self.log_message(f"❌ Error selecting challenge battle: {e}")
            return False
        
    def execute_battle_loop(self):
        """Execute one battle loop"""
        sequence = self.phase1_sequence if self.phase == "initial" else self.phase2_sequence
        
        self.log_message(f"⚔️ Battle Loop {self.loop_count + 1} [{self.phase.upper()}]")
        
        for step in sequence:
            if not self.is_running:
                return False
            
            if step == "Hero_Selection" and self.phase == "secondary":
                if not self.select_heroes_for_battle_phase2():
                    return False
            else:
                if not self.click_button(step):
                    return False
        
        if self.phase == "secondary":
            self.update_hero_usage_after_battle_phase2()
        
        return True
    
    def determine_phase(self):
        """Determine current phase"""
        self.phase = "initial" if self.loop_count < self.config.initial_phase_loops else "secondary"
    
    def get_available_heroes_for_phase2(self):
        """Get available heroes for phase 2"""
        return [f"Hero_{i}" for i in range(1, 5) 
                if self.hero_usage.get(f"Hero_{i}_secondary", 0) == 0]
    
    def select_heroes_for_battle_phase2(self):
        """Select heroes for phase 2 battle"""
        available_heroes = self.get_available_heroes_for_phase2()
        
        if not available_heroes:
            self.log_message("❌ No heroes available for phase 2!")
            return False
        
        self.heroes_selected_for_battle = []
        success_count = 0
        
        for hero_name in available_heroes:
            if self.click_button(hero_name):
                self.heroes_selected_for_battle.append(hero_name)
                success_count += 1
                time.sleep(0.3)
        
        self.log_message(f"🎭 Selected {success_count} heroes for battle")
        return success_count > 0
    
    def update_hero_usage_after_battle_phase2(self):
        """Update hero usage after phase 2 battle"""
        for hero_name in self.heroes_selected_for_battle:
            self.hero_usage[f"{hero_name}_secondary"] = 1
        self.heroes_selected_for_battle = []
    
    def reset_secondary_phase_usage(self):
        """Reset secondary phase hero usage"""
        for i in range(1, 5):
            self.hero_usage[f"Hero_{i}_secondary"] = 0
        self.log_message("🔄 Secondary phase hero usage reset")
    
    def click_button(self, button_name):
        """Click button with saved coordinates"""
        if button_name not in self.coordinates:
            self.log_message(f"❌ Button {button_name} not found")
            return False
        
        try:
            x, y = self.coordinates[button_name]
            pyautogui.click(x, y)
            
            delay = self.delays.get(button_name, 0.5)
            time.sleep(delay)
            
            return True
        except Exception as e:
            self.log_message(f"❌ Error clicking {button_name}: {e}")
            return False
    
    def reset_hero_usage(self):
        """Reset all hero usage counters"""
        for key in self.hero_usage:
            self.hero_usage[key] = 0
        self.log_message("🔄 All hero usage counters reset!")
        messagebox.showinfo("Reset", "Hero usage counters have been reset!")
    
    def show_hero_status(self):
        """Show hero usage status"""
        status_window = tk.Toplevel(self.root)
        status_window.title("👥 Hero Status")
        status_window.geometry("400x300")
        
        text_area = scrolledtext.ScrolledText(status_window, width=50, height=15)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_area.insert(tk.END, "👥 HERO USAGE STATUS\n")
        text_area.insert(tk.END, "=" * 40 + "\n\n")
        
        text_area.insert(tk.END, "PHASE 2 HEROES (4 Generals):\n")
        for i in range(1, 5):
            hero_name = f"Hero_{i}"
            usage = self.hero_usage.get(f"{hero_name}_secondary", 0)
            status = "🔴 Used" if usage > 0 else "🟢 Available"
            text_area.insert(tk.END, f"   {hero_name}: {usage}/1 use {status}\n")
        
        text_area.config(state=tk.DISABLED)
    
    def print_summary(self, duration):
        """Print automation summary"""
        self.log_message("\n" + "="*50)
        self.log_message("📊 AUTOMATION SUMMARY")
        self.log_message("="*50)
        self.log_message(f"⏱️ Duration: {duration:.1f}s ({duration/60:.1f}m)")
        self.log_message(f"✅ Success: {self.successful_loops}/{self.config.max_loops}")
        self.log_message(f"📈 Rate: {(self.successful_loops/self.config.max_loops)*100:.1f}%")
        
        if self.successful_loops > 0:
            avg = duration / self.successful_loops
            self.log_message(f"⚡ Avg/loop: {avg:.1f}s")
        
        self.log_message("="*50)
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

class CoordinateSetupWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("🎯 Coordinate Setup")
        self.window.geometry("800x700")
        self.window.grab_set()
        
        self.setup_gui()
    
    def setup_gui(self):
        """Setup coordinate configuration GUI"""
        # Instructions
        instructions = tk.Label(self.window, 
                               text="Click 'Capture' then click on the target element in the game\n"
                                    "You have 3 seconds after clicking 'Capture' to position your mouse",
                               font=("Arial", 12), fg="blue", wraplength=750)
        instructions.pack(pady=15)
        
        # Scrollable frame
        canvas = tk.Canvas(self.window)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Coordinate entries
        coord_labels = {
            'Challenge_Setup': 'Challenge Button (Main Menu)',
            'Crusade': 'Crusade Mode Button',
            'Challenge_Loop': 'Challenge Button (In Crusade)',
            'Confirm': 'Confirm Button (Green)',
            'Fight': 'Fight Button',
            'Quick_Combat': 'Quick Combat Button',
            'OK': 'OK Button (After Battle)',
            'Claim': 'Claim Reward Button',
            'Start': 'Start Button (After Challenge Selection)',
            'OK_After_Start': 'OK Button (After Start)',  # <- TAMBAHAN INI
            **{f'Challenge_Battle_{i}': f'Challenge Battle Position {i}' 
                for i in range(1, 7)},
            **{f'Hero_{i}': f'Hero Position {i} {"(Top Row)" if i <= 5 else "(Bottom Row)"}' 
                for i in range(1, 9)}
}
        
        self.coord_vars = {}
        
        for coord_key, label in coord_labels.items():
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=3, padx=15)
            
            tk.Label(frame, text=label, width=30, anchor='w').pack(side=tk.LEFT)
            
            # X coordinate
            tk.Label(frame, text="X:").pack(side=tk.LEFT, padx=(10, 5))
            x_var = tk.StringVar(value=str(self.parent.coordinates.get(coord_key, (0, 0))[0]))
            x_entry = ttk.Entry(frame, textvariable=x_var, width=8)
            x_entry.pack(side=tk.LEFT, padx=(0, 10))
            
            # Y coordinate
            tk.Label(frame, text="Y:").pack(side=tk.LEFT, padx=(0, 5))
            y_var = tk.StringVar(value=str(self.parent.coordinates.get(coord_key, (0, 0))[1]))
            y_entry = ttk.Entry(frame, textvariable=y_var, width=8)
            y_entry.pack(side=tk.LEFT, padx=(0, 15))
            
            # Capture button
            capture_btn = ttk.Button(frame, text="📍 Capture", 
                                   command=lambda k=coord_key, xv=x_var, yv=y_var: self.capture_coordinate(k, xv, yv))
            capture_btn.pack(side=tk.LEFT, padx=5)
            
            self.coord_vars[coord_key] = {'x': x_var, 'y': y_var}
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, pady=15)
        
        ttk.Button(button_frame, text="💾 Save & Close", 
                  command=self.save_and_close).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="❌ Cancel", 
                  command=self.window.destroy).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="🧪 Test All", 
                  command=self.test_all_coordinates).pack(side=tk.LEFT, padx=10)
    
    def capture_coordinate(self, coord_key, x_var, y_var):
        """Capture mouse coordinate"""
        def on_click(x, y, button, pressed):
            if pressed and button == button.left:
                x_var.set(str(x))
                y_var.set(str(y))
                return False
        
        def start_capture():
            self.window.withdraw()
            self.parent.root.withdraw()
            
            with mouse.Listener(on_click=on_click) as listener:
                listener.join()
            
            self.parent.root.deiconify()
            self.window.deiconify()
            self.window.lift()
        
        threading.Thread(target=start_capture, daemon=True).start()
    
    def test_all_coordinates(self):
        """Test all configured coordinates"""
        if messagebox.askyesno("Test Coordinates", "This will click all coordinates. Continue?"):
            def test():
                for coord_key, vars_dict in self.coord_vars.items():
                    try:
                        x = int(vars_dict['x'].get())
                        y = int(vars_dict['y'].get())
                        if x > 0 and y > 0:
                            pyautogui.click(x, y)
                            time.sleep(1)
                    except ValueError:
                        continue
            
            threading.Thread(target=test, daemon=True).start()
    
    def save_and_close(self):
        """Save coordinates and close"""
        try:
            for coord_key, vars_dict in self.coord_vars.items():
                x = int(vars_dict['x'].get())
                y = int(vars_dict['y'].get())
                self.parent.coordinates[coord_key] = (x, y)
            
            self.parent.save_coordinates()
            
            if self.parent.is_coordinates_ready():
                self.parent.start_btn.config(state="normal")
                self.parent.coord_status.config(text="Coordinates: Ready", fg="#27ae60")
            
            self.window.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid coordinate values!")

def main():
    """Main application entry point"""
    root = tk.Tk()
    root.eval('tk::PlaceWindow . center')
    
    # Set icon and style
    try:
        root.iconbitmap(default='icon.ico')  # Add icon if available
    except:
        pass
    
    app = ClashOfThreeKingdomsGUI(root)
    
    # Handle window close
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("Quit", "Automation is running. Do you want to quit?"):
                app.stop_automation()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()