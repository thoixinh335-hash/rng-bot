"""
Royal City Admin Panel - Quản trị hồ sơ & log
Kết nối API qua VPS
Build .exe: pyinstaller --onefile --windowed --name "RoyalCity_Admin" admin_app.py
"""
import customtkinter as ctk
import requests
import json
from datetime import datetime
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# === CONFIG VPS ===
API_URL = "http://localhost:5555"  # Sửa thành IP VPS thật


class AdminApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Royal City - Admin Panel")
        self.geometry("1100x700")
        self.minsize(900, 600)

        # VPS Connection
        conn_frame = ctk.CTkFrame(self)
        conn_frame.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(conn_frame, text="🌐 VPS API:").pack(side="left", padx=5)
        self.vps_entry = ctk.CTkEntry(conn_frame, width=250, placeholder_text="http://VPS_IP:5555")
        self.vps_entry.insert(0, API_URL)
        self.vps_entry.pack(side="left", padx=5)
        ctk.CTkButton(conn_frame, text="🔌 Kết nối", width=80, command=self.test_connection).pack(side="left", padx=5)
        self.conn_status = ctk.CTkLabel(conn_frame, text="⚫", font=("", 16))
        self.conn_status.pack(side="left", padx=10)

        # Tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabview.add("📊 Dashboard")
        self.tabview.add("👤 Hồ sơ")
        self.tabview.add("📋 Logs")
        self.tabview.add("⚙️ Config")

        self.build_dashboard()
        self.build_profiles()
        self.build_logs()
        self.build_config()

        self.test_connection()

    def api(self, path, method="GET", data=None):
        url = f"{self.vps_entry.get().strip()}{path}"
        try:
            if method == "GET":
                return requests.get(url, timeout=5).json()
            elif method == "PUT":
                return requests.put(url, json=data, timeout=5).json()
            elif method == "DELETE":
                return requests.delete(url, timeout=5).json()
        except Exception as e:
            return {"error": str(e)}

    def test_connection(self):
        result = self.api("/")
        if result and "name" in result:
            self.conn_status.configure(text="🟢 Online", text_color="green")
            self.refresh_dashboard()
        else:
            self.conn_status.configure(text="🔴 Offline", text_color="red")

    # ==========================================
    # DASHBOARD
    # ==========================================
    def build_dashboard(self):
        tab = self.tabview.tab("📊 Dashboard")
        self.dash_frame = ctk.CTkScrollableFrame(tab)
        self.dash_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.dash_content = ctk.CTkLabel(self.dash_frame, text="", justify="left", font=("Consolas", 13))
        self.dash_content.pack(anchor="w", padx=10, pady=10)
        ctk.CTkButton(tab, text="🔄 Làm mới", command=self.refresh_dashboard).pack(pady=5)

    def refresh_dashboard(self):
        data = self.api("/api/dashboard")
        if "error" in data:
            self.dash_content.configure(text=f"❌ Không kết nối được VPS: {data['error']}")
            return
        text = f"""
╔══════════════════════════════════╗
║   🏰 ROYAL CITY ADMIN PANEL    ║
╚══════════════════════════════════╝

📊 THỐNG KÊ TỔNG QUAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  👤 Tổng hồ sơ cư dân:      {data['profiles']}
  🎮 Tổng người chơi RNG:     {data['players']}
  💍 Cặp đôi đã kết hôn:     {data['married']}
  💕 Điểm tri kỷ cao nhất:   {data['max_love']}
  📦 Tổng danh hiệu thu thập: {data['collections']}
  🎲 Tổng lượt roll:         {data['history']}
  💌 Confessions:            {data['confessions']}

💾 HỆ THỐNG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📁 Dung lượng DB:          {data['db_size_kb']:.1f} KB
  🕐 Cập nhật lúc:           {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
"""
        self.dash_content.configure(text=text)

    # ==========================================
    # PROFILES
    # ==========================================
    def build_profiles(self):
        tab = self.tabview.tab("👤 Hồ sơ")
        top = ctk.CTkFrame(tab)
        top.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(top, text="🔍 Tìm kiếm:").pack(side="left", padx=5)
        self.search_entry = ctk.CTkEntry(top, width=200, placeholder_text="ID hoặc user_id...")
        self.search_entry.pack(side="left", padx=5)
        ctk.CTkButton(top, text="Tìm", width=60, command=self.search_profiles).pack(side="left", padx=5)
        ctk.CTkButton(top, text="🔄 Tất cả", width=80, command=self.load_all_profiles).pack(side="left", padx=5)

        self.profile_list = ctk.CTkScrollableFrame(tab)
        self.profile_list.pack(fill="both", expand=True, padx=10, pady=5)
        self.load_all_profiles()

    def load_all_profiles(self):
        for w in self.profile_list.winfo_children():
            w.destroy()
        rows = self.api("/api/profiles")
        if "error" in rows:
            ctk.CTkLabel(self.profile_list, text=f"❌ Lỗi: {rows['error']}").pack(pady=20)
            return
        if not rows:
            ctk.CTkLabel(self.profile_list, text="Chưa có hồ sơ nào.").pack(pady=20)
            return
        for row in rows:
            pid = row.get("id", "?")
            uid = row.get("user_id", "?")
            gender = row.get("gender", "?")
            bday = row.get("birthday", "?")
            spouse = row.get("spouse_id")
            love = row.get("love_points", 0)
            spouse_text = f"💍 <@{spouse}>" if spouse else "💔 Độc thân"

            frame = ctk.CTkFrame(self.profile_list)
            frame.pack(fill="x", padx=5, pady=3)
            info = f"#{pid:03d} | ID:{uid} | {gender} | {bday} | {spouse_text} | 💕{love or 0}"
            ctk.CTkLabel(frame, text=info, font=("Consolas", 11)).pack(side="left", padx=10)
            ctk.CTkButton(frame, text="✏️ Sửa", width=50, font=("", 10),
                          command=lambda r=row: self.edit_profile(r)).pack(side="right", padx=3, pady=3)
            ctk.CTkButton(frame, text="🗑️", width=40, font=("", 10), fg_color="red",
                          command=lambda r=row: self.delete_profile(r)).pack(side="right", padx=3, pady=3)

    def search_profiles(self):
        query = self.search_entry.get().strip()
        if not query:
            return self.load_all_profiles()
        for w in self.profile_list.winfo_children():
            w.destroy()
        rows = self.api(f"/api/profiles?search={query}")
        if "error" in rows:
            ctk.CTkLabel(self.profile_list, text=f"❌ Lỗi: {rows['error']}").pack(pady=20)
            return
        if not rows:
            ctk.CTkLabel(self.profile_list, text=f"Không tìm thấy '{query}'").pack(pady=20)
            return
        for row in rows:
            pid = row.get("id", "?")
            uid = row.get("user_id", "?")
            gender = row.get("gender", "?")
            spouse = row.get("spouse_id")
            love = row.get("love_points", 0)
            spouse_text = f"💍 <@{spouse}>" if spouse else "💔 Độc thân"
            frame = ctk.CTkFrame(self.profile_list)
            frame.pack(fill="x", padx=5, pady=3)
            info = f"#{pid:03d} | ID:{uid} | {gender} | {spouse_text} | 💕{love or 0}"
            ctk.CTkLabel(frame, text=info, font=("Consolas", 11)).pack(side="left", padx=10)
            ctk.CTkButton(frame, text="✏️ Sửa", width=50, font=("", 10),
                          command=lambda r=row: self.edit_profile(r)).pack(side="right", padx=3, pady=3)
            ctk.CTkButton(frame, text="🗑️", width=40, font=("", 10), fg_color="red",
                          command=lambda r=row: self.delete_profile(r)).pack(side="right", padx=3, pady=3)

    def edit_profile(self, row):
        pid = row["id"]
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Sửa hồ sơ #{pid:03d}")
        dialog.geometry("450x400")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"User ID: {row['user_id']}", font=("", 12, "bold")).pack(pady=5)
        fields = {}
        labels = [
            ("Giới tính:", "gender", row.get("gender") or "Bí mật 🤫"),
            ("Ngày sinh:", "birthday", row.get("birthday") or "Chưa cập nhật 📅"),
            ("Status:", "status", row.get("status") or "Đang tận hưởng cuộc sống ✨"),
            ("Tri kỷ ID:", "spouse_id", str(row["spouse_id"]) if row.get("spouse_id") else ""),
            ("Điểm tri kỷ:", "love_points", str(row.get("love_points") or 0)),
        ]
        for label, key, default in labels:
            ctk.CTkLabel(dialog, text=label).pack()
            e = ctk.CTkEntry(dialog, width=300)
            e.insert(0, default)
            e.pack(pady=2)
            fields[key] = e

        def save():
            data = {}
            sv = fields["spouse_id"].get().strip()
            data["gender"] = fields["gender"].get()
            data["birthday"] = fields["birthday"].get()
            data["status"] = fields["status"].get()
            data["spouse_id"] = int(sv) if sv else None
            data["love_points"] = int(fields["love_points"].get())
            result = self.api(f"/api/profiles/{pid}", method="PUT", data=data)
            if result.get("ok"):
                dialog.destroy()
                self.load_all_profiles()
                messagebox.showinfo("OK", f"Đã cập nhật hồ sơ #{pid:03d}")
            else:
                messagebox.showerror("Lỗi", str(result))

        ctk.CTkButton(dialog, text="💾 Lưu", command=save).pack(pady=10)

    def delete_profile(self, row):
        pid = row["id"]
        if messagebox.askyesno("Xác nhận", f"Xóa hồ sơ #{pid:03d} (User ID: {row['user_id']})?\nHành động này không thể hoàn tác!"):
            result = self.api(f"/api/profiles/{pid}", method="DELETE")
            if result.get("ok"):
                self.load_all_profiles()
                messagebox.showinfo("OK", f"Đã xóa hồ sơ #{pid:03d}")
            else:
                messagebox.showerror("Lỗi", str(result))

    # ==========================================
    # LOGS
    # ==========================================
    def build_logs(self):
        tab = self.tabview.tab("📋 Logs")
        top = ctk.CTkFrame(tab)
        top.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(top, text="📋 Bot Logs (VPS)", font=("", 14, "bold")).pack(side="left", padx=10)
        ctk.CTkButton(top, text="🔄 Refresh", command=self.refresh_logs).pack(side="right", padx=5)

        self.log_text = ctk.CTkTextbox(tab, font=("Consolas", 11))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
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

    # ==========================================
    # CONFIG
    # ==========================================
    def build_config(self):
        tab = self.tabview.tab("⚙️ Config")
        ctk.CTkButton(tab, text="🔄 Tải Config", command=self.load_config).pack(pady=5)
        self.config_text = ctk.CTkTextbox(tab, font=("Consolas", 12), height=25)
        self.config_text.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkButton(tab, text="💾 Lưu Config lên VPS", command=self.save_config).pack(pady=5)
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
            config_data = json.loads(text)
            result = self.api("/api/config", method="PUT", data=config_data)
            if result.get("ok"):
                messagebox.showinfo("OK", "Đã lưu config!")
            else:
                messagebox.showerror("Lỗi", str(result))
        except json.JSONDecodeError as e:
            messagebox.showerror("Lỗi JSON", f"Sai định dạng JSON: {e}")


if __name__ == "__main__":
    app = AdminApp()
    app.mainloop()
