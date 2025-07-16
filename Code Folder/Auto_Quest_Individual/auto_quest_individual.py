import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import time
import threading
import json
import os
import pyautogui
from pynput import mouse

class AutoQuestIndividual:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Auto Quest Individual")
        self.root.geometry("700x650")
        
        # Data storage
        self.coordinates = {}
        self.config_folder = "Configuration_Save"
        self.current_config_name = ""
        
        # Delay settings (in seconds)
        self.default_delay = 0.5
        self.navigation_delay = 1.0
        self.combat_delay = 2.0
        self.reward_delay = 1.5
        
        # PyAutoGUI settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1  # Set to minimal, we'll handle delays manually
        
        # Create config folder if not exists
        os.makedirs(self.config_folder, exist_ok=True)
        
        # Setup GUI
        self.setup_gui()
        
        # Load default coordinates structure
        self.load_default_coordinates()
    
    def load_default_coordinates(self):
        """Load default coordinate structure"""
        self.coordinates = {
            'challenge_button': {'x': 0, 'y': 0},
            'crusade_button': {'x': 0, 'y': 0},
            'individual_button': {'x': 0, 'y': 0},
            'fight_button': {'x': 0, 'y': 0},
            'quick_combat': {'x': 0, 'y': 0},
            'ok_button': {'x': 0, 'y': 0},
            'claim_button': {'x': 0, 'y': 0},
            'reset_button': {'x': 0, 'y': 0},
            'exit_button': {'x': 0, 'y': 0}
        }
        
        # Add stage and reward coordinates (1-10)
        for i in range(1, 11):
            self.coordinates[f'stage_{i}'] = {'x': 0, 'y': 0}
            self.coordinates[f'reward_{i}'] = {'x': 0, 'y': 0}
    
    def setup_gui(self):
        """Setup main GUI interface"""
        # Title
        title = tk.Label(self.root, text="🎮 Auto Quest Individual", 
                        font=("Arial", 16, "bold"), fg="#2c3e50")
        title.pack(pady=10)
        
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configuration Management Section
        config_frame = ttk.LabelFrame(main_frame, text="Configuration Management", padding="10")
        config_frame.pack(fill=tk.X, pady=5)
        
        config_btn_frame = ttk.Frame(config_frame)
        config_btn_frame.pack(fill=tk.X)
        
        ttk.Button(config_btn_frame, text="🎯 Configure Coordinates", 
                  command=self.open_coordinate_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_btn_frame, text="💾 Save Configuration", 
                  command=self.save_configuration).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_btn_frame, text="📂 Load Configuration", 
                  command=self.load_configuration).pack(side=tk.LEFT, padx=5)
        
        # Stage Settings Section
        stage_frame = ttk.LabelFrame(main_frame, text="Stage Settings", padding="10")
        stage_frame.pack(fill=tk.X, pady=5)
        
        stages_row = ttk.Frame(stage_frame)
        stages_row.pack(fill=tk.X, pady=5)
        
        tk.Label(stages_row, text="Number of Stages to Complete:").pack(side=tk.LEFT)
        self.stages_var = tk.StringVar(value="10")
        stages_spin = tk.Spinbox(stages_row, from_=1, to=10, width=5, 
                               textvariable=self.stages_var)
        stages_spin.pack(side=tk.LEFT, padx=(10, 0))
        
        # Delay Settings Section
        delay_frame = ttk.LabelFrame(main_frame, text="Delay Settings (seconds)", padding="10")
        delay_frame.pack(fill=tk.X, pady=5)
        
        # First row of delays
        delay_row1 = ttk.Frame(delay_frame)
        delay_row1.pack(fill=tk.X, pady=2)
        
        tk.Label(delay_row1, text="Default Delay:").pack(side=tk.LEFT)
        self.default_delay_var = tk.StringVar(value="0.5")
        tk.Spinbox(delay_row1, from_=0.1, to=5.0, increment=0.1, width=8, 
                  textvariable=self.default_delay_var, format="%.1f").pack(side=tk.LEFT, padx=(5, 20))
        
        tk.Label(delay_row1, text="Navigation Delay:").pack(side=tk.LEFT)
        self.navigation_delay_var = tk.StringVar(value="1.0")
        tk.Spinbox(delay_row1, from_=0.1, to=10.0, increment=0.1, width=8, 
                  textvariable=self.navigation_delay_var, format="%.1f").pack(side=tk.LEFT, padx=(5, 0))
        
        # Second row of delays
        delay_row2 = ttk.Frame(delay_frame)
        delay_row2.pack(fill=tk.X, pady=2)
        
        tk.Label(delay_row2, text="Combat Delay:").pack(side=tk.LEFT)
        self.combat_delay_var = tk.StringVar(value="2.0")
        tk.Spinbox(delay_row2, from_=0.1, to=10.0, increment=0.1, width=8, 
                  textvariable=self.combat_delay_var, format="%.1f").pack(side=tk.LEFT, padx=(5, 20))
        
        tk.Label(delay_row2, text="Reward Delay:").pack(side=tk.LEFT)
        self.reward_delay_var = tk.StringVar(value="1.5")
        tk.Spinbox(delay_row2, from_=0.1, to=10.0, increment=0.1, width=8, 
                  textvariable=self.reward_delay_var, format="%.1f").pack(side=tk.LEFT, padx=(5, 0))
        
        # Reset delays button
        delay_row3 = ttk.Frame(delay_frame)
        delay_row3.pack(fill=tk.X, pady=5)
        
        ttk.Button(delay_row3, text="🔄 Reset to Default", 
                  command=self.reset_delays).pack(side=tk.LEFT)
        
        # Action buttons
        action_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
        action_frame.pack(fill=tk.X, pady=5)
        
        btn_frame = ttk.Frame(action_frame)
        btn_frame.pack()
        
        self.execute_btn = ttk.Button(btn_frame, text="🚀 Execute Stages", 
                                    command=self.start_execution)
        self.execute_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="🔄 Reset", command=self.execute_reset).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🚪 Clear/Exit", command=self.execute_exit).pack(side=tk.LEFT, padx=5)
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status & Logs", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=12, width=70)
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Current config display
        self.config_label = tk.Label(status_frame, text="No configuration loaded", 
                                   fg="gray", font=("Arial", 9))
        self.config_label.pack(pady=2)
    
    def reset_delays(self):
        """Reset all delays to default values"""
        self.default_delay_var.set("0.5")
        self.navigation_delay_var.set("1.0")
        self.combat_delay_var.set("2.0")
        self.reward_delay_var.set("1.5")
        self.log_message("🔄 Delays reset to default values")
    
    def get_current_delays(self):
        """Get current delay values from GUI"""
        try:
            return {
                'default': float(self.default_delay_var.get()),
                'navigation': float(self.navigation_delay_var.get()),
                'combat': float(self.combat_delay_var.get()),
                'reward': float(self.reward_delay_var.get())
            }
        except ValueError:
            self.log_message("⚠️ Invalid delay values, using defaults")
            return {
                'default': 0.5,
                'navigation': 1.0,
                'combat': 2.0,
                'reward': 1.5
            }
        """Open coordinate configuration window"""
    def open_coordinate_config(self):
        """Open coordinate configuration window"""
        CoordinateConfigWindow(self)
    
    def save_configuration(self):
        """Save current coordinates configuration"""
        config_name = simpledialog.askstring("Save Configuration", 
                                            "Enter configuration name:")
        if config_name:
            try:
                config_path = os.path.join(self.config_folder, f"{config_name}.json")
                with open(config_path, 'w') as f:
                    json.dump(self.coordinates, f, indent=4)
                self.log_message(f"💾 Configuration '{config_name}' saved successfully")
                self.current_config_name = config_name
                self.update_config_label()
                messagebox.showinfo("Success", f"Configuration '{config_name}' saved!")
            except Exception as e:
                self.log_message(f"❌ Error saving configuration: {str(e)}")
                messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def load_configuration(self):
        """Load coordinates configuration"""
        config_files = [f[:-5] for f in os.listdir(self.config_folder) if f.endswith('.json')]
        
        if not config_files:
            messagebox.showinfo("Info", "No saved configurations found")
            return
        
        # Create selection window
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Load Configuration")
        selection_window.geometry("300x200")
        selection_window.grab_set()
        
        tk.Label(selection_window, text="Select Configuration:", font=("Arial", 12)).pack(pady=10)
        
        listbox = tk.Listbox(selection_window)
        listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        for config in config_files:
            listbox.insert(tk.END, config)
        
        def load_selected():
            try:
                selection = listbox.curselection()
                if not selection:
                    messagebox.showwarning("Warning", "Please select a configuration")
                    return
                
                config_name = listbox.get(selection[0])
                config_path = os.path.join(self.config_folder, f"{config_name}.json")
                
                with open(config_path, 'r') as f:
                    self.coordinates = json.load(f)
                
                self.current_config_name = config_name
                self.update_config_label()
                self.log_message(f"📂 Configuration '{config_name}' loaded successfully")
                messagebox.showinfo("Success", f"Configuration '{config_name}' loaded!")
                selection_window.destroy()
                
            except Exception as e:
                self.log_message(f"❌ Error loading configuration: {str(e)}")
                messagebox.showerror("Error", f"Failed to load: {str(e)}")
        
        ttk.Button(selection_window, text="Load", command=load_selected).pack(pady=10)
    
    def update_config_label(self):
        """Update configuration label"""
        if self.current_config_name:
            self.config_label.config(text=f"Current config: {self.current_config_name}", fg="green")
        else:
            self.config_label.config(text="No configuration loaded", fg="gray")
    
    def log_message(self, message):
        """Add message to status log"""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
    
    def click_coordinate(self, coord_name, delay_type='default'):
        """Click on specified coordinate with specified delay type"""
        if coord_name in self.coordinates:
            coord = self.coordinates[coord_name]
            if coord['x'] != 0 or coord['y'] != 0:
                pyautogui.click(coord['x'], coord['y'])
                
                # Get current delays and apply appropriate delay
                delays = self.get_current_delays()
                delay_time = delays.get(delay_type, delays['default'])
                
                time.sleep(delay_time)
                return True
        self.log_message(f"❌ Coordinate '{coord_name}' not configured")
        return False
    
    def stage_loop(self):
        """Execute stage loop (Fight -> Quick Combat -> OK)"""
        self.log_message("⚔️ Executing stage loop...")
        self.click_coordinate('fight_button', 'default')
        self.click_coordinate('quick_combat', 'combat')
        self.click_coordinate('ok_button', 'default')
    
    def start_execution(self):
        """Start stage execution process"""
        if not self.validate_coordinates():
            return
        
        self.execute_btn.config(state="disabled")
        self.root.iconify()
        thread = threading.Thread(target=self.execute_stages)
        thread.daemon = True
        thread.start()
    
    def validate_coordinates(self):
        """Validate if coordinates are configured"""
        required_coords = ['challenge_button', 'crusade_button', 'individual_button', 
                          'fight_button', 'quick_combat', 'ok_button', 'claim_button']
        
        for coord in required_coords:
            if coord not in self.coordinates or (self.coordinates[coord]['x'] == 0 and self.coordinates[coord]['y'] == 0):
                messagebox.showerror("Error", f"Please configure '{coord}' coordinate first!")
                return False
        return True
    
    def execute_stages(self):
        """Execute stage process based on user input"""
        try:
            total_stages = int(self.stages_var.get())
            delays = self.get_current_delays()
            
            self.log_message(f"🚀 Starting execution for {total_stages} stages")
            self.log_message(f"⏱️ Using delays - Default: {delays['default']}s, Navigation: {delays['navigation']}s, Combat: {delays['combat']}s, Reward: {delays['reward']}s")
            
            # Initial navigation (Steps 1-3)
            self.log_message("📍 Step 1-3: Initial Navigation")
            self.click_coordinate('challenge_button', 'navigation')
            self.click_coordinate('crusade_button', 'navigation')
            self.click_coordinate('individual_button', 'navigation')
            
            # Execute stages
            for stage_num in range(1, total_stages + 1):
                self.log_message(f"🎯 Stage {stage_num} - Clicking Stage Button")
                self.click_coordinate(f'stage_{stage_num}', 'default')
                
                self.log_message(f"⚔️ Stage {stage_num} - Running Stage Loop")
                self.stage_loop()
                
                # Updated reward claiming process
                self.log_message(f"🏆 Stage {stage_num} - Clicking Reward Button")
                self.click_coordinate(f'reward_{stage_num}', 'reward')
                
                self.log_message(f"💰 Stage {stage_num} - Claiming Reward")
                self.click_coordinate('claim_button', 'reward')
                
                self.log_message(f"✅ Stage {stage_num} completed")
            
            self.log_message("🎉 All stages completed successfully!")
            messagebox.showinfo("Complete", f"Successfully completed {total_stages} stages!")
            
        except Exception as e:
            self.log_message(f"❌ Error during execution: {str(e)}")
            messagebox.showerror("Error", f"Execution failed: {str(e)}")
        
        finally:
            self.execute_btn.config(state="normal")
    
    def execute_reset(self):
        """Execute reset process"""
        try:
            self.log_message("🔄 Executing reset...")
            self.click_coordinate('reset_button', 'default')
            self.log_message("✅ Reset completed")
            messagebox.showinfo("Complete", "Reset executed successfully!")
        except Exception as e:
            self.log_message(f"❌ Error during reset: {str(e)}")
            messagebox.showerror("Error", f"Reset failed: {str(e)}")
    
    def execute_exit(self):
        """Execute exit process"""
        try:
            self.log_message("🚪 Executing exit...")
            self.click_coordinate('exit_button', 'default')
            self.log_message("✅ Exit completed")
            messagebox.showinfo("Complete", "Exit executed successfully!")
        except Exception as e:
            self.log_message(f"❌ Error during exit: {str(e)}")
            messagebox.showerror("Error", f"Exit failed: {str(e)}")

class CoordinateConfigWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent.root)
        self.window.title("Coordinate Configuration")
        self.window.geometry("700x700")
        self.window.grab_set()
        
        self.setup_config_gui()
    
    def setup_config_gui(self):
        """Setup coordinate configuration GUI"""
        # Instructions
        instructions = tk.Label(self.window, 
                               text="Click 'Capture' then click on the target element in the game\n"
                                    "Configure all required coordinates before saving",
                               font=("Arial", 10), fg="blue", wraplength=650)
        instructions.pack(pady=10)
        
        # Scrollable frame
        canvas = tk.Canvas(self.window)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Coordinate entries
        coord_labels = {
            'challenge_button': 'Challenge Button',
            'crusade_button': 'Crusade Button', 
            'individual_button': 'Individual Button',
            'fight_button': 'Fight Button',
            'quick_combat': 'Quick Combat Button',
            'ok_button': 'OK Button',
            'claim_button': 'Claim Button',
            'reset_button': 'Reset Button',
            'exit_button': 'Exit Button'
        }
        
        # Add stage and reward labels
        for i in range(1, 11):
            coord_labels[f'stage_{i}'] = f'Stage {i} Button'
            coord_labels[f'reward_{i}'] = f'Reward {i} Button'
        
        self.coord_vars = {}
        
        for coord_key, label in coord_labels.items():
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=2, padx=10)
            
            tk.Label(frame, text=label, width=20).pack(side=tk.LEFT)
            
            # X coordinate
            tk.Label(frame, text="X:").pack(side=tk.LEFT, padx=(10, 0))
            x_var = tk.StringVar(value=str(self.parent.coordinates.get(coord_key, {}).get('x', 0)))
            x_entry = ttk.Entry(frame, textvariable=x_var, width=8)
            x_entry.pack(side=tk.LEFT, padx=(5, 10))
            
            # Y coordinate
            tk.Label(frame, text="Y:").pack(side=tk.LEFT)
            y_var = tk.StringVar(value=str(self.parent.coordinates.get(coord_key, {}).get('y', 0)))
            y_entry = ttk.Entry(frame, textvariable=y_var, width=8)
            y_entry.pack(side=tk.LEFT, padx=(5, 10))
            
            # Capture button
            capture_btn = ttk.Button(frame, text="Capture", 
                                   command=lambda k=coord_key, xv=x_var, yv=y_var: self.capture_coordinate(k, xv, yv))
            capture_btn.pack(side=tk.LEFT, padx=5)
            
            self.coord_vars[coord_key] = {'x': x_var, 'y': y_var}
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Save & Close", command=self.save_and_close).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
    
    def capture_coordinate(self, coord_key, x_var, y_var):
        """Capture mouse coordinate on click"""
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
    
    def save_and_close(self):
        """Save coordinates and close window"""
        for coord_key, vars_dict in self.coord_vars.items():
            try:
                x = int(vars_dict['x'].get())
                y = int(vars_dict['y'].get())
                self.parent.coordinates[coord_key] = {'x': x, 'y': y}
            except ValueError:
                messagebox.showerror("Error", f"Invalid coordinate values for {coord_key}")
                return
        
        self.parent.log_message("📍 Coordinates updated successfully")
        self.window.destroy()

def main():
    root = tk.Tk()
    app = AutoQuestIndividual(root)
    root.eval('tk::PlaceWindow . center')
    root.mainloop()

if __name__ == "__main__":
    main()