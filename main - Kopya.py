import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
import threading
import time

# Merkezi Ayarlar (Font ve Renkler)
config = {
    "font": ("Montserrat", 12),
    "title_font": ("Montserrat", 16),
    "bg_color": "#0078D7",
    "button_color": "#004080",
    "text_color": "#FFFFFF",
}


# ---------------------------- VERİTABANI İŞLEMLERİ ----------------------------

def initialize_database():
    """
    Uygulama ilk çalıştığında veritabanını (SQLite) başlatır.
    'therapy_history.db' adında bir dosya oluşturur ve
    'history' ile 'users' tablolarını oluşturur.
    """
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()

    # Terapi geçmişi tablosu
    cursor.execute("""CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        therapy_type TEXT,
                        mode TEXT,
                        duration INTEGER,
                        status TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        user_id INTEGER,
                        FOREIGN KEY(user_id) REFERENCES users(id))""")

    # Kullanıcılar tablosu
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        surname TEXT,
                        serial_number TEXT,
                        password TEXT,
                        role TEXT DEFAULT 'user')""")

    # Varsayılan admin kullanıcısı ekleme (yoksa)
    admin_password = hashlib.sha256("admin".encode()).hexdigest()
    cursor.execute("""INSERT OR IGNORE INTO users (name, surname, serial_number, password, role)
                      VALUES ('Admin', 'User', 'admin', ?, 'admin')""", (admin_password,))

    conn.commit()
    conn.close()


def validate_serial_number(serial_number, password):
    """
    Girilen seri numarası ve şifrenin veritabanındaki bir kullanıcıya ait olup olmadığını kontrol eder.
    Eşleşme varsa, o kullanıcıyı (tuple) döndürür, yoksa None döndürür.
    """
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE serial_number = ?", (serial_number,))
    user = cursor.fetchone()
    conn.close()

    if user:
        stored_password = user[4]
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if stored_password == hashed_password:
            return user
    return None


def register_user(name, surname, serial_number, password, role="user"):
    """
    Yeni kullanıcı kayıt fonksiyonu.
    Şifre, SHA-256 ile kriptolanarak saklanır.
    """
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("""INSERT INTO users (name, surname, serial_number, password, role)
                      VALUES (?, ?, ?, ?, ?)""",
                   (name, surname, serial_number, hashed_password, role))
    conn.commit()
    conn.close()


def log_therapy(therapy_type, duration, status, user_id):
    """
    Terapi tamamlandığında (veya durdurulduğunda) history tablosuna kayıt ekler.
    Mode: Manual (sabit)
    """
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO history (therapy_type, mode, duration, status, user_id)
                      VALUES (?, ?, ?, ?, ?)""",
                   (therapy_type, "Manual", duration, status, user_id))
    conn.commit()
    conn.close()


def fetch_all_users():
    """
    Tüm kullanıcıları döndürür: [(id, name, surname, serial_number, role), ...]
    """
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, surname, serial_number, role FROM users")
    users = cursor.fetchall()
    conn.close()
    return users


def fetch_therapy_history(include_user_info=False):
    """
    Terapi geçmişini döndürür.
    include_user_info=True ise, history JOIN users sorgusu çalışır ve kullanıcı ad-soyad bilgisi de gelir.
    """
    conn = sqlite3.connect("therapy_history.db")
    cursor = conn.cursor()
    if include_user_info:
        cursor.execute("""SELECT history.id,
                                 history.therapy_type,
                                 history.mode,
                                 history.duration,
                                 history.status,
                                 history.timestamp,
                                 users.name,
                                 users.surname
                          FROM history
                          JOIN users ON history.user_id = users.id
                          ORDER BY history.timestamp DESC""")
    else:
        cursor.execute("SELECT * FROM history ORDER BY timestamp DESC")
    history = cursor.fetchall()
    conn.close()
    return history


# ---------------------------- ANA UYGULAMA SINIFI ----------------------------

class TherapyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Göğüs Terapi Cihazı")
        self.geometry("1080x1080")  # Pencere boyutu 1080 x 1080
        self.config(bg=config["bg_color"])
        self.current_frame = None
        self.user = None  # Oturum açan kullanıcının bilgisi burada tutulur

        # Veritabanı başlat
        initialize_database()

        # Giriş ekranıyla başla
        self.show_login_screen()

    def switch_frame(self, frame_class, *args):
        """
        Ekranda gösterilecek çerçeveyi (frame) değiştirir.
        *args: yeni frame'e parametre olarak geçirilebilecek veriler.
        """
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = frame_class(self, *args)
        self.current_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # --- Ekran geçişlerini sağlayan yardımcı metotlar ---

    def show_login_screen(self):
        self.switch_frame(LoginScreen)

    def show_registration_screen(self):
        self.switch_frame(RegisterScreen)

    def show_user_dashboard(self):
        self.switch_frame(UserDashboard)

    def show_admin_dashboard(self):
        self.switch_frame(AdminDashboard)

    def show_therapy_selection(self):
        self.switch_frame(TherapySelectionScreen)

    def show_therapy_control(self, therapy_type):
        self.switch_frame(TherapyControlScreen, therapy_type)

    def show_history_screen(self, admin_view=False):
        self.switch_frame(HistoryScreen, admin_view)

    def show_all_users_screen(self):
        self.switch_frame(UsersListScreen)


# ---------------------------- EKRANLAR (FRAMES) ----------------------------

class LoginScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.config(bg=config["bg_color"])

        tk.Label(self,
                 text="Giriş Yapın",
                 font=config["title_font"],
                 bg=config["bg_color"],
                 fg=config["text_color"]).pack(pady=20)

        tk.Label(self,
                 text="Kullanıcı Adı / Seri Numarası:",
                 font=config["font"],
                 bg=config["bg_color"],
                 fg=config["text_color"]).pack()
        self.serial_entry = tk.Entry(self, font=config["font"])
        self.serial_entry.pack(pady=5)

        tk.Label(self,
                 text="Şifre:",
                 font=config["font"],
                 bg=config["bg_color"],
                 fg=config["text_color"]).pack()
        self.password_entry = tk.Entry(self, font=config["font"], show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self,
                  text="Giriş Yap",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=self.login).pack(pady=20)

        tk.Button(self,
                  text="Kayıt Ol",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=master.show_registration_screen).pack(pady=10)

    def login(self):
        """
        Giriş yap butonuna basıldığında çağrılır.
        Doğru giriş bilgisi girilmişse, ilgili role'e göre ekrana yönlendirir.
        """
        serial_number = self.serial_entry.get()
        password = self.password_entry.get()
        user = validate_serial_number(serial_number, password)

        if user:
            self.master.user = user
            # user tuple: (id, name, surname, serial_number, password, role)
            if user[5] == "admin":
                self.master.show_admin_dashboard()
            else:
                self.master.show_user_dashboard()
        else:
            messagebox.showerror("Hata", "Geçersiz giriş bilgileri!")


class RegisterScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.config(bg=config["bg_color"])

        tk.Label(self,
                 text="Kayıt Ol",
                 font=config["title_font"],
                 bg=config["bg_color"],
                 fg=config["text_color"]).pack(pady=20)

        tk.Label(self,
                 text="Ad:",
                 font=config["font"],
                 bg=config["bg_color"],
                 fg=config["text_color"]).pack()
        self.name_entry = tk.Entry(self, font=config["font"])
        self.name_entry.pack(pady=5)

        tk.Label(self,
                 text="Soyad:",
                 font=config["font"],
                 bg=config["bg_color"],
                 fg=config["text_color"]).pack()
        self.surname_entry = tk.Entry(self, font=config["font"])
        self.surname_entry.pack(pady=5)

        tk.Label(self,
                 text="Seri Numara:",
                 font=config["font"],
                 bg=config["bg_color"],
                 fg=config["text_color"]).pack()
        self.serial_entry = tk.Entry(self, font=config["font"])
        self.serial_entry.pack(pady=5)

        tk.Label(self,
                 text="Şifre:",
                 font=config["font"],
                 bg=config["bg_color"],
                 fg=config["text_color"]).pack()
        self.password_entry = tk.Entry(self, font=config["font"], show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self,
                  text="Kayıt Ol",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=self.register).pack(pady=20)

        tk.Button(self,
                  text="Geri",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=master.show_login_screen).pack(pady=10)

    def register(self):
        """
        Kayıt ol butonuna basıldığında çağrılır.
        Form alanları doluysa, yeni kullanıcı olarak veritabanına kaydeder.
        """
        name = self.name_entry.get()
        surname = self.surname_entry.get()
        serial_number = self.serial_entry.get()
        password = self.password_entry.get()

        if not name or not surname or not serial_number or not password:
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurun!")
            return

        register_user(name, surname, serial_number, password)
        messagebox.showinfo("Başarılı", "Kayıt başarılı! Giriş yapabilirsiniz.")
        self.master.show_login_screen()


