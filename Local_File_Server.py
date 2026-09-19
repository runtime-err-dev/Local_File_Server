import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import socket
import http.server
import os
import webbrowser
import json


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


class FileServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local File Server")
        self.root.geometry("480x420")
        self.root.resizable(False, False)

        appdata_dir = os.getenv('APPDATA') # Получаем путь к C:\Users\Имя\AppData\Roaming
        base_dir = os.path.join(appdata_dir, "LocalFileServer")
        
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            
        self.settings_file = os.path.join(base_dir, "settings.json")

        self.server_thread = None
        self.httpd = None
        self.is_running = False
        
        settings = self.load_settings()
        
        self.selected_folder = tk.StringVar(value=settings["default_folder"])
        self.default_folder_var = tk.StringVar(value=settings["default_folder"])
        self.autostart_var = tk.BooleanVar(value=settings["autostart"])
        self.port_var = tk.IntVar(value=8000)

        self.setup_ui()

        if self.autostart_var.get():
            self.root.after(100, self.start_server)

    def load_settings(self):
        settings = {"default_folder": os.getcwd(), "autostart": False}
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    folder = data.get("default_folder", "")
                    if os.path.isdir(folder):
                        settings["default_folder"] = folder
                    settings["autostart"] = data.get("autostart", False)
            except Exception:
                pass
        return settings

    def save_settings(self):
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump({
                    "default_folder": self.default_folder_var.get(),
                    "autostart": self.autostart_var.get()
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки:\n{e}")

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("192.168.1.1", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            try:
                ips = socket.gethostbyname_ex(socket.gethostname())[2]
                for ip in ips:
                    if ip.startswith("192.168."):
                        return ip
                return ips[0] if ips else "127.0.0.1"
            except Exception:
                return "127.0.0.1"

    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.tab_main = ttk.Frame(self.notebook)
        self.tab_settings = ttk.Frame(self.notebook)
        self.tab_about = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_main, text="Главная")
        self.notebook.add(self.tab_settings, text="Настройки")
        self.notebook.add(self.tab_about, text="О программе")

    # === Вкладка 1: Главная ===
        ttk.Label(self.tab_main, text="Текущая папка для раздачи:").pack(pady=(15, 5))
        
        self.lbl_folder = ttk.Label(self.tab_main, textvariable=self.selected_folder, foreground="#005bb5", wraplength=440, justify="center")
        self.lbl_folder.pack(pady=5)

        ttk.Button(self.tab_main, text="Выбрать другую папку", command=self.choose_folder).pack(pady=5)

        self.btn_toggle = ttk.Button(self.tab_main, text="Запустить сервер", command=self.toggle_server)
        self.btn_toggle.pack(pady=15)

        self.lbl_status = ttk.Label(self.tab_main, text="Остановлен", foreground="gray", font=("Arial", 10, "bold"))
        self.lbl_status.pack()

        self.url_frame = ttk.Frame(self.tab_main)
        self.url_frame.pack(pady=5)

        self.lbl_url = ttk.Entry(self.url_frame, justify="center", state="readonly", width=28)
        self.lbl_url.pack(side="left", padx=(0, 5))

        self.btn_copy = ttk.Button(self.url_frame, text="Скопировать", command=self.copy_url, state="disabled")
        self.btn_copy.pack(side="left")

    # === Вкладка 2: Настройки ===
        ttk.Label(self.tab_settings, text="Сетевой порт:").pack(pady=(15, 5))
        ttk.Entry(self.tab_settings, textvariable=self.port_var, width=15, justify="center").pack()
        ttk.Label(self.tab_settings, text="Оставьте 8000, если не было конфликтов.", foreground="gray").pack(pady=(0, 10))
        
        ttk.Separator(self.tab_settings, orient='horizontal').pack(fill='x', padx=20, pady=10)
        
        ttk.Label(self.tab_settings, text="Папка по умолчанию при запуске:").pack(pady=(5, 5))
        self.lbl_def_folder = ttk.Label(self.tab_settings, textvariable=self.default_folder_var, foreground="#005bb5", wraplength=440, justify="center")
        self.lbl_def_folder.pack(pady=5)
        
        ttk.Button(self.tab_settings, text="Изменить папку", command=self.choose_default_folder).pack(pady=5)

        ttk.Checkbutton(
            self.tab_settings, 
            text="Автоматически запускать сервер при открытии", 
            variable=self.autostart_var,
            command=self.save_settings 
        ).pack(pady=10)

    # === Вкладка 3: О программе ===
        ttk.Label(self.tab_about, text="Local File Server GUI", font=("Arial", 14, "bold")).pack(pady=(30, 5))
        link_tg = tk.Label(self.tab_about, text="Разработчик: @runtime_err (телеграмм)", fg="#005bb5", font=("Arial", 10, "underline"), cursor="hand2")
        link_tg.pack(pady=5)
        link_tg.bind("<Button-1>", lambda e: webbrowser.open_new("https://t.me/runtime_err"))
        
        link_github = tk.Label(self.tab_about, text="GitHub: https://github.com/runtime-err-dev/Local_File_Server", fg="#005bb5", font=("Arial", 10, "underline"), cursor="hand2")
        link_github.pack(pady=5)
        link_github.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/runtime-err-dev"))

        ttk.Label(self.tab_about, text="Версия: v1.0", justify="center", foreground="gray").pack(pady=15)
        ttk.Label(self.tab_about, text="Оболочка для быстрого поднятия сервера\nи передачи файлов на ваши устройства.", justify="center", foreground="gray").pack(pady=15)

    def copy_url(self):
        url = self.lbl_url.get()
        if url:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            self.root.update()

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.selected_folder.get())
        if folder:
            self.selected_folder.set(folder)

    def choose_default_folder(self):
        folder = filedialog.askdirectory(initialdir=self.default_folder_var.get())
        if folder:
            self.default_folder_var.set(folder)
            self.save_settings()
            if not self.is_running:
                self.selected_folder.set(folder)

    def toggle_server(self):
        if self.is_running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        port = self.port_var.get()
        folder = self.selected_folder.get()
        
        os.chdir(folder)

        try:
            self.httpd = http.server.ThreadingHTTPServer(("", port), QuietHandler)
            self.is_running = True
            
            self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.server_thread.start()

            self.btn_toggle.config(text="Остановить сервер")
            self.lbl_status.config(text="Сервер работает", foreground="green")
            self.btn_copy.config(state="normal")
            
            ip = self.get_local_ip()
            self.lbl_url.config(state="normal")
            self.lbl_url.delete(0, tk.END)
            self.lbl_url.insert(0, f"http://{ip}:{port}")
            self.lbl_url.config(state="readonly")
            
        except OSError as e:
            messagebox.showerror("Ошибка порта", f"Не удалось запустить сервер.\nВозможно, порт {port} занят.\n\nКод: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{e}")

    def stop_server(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.is_running = False
            
            self.btn_toggle.config(text="Запустить сервер")
            self.lbl_status.config(text="Остановлен", foreground="gray")
            self.btn_copy.config(state="disabled")
            
            self.lbl_url.config(state="normal")
            self.lbl_url.delete(0, tk.END)
            self.lbl_url.config(state="readonly")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileServerApp(root)
    root.mainloop()