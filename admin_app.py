"""
Royal City Admin Panel - Quan tri ho so & log
Ket noi API qua VPS
"""
import customtkinter as ctk
import requests, json, io, threading
from datetime import datetime
from tkinter import messagebox
from PIL import Image as PILImage

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

API_URL = "http://160.250.247.142/rng-api"

# Cache avatar
_avatar_cache = {}

def load_avatar(url, size=48):
    if url in _avatar_cache:
        return _avatar_cache[url]
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            img = PILImage.open(io.BytesIO(resp.content))
            img = img.resize((size, size), PILImage.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
            _avatar_cache[url] = ctk_img
            return ctk_img
    except:
        pass
    return None


class AdminApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Royal City - Admin Panel")
        self.geometry("1200x750")
        self.minsize(1000, 600)
        ctk.set_appearance_mode("dark")

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(20, 30))
        ctk.CTkLabel(logo_frame, text="🏰", font=("", 40)).pack()
        ctk.CTkLabel(logo_frame, text="ROYAL CITY", font=("", 16, "bold")).pack()
        ctk.CTkLabel(logo_frame, text="Admin Panel", font=("", 11), text_color="gray").pack()

        # Nav buttons
        self.nav_btns = {}
        nav_items = [
            ("dashboard", "📊 Dashboard"),
            ("profiles", "👤 Hồ sơ cư dân"),
            ("logs", "📋 Logs hệ thống"),
            ("config", "⚙️ Config"),
        ]
        for key, label in nav_items:
            btn = ctk.CTkButton(self.sidebar, text=label, fg_color="transparent",
                                anchor="w", font=("", 13), height=40,
                                command=lambda k=key: self.switch_tab(k))
            btn.pack(fill="x", padx=10, pady=3)
            self.nav_btns[key] = btn

        # Connection status at bottom
        self.conn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.conn_frame.pack(side="bottom", fill="x", padx=10, pady=15)
        self.conn_dot = ctk.CTkLabel(self.conn_frame, text="🟢", font=("", 12))
        self.conn_dot.pack(side="left")
        self.conn_label = ctk.CTkLabel(self.conn_frame, text="VPS Online", font=("", 11), text_color="gray")
        self.conn_label.pack(side="left", padx=5)

        # Main content
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Header
        header = ctk.CTkFrame(self.content, fg_color="transparent", height=40)
        header.pack(fill="x", pady=(0, 10))
        self.header_title = ctk.CTkLabel(header, text="📊 Dashboard", font=("", 20, "bold"))
        self.header_title.pack(side="left")

        self.refresh_btn = ctk.CTkButton(header, text="🔄 Làm mới", width=100, command=self.refresh_current)
        self.refresh_btn.pack(side="right")

        # Tab container
        self.tab_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.tab_frame.pack(fill="both", expand=True)

        self.current_tab = None
        self.switch_tab("dashboard")

    def api(self, path, method="GET", data=None):
        url = f"{API_URL}{path}"
        try:
            if method == "GET":
                return requests.get(url, timeout=10).json()
            elif method == "PUT":
                return requests.put(url, json=data, timeout=10).json()
            elif method == "DELETE":
                return requests.delete(url, timeout=10).json()
            elif method == "POST":
                return requests.post(url, timeout=10).json()
        except Exception as e:
            return {"error": str(e)}

    def switch_tab(self, key):
        for btn_key, btn in self.nav_btns.items():
            if btn_key == key:
                btn.configure(fg_color=("#3B8ED0", "#1F6AA5"))
            else:
                btn.configure(fg_color="transparent")

        for w in self.tab_frame.winfo_children():
            w.destroy()

        if key == "dashboard":
            self.header_title.configure(text="📊 Dashboard")
            self.build_dashboard()
        elif key == "profiles":
            self.header_title.configure(text="👤 Hồ sơ cư dân")
            self.build_profiles()
        elif key == "logs":
            self.header_title.configure(text="📋 Logs hệ thống")
            self.build_logs()
        elif key == "config":
            self.header_title.configure(text="⚙️ Config")
            self.build_config()

        self.current_tab = key

    def refresh_current(self):
        self.switch_tab(self.current_tab)

    # ==========================================
    # DASHBOARD
    # ==========================================
    def build_dashboard(self):
        data = self.api("/api/dashboard")
        if "error" in data:
            ctk.CTkLabel(self.tab_frame, text=f"❌ {data['error']}", font=("", 14), text_color="red").pack(pady=30)
            return

        # Stat cards row 1
        row1 = ctk.CTkFrame(self.tab_frame, fg_color="transparent")
        row1.pack(fill="x", padx=5, pady=(10, 5))
        cards = [
            ("👤 Hồ sơ", data["profiles"], "cư dân"),
            ("🎮 Người chơi", data["players"], "players"),
            ("💍 Đã kết hôn", data["married"], "cặp đôi"),
            ("💕 Top điểm", data["max_love"], "điểm"),
        ]
        for icon, val, label in cards:
            card = ctk.CTkFrame(row1, corner_radius=10)
            card.pack(side="left", fill="x", expand=True, padx=5)
            ctk.CTkLabel(card, text=icon, font=("", 24)).pack(pady=(10, 0))
            ctk.CTkLabel(card, text=str(val), font=("", 28, "bold")).pack()
            ctk.CTkLabel(card, text=label, font=("", 11), text_color="gray").pack(pady=(0, 10))

        # Stat cards row 2
        row2 = ctk.CTkFrame(self.tab_frame, fg_color="transparent")
        row2.pack(fill="x", padx=5, pady=5)
        cards2 = [
            ("📦 Bộ sưu tập", data["collections"], "danh hiệu"),
            ("🎲 Lượt roll", data["history"], "lượt"),
            ("💌 Confessions", data["confessions"], "tâm sự"),
            ("💾 Dung lượng DB", data["db_size_kb"], "KB"),
        ]
        for icon, val, label in cards2:
            card = ctk.CTkFrame(row2, corner_radius=10)
            card.pack(side="left", fill="x", expand=True, padx=5)
            ctk.CTkLabel(card, text=icon, font=("", 24)).pack(pady=(10, 0))
            ctk.CTkLabel(card, text=str(val), font=("", 28, "bold")).pack()
            ctk.CTkLabel(card, text=label, font=("", 11), text_color="gray").pack(pady=(0, 10))

        # Footer
        footer = ctk.CTkFrame(self.tab_frame, fg_color="transparent")
        footer.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(footer, text=f"📋 {data['log_lines']} dòng log", font=("", 11), text_color="gray").pack(side="left", padx=10)
        ctk.CTkLabel(footer, text=f"🕐 Cập nhật: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}",
                     font=("", 11), text_color="gray").pack(side="right", padx=10)

    # ==========================================
    # PROFILES
    # ==========================================
    def build_profiles(self):
        # Search bar
        search_frame = ctk.CTkFrame(self.tab_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=5, pady=5)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 Tìm ID hoặc user_id...", width=250)
        self.search_entry.pack(side="left", padx=5)
        ctk.CTkButton(search_frame, text="Tìm", width=70, command=self.search_profiles).pack(side="left", padx=5)
        ctk.CTkButton(search_frame, text="Tất cả", width=70, fg_color="gray", command=self.load_profiles).pack(side="left", padx=5)

        ctk.CTkLabel(search_frame, text="", font=("", 11)).pack(side="left", padx=20)

        self.profile_count = ctk.CTkLabel(search_frame, text="", font=("", 12), text_color="gray")
        self.profile_count.pack(side="right", padx=10)

        # Scrollable list
        self.profile_list = ctk.CTkScrollableFrame(self.tab_frame)
        self.profile_list.pack(fill="both", expand=True, padx=5, pady=5)

        self.load_profiles()

    def load_profiles(self):
        self._show_profiles("/api/profiles")

    def search_profiles(self):
        q = self.search_entry.get().strip()
        if q:
            self._show_profiles(f"/api/profiles?search={q}")
        else:
            self.load_profiles()

    def _show_profiles(self, path):
        for w in self.profile_list.winfo_children():
            w.destroy()

        rows = self.api(path)
        if "error" in rows:
            ctk.CTkLabel(self.profile_list, text=f"❌ {rows['error']}").pack(pady=20)
            return
        if not rows:
            ctk.CTkLabel(self.profile_list, text="Không tìm thấy hồ sơ nào.", font=("", 13)).pack(pady=20)
            self.profile_count.configure(text="0 hồ sơ")
            return

        self.profile_count.configure(text=f"{len(rows)} hồ sơ")

        for row in rows:
            pid = row.get("id", "?")
            uid = row.get("user_id", "?")
            gender = row.get("gender", "Bí mật 🤫")
            bday = row.get("birthday", "Chưa cập nhật")
            spouse = row.get("spouse_id")
            love = row.get("love_points", 0)
            status = row.get("status", "")
            discord = row.get("discord_user", {})

            card = ctk.CTkFrame(self.profile_list, corner_radius=8)
            card.pack(fill="x", padx=5, pady=4)

            # Left: avatar
            avatar_frame = ctk.CTkFrame(card, fg_color="transparent", width=56, height=56)
            avatar_frame.pack(side="left", padx=10, pady=8)
            avatar_frame.pack_propagate(False)

            if discord and discord.get("avatar_url"):
                avatar_img = load_avatar(discord["avatar_url"], 48)
                if avatar_img:
                    avatar_label = ctk.CTkLabel(avatar_frame, image=avatar_img, text="")
                    avatar_label.pack(expand=True)
                else:
                    ctk.CTkLabel(avatar_frame, text="👤", font=("", 24)).pack(expand=True)
            else:
                ctk.CTkLabel(avatar_frame, text="👤", font=("", 24)).pack(expand=True)

            # Middle: info
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=8)

            name = discord.get("display_name") or discord.get("username") or f"User {uid}"
            ctk.CTkLabel(info_frame, text=f"#{pid:03d} • {name}", font=("", 14, "bold")).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"ID: {uid} | {gender} | 🎂 {bday}", font=("Consolas", 11), text_color="gray").pack(anchor="w")

            # Sub info row
            sub = ctk.CTkFrame(info_frame, fg_color="transparent")
            sub.pack(anchor="w", pady=(3, 0))
            if spouse:
                ctk.CTkLabel(sub, text=f"💍 Tri kỷ: {spouse}", font=("", 10), text_color="#FF69B4").pack(side="left", padx=(0, 10))
                ctk.CTkLabel(sub, text=f"💕 {love or 0} điểm", font=("", 10), text_color="#FF69B4").pack(side="left")
            else:
                ctk.CTkLabel(sub, text="💔 Độc thân", font=("", 10), text_color="gray").pack(side="left")
            if status:
                ctk.CTkLabel(sub, text=f"  | 💬 {status[:50]}", font=("", 10), text_color="gray").pack(side="left")

            # Right: buttons
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=10, pady=8)

            ctk.CTkButton(btn_frame, text="✏️ Sửa", width=60, font=("", 11),
                          command=lambda r=row: self.edit_profile(r)).pack(side="top", pady=2)
            ctk.CTkButton(btn_frame, text="🗑️ Xóa", width=60, font=("", 11), fg_color="#C0392B",
                          command=lambda r=row: self.delete_profile(r)).pack(side="top", pady=2)

    def edit_profile(self, row):
        pid = row["id"]
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Sửa hồ sơ #{pid:03d}")
        dialog.geometry("480x450")
        dialog.grab_set()
        dialog.after(200, lambda: dialog.lift())

        # Header
        h = ctk.CTkFrame(dialog, fg_color="transparent")
        h.pack(fill="x", padx=15, pady=(15, 10))
        discord = row.get("discord_user", {})
        name = discord.get("display_name") or f"User {row.get('user_id')}"
        ctk.CTkLabel(h, text=f"✏️ #{pid:03d} • {name}", font=("", 16, "bold")).pack(side="left")
        ctk.CTkLabel(h, text=f"ID: {row.get('user_id')}", font=("", 11), text_color="gray").pack(side="right")

        # Scrollable form
        form = ctk.CTkScrollableFrame(dialog, height=300)
        form.pack(fill="both", expand=True, padx=15, pady=5)

        fields = {}
        field_defs = [
            ("⚧️ Giới tính", "gender", row.get("gender") or "Bí mật 🤫"),
            ("🎂 Ngày sinh", "birthday", row.get("birthday") or "Chưa cập nhật 📅"),
            ("💬 Status", "status", row.get("status") or "Đang tận hưởng cuộc sống ✨"),
            ("💍 Tri kỷ ID", "spouse_id", str(row["spouse_id"]) if row.get("spouse_id") else ""),
            ("💕 Điểm tri kỷ", "love_points", str(row.get("love_points") or 0)),
        ]
        for label, key, default in field_defs:
            ctk.CTkLabel(form, text=label, font=("", 12), anchor="w").pack(fill="x", pady=(8, 0))
            e = ctk.CTkEntry(form, height=32)
            e.insert(0, default)
            e.pack(fill="x", pady=2)
            fields[key] = e

        def save():
            sv = fields["spouse_id"].get().strip()
            data = {
                "gender": fields["gender"].get(),
                "birthday": fields["birthday"].get(),
                "status": fields["status"].get(),
                "spouse_id": int(sv) if sv else None,
                "love_points": int(fields["love_points"].get()),
            }
            result = self.api(f"/api/profiles/{pid}", method="PUT", data=data)
            if result.get("ok"):
                dialog.destroy()
                self.refresh_current()
                messagebox.showinfo("✅", f"Đã cập nhật hồ sơ #{pid:03d}")
            else:
                messagebox.showerror("Lỗi", str(result))

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=15)
        ctk.CTkButton(btn_row, text="💾 Lưu thay đổi", command=save, height=35).pack(side="right")
        ctk.CTkButton(btn_row, text="❌ Hủy", fg_color="gray", height=35, command=dialog.destroy).pack(side="right", padx=10)

    def delete_profile(self, row):
        pid = row["id"]
        uid = row.get("user_id")
        if messagebox.askyesno("⚠️ Xác nhận xóa", f"Xóa vĩnh viễn hồ sơ #{pid:03d}?\nUser ID: {uid}\n\nKhông thể hoàn tác!"):
            result = self.api(f"/api/profiles/{pid}", method="DELETE")
            if result.get("ok"):
                self.refresh_current()
                messagebox.showinfo("✅", f"Đã xóa hồ sơ #{pid:03d}")
            else:
                messagebox.showerror("Lỗi", str(result))

    # ==========================================
    # LOGS
    # ==========================================
    def build_logs(self):
        btn_row = ctk.CTkFrame(self.tab_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(btn_row, text="🗑️ Clear Logs", fg_color="#C0392B", width=120, command=self.clear_logs).pack(side="left", padx=5)

        self.log_text = ctk.CTkTextbox(self.tab_frame, font=("Consolas", 11))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.refresh_logs()

    def refresh_logs(self):
        self.log_text.delete("1.0", "end")
        data = self.api("/api/logs")
        if "error" in data:
            self.log_text.insert("1.0", f"❌ {data['error']}")
            return
        for line in data.get("lines", []):
            self.log_text.insert("end", line)
        self.log_text.see("end")

    def clear_logs(self):
        if messagebox.askyesno("⚠️ Xác nhận", "Xóa toàn bộ log hệ thống?"):
            self.api("/api/logs/clear", method="POST")
            self.refresh_logs()

    # ==========================================
    # CONFIG
    # ==========================================
    def build_config(self):
        btn_row = ctk.CTkFrame(self.tab_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(btn_row, text="💾 Lưu Config lên VPS", command=self.save_config).pack(side="right", padx=5)

        self.config_text = ctk.CTkTextbox(self.tab_frame, font=("Consolas", 12))
        self.config_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.load_config()

    def load_config(self):
        self.config_text.delete("1.0", "end")
        data = self.api("/api/config")
        if "error" not in data:
            self.config_text.insert("1.0", json.dumps(data, indent=2, ensure_ascii=False))
        else:
            self.config_text.insert("1.0", str(data))

    def save_config(self):
        try:
            text = self.config_text.get("1.0", "end-1c")
            data = json.loads(text)
            result = self.api("/api/config", method="PUT", data=data)
            if result.get("ok"):
                messagebox.showinfo("✅", "Đã lưu config!")
            else:
                messagebox.showerror("Lỗi", str(result))
        except json.JSONDecodeError as e:
            messagebox.showerror("❌ Lỗi JSON", str(e))


if __name__ == "__main__":
    app = AdminApp()
    app.mainloop()
