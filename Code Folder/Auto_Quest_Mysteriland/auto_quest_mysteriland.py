import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import time
import threading
import json
import os
import pyautogui
from datetime import datetime
from pynput import mouse

class AutoQuestMysteriland:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Quest Mysteriland Bot")
        self.root.geometry("900x700")
        
        # Data storage
        self.static_coords = {}
        self.stage_coords = {}
        self.config_folder = "Configuration_Save"
        
        # PyAutoGUI settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        
        # Day mapping
        self.days = {
            0: "senin", 1: "selasa", 2: "rabu", 
            3: "kamis", 4: "jumat", 5: "sabtu"
        }
        
        # Create config folder if not exists
        if not os.path.exists(self.config_folder):
            os.makedirs(self.config_folder)
        
        self.setup_gui()
        self.load_configurations()
    
    def setup_gui(self):
        """Setup main GUI"""
        # Title
        title = tk.Label(self.root, text="🎮 Auto Quest Mysteriland Bot", 
                        font=("Arial", 16, "bold"), fg="#2c3e50")
        title.pack(pady=10)
        
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configuration Section
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=5)
        
        # Static coordinates config
        static_frame = ttk.Frame(config_frame)
        static_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(static_frame, text="🎯 Configure Static Coordinates", 
                  command=self.open_static_config).pack(side=tk.LEFT, padx=5)
        
        self.static_config_var = tk.StringVar()
        ttk.Label(static_frame, text="Load Config:").pack(side=tk.LEFT, padx=(20, 5))
        self.static_combo = ttk.Combobox(static_frame, textvariable=self.static_config_var, 
                                        state="readonly", width=15)
        self.static_combo.pack(side=tk.LEFT, padx=5)
        self.static_combo.bind('<<ComboboxSelected>>', self.load_static_config)
        
        # Stage coordinates config
        stage_frame = ttk.Frame(config_frame)
        stage_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(stage_frame, text="📅 Configure Stage Coordinates", 
                  command=self.open_stage_config).pack(side=tk.LEFT, padx=5)
        
        self.stage_day_var = tk.StringVar(value=self.days[datetime.now().weekday()])
        ttk.Label(stage_frame, text="Day:").pack(side=tk.LEFT, padx=(20, 5))
        day_combo = ttk.Combobox(stage_frame, textvariable=self.stage_day_var,
                                values=list(self.days.values()), state="readonly", width=10)
        day_combo.pack(side=tk.LEFT, padx=5)
        
        # Quest Settings
        quest_frame = ttk.LabelFrame(main_frame, text="Quest Settings", padding="10")
        quest_frame.pack(fill=tk.X, pady=5)
        
        # Number of stages
        stages_frame = ttk.Frame(quest_frame)
        stages_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(stages_frame, text="Number of Stages (1-5):").pack(side=tk.LEFT)
        self.stages_var = tk.StringVar(value="5")
        stages_spin = tk.Spinbox(stages_frame, from_=1, to=5, width=5, 
                               textvariable=self.stages_var)
        stages_spin.pack(side=tk.LEFT, padx=(10, 0))
        
        # Swipe settings
        swipe_frame = ttk.Frame(quest_frame)
        swipe_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(swipe_frame, text="Swipe Stage (1-5):").pack(side=tk.LEFT)
        self.swipe_stage_var = tk.StringVar(value="5")
        swipe_spin = tk.Spinbox(swipe_frame, from_=1, to=5, width=5,
                              textvariable=self.swipe_stage_var)
        swipe_spin.pack(side=tk.LEFT, padx=(10, 0))
        
        tk.Label(swipe_frame, text="Swipe Count:").pack(side=tk.LEFT, padx=(20, 5))
        self.swipe_count_var = tk.StringVar(value="1x")
        swipe_combo = ttk.Combobox(swipe_frame, textvariable=self.swipe_count_var,
                                 values=["1x", "5x"], state="readonly", width=5)
        swipe_combo.pack(side=tk.LEFT, padx=5)
        
        # Action Buttons
        action_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
        action_frame.pack(fill=tk.X, pady=5)
        
        btn_frame = ttk.Frame(action_frame)
        btn_frame.pack()
        
        self.stage_btn = ttk.Button(btn_frame, text="🚀 Execute Stages", 
                                   command=self.execute_stages)
        self.stage_btn.pack(side=tk.LEFT, padx=5)
        
        self.swipe_btn = ttk.Button(btn_frame, text="🔄 Execute Swipe", 
                                   command=self.execute_swipe)
        self.swipe_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(btn_frame, text="🚪 Exit", 
                                   command=self.execute_exit)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress and logs
        progress_frame = ttk.LabelFrame(main_frame, text="Progress & Status", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(progress_frame, height=10, width=80)
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.update_config_list()
    
    def log_message(self, message):
        """Add message to status log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
    
    def load_configurations(self):
        """Load all configurations"""
        # Load static coordinates
        static_files = [f for f in os.listdir(self.config_folder) 
                       if f.startswith("static_") and f.endswith(".json")]
        
        # Load stage coordinates for each day
        for day in self.days.values():
            stage_file = os.path.join(self.config_folder, f"stage_{day}.json")
            if os.path.exists(stage_file):
                with open(stage_file, 'r') as f:
                    self.stage_coords[day] = json.load(f)
    
    def update_config_list(self):
        """Update configuration combo box"""
        config_files = [f.replace("static_", "").replace(".json", "") 
                       for f in os.listdir(self.config_folder) 
                       if f.startswith("static_") and f.endswith(".json")]
        self.static_combo['values'] = config_files
        if config_files:
            self.static_combo.set(config_files[0])
            self.load_static_config()  # Auto-load first config
    
    def load_static_config(self, event=None):
        """Load static configuration when combo selection changes"""
        config_name = self.static_config_var.get()
        if config_name:
            try:
                static_file = os.path.join(self.config_folder, f"static_{config_name}.json")
                with open(static_file, 'r') as f:
                    self.static_coords = json.load(f)
                self.log_message(f"📂 Loaded static configuration: {config_name}")
            except Exception as e:
                self.log_message(f"❌ Failed to load config {config_name}: {str(e)}")
                messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def open_static_config(self):
        """Open static coordinates configuration"""
        StaticConfigWindow(self)
    
    def open_stage_config(self):
        """Open stage coordinates configuration"""
        StageConfigWindow(self)
    
    def click_coordinate(self, coord_dict, coord_name, wait=0.5):
        """Click on coordinate"""
        if coord_name in coord_dict:
            coord = coord_dict[coord_name]
            pyautogui.click(coord['x'], coord['y'])
            time.sleep(wait)
            return True
        return False
    
    def stage_loop(self, static_coords):
        """Execute stage loop (Enter Challenge -> Fight -> Quick Combat -> OK)"""
        self.click_coordinate(static_coords, 'enter_challenge')
        self.click_coordinate(static_coords, 'fight')
        self.click_coordinate(static_coords, 'quick_combat')
        self.click_coordinate(static_coords, 'ok')
    
    def execute_stages(self):
        """Execute stage quest process"""
        if not self.validate_configs():
            return
        
        self.stage_btn.config(state="disabled")
        thread = threading.Thread(target=self._run_stages)
        thread.daemon = True
        thread.start()
    
    def _run_stages(self):
        """Run stage execution in thread"""
        try:
            # Load configurations
            config_name = self.static_config_var.get()
            day = self.stage_day_var.get()
            num_stages = int(self.stages_var.get())
            
            static_file = os.path.join(self.config_folder, f"static_{config_name}.json")
            with open(static_file, 'r') as f:
                static_coords = json.load(f)
            
            stage_coords = self.stage_coords.get(day, {})
            
            self.progress['maximum'] = num_stages * 2 + 3  # stages + rewards + initial clicks
            self.progress['value'] = 0
            
            # Initial navigation
            self.log_message("🎯 Starting quest execution...")
            self.click_coordinate(static_coords, 'challenge')
            self.progress['value'] += 1
            
            self.click_coordinate(static_coords, 'crusade')
            self.progress['value'] += 1
            
            self.click_coordinate(static_coords, 'mysteriland')
            self.progress['value'] += 1
            
            # Execute stages
            for stage in range(1, num_stages + 1):
                self.log_message(f"🚀 Executing Stage {stage}...")
                
                # Click stage button
                stage_key = f'stage_{stage}'
                if self.click_coordinate(stage_coords, stage_key):
                    # Run stage loop
                    self.stage_loop(static_coords)
                    self.progress['value'] += 1
                    
                    # Click reward
                    reward_key = f'reward_{stage}'
                    self.click_coordinate(stage_coords, reward_key)
                    self.progress['value'] += 1
                    
                    self.log_message(f"✅ Stage {stage} completed")
                else:
                    self.log_message(f"❌ Stage {stage} coordinate not found")
            
            self.log_message("🎉 All stages completed!")
            messagebox.showinfo("Success", f"Successfully completed {num_stages} stages!")
            
        except Exception as e:
            self.log_message(f"❌ Error during execution: {str(e)}")
            messagebox.showerror("Error", f"Execution failed: {str(e)}")
        
        finally:
            self.stage_btn.config(state="normal")
    
    def execute_swipe(self):
        """Execute swipe stage process"""
        if not self.validate_configs():
            return
        
        self.swipe_btn.config(state="disabled")
        thread = threading.Thread(target=self._run_swipe)
        thread.daemon = True
        thread.start()
    
    def _run_swipe(self):
        """Run swipe execution in thread"""
        try:
            config_name = self.static_config_var.get()
            day = self.stage_day_var.get()
            swipe_stage = int(self.swipe_stage_var.get())
            swipe_count = self.swipe_count_var.get()
            
            static_file = os.path.join(self.config_folder, f"static_{config_name}.json")
            with open(static_file, 'r') as f:
                static_coords = json.load(f)
            
            stage_coords = self.stage_coords.get(day, {})
            
            self.log_message(f"🔄 Starting swipe for Stage {swipe_stage}...")
            
            # Click target stage
            stage_key = f'stage_{swipe_stage}'
            self.click_coordinate(stage_coords, stage_key)
            
            # Click swipe count button
            swipe_key = f'swipe_{swipe_count}'
            self.click_coordinate(static_coords, swipe_key)
            
            # Click anywhere on screen
            pyautogui.click(500, 500)  # Click center screen
            time.sleep(0.5)
            
            self.log_message("✅ Swipe execution completed!")
            messagebox.showinfo("Success", "Swipe execution completed!")
            
        except Exception as e:
            self.log_message(f"❌ Error during swipe: {str(e)}")
            messagebox.showerror("Error", f"Swipe failed: {str(e)}")
        
        finally:
            self.swipe_btn.config(state="normal")
    
    def execute_exit(self):
        """Execute exit process"""
        try:
            config_name = self.static_config_var.get()
            if not config_name:
                messagebox.showerror("Error", "Please select a static configuration!")
                return
            
            static_file = os.path.join(self.config_folder, f"static_{config_name}.json")
            with open(static_file, 'r') as f:
                static_coords = json.load(f)
            
            self.log_message("🚪 Executing exit...")
            self.click_coordinate(static_coords, 'exit')
            self.log_message("✅ Exit completed!")
            
        except Exception as e:
            self.log_message(f"❌ Error during exit: {str(e)}")
            messagebox.showerror("Error", f"Exit failed: {str(e)}")
    
    def validate_configs(self):
        """Validate configurations before execution"""
        config_name = self.static_config_var.get()
        day = self.stage_day_var.get()
        
        if not config_name:
            messagebox.showerror("Error", "Please select a static configuration!")
            return False
        
        if day not in self.stage_coords:
            messagebox.showerror("Error", f"Stage configuration for {day} not found!")
            return False
        
        return True

class StaticConfigWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("Static Coordinates Configuration")
        self.window.geometry("700x600")
        self.window.grab_set()
        
        self.coord_vars = {}
        self.setup_gui()
        self.load_existing_config()

    
    def setup_gui(self):
        """Setup static config GUI"""
        # Instructions
        instructions = tk.Label(self.window, 
                               text="Configure static coordinates (same for all days)\n"
                                    "Click 'Capture' then click on target element",
                               font=("Arial", 10), fg="blue")
        instructions.pack(pady=10)
        
        # Config name
        name_frame = ttk.Frame(self.window)
        name_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(name_frame, text="Configuration Name:").pack(side=tk.LEFT)
        self.config_name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.config_name_var, width=20).pack(side=tk.LEFT, padx=10)
        
        # Scrollable coordinates
        canvas = tk.Canvas(self.window)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Static coordinate fields
        static_coords = [
            ('challenge', 'Challenge Button'),
            ('crusade', 'Crusade Button'),
            ('mysteriland', 'Mysteriland Button'),
            ('enter_challenge', 'Enter Challenge Button'),
            ('fight', 'Fight Button'),
            ('quick_combat', 'Quick Combat Button'),
            ('ok', 'OK Button'),
            ('swipe_1x', 'Swipe 1x Button'),
            ('swipe_5x', 'Swipe 5x Button'),
            ('exit', 'Exit Button')
        ]
        
        for coord_key, label in static_coords:
            self.create_coord_row(scrollable_frame, coord_key, label)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="💾 Save Configuration", 
                  command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", 
                  command=self.window.destroy).pack(side=tk.LEFT, padx=5)
    
    def load_existing_config(self):
        """Load existing configuration if available"""
        config_name = self.parent.static_config_var.get()
        if config_name:
            try:
                static_file = os.path.join(self.parent.config_folder, f"static_{config_name}.json")
                if os.path.exists(static_file):
                    with open(static_file, 'r') as f:
                        coords = json.load(f)
                
                    # Set config name
                    self.config_name_var.set(config_name)
                
                    # Load coordinates to form
                    for coord_key, coord_data in coords.items():
                        if coord_key in self.coord_vars:
                            self.coord_vars[coord_key]['x'].set(str(coord_data['x']))
                            self.coord_vars[coord_key]['y'].set(str(coord_data['y']))
                self.log_message(f"📂 Loaded static configuration: {config_name}")        
            except Exception as e:
                print(f"Error loading config: {e}")
            
    def create_coord_row(self, parent, coord_key, label):
        """Create coordinate input row"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        tk.Label(frame, text=label, width=20).pack(side=tk.LEFT)
        
        tk.Label(frame, text="X:").pack(side=tk.LEFT, padx=(10, 0))
        x_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=x_var, width=8).pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame, text="Y:").pack(side=tk.LEFT)
        y_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=y_var, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame, text="Capture", 
                  command=lambda: self.capture_coordinate(x_var, y_var)).pack(side=tk.LEFT, padx=5)
        
        self.coord_vars[coord_key] = {'x': x_var, 'y': y_var}
    
    def capture_coordinate(self, x_var, y_var):
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
        
        thread = threading.Thread(target=start_capture)
        thread.daemon = True
        thread.start()
    
    def save_config(self):
        """Save static configuration"""
        config_name = self.config_name_var.get().strip()
        if not config_name:
            messagebox.showerror("Error", "Please enter configuration name!")
            return
        
        coords = {}
        for coord_key, vars_dict in self.coord_vars.items():
            try:
                x = int(vars_dict['x'].get())
                y = int(vars_dict['y'].get())
                coords[coord_key] = {'x': x, 'y': y}
            except ValueError:
                messagebox.showerror("Error", f"Invalid coordinate for {coord_key}")
                return
        
        # Save to file
        filename = os.path.join(self.parent.config_folder, f"static_{config_name}.json")
        with open(filename, 'w') as f:
            json.dump(coords, f, indent=4)
        
        self.parent.update_config_list()
        self.parent.log_message(f"💾 Static configuration '{config_name}' saved")
        messagebox.showinfo("Success", "Configuration saved successfully!")
        self.window.destroy()

class StageConfigWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("Stage Coordinates Configuration")
        self.window.geometry("800x700")
        self.window.grab_set()
        
        self.coord_vars = {}
        self.day_var = tk.StringVar(value="senin")
        self.setup_gui()
    
    def setup_gui(self):
        """Setup stage config GUI"""
        # Instructions
        instructions = tk.Label(self.window, 
                               text="Configure stage coordinates (different for each day)\n"
                                    "Each stage has 6 different coordinates per day",
                               font=("Arial", 10), fg="blue")
        instructions.pack(pady=10)
        
        # Day selection
        day_frame = ttk.Frame(self.window)
        day_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(day_frame, text="Select Day:").pack(side=tk.LEFT)
        day_combo = ttk.Combobox(day_frame, textvariable=self.day_var,
                                values=list(self.parent.days.values()), 
                                state="readonly", width=10)
        day_combo.pack(side=tk.LEFT, padx=10)
        day_combo.bind('<<ComboboxSelected>>', self.load_day_config)
        
        # Scrollable coordinates
        canvas = tk.Canvas(self.window)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.create_stage_coords()
        
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="💾 Save Configuration", 
                  command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", 
                  command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        
        self.load_day_config()
    
    def create_stage_coords(self):
        """Create stage coordinate fields"""
        # Stage and reward coordinates
        for stage in range(1, 6):
            # Stage section
            stage_frame = ttk.LabelFrame(self.scrollable_frame, text=f"Stage {stage}", padding="5")
            stage_frame.pack(fill=tk.X, pady=5)
            
            self.create_coord_row(stage_frame, f'stage_{stage}', f'Stage {stage} Button')
            self.create_coord_row(stage_frame, f'reward_{stage}', f'Reward {stage} Button')
    
    def create_coord_row(self, parent, coord_key, label):
        """Create coordinate input row"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        tk.Label(frame, text=label, width=20).pack(side=tk.LEFT)
        
        tk.Label(frame, text="X:").pack(side=tk.LEFT, padx=(10, 0))
        x_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=x_var, width=8).pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame, text="Y:").pack(side=tk.LEFT)
        y_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=y_var, width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame, text="Capture", 
                  command=lambda: self.capture_coordinate(x_var, y_var)).pack(side=tk.LEFT, padx=5)
        
        self.coord_vars[coord_key] = {'x': x_var, 'y': y_var}
    
    def capture_coordinate(self, x_var, y_var):
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
        
        thread = threading.Thread(target=start_capture)
        thread.daemon = True
        thread.start()
    
    def load_day_config(self, event=None):
        """Load configuration for selected day"""
        day = self.day_var.get()
        if day in self.parent.stage_coords:
            coords = self.parent.stage_coords[day]
            for coord_key, vars_dict in self.coord_vars.items():
                if coord_key in coords:
                    vars_dict['x'].set(str(coords[coord_key]['x']))
                    vars_dict['y'].set(str(coords[coord_key]['y']))
    
    def save_config(self):
        """Save stage configuration"""
        day = self.day_var.get()
        coords = {}
        
        for coord_key, vars_dict in self.coord_vars.items():
            try:
                x = int(vars_dict['x'].get())
                y = int(vars_dict['y'].get())
                coords[coord_key] = {'x': x, 'y': y}
            except ValueError:
                messagebox.showerror("Error", f"Invalid coordinate for {coord_key}")
                return
        
        # Save to file
        filename = os.path.join(self.parent.config_folder, f"stage_{day}.json")
        with open(filename, 'w') as f:
            json.dump(coords, f, indent=4)
        
        # Update parent data
        self.parent.stage_coords[day] = coords
        
        self.parent.log_message(f"💾 Stage configuration for '{day}' saved")
        messagebox.showinfo("Success", f"Configuration for {day} saved successfully!")
        self.window.destroy()

def main():
    root = tk.Tk()
    app = AutoQuestMysteriland(root)
    root.eval('tk::PlaceWindow . center')
    root.mainloop()

if __name__ == "__main__":
    main()