class UserDashboard(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.config(bg=config["bg_color"])

        user = master.user
        # user tuple: (id, name, surname, serial_number, password, role)
        welcome_message = f"Hoşgeldiniz {user[1]} {user[2]}"
        tk.Label(self,
                 text=welcome_message,
                 font=config["title_font"],
                 bg=config["bg_color"],
                 fg=config["text_color"]).pack(pady=20)

        tk.Button(self,
                  text="Terapi Seç",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=master.show_therapy_selection).pack(pady=20)

        tk.Button(self,
                  text="Geçmişi Görüntüle",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=lambda: master.show_history_screen(admin_view=False)).pack(pady=10)

        tk.Button(self,
                  text="Çıkış",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=master.show_login_screen).pack(pady=10)


class TherapySelectionScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.config(bg=config["bg_color"])

        tk.Label(self,
                 text="Terapi Seçim Ekranı",
                 font=config["title_font"],
                 bg=config["bg_color"],
                 fg=config["text_color"]).pack(pady=20)

        tk.Button(self,
                  text="Göğüs Terapi",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=lambda: master.show_therapy_control("Göğüs Terapi")).pack(pady=10)

        tk.Button(self,
                  text="Bacak Terapi",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=lambda: master.show_therapy_control("Bacak Terapi")).pack(pady=10)

        tk.Button(self,
                  text="Kol Terapi",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=lambda: master.show_therapy_control("Kol Terapi")).pack(pady=10)

        tk.Button(self,
                  text="Geri",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=master.show_user_dashboard).pack(pady=10)


class TherapyControlScreen(tk.Frame):
    def __init__(self, master, therapy_type):
        super().__init__(master)
        self.config(bg=config["bg_color"])
        self.therapy_type = therapy_type
        self.running = False  # Terapi çalışıyor mu kontrolü

        tk.Label(self,
                 text=f"{therapy_type} Kontrol Ekranı",
                 font=config["title_font"],
                 bg=config["bg_color"],
                 fg=config["text_color"]).pack(pady=20)

        self.timer_label = tk.Label(self,
                                    text="00:00",
                                    font=config["title_font"],
                                    bg=config["bg_color"],
                                    fg=config["text_color"])
        self.timer_label.pack(pady=10)

        # Süre seçenekleri (varsayılan 10 saniye)
        self.duration_var = tk.IntVar(value=10)
        duration_options = [10, 60, 180]  # 10 saniye, 1 dakika, 3 dakika
        for option in duration_options:
            tk.Radiobutton(self,
                           text=f"{option} saniye",
                           variable=self.duration_var,
                           value=option,
                           font=config["font"],
                           bg=config["bg_color"],
                           fg=config["text_color"],
                           selectcolor=config["button_color"]).pack(pady=5)

        self.start_button = tk.Button(self,
                                      text="Başlat",
                                      font=config["font"],
                                      bg=config["button_color"],
                                      fg=config["text_color"],
                                      width=20, height=2,
                                      command=self.start_therapy)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(self,
                                     text="Durdur",
                                     font=config["font"],
                                     bg=config["button_color"],
                                     fg=config["text_color"],
                                     width=20, height=2,
                                     command=self.stop_therapy,
                                     state="disabled")
        self.stop_button.pack(pady=10)

        tk.Button(self,
                  text="Geri",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=master.show_therapy_selection).pack(pady=10)

    def start_therapy(self):
        """
        Terapiyi başlatır. Sayaç (timer) bir thread içinde geriye doğru sayar.
        """
        if not self.running:
            self.running = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.duration = self.duration_var.get()
            threading.Thread(target=self.run_timer, daemon=True).start()

    def stop_therapy(self):
        """
        Terapiyi manuel olarak durdurur ve süreyi veritabanına işler.
        """
        if self.running:
            self.running = False
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")

            # Şu ana kadar kaç saniye geçmişti?
            min_sec = self.timer_label["text"].split(":")
            elapsed_seconds = int(min_sec[0]) * 60 + int(min_sec[1])
            log_therapy(self.therapy_type, elapsed_seconds, "Tamamlandı", self.master.user[0])
            messagebox.showinfo("Tamamlandı", f"{self.therapy_type} tamamlandı.")
            self.timer_label.config(text="00:00")

    def run_timer(self):
        """
        Geriye doğru sayan zamanlayıcı. Süre bittiğinde terapi otomatik durur.
        """
        seconds = self.duration
        while self.running and seconds > 0:
            minutes, sec = divmod(seconds, 60)
            self.timer_label.config(text=f"{minutes:02}:{sec:02}")
            time.sleep(1)
            seconds -= 1

        # Süre tamamlandıysa da durdur
        if self.running:
            self.running = False
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")

            # Terapi otomatik tamamlandı, geçen süre = self.duration
            log_therapy(self.therapy_type, self.duration, "Tamamlandı", self.master.user[0])
            messagebox.showinfo("Tamamlandı", f"{self.therapy_type} süresi tamamlandı.")
            self.timer_label.config(text="00:00")


class HistoryScreen(tk.Frame):
    def __init__(self, master, admin_view):
        super().__init__(master)
        self.config(bg=config["bg_color"])

        tk.Label(self,
                 text="Terapi Geçmişi",
                 font=config["title_font"],
                 bg=config["bg_color"],
                 fg=config["text_color"]).pack(pady=20)

        # Admin için ek kolonlar: Ad, Soyad
        columns = ["therapy_type", "mode", "duration", "status", "timestamp"]
        if admin_view:
            columns.extend(["name", "surname"])

        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("therapy_type", text="Terapi Tipi")
        self.tree.heading("mode", text="Mod")
        self.tree.heading("duration", text="Süre (sn)")
        self.tree.heading("status", text="Durum")
        self.tree.heading("timestamp", text="Zaman")

        if admin_view:
            self.tree.heading("name", text="Ad")
            self.tree.heading("surname", text="Soyad")

        self.tree.pack(fill="both", expand=True, pady=10)

        # Geri butonunun admin veya kullanıcı paneline yönlendirmesi
        if admin_view:
            back_command = master.show_admin_dashboard
        else:
            back_command = master.show_user_dashboard

        tk.Button(self,
                  text="Geri",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=back_command).pack(pady=10)

        self.load_history(admin_view)

    def load_history(self, admin_view):
        """
        Terapi geçmişini tabloya yükler.
        """
        history = fetch_therapy_history(include_user_info=admin_view)
        for row in history:
            # row yapısı (admin_view=True):
            #   (id, therapy_type, mode, duration, status, timestamp, name, surname)
            # row yapısı (admin_view=False):
            #   (id, therapy_type, mode, duration, status, timestamp, user_id)
            if admin_view:
                # id'yi tabloya eklemiyoruz, o yüzden row[1:] alabiliriz.
                # row[1:] = (therapy_type, mode, duration, status, timestamp, name, surname)
                self.tree.insert("", "end", values=row[1:])
            else:
                # row[1:6] = (therapy_type, mode, duration, status, timestamp)
                self.tree.insert("", "end", values=row[1:6])


class AdminDashboard(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.config(bg=config["bg_color"])

        tk.Label(self,
                 text="Yönetici Paneli",
                 font=config["title_font"],
                 bg=config["bg_color"],
                 fg=config["text_color"]).pack(pady=20)

        tk.Button(self,
                  text="Tüm Kullanıcıları Gör",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=master.show_all_users_screen).pack(pady=10)

        tk.Button(self,
                  text="Terapi Geçmişi",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=lambda: master.show_history_screen(admin_view=True)).pack(pady=10)

        tk.Button(self,
                  text="Çıkış",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=master.show_login_screen).pack(pady=10)


class UsersListScreen(tk.Frame):
    """
    Admin'in tüm kullanıcıları görebileceği ekran.
    """

    def __init__(self, master):
        super().__init__(master)
        self.config(bg=config["bg_color"])

        tk.Label(self,
                 text="Kullanıcı Listesi",
                 font=config["title_font"],
                 bg=config["bg_color"],
                 fg=config["text_color"]).pack(pady=20)

        columns = ["id", "name", "surname", "serial_number", "role"]
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Ad")
        self.tree.heading("surname", text="Soyad")
        self.tree.heading("serial_number", text="Seri No")
        self.tree.heading("role", text="Rol")

        self.tree.pack(fill="both", expand=True, pady=10)

        tk.Button(self,
                  text="Geri",
                  font=config["font"],
                  bg=config["button_color"],
                  fg=config["text_color"],
                  width=20, height=2,
                  command=master.show_admin_dashboard).pack(pady=10)

        self.load_users()

    def load_users(self):
        """
        Veritabanındaki tüm kullanıcıları Treeview'a yükler.
        """
        users = fetch_all_users()
        for user in users:
            # user: (id, name, surname, serial_number, role)
            self.tree.insert("", "end", values=user)


# ---------------------------- UYGULAMAYI BAŞLAT ----------------------------

if __name__ == "__main__":
    app = TherapyApp()
    app.mainloop()
