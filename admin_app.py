"""
Royal City Admin Panel - Quan tri ho so & log
Ket noi API qua VPS
"""
import customtkinter as ctk
import requests, json, io, threading
from datetime import datetime
from tkinter import messagebox, filedialog
from PIL import Image, ImageDraw, ImageFont
import io as io_module

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

API_URL = "http://160.250.247.142:5555"

# Cache avatar
_avatar_cache = {}

def load_avatar(url, size=48):
    if url in _avatar_cache:
        return _avatar_cache[url]
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            img = Image.open(io_module.BytesIO(resp.content))
            img = img.resize((size, size), Image.LANCZOS)
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
        self.geometry("1280x780")
        self.minsize(1000, 600)
        ctk.set_appearance_mode("dark")

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(20, 20))
        ctk.CTkLabel(logo_frame, text="🏰", font=("", 40)).pack()
        ctk.CTkLabel(logo_frame, text="ROYAL CITY", font=("", 16, "bold")).pack()
        ctk.CTkLabel(logo_frame, text="Admin Panel v2.0", font=("", 11), text_color="gray").pack()

        # Nav buttons
        self.nav_btns = {}
        nav_items = [
            ("dashboard", "📊 Dashboard"),
            ("profiles", "👤 Hồ sơ"),
            ("players", "🎮 Players RNG"),
            ("seasons", "🏆 Seasons"),
            ("confessions", "💌 Confessions"),
            ("backup", "💾 Backup"),
            ("logs", "📋 Logs"),
            ("config", "⚙️ Config"),
        ]
        for key, label in nav_items:
            btn = ctk.CTkButton(self.sidebar, text=label, fg_color="transparent",
                                anchor="w", font=("", 13), height=40,
                                command=lambda k=key: self.switch_tab(k))
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_btns[key] = btn

        # Separator
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color="gray")
        sep.pack(fill="x", padx=15, pady=10)

        # Maintenance button
        self.maintain_btn = ctk.CTkButton(self.sidebar, text="⚠️ Reset All", fg_color="#C0392B",
                                          font=("", 12), command=self.open_maintenance)
        self.maintain_btn.pack(fill="x", padx=10, pady=5)

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
                return requests.get(url, timeout=30).json()
            elif method == "PUT":
                return requests.put(url, json=data, timeout=30).json()
            elif method == "DELETE":
                return requests.delete(url, timeout=30).json()
            elif method == "POST":
                return requests.post(url, json=data, timeout=30).json()
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

        tab_map = {
            "dashboard": ("📊 Dashboard", self.build_dashboard),
            "profiles": ("👤 Hồ sơ cư dân", self.build_profiles),
            "players": ("🎮 Players RNG", self.build_players),
            "seasons": ("🏆 Seasons", self.build_seasons),
            "confessions": ("💌 Confessions", self.build_confessions),
            "backup": ("💾 Backup & Restore", self.build_backup),
            "logs": ("📋 Logs hệ thống", self.build_logs),
            "config": ("⚙️ Config", self.build_config),
        }
        title, builder = tab_map[key]
        self.header_title.configure(text=title)
        builder()
        self.current_tab = key

    def refresh_current(self):
        self.switch_tab(self.current_tab)

    def api_task(self, path, method="GET", data=None, callback=None):
        """Chạy API call trong thread riêng"""
        def task():
            result = self.api(path, method, data)
            if callback:
                self.after(0, callback, result)
        threading.Thread(target=task, daemon=True).start()

    # ==========================================
    # DASHBOARD
    # ==========================================
    def build_dashboard(self):
        data = self.api("/api/dashboard")
        if "error" in data:
            ctk.CTkLabel(self.tab_frame, text=f"❌ {data['error']}", font=("", 14), text_color="red").pack(pady=30)
            return

        # Main grid
        main = ctk.CTkScrollableFrame(self.tab_frame)
        main.pack(fill="both", expand=True)

        # Row 1: Stats
        row1 = ctk.CTkFrame(main, fg_color="transparent")
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

        # Row 2
        row2 = ctk.CTkFrame(main, fg_color="transparent")
        row2.pack(fill="x", padx=5, pady=5)
        cards2 = [
            ("📦 Bộ sưu tập", data["collections"], "danh hiệu"),
            ("🎲 Lượt roll", data["history"], "lượt"),
            ("💌 Confessions", data["confessions"], "tâm sự"),
            ("📋 Nhiệm vụ", data.get("missions", 0), "missions"),
        ]
        for icon, val, label in cards2:
            card = ctk.CTkFrame(row2, corner_radius=10)
            card.pack(side="left", fill="x", expand=True, padx=5)
            ctk.CTkLabel(card, text=icon, font=("", 24)).pack(pady=(10, 0))
            ctk.CTkLabel(card, text=str(val), font=("", 28, "bold")).pack()
            ctk.CTkLabel(card, text=label, font=("", 11), text_color="gray").pack(pady=(0, 10))

        # Row 3: DB + Seasons
        row3 = ctk.CTkFrame(main, fg_color="transparent")
        row3.pack(fill="x", padx=5, pady=5)
        cards3 = [
            ("💾 Dung lượng DB", f"{data['db_size_kb']} KB", ""),
            ("🏆 Seasons", data.get("seasons", 0), "mùa"),
            ("📋 Dòng log", data["log_lines"], "dòng"),
        ]
        for icon, val, label in cards3:
            card = ctk.CTkFrame(row3, corner_radius=10)
            card.pack(side="left", fill="x", expand=True, padx=5)
            ctk.CTkLabel(card, text=icon, font=("", 24)).pack(pady=(10, 0))
            ctk.CTkLabel(card, text=str(val), font=("", 28, "bold")).pack()
            ctk.CTkLabel(card, text=label, font=("", 11), text_color="gray").pack(pady=(0, 10))

        # Footer
        footer = ctk.CTkFrame(main, fg_color="transparent")
        footer.pack(fill="x", padx=5, pady=10)
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
            discord = row.get("discord", {})

            card = ctk.CTkFrame(self.profile_list, corner_radius=8)
            card.pack(fill="x", padx=5, pady=4)

            # Avatar
            avatar_frame = ctk.CTkFrame(card, fg_color="transparent", width=56, height=56)
            avatar_frame.pack(side="left", padx=10, pady=8)
            avatar_frame.pack_propagate(False)

            avatar_url = discord.get("avatar_url")
            if avatar_url:
                avatar_img = load_avatar(avatar_url)
                if avatar_img:
                    ctk.CTkLabel(avatar_frame, image=avatar_img, text="").pack(expand=True)
                else:
                    ctk.CTkLabel(avatar_frame, text="👤", font=("", 24)).pack(expand=True)
            else:
                ctk.CTkLabel(avatar_frame, text="👤", font=("", 24)).pack(expand=True)

            # Info
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=8)

            username = discord.get("username") if discord else f"User {uid}"
            ctk.CTkLabel(info_frame, text=f"#{pid:03d} • {username}", font=("", 14, "bold")).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"ID: {uid} | {gender} | 🎂 {bday}", font=("Consolas", 11), text_color="gray").pack(anchor="w")

            sub = ctk.CTkFrame(info_frame, fg_color="transparent")
            sub.pack(anchor="w", pady=(3, 0))
            if spouse:
                ctk.CTkLabel(sub, text=f"💍 Tri kỷ: {spouse}", font=("", 10), text_color="#FF69B4").pack(side="left", padx=(0, 10))
                ctk.CTkLabel(sub, text=f"💕 {love or 0} điểm", font=("", 10), text_color="#FF69B4").pack(side="left")
            else:
                ctk.CTkLabel(sub, text="💔 Độc thân", font=("", 10), text_color="gray").pack(side="left")
            if status:
                ctk.CTkLabel(sub, text=f"  | 💬 {status[:50]}", font=("", 10), text_color="gray").pack(side="left")

            # Buttons
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

        h = ctk.CTkFrame(dialog, fg_color="transparent")
        h.pack(fill="x", padx=15, pady=(15, 10))
        discord = row.get("discord_user", {}) or row.get("discord", {})
        name = discord.get("username") or f"User {row.get('user_id')}"
        ctk.CTkLabel(h, text=f"✏️ #{pid:03d} • {name}", font=("", 16, "bold")).pack(side="left")

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
    # PLAYERS (RNG)
    # ==========================================
    def build_players(self):
        # Search
        search_frame = ctk.CTkFrame(self.tab_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=5, pady=5)

        self.player_search = ctk.CTkEntry(search_frame, placeholder_text="🔍 Tìm user_id hoặc username...", width=250)
        self.player_search.pack(side="left", padx=5)
        ctk.CTkButton(search_frame, text="Tìm", width=70, command=self.search_players).pack(side="left", padx=5)
        ctk.CTkButton(search_frame, text="Tất cả", width=70, fg_color="gray", command=self.load_players).pack(side="left", padx=5)

        self.player_count = ctk.CTkLabel(search_frame, text="", font=("", 12), text_color="gray")
        self.player_count.pack(side="right", padx=10)

        # Columns header
        header_frame = ctk.CTkFrame(self.tab_frame, fg_color="transparent", height=30)
        header_frame.pack(fill="x", padx=5, pady=(0, 2))
        for col, w in [("User", 180), ("Username", 150), ("Current Role", 200), ("Highest Rank", 80), ("Luck", 60), ("Rolls", 60), ("Collection", 80), ("Action", 80)]:
            ctk.CTkLabel(header_frame, text=col, font=("", 11, "bold"), width=w).pack(side="left")

        self.player_list = ctk.CTkScrollableFrame(self.tab_frame)
        self.player_list.pack(fill="both", expand=True, padx=5, pady=5)

        self.load_players()

    def load_players(self):
        self._show_players("/api/players")

    def search_players(self):
        q = self.player_search.get().strip()
        if q:
            self._show_players(f"/api/players?search={q}")
        else:
            self.load_players()

    def _show_players(self, path):
        for w in self.player_list.winfo_children():
            w.destroy()

        data = self.api(path)
        if "error" in data:
            ctk.CTkLabel(self.player_list, text=f"❌ {data['error']}").pack(pady=20)
            return
        if not data:
            ctk.CTkLabel(self.player_list, text="Không có người chơi nào.", font=("", 13)).pack(pady=20)
            self.player_count.configure(text="0 players")
            return

        self.player_count.configure(text=f"{len(data)} players")

        for p in data:
            uid = p.get("user_id", "?")
            username = p.get("username", "Unknown")
            current_role = p.get("current_role_name", "N/A")
            highest_rank = p.get("highest_rank", 0)
            lucky = p.get("lucky", 0)
            total_rolls = p.get("total_rolls", 0)
            coll_count = p.get("collection_count", 0)
            discord = p.get("discord", {})

            card = ctk.CTkFrame(self.player_list, corner_radius=6)
            card.pack(fill="x", padx=5, pady=2)

            disp_name = discord.get("username") or username
            ctk.CTkLabel(card, text=str(uid), font=("Consolas", 11), width=180).pack(side="left", padx=5)
            ctk.CTkLabel(card, text=disp_name[:20], font=("", 11), width=150).pack(side="left")
            ctk.CTkLabel(card, text=current_role[:25], font=("", 11), width=200).pack(side="left")
            ctk.CTkLabel(card, text=f"{highest_rank}/30", font=("Consolas", 11), width=80).pack(side="left")
            ctk.CTkLabel(card, text=f"+{lucky}%", font=("Consolas", 11), width=60).pack(side="left")
            ctk.CTkLabel(card, text=str(total_rolls), font=("Consolas", 11), width=60).pack(side="left")
            ctk.CTkLabel(card, text=f"{coll_count}/30", font=("Consolas", 11), width=80).pack(side="left")

            ctk.CTkButton(card, text="🗑️", width=50, fg_color="#C0392B", font=("", 10),
                          command=lambda u=uid: self.delete_player(u)).pack(side="right", padx=5)

    def delete_player(self, user_id):
        if messagebox.askyesno("⚠️ Xác nhận", f"Xóa toàn bộ dữ liệu RNG của user {user_id}?\n(Không thể hoàn tác!)"):
            result = self.api(f"/api/players/{user_id}", method="DELETE")
            if result.get("ok"):
                self.refresh_current()
                messagebox.showinfo("✅", f"Đã xóa player {user_id}")
            else:
                messagebox.showerror("Lỗi", str(result))

    # ==========================================
    # SEASONS
    # ==========================================
    def build_seasons(self):
        data = self.api("/api/seasons")
        if "error" in data:
            ctk.CTkLabel(self.tab_frame, text=f"❌ {data['error']}", font=("", 14), text_color="red").pack(pady=30)
            return

        # Stats
        if data:
            current = data[0]
            info_frame = ctk.CTkFrame(self.tab_frame)
            info_frame.pack(fill="x", padx=5, pady=10)

            status = current.get("status", "ACTIVE")
            status_color = "#2ECC71" if status == "ACTIVE" else "#E74C3C"

            ctk.CTkLabel(info_frame, text=f"🏆 Mùa hiện tại: Season {current.get('season_number')}",
                         font=("", 18, "bold")).pack(pady=(10, 5))
            ctk.CTkLabel(info_frame, text=f"Status: {status}", font=("", 14), text_color=status_color).pack()
            ctk.CTkLabel(info_frame, text=f"Bắt đầu: {current.get('start_date', 'N/A')}", font=("", 12), text_color="gray").pack()
            ctk.CTkLabel(info_frame, text=f"Kết thúc: {current.get('end_date', 'N/A')}", font=("", 12), text_color="gray").pack()

        # Table: All seasons
        list_frame = ctk.CTkFrame(self.tab_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        header_row = ctk.CTkFrame(list_frame, fg_color="transparent")
        header_row.pack(fill="x", padx=5, pady=5)
        for col, w in [("#", 60), ("Season", 100), ("Start", 200), ("End", 200), ("Status", 100)]:
            ctk.CTkLabel(header_row, text=col, font=("", 11, "bold"), width=w).pack(side="left")

        scroll = ctk.CTkScrollableFrame(list_frame)
        scroll.pack(fill="both", expand=True)

        for i, s in enumerate(data, 1):
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=2)
            st = s.get("status", "?")
            sc = "#2ECC71" if st == "ACTIVE" else "#7F8C8D"
            ctk.CTkLabel(row, text=str(i), font=("Consolas", 11), width=60).pack(side="left")
            ctk.CTkLabel(row, text=f"Season {s.get('season_number')}", font=("", 11), width=100).pack(side="left")
            ctk.CTkLabel(row, text=s.get("start_date", "N/A")[:19], font=("", 11), width=200).pack(side="left")
            ctk.CTkLabel(row, text=s.get("end_date", "N/A")[:19], font=("", 11), width=200).pack(side="left")
            ctk.CTkLabel(row, text=st, font=("", 11), text_color=sc, width=100).pack(side="left")

    # ==========================================
    # CONFESSIONS
    # ==========================================
    def build_confessions(self):
        # Controls
        ctrl = ctk.CTkFrame(self.tab_frame, fg_color="transparent")
        ctrl.pack(fill="x", padx=5, pady=5)

        self.conf_limit = ctk.CTkEntry(ctrl, placeholder_text="Số lượng (mặc định 50)", width=120)
        self.conf_limit.insert(0, "50")
        self.conf_limit.pack(side="left", padx=5)
        ctk.CTkButton(ctrl, text="Tải", width=70, command=self.load_confessions).pack(side="left", padx=5)

        self.conf_count = ctk.CTkLabel(ctrl, text="", font=("", 12), text_color="gray")
        self.conf_count.pack(side="right", padx=10)

        # List
        self.conf_list = ctk.CTkScrollableFrame(self.tab_frame)
        self.conf_list.pack(fill="both", expand=True, padx=5, pady=5)

        self.load_confessions()

    def load_confessions(self):
        for w in self.conf_list.winfo_children():
            w.destroy()

        limit = self.conf_limit.get().strip() or "50"
        data = self.api(f"/api/confessions?limit={limit}")

        if "error" in data:
            ctk.CTkLabel(self.conf_list, text=f"❌ {data['error']}").pack(pady=20)
            return
        if not data:
            ctk.CTkLabel(self.conf_list, text="Chưa có confession nào.", font=("", 13)).pack(pady=20)
            self.conf_count.configure(text="0")
            return

        self.conf_count.configure(text=f"{len(data)} confessions")

        for c in data:
            cid = c.get("id")
            uid = c.get("user_id")
            content = c.get("content", "")
            created = c.get("created_at", "N/A")[:16]
            discord = c.get("discord", {})
            username = discord.get("username") if discord else f"User {uid}"

            card = ctk.CTkFrame(self.conf_list, corner_radius=6)
            card.pack(fill="x", padx=5, pady=3)

            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=(8, 2))
            ctk.CTkLabel(header, text=f"#{cid} • {username} ({uid})", font=("", 12, "bold")).pack(side="left")
            ctk.CTkLabel(header, text=created, font=("", 10), text_color="gray").pack(side="right")

            preview = content[:200] + ("..." if len(content) > 200 else "")
            ctk.CTkLabel(card, text=preview, font=("", 11), wraplength=700, justify="left",
                         fg_color="#1E1E1E", corner_radius=4).pack(fill="x", padx=10, pady=5)

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=(0, 8))
            ctk.CTkButton(btn_frame, text="🗑️ Xóa", width=70, fg_color="#C0392B", font=("", 10),
                          command=lambda cid=cid: self.delete_confession(cid)).pack(side="right")

    def delete_confession(self, cid):
        if messagebox.askyesno("⚠️ Xác nhận", f"Xóa confession #{cid}?"):
            result = self.api(f"/api/confessions/{cid}", method="DELETE")
            if result.get("ok"):
                self.load_confessions()
                messagebox.showinfo("✅", f"Đã xóa confession #{cid}")

    # ==========================================
    # BACKUP & RESTORE
    # ==========================================
    def build_backup(self):
        # Actions
        action_frame = ctk.CTkFrame(self.tab_frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=5, pady=10)

        ctk.CTkButton(action_frame, text="💾 Tạo Backup mới", font=("", 13), height=40,
                      command=self.create_backup).pack(side="left", padx=5)
        ctk.CTkLabel(action_frame, text=self.get_backup_status(), font=("", 11), text_color="gray").pack(side="left", padx=20)

        # List backups
        self.backup_list = ctk.CTkScrollableFrame(self.tab_frame)
        self.backup_list.pack(fill="both", expand=True, padx=5, pady=5)

        self.refresh_backups()

    def get_backup_status(self):
        result = self.api("/api/backups")
        if "error" in result:
            return "⚠️ Lỗi kết nối"
        return f"📁 {len(result)} bản backup"

    def refresh_backups(self):
        for w in self.backup_list.winfo_children():
            w.destroy()

        data = self.api("/api/backups")
        if "error" in data:
            ctk.CTkLabel(self.backup_list, text=f"❌ {data['error']}").pack(pady=20)
            return
        if not data:
            ctk.CTkLabel(self.backup_list, text="Chưa có bản backup nào.", font=("", 13)).pack(pady=20)
            return

        for b in data:
            fname = b["filename"]
            size = b["size_kb"]
            created = b.get("created", "")

            card = ctk.CTkFrame(self.backup_list, corner_radius=6)
            card.pack(fill="x", padx=5, pady=3)

            ctk.CTkLabel(card, text=f"📄 {fname}", font=("", 12, "bold")).pack(side="left", padx=10)
            ctk.CTkLabel(card, text=f"{size} KB", font=("", 11), text_color="gray", width=80).pack(side="left")

            btn_f = ctk.CTkFrame(card, fg_color="transparent")
            btn_f.pack(side="right", padx=5)

            ctk.CTkButton(btn_f, text="🔄 Restore", width=80, font=("", 10),
                          command=lambda f=fname: self.restore_backup(f)).pack(side="left", padx=2)
            ctk.CTkButton(btn_f, text="🗑️ Xóa", width=60, font=("", 10), fg_color="#C0392B",
                          command=lambda f=fname: self.delete_backup(f)).pack(side="left", padx=2)

    def create_backup(self):
        result = self.api("/api/backup", method="POST")
        if result.get("ok"):
            self.refresh_backups()
            messagebox.showinfo("✅", f"Backup thành công: {result['filename']}")
        else:
            messagebox.showerror("Lỗi", str(result))

    def restore_backup(self, filename):
        if messagebox.askyesno("⚠️ Xác nhận Restore",
                               f"Khôi phục database từ:\n{filename}\n\n"
                               "Bot sẽ cần được reload config sau khi restore!\n\nTiếp tục?"):
            result = self.api(f"/api/restore/{filename}", method="POST")
            if result.get("ok"):
                messagebox.showinfo("✅", f"Đã restore từ {filename}\nVui lòng reload config!")
            else:
                messagebox.showerror("Lỗi", str(result))

    def delete_backup(self, filename):
        if messagebox.askyesno("⚠️ Xác nhận", f"Xóa backup {filename}?"):
            result = self.api(f"/api/backups/{filename}", method="DELETE")
            if result.get("ok"):
                self.refresh_backups()
                messagebox.showinfo("✅", "Đã xóa backup")

    # ==========================================
    # MAINTENANCE (Reset All window)
    # ==========================================
    def open_maintenance(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("⚠️ Maintenance - Reset Dữ Liệu")
        dialog.geometry("500x400")
        dialog.grab_set()
        dialog.after(200, lambda: dialog.lift())

        ctk.CTkLabel(dialog, text="⚠️ CẢNH BÁO: CÁC HÀNH ĐỘNG NÀY KHÔNG THỂ HOÀN TÁC",
                     font=("", 14, "bold"), text_color="#E74C3C").pack(pady=(20, 10))

        # Backup first
        backup_frame = ctk.CTkFrame(dialog)
        backup_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(backup_frame, text="Bước 1: Tạo backup trước khi reset", font=("", 12)).pack(anchor="w", pady=5)
        ctk.CTkButton(backup_frame, text="💾 Tạo Backup Ngay", command=lambda: self.backup_before_reset(dialog)).pack()

        ctk.CTkLabel(dialog, text="─── hoặc ───", font=("", 12), text_color="gray").pack(pady=5)

        # Reset buttons
        btn_f = ctk.CTkFrame(dialog)
        btn_f.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(btn_f, text="🗑️ Reset Players (giữ seasons)", fg_color="#E67E22", font=("", 12), height=40,
                      command=lambda: self.confirm_reset(dialog, "players_only")).pack(fill="x", pady=5)
        ctk.CTkButton(btn_f, text="⚠️ Reset ALL (xóa hết)", fg_color="#C0392B", font=("", 12), height=40,
                      command=lambda: self.confirm_reset(dialog, "all")).pack(fill="x", pady=5)

        ctk.CTkLabel(dialog, text="Sau khi reset, bot cần được reload config (/admin reload trước đây)",
                     font=("", 10), text_color="gray", wraplength=400).pack(pady=10)

    def backup_before_reset(self, dialog):
        result = self.api("/api/backup", method="POST")
        if result.get("ok"):
            messagebox.showinfo("✅", f"Đã tạo backup: {result['filename']}")
        else:
            messagebox.showerror("Lỗi", str(result))

    def confirm_reset(self, dialog, mode):
        if mode == "players_only":
            msg = "Xóa toàn bộ dữ liệu người chơi RNG?\n(players, collections, history, missions)\nGiữ lại seasons."
            endpoint = "/api/reset_player_all"
        else:
            msg = "⚠️ XÓA TẤT CẢ?\n(players, collections, history, missions, seasons)\nKHÔNG THỂ HOÀN TÁC!"
            endpoint = "/api/reset_all"

        if messagebox.askyesno("⚠️ Xác nhận cuối cùng", msg + "\n\nChắc chắn?", icon="warning"):
            result = self.api(endpoint, method="POST")
            if result.get("ok"):
                dialog.destroy()
                messagebox.showinfo("✅", result.get("message", "Đã reset thành công!"))
            else:
                messagebox.showerror("Lỗi", str(result))

    # ==========================================
    # LOGS
    # ==========================================
    def build_logs(self):
        btn_row = ctk.CTkFrame(self.tab_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(btn_row, text="🗑️ Clear Logs", fg_color="#C0392B", width=120, command=self.clear_logs).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="🔄 Refresh", width=100, command=self.refresh_logs).pack(side="left", padx=5)

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
        ctk.CTkButton(btn_row, text="🔄 Reload từ VPS", command=self.load_config, fg_color="gray").pack(side="right", padx=5)

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
