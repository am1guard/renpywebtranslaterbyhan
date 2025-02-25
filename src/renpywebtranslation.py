import os
import re
import html
import json
import requests
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import string

class TranslationApp:
    DEFAULT_PLACEHOLDER = "{c100}"   # Yeni varsayılan placeholder

    def __init__(self, root):
        self.root = root
        self.root.title("Ren'Py Web Translator Tool")
        self.root.configure(bg='black')
        
        # Stil ayarları
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('.', background='black', foreground='cyan', fieldbackground='black')
        self.style.map('TButton', foreground=[('active', 'cyan')], background=[('active', 'black')])
        
        # Değişkenler
        self.directory = ""
        self.original_strings = []    # HTML ve çeviri metin alanında gösterilecek metinler
        self.translation_entries = [] # Her metnin detaylarını tutan liste (choice_pair için çift satır)
        
        # Özel filtre regex'leri
        self.exclude_patterns = [
            re.compile(r'\{.*?\}'),
            re.compile(r'\[.*?\]'),
            re.compile(r'\.(png|jpg|jpeg|gif|mp3|wav|ogg)\b', re.IGNORECASE)
        ]

        # GUI bileşenleri
        self.create_widgets()
    
    def create_widgets(self):
        self.dir_btn = ttk.Button(self.root, text="Select folder", command=self.select_directory)
        self.dir_btn.pack(pady=10)
        
        self.info_label = ttk.Label(self.root, text="No folder selected")
        self.info_label.pack()
        
        self.export_btn = ttk.Button(self.root, text="Extract to the html", command=self.export_html, state='disabled')
        self.export_btn.pack(pady=5)
        
        self.translate_frame = ttk.Frame(self.root)
        self.translate_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.original_text = scrolledtext.ScrolledText(self.translate_frame, width=40, height=20,
                                                        bg='black', fg='cyan', insertbackground='cyan')
        self.original_text.pack(side='left', fill='both', expand=True)
        
        self.translated_text = scrolledtext.ScrolledText(self.translate_frame, width=40, height=20,
                                                          bg='black', fg='cyan', insertbackground='cyan')
        self.translated_text.pack(side='right', fill='both', expand=True)
        
        self.apply_btn = ttk.Button(self.root, text="Aplly Translations", command=self.apply_translations, state='disabled')
        self.apply_btn.pack(pady=10)

        # Repair window button
        self.custom_replace_btn = ttk.Button(self.root, text="Repair window", command=self.open_replacement_window)
        self.custom_replace_btn.pack(pady=10)
        
        # Auto Translate and target language entry
        auto_frame = ttk.Frame(self.root)
        auto_frame.pack(pady=10)
        self.auto_translate_btn = ttk.Button(auto_frame, text="Auto Translate", command=self.auto_translate)
        self.auto_translate_btn.pack(side='left', padx=5)
        lang_label = ttk.Label(auto_frame, text="Target Lang:", background='black', foreground='cyan')
        lang_label.pack(side='left', padx=5)
        self.target_lang_entry = ttk.Entry(auto_frame, width=5)
        self.target_lang_entry.pack(side='left', padx=5)
        self.target_lang_entry.insert(0, "tr")  # default target language
    
    def is_only_punctuation(self, s):
        """Verilen s dizesinin yalnızca noktalama ve boşluk içerip içermediğini kontrol eder."""
        s = s.strip()
        return s != "" and all(ch in string.punctuation for ch in s)
    
    def process_brackets(self, s):
        mapping_sq = []
        mapping_cr = []
        def repl_sq(match):
            mapping_sq.append(match.group(0))
            return f'[sq{len(mapping_sq)-1}]'
        processed = re.sub(r'\[(.*?)\]', repl_sq, s)
        def repl_cr(match):
            mapping_cr.append(match.group(0))
            return f'{{cr{len(mapping_cr)-1}}}'
        processed = re.sub(r'\{(.*?)\}', repl_cr, processed)
        return s, processed, (mapping_sq, mapping_cr)
    
    def restore_brackets(self, s, mapping):
        mapping_sq, mapping_cr = mapping
        def repl_sq(match):
            idx = int(match.group(1))
            return mapping_sq[idx] if idx < len(mapping_sq) else match.group(0)
        def repl_cr(match):
            idx = int(match.group(1))
            return mapping_cr[idx] if idx < len(mapping_cr) else match.group(0)
        s = re.sub(r'\[sq(\d+)\]', repl_sq, s)
        s = re.sub(r'\{cr(\d+)\}', repl_cr, s)
        return s
    
    def select_directory(self):
        self.directory = filedialog.askdirectory()
        if self.directory:
            self.info_label.config(text=f"Seçilen Klasör: {self.directory}")
            self.translation_entries = self.parse_rpy_files()
            self.original_text.delete(1.0, tk.END)
            self.original_text.insert(tk.END, '\n'.join(self.original_strings))
            self.export_btn.config(state='normal')
    
    def parse_rpy_files(self):
        entries = []
        self.original_strings = []  # HTML ve çeviri metin alanında kullanılacak metinler
        for root_dir, _, files in os.walk(self.directory):
            for file in files:
                if file.endswith('.rpy'):
                    path = os.path.join(root_dir, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # İşle: translate blokları (varsa)
                    in_translate_block = False
                    block_lines = []
                    block_line_indices = []
                    i = 0
                    while i < len(lines):
                        line = lines[i]
                        if re.match(r'^\s*translate\s+', line):
                            in_translate_block = True
                            block_lines = []
                            block_line_indices = []
                            i += 1
                            continue
                        if in_translate_block:
                            if line.startswith(' ') or line.startswith('\t'):
                                block_lines.append(line)
                                block_line_indices.append(i)
                                i += 1
                                continue
                            else:
                                active = None
                                active_idx = None
                                commented = None
                                commented_idx = None
                                for bline, bidx in zip(block_lines, block_line_indices):
                                    if not bline.lstrip().startswith('#'):
                                        m = re.findall(r'"((?:[^"\\]|\\.)*?)"', bline, re.DOTALL)
                                        if m:
                                            active = m[0]
                                            active_idx = bidx
                                            break
                                    else:
                                        m = re.findall(r'"((?:[^"\\]|\\.)*?)"', bline, re.DOTALL)
                                        if m and commented is None:
                                            commented = m[0]
                                            commented_idx = bidx
                                chosen = active if active is not None else commented
                                chosen_idx = active_idx if active is not None else commented_idx
                                if chosen is not None:
                                    raw, processed, mapping = self.process_brackets(chosen)
                                    if raw.strip() == "":
                                        processed = self.DEFAULT_PLACEHOLDER
                                    if chosen.strip().startswith('old'):
                                        category = 'old'
                                    elif chosen.strip().startswith('new'):
                                        category = 'choice'
                                    else:
                                        category = 'dialog'
                                    if self.is_only_punctuation(processed):
                                        if self.original_strings:
                                            self.original_strings[-1] += processed
                                            entries[-1]['processed'] += processed
                                        else:
                                            entries.append({
                                                'file': path,
                                                'line_index': chosen_idx,
                                                'raw': raw,
                                                'processed': processed,
                                                'mapping': mapping,
                                                'category': category
                                            })
                                            self.original_strings.append(processed)
                                    else:
                                        entries.append({
                                            'file': path,
                                            'line_index': chosen_idx,
                                            'raw': raw,
                                            'processed': processed,
                                            'mapping': mapping,
                                            'category': category
                                        })
                                        self.original_strings.append(processed)
                                in_translate_block = False
                                continue
                        
                        # Normal kısım; burada çift (old/new) satır çifti kontrolü
                        stripped = line.lstrip()
                        if stripped.startswith('#'):
                            i += 1
                            continue
                        if stripped.startswith('old'):
                            j = i + 1
                            while j < len(lines) and lines[j].strip() == '':
                                j += 1
                            if j < len(lines) and lines[j].lstrip().startswith('new'):
                                m_old = re.findall(r'"((?:[^"\\]|\\.)*?)"', line, re.DOTALL)
                                m_new = re.findall(r'"((?:[^"\\]|\\.)*?)"', lines[j], re.DOTALL)
                                if m_old and m_new:
                                    raw_old, processed_old, mapping_old = self.process_brackets(m_old[0])
                                    raw_new, processed_new, mapping_new = self.process_brackets(m_new[0])
                                    if raw_new.strip() == "":
                                        processed_new = self.DEFAULT_PLACEHOLDER
                                    if self.is_only_punctuation(processed_new):
                                        if self.original_strings:
                                            self.original_strings[-1] += processed_new
                                            if entries:
                                                if 'processed_new' in entries[-1]:
                                                    entries[-1]['processed_new'] += processed_new
                                                else:
                                                    entries[-1]['processed'] += processed_new
                                        else:
                                            entries.append({
                                                'file': path,
                                                'old_line_index': i,
                                                'new_line_index': j,
                                                'raw_old': raw_old,
                                                'processed_old': processed_old,
                                                'mapping_old': mapping_old,
                                                'raw_new': raw_new,
                                                'processed_new': processed_new,
                                                'mapping_new': mapping_new,
                                                'category': 'choice_pair'
                                            })
                                            self.original_strings.append(processed_new)
                                    else:
                                        entries.append({
                                            'file': path,
                                            'old_line_index': i,
                                            'new_line_index': j,
                                            'raw_old': raw_old,
                                            'processed_old': processed_old,
                                            'mapping_old': mapping_old,
                                            'raw_new': raw_new,
                                            'processed_new': processed_new,
                                            'mapping_new': mapping_new,
                                            'category': 'choice_pair'
                                        })
                                        self.original_strings.append(processed_new)
                                i = j + 1
                                continue
                            else:
                                m = re.findall(r'"((?:[^"\\]|\\.)*?)"', line, re.DOTALL)
                                for s in m:
                                    raw, processed, mapping = self.process_brackets(s)
                                    if raw.strip() == "":
                                        processed = self.DEFAULT_PLACEHOLDER
                                    if self.is_only_punctuation(processed):
                                        if self.original_strings:
                                            self.original_strings[-1] += processed
                                            entries[-1]['processed'] += processed
                                        else:
                                            entries.append({
                                                'file': path,
                                                'line_index': i,
                                                'raw': raw,
                                                'processed': processed,
                                                'mapping': mapping,
                                                'category': 'old'
                                            })
                                            self.original_strings.append(processed)
                                    else:
                                        entries.append({
                                            'file': path,
                                            'line_index': i,
                                            'raw': raw,
                                            'processed': processed,
                                            'mapping': mapping,
                                            'category': 'old'
                                        })
                                        self.original_strings.append(processed)
                                i += 1
                                continue
                        elif stripped.startswith('new'):
                            m = re.findall(r'"((?:[^"\\]|\\.)*?)"', line, re.DOTALL)
                            for s in m:
                                raw, processed, mapping = self.process_brackets(s)
                                if raw.strip() == "":
                                    processed = self.DEFAULT_PLACEHOLDER
                                if self.is_only_punctuation(processed):
                                    if self.original_strings:
                                        self.original_strings[-1] += processed
                                        entries[-1]['processed'] += processed
                                    else:
                                        entries.append({
                                            'file': path,
                                            'line_index': i,
                                            'raw': raw,
                                            'processed': processed,
                                            'mapping': mapping,
                                            'category': 'choice'
                                        })
                                        self.original_strings.append(processed)
                                else:
                                    entries.append({
                                        'file': path,
                                        'line_index': i,
                                        'raw': raw,
                                        'processed': processed,
                                        'mapping': mapping,
                                        'category': 'choice'
                                    })
                                    self.original_strings.append(processed)
                            i += 1
                            continue
                        else:
                            m = re.findall(r'"((?:[^"\\]|\\.)*?)"', line, re.DOTALL)
                            for s in m:
                                raw, processed, mapping = self.process_brackets(s)
                                if raw.strip() == "":
                                    processed = self.DEFAULT_PLACEHOLDER
                                if self.is_only_punctuation(processed):
                                    if self.original_strings:
                                        self.original_strings[-1] += processed
                                        entries[-1]['processed'] += processed
                                    else:
                                        entries.append({
                                            'file': path,
                                            'line_index': i,
                                            'raw': raw,
                                            'processed': processed,
                                            'mapping': mapping,
                                            'category': 'dialog'
                                        })
                                        self.original_strings.append(processed)
                                else:
                                    entries.append({
                                        'file': path,
                                        'line_index': i,
                                        'raw': raw,
                                        'processed': processed,
                                        'mapping': mapping,
                                        'category': 'dialog'
                                    })
                                    self.original_strings.append(processed)
                            i += 1
        return entries

    def export_html(self):
        if not self.original_strings:
            messagebox.showwarning("Warning!!?!", "No text found to translate!\nMake sure this is a renpy game \nor select the translation folder")
            return

        html_content = """<html>
    <head>
        <style>
            body { background-color: black; color: cyan; font-family: monospace; }
            .container {
                display: flex;
                flex-wrap: wrap;
                justify-content: space-around;
                padding: 10px;
            }
            .item {
                margin: 10px;
                padding: 5px;
                border: 1px solid cyan;
                white-space: pre-wrap;
                max-width: 300px;
            }
        </style>
    </head>
    <body>
        <div class="container">
    """
        for s in self.original_strings:
            s_clean = s.replace("\n", "").strip()
            html_content += f'        <div class="item">{html.escape(s_clean)}</div>\n'
        html_content += """    </div>
    </body>
    </html>"""

        with open('translations.html', 'w', encoding='utf-8') as f:
            f.write(html_content)

        webbrowser.open('translations.html')
        self.apply_btn.config(state='normal')
    
    def apply_translations(self):
        # Çeviri alanındaki satırları al (boş satırlar atlanır)
        translated_lines = [t.strip() for t in self.translated_text.get(1.0, tk.END).split('\n') if t.strip()]
        non_old_idx = 0  # "old" dışındaki girdiler için index
        
        for entry in self.translation_entries:
            if entry['category'] == 'old':
                entry['translated'] = entry['raw']
            elif entry['category'] == 'choice_pair':
                if non_old_idx < len(translated_lines):
                    if translated_lines[non_old_idx].strip() == "{c}":
                        entry['translated_new'] = entry['raw_new']
                    else:
                        entry['translated_new'] = self.restore_brackets(
                            translated_lines[non_old_idx].replace('"', r'\"'),
                            entry['mapping_new']
                        )
                    non_old_idx += 1
                else:
                    entry['translated_new'] = entry['raw_new']
            else:
                if non_old_idx < len(translated_lines):
                    if translated_lines[non_old_idx].strip() == "{c}":
                        entry['translated'] = entry['raw']
                    else:
                        entry['translated'] = self.restore_brackets(
                            translated_lines[non_old_idx].replace('"', r'\"'),
                            entry['mapping']
                        )
                    non_old_idx += 1
                else:
                    entry['translated'] = entry['raw']
        
        files_data = {}
        for entry in self.translation_entries:
            fpath = entry['file']
            if fpath not in files_data:
                with open(fpath, 'r', encoding='utf-8') as f:
                    files_data[fpath] = f.readlines()
        
        for entry in self.translation_entries:
            lines = files_data[entry['file']]
            if entry['category'] == 'choice_pair':
                line_idx = entry['new_line_index']
                pattern = rf'"{re.escape(entry["raw_new"])}"'
                lines[line_idx] = re.sub(pattern, lambda m: f'"{entry["translated_new"]}"', lines[line_idx], count=1)
            else:
                line_idx = entry['line_index']
                pattern = rf'"{re.escape(entry["raw"])}"'
                lines[line_idx] = re.sub(pattern, lambda m: f'"{entry["translated"]}"', lines[line_idx], count=1)
        
        for fpath, lines in files_data.items():
            with open(fpath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
        messagebox.showinfo("Niicee", "Translations applied succesfully!")
    
    def perform_replacements(self, text):
        # Sabit metin değişiklikleri
        text = text.replace("{C", "{c")
        text = text.replace("[kare ", "[sq")
        text = text.replace("% ", "%")
        text = text.replace("%S", "%s")
        text = text.replace("[Sq", "[sq")
        return text
    
    def open_replacement_window(self):
        rep_window = tk.Toplevel(self.root)
        rep_window.title("Paste translation here")
        rep_window.configure(bg='black')
        
        # Main text widget
        text_widget = scrolledtext.ScrolledText(rep_window, width=60, height=20,
                                                bg='black', fg='cyan', insertbackground='cyan')
        text_widget.pack(padx=10, pady=10)
        
        # Button to apply built-in replacements
        def apply_replacements_in_window():
            original_text = text_widget.get(1.0, tk.END)
            modified_text = self.perform_replacements(original_text)
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, modified_text)
            messagebox.showinfo("Info", "Fixed replacements implemented!")
        
        rep_button = ttk.Button(rep_window, text="Change", command=apply_replacements_in_window)
        rep_button.pack(pady=5)
        
        # New frame for custom replacement inputs
        custom_frame = ttk.Frame(rep_window)
        custom_frame.pack(pady=10)
        
        find_label = ttk.Label(custom_frame, text="Find:", background="black", foreground="cyan")
        find_label.pack(side="left", padx=(0,5))
        
        find_entry = ttk.Entry(custom_frame, width=10)
        find_entry.pack(side="left", padx=(0,5))
        
        replace_label = ttk.Label(custom_frame, text="Replace with:", background="black", foreground="cyan")
        replace_label.pack(side="left", padx=(0,5))
        
        replace_entry = ttk.Entry(custom_frame, width=10)
        replace_entry.pack(side="left", padx=(0,5))
        
        def apply_custom_replacement():
            find_text = find_entry.get()
            replace_text = replace_entry.get()
            if not find_text:
                messagebox.showwarning("Warning", "Please enter text to find.")
                return
            original_text = text_widget.get(1.0, tk.END)
            modified_text = original_text.replace(find_text, replace_text)
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, modified_text)
            messagebox.showinfo("Info", f"Replaced '{find_text}' with '{replace_text}'.")
        
        custom_button = ttk.Button(custom_frame, text="Custom Replace", command=apply_custom_replacement)
        custom_button.pack(side="left", padx=5)
    
    def google_translate(self, texts, from_lang="auto", to_lang="tr"):
        """
        Gönderilen metin listesini Google API aracılığıyla çevirir.
        """
        body = [
            [texts, from_lang, to_lang],
            "te_lib"
        ]
        
        headers = {
            'Content-Type': 'application/json+protobuf',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36',
            'Referer': 'https://www.amazon.com',
            'x-goog-api-key': 'AIzaSyATBXajvzQLTDHEQbcpq0Ihe0vWDHmO520'
        }
        
        try:
            response = requests.post(
                'https://translate-pa.googleapis.com/v1/translateHtml',
                headers=headers,
                data=json.dumps(body)
            )
            response.raise_for_status()
            translated_texts = [html.unescape(line) for line in response.json()[0]]
            return translated_texts
        except Exception as e:
            print(f"Erro ao realizar tradução: {e}")
            return []
    
    def auto_translate(self):
        if not self.original_strings:
            messagebox.showwarning("Warning", "No text found to translate!")
            return
        
        target_lang = self.target_lang_entry.get().strip() or "tr"
        self.auto_translate_btn.config(state='disabled')
        translated_texts = self.google_translate(self.original_strings, from_lang="auto", to_lang=target_lang)
        if translated_texts:
            self.translated_text.delete(1.0, tk.END)
            self.translated_text.insert(tk.END, "\n".join(translated_texts))
            messagebox.showinfo("Info", "Auto translation completed!")
            self.apply_btn.config(state='normal')
        else:
            messagebox.showerror("Error", "Auto translation failed!")
        self.auto_translate_btn.config(state='normal')
        
if __name__ == "__main__":
    root = tk.Tk()
    app = TranslationApp(root)
    root.mainloop()
