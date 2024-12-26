import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import time
import sqlite3
from playsound import playsound


# Veritabanı oluşturma
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


# Veritabanına kayıt ekleme
def log_therapy(therapy_type, mode, duration, status):
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO history (therapy_type, mode, duration, status)
        VALUES (?, ?, ?, ?)
    """, (therapy_type, mode, duration, status))
    conn.commit()
    conn.close()


# Geçmişi görüntüleme
def view_history():
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history ORDER BY timestamp DESC")
    records = cursor.fetchall()
    conn.close()
    return records


# Sesli bildirim (playsound kullanılıyor)
def play_sound():
    if app.sound_enabled:
        playsound('D:/calismalar/Python/chatapp/complete.wav')  # Ses dosyasını buraya ekleyin


# Tkinter arayüzü
class TherapyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Göğüs Terapi Cihazı")
        self.current_frame = None
        self.therapy_type = tk.StringVar()
        self.mode = tk.StringVar()
        self.duration = tk.IntVar(value=1)
        self.running = False
        self.timer_thread = None
        self.sound_enabled = True  # Varsayılan olarak sesi aç
        initialize_database()
        self.show_welcome_screen()

    def switch_frame(self, frame_class):
        # Eğer mevcut bir sayfa varsa, onu yok et
        if self.current_frame:
            self.current_frame.destroy()
        # Yeni sayfayı oluştur
        self.current_frame = frame_class(self)
        self.current_frame.pack(fill="both", expand=True)

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
        for elapsed in range(1, duration + 1):
            if not self.running:
                break
            time.sleep(1)
            progress = int((elapsed / duration) * 100)
            self.current_frame.update_timer(duration - elapsed, progress)
        if self.running:
            self.current_frame.update_timer(0, 100)
            log_therapy(self.therapy_type.get(), self.mode.get(), self.duration.get(), "Tamamlandı")
            play_sound()  # Sesi oynat
            messagebox.showinfo("Terapi Tamamlandı", "Terapi tamamlandı!")
            self.show_therapy_selection_screen()

    def stop_timer(self):
        self.running = False
        log_therapy(self.therapy_type.get(), self.mode.get(), self.duration.get(), "Durduruldu")

    def finish_therapy(self):
        self.running = False
        self.show_therapy_selection_screen()


class WelcomeScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack()
        tk.Label(self, text="Göğüs Terapi Cihazı'na Hoş Geldiniz", font=("Arial", 16)).pack(pady=20)
        tk.Button(self, text="Başla", command=master.show_therapy_selection_screen).pack(pady=10)
        tk.Button(self, text="Geçmiş", command=master.show_history_screen).pack(pady=10)
        tk.Button(self, text="Ayarlar", command=master.show_settings_screen).pack(pady=10)


class TherapySelectionScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.pack()
        tk.Label(self, text="Terapi Türü Seçin").pack()
        ttk.Combobox(self, textvariable=master.therapy_type,
                     values=["Kol Terapisi", "Göğüs Terapisi", "Bacak Terapisi"]).pack(pady=10)
        tk.Label(self, text="Mod Seçin").pack()
        ttk.Combobox(self, textvariable=master.mode, values=["Hafif", "Orta", "Yoğun"]).pack(pady=10)
        tk.Button(self, text="Devam Et", command=master.show_therapy_control_screen).pack(pady=20)


class TherapyControlScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.pack()
        tk.Label(self, text="Süreyi Ayarlayın (Dakika)").pack()
        tk.Spinbox(self, from_=1, to=60, textvariable=master.duration).pack(pady=10)
        tk.Button(self, text="Başlat", command=lambda: master.start_timer(master.duration.get() * 60)).pack(pady=10)
        tk.Button(self, text="Durdur", command=master.stop_timer).pack(pady=10)
        tk.Button(self, text="Bitir", command=master.finish_therapy).pack(pady=10)
        self.timer_label = tk.Label(self, text="")
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
        self.pack()
        records = view_history()
        tk.Label(self, text="Terapi Geçmişi", font=("Arial", 16)).pack(pady=10)
        for record in records:
            tk.Label(self, text=f"{record[1]} | {record[2]} | {record[3]} dk | {record[4]}").pack()
        tk.Button(self, text="Geri Dön", command=master.show_welcome_screen).pack(pady=10)


class SettingsScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.pack()
        tk.Label(self, text="Ayarlar", font=("Arial", 16)).pack(pady=20)

        # Ses açma/kapama seçeneği
        self.sound_check = tk.Checkbutton(self, text="Sesi Aç/Kapat",
                                          variable=tk.BooleanVar(value=master.sound_enabled), command=self.toggle_sound)
        self.sound_check.pack(pady=20)

        tk.Button(self, text="Geri Dön", command=master.show_welcome_screen).pack(pady=10)

    def toggle_sound(self):
        self.master.sound_enabled = not self.master.sound_enabled


if __name__ == "__main__":
    app = TherapyApp()
    app.mainloop()
