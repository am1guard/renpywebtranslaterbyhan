import os
import re
import tkinter as tk
from tkinter import filedialog

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()

    # Regex ifadeleri ve dönüşümleri
    replacements = [
        (r'text\s* "(.*?)"', r'text _("\g<1>")'),
        (r'textbutton\s* "(.*?)"', r'textbutton _("\g<1>")'),
        (r'renpy\.input\(\s*"([^"]*)"', r'renpy.input(_("\g<1>"))'),
        (r'(\$ \w+ = )(".*?")', r'\1_(\2)'),
        (r'tooltip\s* "(.*?)"', r'tooltip _("\g<1>")'),
        (r'renpy\.notify\(\s*"([^"]*)"', r'renpy.notify(_("\g<1>"))'),
    ]

    for pattern, repl in replacements:
        content = re.sub(pattern, repl, content)

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content)
    print(f"İşlendi: {filepath}")

def main():
    # Tkinter ile klasör seçimi
    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(title="İşlenecek klasörü seçiniz")
    if not folder_selected:
        print("Herhangi bir klasör seçilmedi.")
        return

    # Seçilen klasör ve alt klasörlerindeki .rpy dosyalarını işle
    for rootdir, dirs, files in os.walk(folder_selected):
        for filename in files:
            if filename.lower().endswith(".rpy"):
                filepath = os.path.join(rootdir, filename)
                process_file(filepath)

    print("Tüm dosyalar başarıyla işlendi.")

if __name__ == "__main__":
    main()
