import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import shutil

# ------------------ Appearance & Global Settings ------------------ #
ctk.set_appearance_mode("dark")          # Use dark mode
ctk.set_default_color_theme("blue")      # You can pick another theme if you wish

app = ctk.CTk()
app.title("Ren'Py Font Replacement Program")
app.geometry("800x300")                  # Window size
app.configure(bg="black")

# Fonts for buttons and labels (adjust sizes as desired)
button_font = ctk.CTkFont(family="Arial", size=14, weight="bold")
label_font = ctk.CTkFont(family="Arial", size=13)

# Let the root window have two columns: column 0 for buttons, column 1 for labels
app.columnconfigure(0, weight=0)  # Button column
app.columnconfigure(1, weight=1)  # Label column (expandable)

# ------------------ Global Variables ------------------ #
translation_folder = ""
font_file = ""

# ------------------ Functions ------------------ #
def select_translation_folder():
    global translation_folder
    folder = filedialog.askdirectory(title="Select Translation Folder")
    if folder:
        translation_folder = folder
        translation_label.configure(text=translation_folder)

def select_font_file():
    global font_file
    file = filedialog.askopenfilename(
        title="Select Font File",
        filetypes=[("Font Files", "*.ttf *.otf *.TTF *.OTF")]
    )
    if file:
        font_file = file
        font_label.configure(text=font_file)

def replace_font():
    if not translation_folder or not font_file:
        messagebox.showerror("Error", "Please select both the translation folder and the font file.")
        return

    # Extract file/folder names
    font_name = os.path.basename(font_file)
    folder_name = os.path.basename(translation_folder.rstrip(os.sep))

    # Build the Ren'Py code
    code = f"""init python early hide:
    import renpy
    if 'tl_font_dic' not in globals():
        global tl_font_dic
        tl_font_dic = dict()
        global old_load_face
        old_load_face = renpy.text.font.load_face

        def my_load_face(fn, *args):
            renpy.text.font.free_memory()
            for key, value in tl_font_dic.items():
                if renpy.game.preferences.language == key:
                    fn = value[0]
                    renpy.config.rtl = value[1]
            return old_load_face(fn, *args)
        renpy.text.font.load_face = my_load_face
    global tl_font_dic
    tl_font_dic["{folder_name}"] = ("fonts/{font_name}", False)
    old_reload_all = renpy.reload_all
    def my_reload_all():
        renpy.text.font.free_memory()
        renpy.text.font.load_face = old_load_face
        ret = old_reload_all()
        renpy.reload_all = old_reload_all
        return ret
    renpy.reload_all = my_reload_all
    """

    # Write gui.rpy inside the selected translation folder
    gui_rpy_path = os.path.join(translation_folder, "gui.rpy")
    try:
        with open(gui_rpy_path, "w", encoding="utf-8") as f:
            f.write(code)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to write gui.rpy:\n{e}")
        return

    # Determine the "game" folder by going two levels up from the translation folder
    # Example: if translation_folder = ".../game/tl/turkish", then game_folder = ".../game"
    game_folder = os.path.dirname(os.path.dirname(translation_folder))
    fonts_dir = os.path.join(game_folder, "fonts")
    os.makedirs(fonts_dir, exist_ok=True)

    # Copy the selected font file to the "fonts" directory in the game folder
    try:
        shutil.copy(font_file, os.path.join(fonts_dir, font_name))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to copy the font file:\n{e}")
        return

    messagebox.showinfo("Success", f"gui.rpy has been created in:\n{translation_folder}\n\nFont copied to:\n{fonts_dir}")

# ------------------ Widgets & Layout ------------------ #

# 1) Translation Folder Row
select_folder_button = ctk.CTkButton(
    master=app,
    text="Select Translation Folder",
    command=select_translation_folder,
    corner_radius=20,
    fg_color="gray20",
    text_color="cyan",
    hover_color="gray30",
    font=button_font,
    width=250,
    height=40
)
select_folder_button.grid(row=0, column=0, padx=20, pady=15, sticky="w")

translation_label = ctk.CTkLabel(
    master=app,
    text="No folder selected",
    text_color="cyan",
    bg_color="black",
    font=label_font
)
translation_label.grid(row=0, column=1, padx=20, pady=15, sticky="w")

# 2) Font File Row
select_font_button = ctk.CTkButton(
    master=app,
    text="Select Font File",
    command=select_font_file,
    corner_radius=20,
    fg_color="gray20",
    text_color="cyan",
    hover_color="gray30",
    font=button_font,
    width=250,
    height=40
)
select_font_button.grid(row=1, column=0, padx=20, pady=15, sticky="w")

font_label = ctk.CTkLabel(
    master=app,
    text="No font file selected",
    text_color="cyan",
    bg_color="black",
    font=label_font
)
font_label.grid(row=1, column=1, padx=20, pady=15, sticky="w")

# 3) Replace Font Row
replace_font_button = ctk.CTkButton(
    master=app,
    text="Replace Font",
    command=replace_font,
    corner_radius=20,
    fg_color="gray20",
    text_color="cyan",
    hover_color="gray30",
    font=button_font,
    width=250,
    height=40
)
replace_font_button.grid(row=2, column=0, columnspan=2, padx=20, pady=20)

# ------------------ Mainloop ------------------ #
app.mainloop()
