import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
from tkinter import PhotoImage
from playsound import playsound
import hashlib
import threading
import time

# Geçerli seri numaraları
valid_serial_numbers = ["ABC123", "DEF456", "GHI789"]

# Veritabanı başlatma ve yönetimi
def initialize_database():
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        therapy_type TEXT,
                        mode TEXT,
                        duration INTEGER,
                        status TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        surname TEXT,
                        serial_number TEXT,
                        password TEXT)""")  # 'password' sütunu eklenmiştir.
    conn.commit()
    conn.close()

def log_therapy(therapy_type, mode, duration, status):
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO history (therapy_type, mode, duration, status)
                      VALUES (?, ?, ?, ?)""", (therapy_type, mode, duration, status))
    conn.commit()
    conn.close()

def view_history():
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history ORDER BY timestamp DESC")
    records = cursor.fetchall()
    conn.close()
    return records

def register_user(name, surname, serial_number, password):
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("""INSERT INTO users (name, surname, serial_number, password)
                      VALUES (?, ?, ?, ?)""", (name, surname, serial_number, hashed_password))
    conn.commit()
    conn.close()

def validate_serial_number(serial_number, password):
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE serial_number = ?", (serial_number,))
    user = cursor.fetchone()
    conn.close()

    if user:
        stored_password = user[4]
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return stored_password == hashed_password
    return False

def validate_serial_number_for_registration(serial_number):
    return serial_number in valid_serial_numbers

def play_sound(file_path):
    if os.path.exists(file_path):
        try:
            playsound(file_path)
        except Exception as e:
            print(f"Ses çalınamadı: {e}")
    else:
        print(f"Ses dosyası bulunamadı: {file_path}")

class TherapyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Göğüs Terapi Cihazı")
        self.geometry("500x500")
        self.config(bg="#0078D7")  # Arka plan rengi
        self.iconbitmap(r"D:\\calismalar\\Python\\terapi\\assets\\icon.ico")
        self.current_frame = None
        self.therapy_type = tk.StringVar()
        self.mode = tk.StringVar()
        self.duration = tk.IntVar(value=1)
        self.running = False
        self.timer_thread = None
        self.sound_enabled = True
        self.sound_file = "complete.wav"
        self.user = None

        # Logo için fotoğraf yükleme
        self.logo = PhotoImage(file=r"D:\\calismalar\\Python\\terapi\\assets\\logo.png")  # Logo dosyasının tam yolu

        initialize_database()
        self.show_login_screen()

    def switch_frame(self, frame_class):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = frame_class(self)
        self.current_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.add_logo()  # Logo ekleme fonksiyonunu burada çağırıyoruz

    def show_login_screen(self):
        self.switch_frame(LoginScreen)

    def show_welcome_screen(self):
        self.switch_frame(WelcomeScreen)

    def show_therapy_selection_screen(self):
        self.switch_frame(TherapySelectionScreen)

    def show_therapy_control_screen(self):
        self.switch_frame(TherapyControlScreen)

    def show_history_screen(self):
        self.switch_frame(HistoryScreen)

    def show_settings_screen(self):
        self.switch_frame(SettingsScreen)

    def start_timer(self, duration):
        self.running = True
        self.timer_thread = threading.Thread(target=self.run_timer, args=(duration,))
        self.timer_thread.start()

    def run_timer(self, duration):
        for elapsed in range(duration):
            if not self.running:
                break
            time.sleep(1)
            remaining_time = duration - elapsed - 1
            progress = int(((elapsed + 1) / duration) * 100)
            # Timer güncellemeyi GUI thread'ine yönlendiriyoruz
            self.after(0, self.current_frame.update_timer, remaining_time, progress)
        if self.running:
            self.after(0, self.current_frame.update_timer, 0, 100)
            log_therapy(self.therapy_type.get(), self.mode.get(), self.duration.get(), "Tamamlandı")
            if self.sound_enabled:
                play_sound(self.sound_file)
            messagebox.showinfo("Terapi Tamamlandı", "Terapi tamamlandı!")
            self.show_therapy_selection_screen()

    def stop_timer(self):
        self.running = False
        log_therapy(self.therapy_type.get(), self.mode.get(), self.duration.get(), "Durduruldu")

    def add_logo(self):
        if self.current_frame:  # Eğer current_frame var ise logo ekle
            logo_label = tk.Label(self.current_frame, image=self.logo, bg="#f2f2f2")
            logo_label.place(relx=1.0, rely=1.0, anchor='se', x=-10, y=-10)


# Giriş Sayfası
class LoginScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Giriş Yapın", font=("Montserrat", 16)).pack(pady=20)
        tk.Label(self, text="Seri Numaranız:", font=("Montserrat", 12)).pack()
        self.serial_entry = tk.Entry(self, font=("Montserrat", 12))
        self.serial_entry.pack(pady=5)

        tk.Label(self, text="Şifre:", font=("Montserrat", 12)).pack()
        self.password_entry = tk.Entry(self, font=("Montserrat", 12), show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self, text="Giriş Yap", width=20, height=2, font=("Montserrat", 12), command=self.login).pack(pady=20)
        tk.Button(self, text="Kayıt Ol", width=20, height=2, font=("Montserrat", 12), command=self.register).pack(pady=10)

    def login(self):
        serial_number = self.serial_entry.get()
        password = self.password_entry.get()

        if not serial_number or not password:
            messagebox.showerror("Hata", "Seri numarası ve şifreyi girin!")
            return

        if not validate_serial_number(serial_number, password):
            messagebox.showerror("Hata", "Geçersiz seri numarası veya şifre!")
            return

        messagebox.showinfo("Başarılı", "Giriş başarılı!")
        self.master.show_welcome_screen()

    def register(self):
        self.master.switch_frame(RegisterScreen)


