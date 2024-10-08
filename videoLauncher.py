import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import (
    colorchooser,
    filedialog,
    messagebox,
    simpledialog,
    Menu,
    font as tkfont,
)
from tkinterdnd2 import DND_FILES, TkinterDnD
from screeninfo import get_monitors  # Import screeninfo

# Path to the settings file
SETTINGS_FILE = "settings.json"

class VideoLauncherApp:
    """
    Main application class for the Video Launcher.
    """

    def __init__(self, root):
        """
        Initialize the application.
        """
        self.root = root
        self.settings = self.load_settings()
        self.fullscreen = self.settings.get("fullscreen", False)
        self.overrideredirect = False  # Track overrideredirect state
        self.buttons = []
        self.font = tkfont.Font(
            family=self.settings.get("font_family", "Arial"),
            size=self.settings.get("font_size", 12)
        )
        self.vlc_path = self.settings.get("vlc_path", "")
        self.vlc_process = None  # Track the vlc process
        self.init_ui()

    def load_settings(self):
        """
        Load settings from the JSON settings file.
        """
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        else:
            # Default settings
            return {
                "background_color": "#000000",
                "button_border_color": "#FFFFFF",
                "button_text_color": "#FFFFFF",
                "font_family": "Arial",
                "font_size": 12,
                "fullscreen": False,
                "window_geometry": "600x600+100+100",
                "vlc_path": "",
                "fullscreen_monitor": None,
                "buttons": [{"title": f"Button {i+1}", "video": ""} for i in range(9)],
            }

    def save_settings(self):
        """
        Save the current settings to the JSON settings file.
        """
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)

    def reset_settings(self):
        """
        Reset settings to default and restart the application.
        """
        if messagebox.askyesno(
            "Reset Settings", "Are you sure you want to reset all settings to default?"
        ):
            if os.path.exists(SETTINGS_FILE):
                os.remove(SETTINGS_FILE)
            self.restart_application()

    def restart_application(self):
        """
        Restart the application.
        """
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def init_ui(self):
        """
        Initialize the user interface.
        """
        self.root.title("Video Launcher")
        self.apply_window_geometry()

        # Set background color
        self.root.configure(bg=self.settings.get("background_color", "#000000"))

        # Bind window resize and move events to save geometry
        self.root.bind("<Configure>", self.save_window_geometry)

        # Create buttons
        self.create_buttons()

        # Create context menu
        self.create_context_menu()

        # Bind right-click to show context menu
        self.root.bind("<Button-3>", self.show_context_menu)

        # Handle fullscreen on startup
        if self.fullscreen:
            self.enter_fullscreen_on_startup()

    def apply_window_geometry(self):
        """
        Apply saved window geometry.
        """
        geometry = self.settings.get("window_geometry", "600x600+100+100")
        self.root.geometry(geometry)

    def save_window_geometry(self, event):
        """
        Save window geometry on resize or move.
        """
        # Avoid saving geometry when in fullscreen
        if not self.fullscreen and not self.overrideredirect:
            self.settings["window_geometry"] = self.root.geometry()
            self.save_settings()

    def create_buttons(self):
        """
        Create the 9 buttons and place them in a 3x3 grid.
        """
        # Configure grid rows and columns to expand equally
        for i in range(3):
            self.root.grid_columnconfigure(i, weight=1, uniform="col")
            self.root.grid_rowconfigure(i, weight=1, uniform="row")

        for i in range(9):
            button_info = self.settings["buttons"][i]
            title = button_info.get("title", f"Button {i+1}")
            command = self.close_vlc if i == 8 else lambda i=i: self.play_video(
                self.settings["buttons"][i]["video"]
            )
            btn = tk.Button(
                self.root,
                text=title if i != 8 else "VR Experience",
                command=command,
                borderwidth=4,
                highlightbackground=self.settings.get(
                    "button_border_color", "#FFFFFF"
                ),
                fg=self.settings.get("button_text_color", "#FFFFFF"),
                bg=self.settings.get("background_color", "#000000"),
                activebackground=self.settings.get("background_color", "#000000"),
                font=self.font,
                relief="flat",
            )
            # Remove default styling to simulate transparency
            btn.configure(highlightthickness=4)
            # Set button border color
            btn.config(
                highlightcolor=self.settings.get("button_border_color", "#FFFFFF"),
                highlightbackground=self.settings.get("button_border_color", "#FFFFFF"),
            )
            # Enable drag-and-drop for buttons 1-8
            if i != 8:
                btn.drop_target_register(DND_FILES)
                btn.dnd_bind("<<Drop>>", lambda event, i=i: self.drag_and_drop(event, i))
            btn.grid(row=i // 3, column=i % 3, sticky="nsew", padx=5, pady=5)
            self.buttons.append(btn)

    def create_context_menu(self):
        """
        Create the right-click context menu.
        """
        self.context_menu = Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Settings", command=self.open_settings)
        self.context_menu.add_command(
            label="Select Font", command=self.select_font
        )
        self.context_menu.add_command(
            label="Toggle Fullscreen", command=self.toggle_fullscreen
        )
        self.context_menu.add_command(label="Help", command=self.show_help)
        self.context_menu.add_command(label="Quit", command=self.quit_program)

    def show_context_menu(self, event):
        """
        Display the context menu.
        """
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def open_settings(self):
        """
        Open the settings window.
        """
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x600")
        settings_window.resizable(False, False)

        # Change vlc Path
        tk.Button(
            settings_window,
            text="Set vlc Executable Path",
            command=self.set_vlc_path,
        ).pack(pady=10, fill="x", padx=20)

        # Change Background Color
        tk.Button(
            settings_window,
            text="Change Background Color",
            command=self.change_background_color,
        ).pack(pady=10, fill="x", padx=20)

        # Change Button Style
        tk.Button(
            settings_window,
            text="Change Button Style",
            command=self.change_button_style,
        ).pack(pady=10, fill="x", padx=20)

        # Reset Settings
        tk.Button(
            settings_window,
            text="Reset Settings",
            command=self.reset_settings,
        ).pack(pady=10, fill="x", padx=20)

        # Configure Buttons
        for i in range(9):
            btn_text = f"Configure Button {i + 1}"
            if i == 8:
                btn_text = "Configure VR Experience Button"
            tk.Button(
                settings_window,
                text=btn_text,
                command=lambda i=i: self.update_button_settings(i),
            ).pack(pady=5, fill="x", padx=20)

    def set_vlc_path(self):
        """
        Set the path to the vlc executable.
        """
        vlc_path = filedialog.askopenfilename(
            title="Select vlc Executable",
            filetypes=[
                ("vlc Executable", "vlc.exe"),
                ("All Files", "*.*"),
            ],
            initialdir=r"C:\Program Files\VideoLAN\vlc",
        )
        if vlc_path and os.path.exists(vlc_path):
            # Normalize the path to use backslashes
            vlc_path = os.path.normpath(vlc_path)
            self.vlc_path = vlc_path
            self.settings["vlc_path"] = vlc_path
            self.save_settings()
            messagebox.showinfo("vlc Path Set", f"vlc path set to: {vlc_path}")
        else:
            messagebox.showerror("Error", "Invalid vlc path selected.")

    def update_button_settings(self, button_index):
        """
        Update the title and video for a button.
        """
        # Ask for new title
        title = simpledialog.askstring(
            "Button Title", f"Set title for Button {button_index + 1}:"
        )
        if title:
            self.settings["buttons"][button_index]["title"] = title
            self.buttons[button_index].config(text=title, font=self.font)

        # For buttons 1-8, ask for video file
        if button_index != 8:
            video_path = filedialog.askopenfilename(
                title="Select Video File",
                filetypes=[
                    ("Video Files", "*.mp4 *.avi *.mkv *.mov *.wmv"),
                    ("All Files", "*.*"),
                ],
            )
            if video_path:
                # Normalize the path to use backslashes
                video_path = os.path.normpath(video_path)
                self.settings["buttons"][button_index]["video"] = video_path

        self.save_settings()

    def change_background_color(self):
        """
        Change the background color of the window.
        """
        color = colorchooser.askcolor(title="Select Background Color")[1]
        if color:
            self.settings["background_color"] = color
            self.root.configure(bg=color)
            for button in self.buttons:
                button.config(
                    bg=color,
                    activebackground=color,
                )
            self.save_settings()

    def change_button_style(self):
        """
        Change the button border and text colors.
        """
        border_color = colorchooser.askcolor(title="Select Button Border Color")[1]
        text_color = colorchooser.askcolor(title="Select Button Text Color")[1]
        if border_color and text_color:
            for button in self.buttons:
                button.config(
                    highlightbackground=border_color,
                    highlightcolor=border_color,
                    fg=text_color,
                )
            self.settings["button_border_color"] = border_color
            self.settings["button_text_color"] = text_color
            self.save_settings()

    def select_font(self):
        """
        Select font and font size for the buttons.
        """
        font_families = list(tkfont.families())
        font_families.sort()

        font_window = tk.Toplevel(self.root)
        font_window.title("Select Font")
        font_window.geometry("300x400")
        font_window.resizable(False, False)

        tk.Label(font_window, text="Select Font Family:").pack(pady=5)
        font_family_var = tk.StringVar(value=self.font.actual("family"))
        font_family_listbox = tk.Listbox(font_window, height=10)
        for family in font_families:
            font_family_listbox.insert(tk.END, family)
        font_family_listbox.pack(fill="both", expand=True, padx=10)
        # Select current font family
        current_family = self.font.actual("family")
        if current_family in font_families:
            index = font_families.index(current_family)
            font_family_listbox.selection_set(index)
            font_family_listbox.see(index)

        tk.Label(font_window, text="Select Font Size:").pack(pady=5)
        font_size_var = tk.IntVar(value=self.font.actual("size"))
        font_size_spinbox = tk.Spinbox(font_window, from_=8, to=72, textvariable=font_size_var)
        font_size_spinbox.pack(pady=5)

        def apply_font():
            selected_indices = font_family_listbox.curselection()
            if selected_indices:
                selected_family = font_family_listbox.get(selected_indices[0])
                selected_size = font_size_var.get()
                self.font.config(family=selected_family, size=selected_size)
                for button in self.buttons:
                    button.config(font=self.font)
                self.settings["font_family"] = selected_family
                self.settings["font_size"] = selected_size
                self.save_settings()
                font_window.destroy()
            else:
                messagebox.showwarning("No Font Selected", "Please select a font family.")

        tk.Button(font_window, text="Apply", command=apply_font).pack(pady=10)

    def play_video(self, video_path):
        """
        Play the selected video using vlc.
        """
        # Close any existing vlc instance started by this application
        self.close_vlc()

        if not self.vlc_path or not os.path.exists(self.vlc_path):
            messagebox.showerror(
                "vlc Not Found",
                "vlc executable not found. Please set the vlc path in Settings.",
            )
            return

        if video_path and os.path.exists(video_path):
            try:
                # Normalize paths
                vlc_path = os.path.normpath(self.vlc_path)
                video_path = os.path.normpath(video_path)

                # Construct the vlc command as a list
                vlc_command = [
                    vlc_path,
                    "--fullscreen",
                    "--loop",
                    "--quiet",
                    "--no-video-title-show",
                    video_path
                ]

                # Print the command for debugging
                print("Executing vlc command:", vlc_command)

                # Launch vlc with the command
                self.vlc_process = subprocess.Popen(vlc_command)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to launch vlc: {e}")
        else:
            messagebox.showwarning(
                "Video Not Found", "No video file assigned or file does not exist."
            )

    def close_vlc(self):
        """
        Close the vlc process started by this application.
        """
        try:
            if self.vlc_process and self.vlc_process.poll() is None:
                # Terminate the vlc process
                self.vlc_process.kill()
                self.vlc_process.wait()
                self.vlc_process = None
        except Exception as e:
            messagebox.showerror("Error", f"Failed to close vlc: {e}")

    def drag_and_drop(self, event, button_index):
        """
        Handle drag-and-drop of video files onto buttons.
        """
        try:
            video_path = event.data.strip("{}")  # Remove braces if present
            if os.path.isfile(video_path):
                # Normalize the path
                video_path = os.path.normpath(video_path)
                self.settings["buttons"][button_index]["video"] = video_path
                self.save_settings()
                messagebox.showinfo(
                    "Success",
                    f"Video assigned to Button {button_index + 1}",
                )
            else:
                raise FileNotFoundError
        except Exception:
            messagebox.showerror(
                "Error", "Invalid file or path. Please drop a valid video file."
            )

    def enter_fullscreen_on_startup(self):
        """
        Enter fullscreen mode on startup, using the saved monitor information.
        """
        monitor_info = self.settings.get("fullscreen_monitor")
        if monitor_info:
            # Check if the monitor is available
            for monitor in get_monitors():
                if (
                    monitor.x == monitor_info['x']
                    and monitor.y == monitor_info['y']
                    and monitor.width == monitor_info['width']
                    and monitor.height == monitor_info['height']
                ):
                    # Remove window borders
                    self.root.overrideredirect(True)
                    self.overrideredirect = True

                    # Set the window geometry to cover the monitor
                    self.root.geometry(
                        f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}"
                    )
                    break
            else:
                # Monitor not found, default to primary monitor
                self.root.attributes("-fullscreen", True)
        else:
            # No saved monitor info, default to primary monitor
            self.root.attributes("-fullscreen", True)

    def toggle_fullscreen(self):
        """
        Toggle between fullscreen and windowed mode on the current monitor.
        """
        self.fullscreen = not self.fullscreen
        self.settings["fullscreen"] = self.fullscreen

        if self.fullscreen:
            # Get the current window position
            self.root.update_idletasks()
            window_x = self.root.winfo_x()
            window_y = self.root.winfo_y()

            # Find the monitor where the window is currently located
            for monitor in get_monitors():
                if (
                    window_x >= monitor.x
                    and window_x < monitor.x + monitor.width
                    and window_y >= monitor.y
                    and window_y < monitor.y + monitor.height
                ):
                    # Remove window borders
                    self.root.overrideredirect(True)
                    self.overrideredirect = True

                    # Save the current geometry to restore later
                    self.windowed_geometry = self.root.geometry()

                    # Set the window geometry to cover the entire monitor
                    self.root.geometry(
                        f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}"
                    )

                    # Save monitor info to settings
                    self.settings["fullscreen_monitor"] = {
                        "x": monitor.x,
                        "y": monitor.y,
                        "width": monitor.width,
                        "height": monitor.height
                    }
                    break
            else:
                # If monitor not found, default to normal fullscreen
                self.root.attributes("-fullscreen", True)
                self.overrideredirect = False
                self.settings["fullscreen_monitor"] = None
        else:
            # Restore window borders
            if self.overrideredirect:
                self.root.overrideredirect(False)
                self.overrideredirect = False

                # Restore the windowed geometry
                if hasattr(self, 'windowed_geometry'):
                    self.root.geometry(self.windowed_geometry)
            else:
                self.root.attributes("-fullscreen", False)
            self.settings["fullscreen_monitor"] = None

        self.save_settings()

    def quit_program(self):
        """
        Quit the application.
        """
        # Close vlc when quitting the application
        self.close_vlc()
        self.root.quit()

    def show_help(self):
        """
        Display the help window.
        """
        help_window = tk.Toplevel(self.root)
        help_window.title("Help")
        help_window.geometry("500x600")
        help_window.resizable(False, False)

        help_text = (
            "Video Launcher Application Help\n\n"
            "Features:\n"
            "1. **Main Screen**: Displays 9 buttons in a 3x3 grid.\n"
            "2. **Button Actions**:\n"
            "   - Click a button to play the assigned video on loop using vlc.\n"
            "   - The 9th button ('VR Experience') closes vlc.\n"
            "3. **Customization**:\n"
            "   - Right-click to access the context menu.\n"
            "   - Settings: Customize background color, button colors, titles, and video files.\n"
            "   - Drag and Drop: Drag video files onto buttons to assign them.\n"
            "4. **Modes**:\n"
            "   - Toggle between fullscreen and windowed modes via the context menu.\n"
            "   - The application remembers the last mode and window position.\n"
            "5. **Additional Options**:\n"
            "   - Select Font: Choose the font and size for button text.\n"
            "   - Reset Settings: Restore default settings.\n"
            "   - Quit: Exit the application.\n\n"
            "For further assistance, contact support."
        )

        tk.Label(
            help_window,
            text=help_text,
            justify=tk.LEFT,
            padx=10,
            pady=10,
            wraplength=480,
        ).pack(expand=True, fill="both")

def main():
    """
    Main function to run the application.
    """
    # Initialize the main window with drag-and-drop support
    root = TkinterDnD.Tk()
    app = VideoLauncherApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
