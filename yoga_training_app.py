import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import json
import os
import sys
import cv2
import importlib.util

# Check required packages
required_packages = ["opencv-python", "mediapipe", "pyttsx3"]
# missing_packages = []

# for package in required_packages:
#     spec = importlib.util.find_spec(package.replace("-", "_").split(">=")[0])
#     if spec is None:
#         missing_packages.append(package)

# if missing_packages:
#     print(f"Missing required packages: {', '.join(missing_packages)}")
#     print("Please install them using:")
#     print(f"pip install {' '.join(missing_packages)}")
#     sys.exit(1)

# Import our yoga corrector
from yoga_pose_corrector import start_pose_correction

class YogaTrainingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Yoga Training Assistant")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TButton', font=('Arial', 12), background='#4CAF50')
        self.style.configure('TLabel', font=('Arial', 12), background='#f0f0f0')
        self.style.configure('Header.TLabel', font=('Arial', 16, 'bold'), background='#f0f0f0')
        
        # Load pose database
        try:
            with open('pose_database.json', 'r') as f:
                self.pose_database = json.load(f)
            print(f"Loaded {len(self.pose_database)} poses from database")
        except FileNotFoundError:
            messagebox.showerror("Error", "pose_database.json not found")
            self.pose_database = {}
        
        # Create main container
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header
        header_label = ttk.Label(self.main_frame, text="Yoga Training Assistant", style='Header.TLabel')
        header_label.pack(pady=(0, 20))
        
        # Create content
        self.create_content_frame()
        
        # Running indicator
        self.running = False
        self.process = None
    
    def create_content_frame(self):
        # Create content frame
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Pose selection
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Pose selection label
        ttk.Label(left_frame, text="Select a pose to practice:").pack(anchor=tk.W, pady=(0, 10))
        
        # Pose list with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.pose_listbox = tk.Listbox(list_frame, font=('Arial', 12), selectbackground='#4CAF50')
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.pose_listbox.yview)
        self.pose_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.pose_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate pose list
        for pose_name in sorted(self.pose_database.keys()):
            display_name = pose_name.replace('_', ' ')
            self.pose_listbox.insert(tk.END, display_name)
        
        # Bind selection event
        self.pose_listbox.bind('<<ListboxSelect>>', self.on_pose_select)
        
        # Right side - Pose information
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Pose information label
        ttk.Label(right_frame, text="Pose Information", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # Information display area
        info_frame = ttk.Frame(right_frame)
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # Pose name
        self.pose_name_var = tk.StringVar()
        ttk.Label(info_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(info_frame, textvariable=self.pose_name_var).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Pose description
        self.pose_desc_var = tk.StringVar()
        ttk.Label(info_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(info_frame, textvariable=self.pose_desc_var).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Instructions frame
        ttk.Label(info_frame, text="Instructions:").grid(row=2, column=0, sticky=tk.NW, pady=5)
        
        # Text widget for instructions
        self.instructions_text = tk.Text(info_frame, height=10, width=40, wrap=tk.WORD, font=('Arial', 11))
        self.instructions_text.grid(row=2, column=1, sticky=tk.W, pady=5)
        self.instructions_text.config(state=tk.DISABLED)
        
        # Button frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Add buttons
        self.practice_button = ttk.Button(button_frame, text="Practice Selected Pose", command=self.start_practice)
        self.practice_button.pack(side=tk.LEFT, padx=5)
        
        self.detect_button = ttk.Button(button_frame, text="Free Practice (Auto-Detect)", command=self.start_detection)
        self.detect_button.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def on_pose_select(self, event):
        # Get selected pose
        if not self.pose_listbox.curselection():
            return
        
        selected_idx = self.pose_listbox.curselection()[0]
        display_name = self.pose_listbox.get(selected_idx)
        pose_name = display_name.replace(' ', '_')
        
        # Update information display
        if pose_name in self.pose_database:
            pose_data = self.pose_database[pose_name]
            self.pose_name_var.set(display_name)
            self.pose_desc_var.set(pose_data.get("description", "No description available"))
            
            # Update instructions
            self.instructions_text.config(state=tk.NORMAL)
            self.instructions_text.delete(1.0, tk.END)
            
            instructions = pose_data.get("instructions", [])
            if instructions:
                self.instructions_text.insert(tk.END, "\n".join(f"• {instr}" for instr in instructions))
            else:
                self.instructions_text.insert(tk.END, "No specific instructions available.")
            
            self.instructions_text.config(state=tk.DISABLED)
    
    def start_practice(self):
        if self.running:
            messagebox.showinfo("Already Running", "A yoga session is already running.")
            return
        
        # Get selected pose
        if not self.pose_listbox.curselection():
            messagebox.showinfo("Select Pose", "Please select a pose to practice first.")
            return
        
        selected_idx = self.pose_listbox.curselection()[0]
        display_name = self.pose_listbox.get(selected_idx)
        pose_name = display_name.replace(' ', '_')
        
        # Start practice in new thread
        self.running = True
        self.status_var.set(f"Practicing: {display_name}")
        
        threading.Thread(target=self._run_practice, args=(pose_name,), daemon=True).start()
    
    def start_detection(self):
        if self.running:
            messagebox.showinfo("Already Running", "A yoga session is already running.")
            return
        
        # Start detection in new thread
        self.running = True
        self.status_var.set("Auto-detecting poses")
        
        threading.Thread(target=self._run_practice, args=(None,), daemon=True).start()
    
    def _run_practice(self, pose_name=None):
        try:
            # Run the yoga corrector
            start_pose_correction(pose_name)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.running = False
            self.status_var.set("Ready")

if __name__ == "__main__":
    # Check if database exists
    if not os.path.exists('pose_database.json'):
        messagebox.showerror("Error", "pose_database.json not found. Make sure it's in the same directory.")
        sys.exit(1)
    
    # Check webcam availability
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Could not access webcam. Please check your camera.")
        sys.exit(1)
    cap.release()
    
    # Start application
    root = tk.Tk()
    app = YogaTrainingApp(root)
    root.mainloop()