import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import sqlite3
import os
from tkinter import PhotoImage

# Veritabanı başlatma ve yönetimi
def initialize_database():
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            therapy_type TEXT,
            mode TEXT,
            duration INTEGER,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def log_therapy(therapy_type, mode, duration, status):
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO history (therapy_type, mode, duration, status)
        VALUES (?, ?, ?, ?)
    """, (therapy_type, mode, duration, status))
    conn.commit()
    conn.close()

def view_history():
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history ORDER BY timestamp DESC")
    records = cursor.fetchall()
    conn.close()
    return records

def play_sound(file_path):
    if os.path.exists(file_path):
        try:
            from playsound import playsound
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
        self.config(bg="#f2f2f2")  # Arka plan rengi

        # Uygulama simgesini ekliyoruz
        self.iconbitmap(r"D:\calismalar\Python\terapi\assets\icon.ico")

        self.current_frame = None
        self.therapy_type = tk.StringVar()
        self.mode = tk.StringVar()
        self.duration = tk.IntVar(value=1)
        self.running = False
        self.timer_thread = None
        self.sound_enabled = True
        self.sound_file = "complete.wav"

        # Logo için fotoğraf yükleme
        self.logo = PhotoImage(file=r"D:\calismalar\Python\terapi\assets\logo.png")  # Logo dosyasının tam yolu

        initialize_database()
        self.show_welcome_screen()


    def switch_frame(self, frame_class):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = frame_class(self)
        self.current_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.add_logo()  # Logo ekleme fonksiyonunu burada çağırıyoruz

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
            self.current_frame.update_timer(remaining_time, progress)
        if self.running:
            self.current_frame.update_timer(0, 100)
            log_therapy(self.therapy_type.get(), self.mode.get(), self.duration.get(), "Tamamlandı")
            if self.sound_enabled:
                play_sound(self.sound_file)
            messagebox.showinfo("Terapi Tamamlandı", "Terapi tamamlandı!")
            self.show_therapy_selection_screen()

    def stop_timer(self):
        self.running = False
        log_therapy(self.therapy_type.get(), self.mode.get(), self.duration.get(), "Durduruldu")

    # Logo eklemek için fonksiyon
    def add_logo(self):
        if self.current_frame:  # Eğer current_frame var ise logo ekle
            logo_label = tk.Label(self.current_frame, image=self.logo, bg="#f2f2f2")
            logo_label.place(relx=1.0, rely=1.0, anchor='se', x=-10, y=-10)


class WelcomeScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Göğüs Terapi Cihazı'na Hoş Geldiniz", font=("Montserrat", 16)).pack(pady=20)
        tk.Button(self, text="Başla", command=master.show_therapy_selection_screen).pack(pady=10)
        tk.Button(self, text="Geçmiş", command=master.show_history_screen).pack(pady=10)
        tk.Button(self, text="Ayarlar", command=master.show_settings_screen).pack(pady=10)


class TherapySelectionScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Terapi Türü Seçin", font=("Montserrat", 14)).pack(pady=10)
        ttk.Combobox(self, textvariable=master.therapy_type,
                     values=["Kol Terapisi", "Göğüs Terapisi", "Bacak Terapisi"]).pack(pady=10)
        tk.Label(self, text="Mod Seçin", font=("Montserrat", 14)).pack(pady=10)
        ttk.Combobox(self, textvariable=master.mode, values=["Hafif", "Orta", "Yoğun"]).pack(pady=10)
        tk.Button(self, text="Devam Et", command=master.show_therapy_control_screen).pack(pady=10)
        tk.Button(self, text="Geri", command=master.show_welcome_screen).pack(pady=10)


class TherapyControlScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Süreyi Ayarlayın (Dakika)", font=("Montserrat", 14)).pack(pady=10)
        tk.Spinbox(self, from_=1, to=60, textvariable=master.duration).pack(pady=10)
        tk.Button(self, text="Başlat", command=lambda: master.start_timer(master.duration.get() * 60)).pack(pady=10)
        tk.Button(self, text="Durdur", command=master.stop_timer).pack(pady=10)
        tk.Button(self, text="Geri", command=master.show_therapy_selection_screen).pack(pady=10)
        self.timer_label = tk.Label(self, text="Kalan Süre: 00:00", font=("Montserrat", 14))
        self.timer_label.pack(pady=10)
        self.progress_bar = ttk.Progressbar(self, length=300, mode='determinate')
        self.progress_bar.pack(pady=10)

    def update_timer(self, remaining_time, progress):
        minutes, seconds = divmod(remaining_time, 60)
        self.timer_label.config(text=f"Kalan Süre: {minutes:02}:{seconds:02}")
        self.progress_bar['value'] = progress


class HistoryScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Terapi Geçmişi", font=("Montserrat", 16)).pack(pady=10)
        records = view_history()
        if records:
            for record in records:
                tk.Label(self, text=f"{record[1]} | {record[2]} | {record[3]} dk | {record[4]}").pack()
        else:
            tk.Label(self, text="Geçmiş bulunamadı.", font=("Montserrat", 14)).pack()
        tk.Button(self, text="Geri Dön", command=master.show_welcome_screen).pack(pady=10)


class SettingsScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Ayarlar", font=("Montserrat", 16)).pack(pady=20)
        self.sound_var = tk.BooleanVar(value=master.sound_enabled)
        tk.Checkbutton(self, text="Sesi Aç/Kapat", variable=self.sound_var, command=self.toggle_sound).pack(pady=20)
        tk.Button(self, text="Geri Dön", command=master.show_welcome_screen).pack(pady=10)

    def toggle_sound(self):
        self.master.sound_enabled = self.sound_var.get()


if __name__ == "__main__":
    app = TherapyApp()
    app.mainloop()