# Kayıt Sayfası
class RegisterScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Kayıt Ol", font=("Montserrat", 16)).pack(pady=20)
        tk.Label(self, text="Ad:", font=("Montserrat", 12)).pack()
        self.name_entry = tk.Entry(self, font=("Montserrat", 12))
        self.name_entry.pack(pady=5)

        tk.Label(self, text="Soyad:", font=("Montserrat", 12)).pack()
        self.surname_entry = tk.Entry(self, font=("Montserrat", 12))
        self.surname_entry.pack(pady=5)

        tk.Label(self, text="Seri Numaranız:", font=("Montserrat", 12)).pack()
        self.serial_entry = tk.Entry(self, font=("Montserrat", 12))
        self.serial_entry.pack(pady=5)

        tk.Label(self, text="Şifre:", font=("Montserrat", 12)).pack()
        self.password_entry = tk.Entry(self, font=("Montserrat", 12), show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self, text="Kayıt Ol", width=20, height=2, font=("Montserrat", 12), command=self.register).pack(pady=20)
        tk.Button(self, text="Geri", width=20, height=2, font=("Montserrat", 12), command=self.master.show_login_screen).pack(pady=10)

    def register(self):
        name = self.name_entry.get()
        surname = self.surname_entry.get()
        serial_number = self.serial_entry.get()
        password = self.password_entry.get()

        if not name or not surname or not serial_number or not password:
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurun!")
            return

        if not validate_serial_number_for_registration(serial_number):
            messagebox.showerror("Hata", "Geçersiz seri numarası!")
            return

        register_user(name, surname, serial_number, password)
        messagebox.showinfo("Başarılı", "Kayıt başarılı!")
        self.master.show_login_screen()


# Hoşgeldiniz Sayfası
class WelcomeScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Hoşgeldiniz", font=("Montserrat", 16)).pack(pady=20)
        tk.Button(self, text="Terapi Seç", width=20, height=2, font=("Montserrat", 12), command=self.master.show_therapy_selection_screen).pack(pady=20)
        tk.Button(self, text="Geçmişi Görüntüle", width=20, height=2, font=("Montserrat", 12), command=self.master.show_history_screen).pack(pady=10)
        tk.Button(self, text="Ayarlar", width=20, height=2, font=("Montserrat", 12), command=self.master.show_settings_screen).pack(pady=10)
        tk.Button(self, text="Çıkış", width=20, height=2, font=("Montserrat", 12), command=self.quit).pack(pady=20)


# Terapilere Özel Seçim Ekranı ve kontrol
class TherapySelectionScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Terapi Seçin", font=("Montserrat", 16)).pack(pady=20)
        tk.Button(self, text="Başla", width=20, height=2, font=("Montserrat", 12), command=self.master.show_therapy_control_screen).pack(pady=10)
        tk.Button(self, text="Geri", width=20, height=2, font=("Montserrat", 12), command=self.master.show_welcome_screen).pack(pady=10)


# Terapiler İçin Kontrol Ekranı
class TherapyControlScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.therapy_duration_label = tk.Label(self, text="Terapi Süresi (Dakika):", font=("Montserrat", 12))
        self.therapy_duration_label.pack(pady=10)

        self.duration_spinbox = ttk.Spinbox(self, from_=1, to=60, textvariable=master.duration, font=("Montserrat", 12))
        self.duration_spinbox.pack(pady=5)

        self.start_button = tk.Button(self, text="Başlat", width=20, height=2, font=("Montserrat", 12), command=self.start_therapy)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(self, text="Durdur", width=20, height=2, font=("Montserrat", 12), command=self.stop_therapy)
        self.stop_button.pack(pady=10)

        self.status_label = tk.Label(self, text="Durum: Hazır", font=("Montserrat", 12))
        self.status_label.pack(pady=20)

        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=300, mode="determinate", maximum=100)
        self.progress_bar.pack(pady=20)

        self.timer_label = tk.Label(self, text="Kalan Süre: 00:00", font=("Montserrat", 12))
        self.timer_label.pack(pady=20)

        tk.Button(self, text="Geri", width=20, height=2, font=("Montserrat", 12), command=self.master.show_therapy_selection_screen).pack(pady=10)

    def start_therapy(self):
        self.master.start_timer(self.master.duration.get())

    def stop_therapy(self):
        self.master.stop_timer()

    def update_timer(self, remaining_time, progress):
        self.timer_label.config(text=f"Kalan Süre: {remaining_time//60:02}:{remaining_time%60:02}")
        self.progress_bar["value"] = progress


# Geçmiş Ekranı
class HistoryScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Geçmiş", font=("Montserrat", 16)).pack(pady=20)

        history_records = view_history()
        for record in history_records:
            tk.Label(self, text=f"{record[1]} - {record[2]} - {record[3]} Dakika - {record[4]}", font=("Montserrat", 12)).pack(pady=5)

        tk.Button(self, text="Geri", width=20, height=2, font=("Montserrat", 12), command=self.master.show_welcome_screen).pack(pady=10)


# Ayarlar Ekranı
class SettingsScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Ayarlar", font=("Montserrat", 16)).pack(pady=20)
        self.sound_checkbox = tk.Checkbutton(self, text="Ses Efektlerini Aç", variable=master.sound_enabled)
        self.sound_checkbox.pack(pady=10)
        tk.Button(self, text="Geri", width=20, height=2, font=("Montserrat", 12), command=self.master.show_welcome_screen).pack(pady=20)


if __name__ == "__main__":
    app = TherapyApp()
    app.mainloop()
