import customtkinter as ctk
import subprocess


# Function to run a given script.
def run_script(script_name):
    try:
        subprocess.Popen(["python", script_name])
    except Exception as e:
        print(f"Failed to run {script_name}: {e}")

# Set the appearance mode to dark.
ctk.set_appearance_mode("dark")
# You can also set a default color theme. We'll adjust colors manually.
ctk.set_default_color_theme("blue")

# Create the main application window.
root = ctk.CTk()
root.title("File Opening Program")
root.geometry("400x300")  # Set an appropriate window size
root.iconbitmap("icon.ico")
# Configure the main window background (CustomTkinter uses its own styling).
root.configure(bg_color="black")

# Button style settings
button_width = 300
button_height = 50
corner_radius = 25  # Rounded edges

# Button for renpywebtranslation.py
btn1 = ctk.CTkButton(
    root, 
    text="Renpy Translation Tool", 
    command=lambda: run_script("renpywebtranslation.py"),
    width=button_width,
    height=button_height,
    corner_radius=corner_radius,
    text_color="cyan",       # Text in cyan
    fg_color="black",        # Button background black
    hover_color="#1a1a1a"    # Slightly lighter on hover
)
btn1.pack(pady=10)

# Button for REGEXDÜZEN.py
btn2 = ctk.CTkButton(
    root, 
    text="Full translation provider", 
    command=lambda: run_script("REGEXDÜZEN.py"),
    width=button_width,
    height=button_height,
    corner_radius=corner_radius,
    text_color="cyan",
    fg_color="black",
    hover_color="#1a1a1a"
)
btn2.pack(pady=10)

# Button for coderepair.py
btn3 = ctk.CTkButton(
    root, 
    text="Code Repair", 
    command=lambda: run_script("coderepair.py"),
    width=button_width,
    height=button_height,
    corner_radius=corner_radius,
    text_color="cyan",
    fg_color="black",
    hover_color="#1a1a1a"
)
btn3.pack(pady=10)

# Button for script4.py
btn4 = ctk.CTkButton(
    root, 
    text="Replace Font", 
    command=lambda: run_script("replacefont.py"),
    width=button_width,
    height=button_height,
    corner_radius=corner_radius,
    text_color="cyan",
    fg_color="black",
    hover_color="#1a1a1a"
)
btn4.pack(pady=10)

# Start the application loop.
root.mainloop()
