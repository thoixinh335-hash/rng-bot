# ROYAL CITY RNG BOT - TAI LIEU TINH NANG TOAN DIEN

> **Phien ban:** 1.0.0
> **Nen tang:** discord.py >= 2.3.0, SQLite (aiosqlite)
> **Tien to mac dinh:** `!` (dung cho lenh prefix) + Slash Commands
> **Ngay cap nhat:** 09/07/2026

---

## MUC LUC

1. [Kien Truc Tong Quan](#1-kien-truc-tong-quan)
2. [Cau Hinh He Thong (config.json)](#2-cau-hinh-he-thong-configjson)
3. [Co So Du Lieu (Database)](#3-co-so-du-lieu-database)
4. [Dich Vu Lo (Services)](#4-dich-vu-lo-services)
5. [Phan He Ping (ping.py)](#5-phan-he-ping-pingpy)
6. [Phan He Quay Thuong (roll.py)](#6-phan-he-quay-thuong-rollpy)
7. [Phan He Ho So (profile.py)](#7-phan-he-ho-so-profilepy)
8. [Phan He Bo Suu Tap (collection.py)](#8-phan-he-bo-suu-tap-collectionpy)
9. [Phan He Lich Su (history.py)](#9-phan-he-lich-su-historypy)
10. [Phan He Bang Xep Hang (leaderboard.py)](#10-phan-he-bang-xep-hang-leaderboardpy)
11. [Phan He Quan Tri Vien (admin.py)](#11-phan-he-quan-tri-vien-adminpy)
12. [Phan He Nhiem Vu Hang Ngay (missions.py)](#12-phan-he-nhiem-vu-hang-ngay-missionspy)
13. [Phan He Boost Slot (boost.py)](#13-phan-he-boost-slot-boostpy)
14. [Phan He Xem Avatar (avatar.py)](#14-phan-he-xem-avatar-avatarpy)
15. [Phan He Chuong Trinh Doi Tac (partner.py)](#15-phan-he-chuong-trinh-doi-tac-partnerpy)
16. [Phan He Tien Ich (utilities.py)](#16-phan-he-tien-ich-utilitiespy)
17. [Phan He Cong Dong (community.py)](#17-phan-he-cong-dong-communitypy)
18. [Phan He Game Diep Vien Nam Vung (spyfall.py)](#18-phan-he-game-diep-vien-nam-vung-spyfallpy)
19. [Phan He Kich Chat (chat_reviver.py)](#19-phan-he-kich-chat-chat_reviverpy)
20. [Phan He Ho So Cu Dan (server_profile.py)](#20-phan-he-ho-so-cu-dan-server_profilepy)
21. [Phan He Xac Minh Thanh Vien (verification.py)](#21-phan-he-xac-minh-thanh-vien-verificationpy)
22. [Phan He Vai Tro Tu Chon (self_roles.py)](#22-phan-he-vai-tro-tu-chon-self_rolespy)
23. [Danh Sach 30 Danh Hieu RNG (roles.json)](#23-danh-sach-30-danh-hieu-rng-rolesjson)
24. [Cac Lenh Prefix (Text Commands)](#24-cac-lenh-prefix-text-commands)

---

## 1. KIEN TRUC TONG QUAN

Bot duoc xay dung bang Python voi kien truc module hoa theo mo hinh **Cog + Service + Database**.

### File chinh (`main.py`)

- `RNGBot` ke thua `commands.Bot` voi tien to lenh la `!` (dung `when_mentioned_or("!")`)
- **Intents bat buoc:** `members`, `message_content`, `guilds`, `guild_messages`
- **18 Cog** duoc nap dong trong `setup_hook()`:
  - `cogs.ping`, `cogs.roll`, `cogs.profile`, `cogs.collection`, `cogs.history`, `cogs.leaderboard`, `cogs.admin`, `cogs.missions`, `cogs.boost`, `cogs.avatar`, `cogs.partner`, `cogs.utilities`, `cogs.community`, `cogs.spyfall`, `cogs.chat_reviver`, `cogs.server_profile`, `cogs.verification`, `cogs.self_roles`
- **9 Dich vu loi (Services):** `ConfigService`, `RNGEngine`, `PlayerService`, `CooldownService`, `RoleManager`, `AnnouncementService`, `LeaderboardService`, `SeasonService`, `DatabaseManager`
- **Sync Slash Commands** chi cho Guild hien tai (khong sync toan cau)
- **Co che chong chay trung** (`bot.lock`): su dung PID de dam bao chi mot instance Bot chay
- **Logging kep:** Terminal (`stdout`) + File (`logs/latest.log`) + File rieng cho loi (`logs/errors.log`)
- **Presence:** `Watching Royal City | /help`

### Trang thai khi khoi dong

Khi `on_ready()` kich hoat:
1. Cho `wait_until_ready()` de Gateway san sang.
2. Dong bo Slash Commands cho guild.
3. Cap nhat trang thai Bot sang Online + hien thi `Watching Royal City | /help`.

### Xu ly loi

- `on_app_command_error`: Xu ly loi `MissingPermissions`, `CommandInvokeError` (bao gom interaction het han), va loi khong xac dinh.
- `on_command_error`: Bo qua `CommandNotFound` (do cac text listener nhu `!so` co the kich hoat), log cac loi khac.

### File ho tro

- `cleanup_slash_commands.py`: Script xoa sach toan bo Slash Commands (Global + Guild) - dung khi can reset lệnh.
- `read_conf.py`: Script debug doc du lieu tu database SQLite.
- `requirements.txt`: `discord.py>=2.3.0`, `python-dotenv>=1.0.0`, `aiosqlite>=0.20.0`

---

## 2. CAU HINH HE THONG (config.json)

| Tham so | Gia tri mac dinh | Mo ta |
|---------|-----------------|------|
| `version` | `"1.0.0"` | Phien ban bot |
| `admin_ids` | `[1119820359500304396, 819822563588964383]` | Danh sach ID Admin toi cao |
| `announcement_channel` | `1523335043064402094` | ID kenh thong bao Roll |
| `cooldown_hours` | `0` | Thoi gian hoi chieu (dang tat) |
| `roll_limit` | `3` | So luot roll toi da trong cua so thoi gian |
| `roll_limit_hours` | `3` | Cua so thoi gian gioi han roll (gio) |
| `season_days` | `90` | Do dai mot Mua Giai (ngay) |
| `galactic_rank` | `19` | Nguong rank de kich hoat thong bao Galactic |
| `seraph_rank` | `25` | Nguong rank de kich hoat thong bao Seraph |
| `secret_rank` | `30` | Nguong rank de kich hoat thong bao Secret |
| `boost_role_id` | `1505505891225567334` | ID Role danh cho Server Booster |
| `clear_global_commands_once` | `true` | Co tu xoa Global Commands khong |

---

## 3. CO SO DU LIEU (DATABASE)

File database: `database/rng.db` (SQLite)

### Cac bang (Tables)

| Bang | Mo ta |
|------|------|
| `players` | Thong tin nguoi choi (user_id, role hien tai, role cao nhat, lucky, tong so roll, gioi han roll...) |
| `collections` | Bo suu tap danh hieu da so huu (user_id, role_id, thoi gian dat duoc) |
| `history` | Lich su tung luot quay (user_id, role_id, thoi gian roll) |
| `seasons` | Quan ly Mua Giai (so mua, ngay bat dau, ngay ket thuc, trang thai) |
| `roll_inventory` | Kho tam thoi sau khi roll - chua chon (user_id, role_id, slot, thoi gian tao) |
| `daily_missions` | Nhiem vu hang ngay (chat_count, roll_count, voice_seconds, free_rolls) |
| `confessions` | Tin nhan confession an danh (user_id, content, created_at) |
| `royal_profiles` | Ho so cu dan (bio, gender, birthday, location, bg_url, spouse_id, marriage_date) |
| `royal_bans` | Danh sach cấm (user_id, unban_time) |
| `royal_afk` | Trang thai treo may AFK (user_id, reason, time) |
| `royal_reminders` | Nhac nho hen gio (user_id, channel_id, remind_time, content) |

### Co che Migration

- Bang `daily_missions` duoc xu ly dac biet: rename + recreate de loai bo Foreign Key vi loi tuong thich upgrade tu phien ban cu.
- Bang tu dong them cac cot moi qua `ALTER TABLE` neu chua ton tai (an toan, khong loi).

---

## 4. DICH VU LO (SERVICES)

### 4.1 ConfigService (`services/config_service.py`)

- **Singleton pattern** - duy nhat mot instance trong toan bo ung dung.
- Quan ly viec doc/ghi file `config/config.json` va `data/roles.json`.
- Cung cap cac phuong thuc:
  - `load_all()`: Nap lai toan bo cau hinh vao bo nho cache.
  - `get(key, default)`: Lay gia tri cau hinh theo key.
  - `set(key, value)`: Dat gia tri cau hinh.
  - `save()`: Luu cau hinh xuong file JSON.
  - `get_role_by_id(role_id)`: Tim role theo ID.
  - `get_roles_list()`: Lay danh sach toan bo role (da sap xep theo rank tang dan).

### 4.2 RNGEngine (`services/rng_engine.py`)

- Cong cu tinh toan xac suat quay thuong (Random Number Generator).
- **Phuong thuc chinh:**
  - `roll(lucky_multiplier)`: Quay 1 lan. Duyet tu rank cao nhat (30) xuong thap nhat (1). Cong thuc: `effective_chance = max(2, base_chance // (1 + lucky_multiplier))`. Random tu 1 den effective_chance, neu trung 1 thi chon role do. Fallback ve Common (rank 1).
  - `roll_multi(lucky_multiplier, count)`: Quay nhieu lan, dam bao khong trung lap giua cac ket qua (unique). Toi da thu `count * 10` lan de tranh vong lap vo han.

### 4.3 PlayerService (`services/player_service.py`)

- Quan ly nguoi choi trong database.
- **Phuong thuc:**
  - `get_player(user_id)`: Lay thong tin nguoi choi.
  - `create_player(user_id, username, default_role)`: Tao nguoi choi moi (mac dinh la role Common).
  - `process_roll_transaction(user_id, username, rolled_role, is_highest, next_lucky)`: Xu ly giao dich roll - cap nhat profile, them vao collection, ghi lich su (su dung SQL transaction).
  - `add_free_roll(user_id, amount)`: Cong luot roll free.

### 4.4 CooldownService (`services/cooldown_service.py`)

- Kiem tra thoi gian hoi chieu giua cac luot roll.
- `check_cooldown(last_roll_str)`: Tra ve `(co_the_roll, thoi_gian_con_lai_tinh_bang_giay)`.

### 4.5 RoleManager (`services/role_manager.py`)

- Quan ly viec gan/go Discord Roles cho nguoi choi.
- `update_discord_roles(member, new_role_id)`: Go bo TAT CA role RNG cu cua user (tru role moi) va gan role moi. Su dung bat dong bo de xu ly nhieu role cung luc.

### 4.6 AnnouncementService (`services/announcement_service.py`)

- Thong bao khi nguoi choi roll duoc danh hieu cao.
- `broadcast_roll(user, role)`: Gui thong bao den kenh `announcement_channel`.
- Co 3 muc thong bao:
  - **Rank >= Secret (30):** Thong bao `@everyone` + GIF dac biet.
  - **Rank >= Seraph (25):** Thong bao `@everyone`.
  - **Rank >= Galactic (19):** Thong bao thuong.
- Su dung embed mau sac tuong ung voi role.

### 4.7 LeaderboardService (`services/leaderboard_service.py`)

- Cung cap du lieu cho bang xep hang.
- 4 phuong thuc truy van:
  - `get_top_rarity(limit=10)`: Xep hang theo rank role cao nhat.
  - `get_top_collection(limit=10)`: Xep hang theo so luong danh hieu da suu tap.
  - `get_top_lucky(limit=10)`: Xep hang theo diem may man (lucky).
  - `get_top_rolls(limit=10)`: Xep hang theo tong so lan roll.

### 4.8 SeasonService (`services/season_service.py`)

- Quan ly Mua Giai (Season).
- `check_and_update_season()`: Kiem tra mua giai hien tai. Neu chua co -> tao Season 1. Neu da het han -> tu dong reset: danh dau `EXPIRED`, tao season moi, reset `lucky` ve 0, xoa lich su roll.
- `get_current_season_number()`: Lay so thu tu mua hien tai.
- `force_reset_season()`: Ep buoc reset mua giai (danh cho Admin).

---

## 5. PHAN HE PING (ping.py)

### Lenh Slash

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/ping` | Kiem tra do tre phan hoi cua he thong Bot (API latency) | Khong co |

- Hien thi Embed mau xanh la voi do tre API tinh bang millisecond.
- **Vi du:** `/ping` => `Pong! Do tre API hien tai: 45ms`

---

## 6. PHAN HE QUAY THUONG (roll.py)

### Lenh Slash

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/roll` | Quay toi da 3 lan va chon 1 danh hieu de nhan. Hoi chieu moi 3 gio. | `count` (int, mac dinh 1): So luot quay (1-3) |
| `/pick` | Chon 1 danh hieu tu inventory sau khi roll | `slot` (int): So slot muon chon |
| `/inventory` | Xem kho bau hien tai - cac danh hieu dang cho chon | Khong co |

### Co che hoat dong

1. **Gioi han roll:** Mac dinh 3 luot / 3 tieng. Su dung `roll_limit` va `roll_limit_hours` trong config.json. Cua so gioi han duoc reset tu dong sau khi het thoi gian.
2. **Inventory tam thoi:** Sau khi roll, cac danh hieu duoc luu vao `roll_inventory`. Het han sau 1 tieng. Nguoi choi phai chon 1 slot (bang `/pick` hoac button).
3. **Cong thuc xac suat:** Su dung `RNGEngine.roll_multi()`. Luck giup tang co hoi trung role cao.
4. **Free roll tu nhiem vu:** Neu nguoi choi co free_rolls tu nhiem vu hang ngay, duoc su dung truoc tien (khong tieu hao luot roll thuong).
5. **Boost slot:** Nguoi choi co Boost Server se duoc +1 slot vinh vien. Role boost slot duoc chon tu collection qua lenh `/equipslot`.
6. **Chon slot:** Sau khi roll, nguoi choi chon slot bang button (giao dien `RollChoiceView`) hoac lenh `/pick <so>`. Khi chon xong:
   - Role moi duoc gan vao Discord (qua `RoleManager`).
   - Neu la role cao nhat tu truoc den nay: cap nhat `highest_role_id`, `highest_role_name`, `highest_rank`.
   - Neu role co rank < `galactic_rank` (=19): Lucky tang +1%. Neu rank >= `galactic_rank`: Lucky reset ve 0%.
   - Gui thong bao qua `AnnouncementService` neu role du cao.
   - Cac role khong duoc chon se bi huy.

### Thanh phan giao dien

- `RollChoiceView`: View chua cac button tuong ung voi moi slot (toi da 5). Timeout sau 1 gio. Chi nguoi roll moi duoc chon.

### Vi du

```
/roll count:3
=> Hien thi 3 slot danh hieu de chon. Nguoi choi click hoac /pick 2 de chon slot 2.
```

---

## 7. PHAN HE HO SO (profile.py)

### Lenh Slash

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/profile` | Xem the thong tin RNG. Co the xem cua nguoi khac bang @user. | `user` (Discord.User, tuy chon): Nguoi muon xem, mac dinh la ban |

### Thong tin hien thi

- Ten nguoi choi (in hoa).
- Mua giai hien tai.
- So luot roll da dung / gioi han (trong 3 tieng).
- Danh hieu dang trang bi (Current).
- Danh hieu dinh cao nhat (Best).
- Diem may man (Luck) hien tai (+X%).
- Bo suu tap danh hieu: Thanh tien trinh 10 o (`🟩` = da mo khoa, `⬛` = chua).
- Tong so luot quay.

### Vi du

```
/profile => Xem ho so cua ban
/profile @nguoikhac => Xem ho so nguoi khac
```

---

## 8. PHAN HE BO SUU TAP (collection.py)

### Lenh Slash

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/collection` | Hien thi bo suu tap day du 30 danh hieu trong game | Khong co |

### Cach hien thi

- Hien thi toan bo 30 danh hieu, danh so `01` den `30`.
- Danh hieu da so huu: hien ten + emoji + ty le.
- Danh hieu chua so huu: hien `???`.
- Chia thanh 2 truong (field) de khong vuot gioi han ky tu Embed (15 role/truong).

---

## 9. PHAN HE LICH SU (history.py)

### Lenh Slash

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/history` | Liet ke danh sach 20 luot quay gan day nhat cua ban | Khong co |

- Hien thi su dung Discord timestamp (`<t:...:R>`) hien thi thoi gian tuong doi.
- Moi dong: so thu tu + emoji + ten role + thoi gian.

---

## 10. PHAN HE BANG XEP HANG (leaderboard.py)

### Lenh Slash (Group)

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/leaderboard rarity` | Xep hang dua tren Danh hieu hiem nhat dat duoc | Khong co |
| `/leaderboard collection` | Xep hang dua tren So luong danh hieu da suu tap | Khong co |
| `/leaderboard lucky` | Xep hang dua tren Diem so may man hien tai | Khong co |
| `/leaderboard rolls` | Xep hang dua tren Tong so lan thuc hien Roll | Khong co |

- Moi bang hien thi top 10 nguoi choi.

---

## 11. PHAN HE QUAN TRI VIEN (admin.py)

### Lenh Slash (Group `/admin`)

Tat ca lenh trong group nay deu yeu cau nguoi dung co ID nam trong `admin_ids` cua config.json.

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/admin reload` | Tai lai toan bo tep cau hinh JSON ngay lap tuc | Khong co |
| `/admin stats` | Xem bao cao hieu nang va thong so ky thuat | Khong co |
| `/admin backup` | Tao ban sao luu an toan cho co so du lieu | Khong co |
| `/admin restore` | Khoi phuc CSDL tu file backup | `filename` (string): Ten file trong thu muc assets |
| `/admin reset-player` | Xoa bo toan bo du lieu cua mot nguoi choi | `target_user` (Discord.User) |
| `/admin reset-season` | Ep buoc reset mua giai hien tai | Khong co |
| `/admin config` | Hien thi nong cac thong so config.json | Khong co |
| `/admin checkperms` | Kiem tra quyen cua bot (Manage Roles, hierarchy) | Khong co |
| `/admin resetall` | XOA TAT CA du lieu. Co nut xac nhan. | Khong co |

### Lenh rieng (ngoai group)

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/admintest` | Kiem tra bot hoat dong (chi admin ID `819822563588964383`) | Khong co |

### Chi tiet `/admin checkperms`

Kiem tra:
- Quyen co ban: `Manage Roles`, `Manage Guild`, `Kick Members`, `Ban Members`.
- Top role cua bot.
- Danh sach role RNG va vi tri cua chung.
- Canh bao neu bot khong the gan role do role position thap hon.

### Chi tiet `/admin resetall`

- Dem so dong se bi xoa trong moi bang.
- Hien thi nut **XAC NHAN XOA TAT CA** (30 giay timeout).
- Sau khi xac nhan: xoa `collections`, `history`, `roll_inventory`, `daily_missions`, `players`, `seasons`.

### Vi du

```
/admin backup
/admin checkperms
/admin reset-player @nguoichoi
```

---

## 12. PHAN HE NHIEM VU HANG NGAY (missions.py)

### Lenh Slash

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/missions` | Xem tien do nhiem vu hang ngay va luot roll free | Khong co |

### 3 Nhiem vu hang ngay

| Nhiem vu | Muc tieu | Mo ta |
|----------|----------|------|
| Chat | 30 tin nhan | Dem tin nhan gui trong server |
| Roll | 3 lan | Dem so lan su dung lenh roll |
| Voice | 30 phut (1800 giay) | Dem thoi gian o trong kenh voice |

### Co che hoat dong

- **Reset luc 0h UTC** moi ngay.
- Moi nhiem vu hoan thanh = **+1 luot roll free**.
- Free roll duoc tu dong "claim" khi nguoi choi su dung `/roll`.
- **Event Listeners:**
  - `on_message`: Dem tin nhan nguoi dung (khong dem bot, khong dem DM).
  - `on_voice_state_update`: Theo doi thoi gian voice. Ghi nhan khi vao kenh, tinh thoi gian khi chuyen kenh hoac roi kenh.

### Bonus Boost Server

- Neu nguoi choi co **Server Boost**: hien thi `+1 slot vinh vien` moi lan roll trong bang nhiem vu.

---

## 13. PHAN HE BOOST SLOT (boost.py)

### Lenh Slash

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/equipslot` | Chon 1 role tu collection de dat vao slot boost vinh vien | Khong co |

### Co che hoat dong

- Chi danh cho **Server Booster** (co role co `boost_role_id` tu config).
- Nguoi choi chon 1 role tu bo suu tap cua minh de dat vao boost slot.
- Khi roll, role trong boost slot se tu dong duoc them vao inventory (slot +1, toi da 4 slot).
- Neu bo boost, role bi khoa tam thoi nhung khong mat.

### Giao dien

- `BoostSlotView`: Hien thi button cho moi role trong collection. Role dang equip duoc danh dau mau xanh va disable.

---

## 14. PHAN HE XEM AVATAR (avatar.py)

### Lenh Slash

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/avatar` | Lay avatar cua ban hoac nguoi khac. Ho tro nhieu dinh dang. | `user` (Discord.User, tuy chon): Nguoi muon lay avatar |

### Thong tin hien thi

- Anh avatar o do phan giai 1024px.
- Links tai: 1024px, 512px, 256px.
- Loai avatar: Global Avatar / Server Avatar / Default Avatar.
- User ID.
- Neu co Server Avatar: hien thi link rieng.
- Neu co Banner: hien thi link banner.

---

## 15. PHAN HE CHUONG TRINH DOI TAC (partner.py)

### Lenh (Hybrid - ca Slash va Prefix)

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/partner` hoac `!partner` | Xem huong dan va dang ky chuong trinh Partner | Khong co |

### Co che hoat dong

#### 1. Kich hoat bang PartnerView
- Nguoi dung go `!partner` hoac `/partner`.
- Hien thi Embed thong tin chuong trinh (dieu kien, dac quyen, huong dan).
- Kem theo nut **"Mo Form Dang Ky"**.

#### 2. Form dien thong tin (PartnerForm Modal)
- **3 truong bat buoc:**
  - Bai gioi thieu + Link server (max 2000 ky tu)
  - So luong thanh vien (max 20 ky tu)
  - Dong y luat va hai long voi server (max 1000 ky tu)
- Khi submit:
  - Tu dong tao kenh rieng `partner-{ten}` trong category "Partner Tickets".
  - Phan quyen: Chi nguoi dang ky + Admin + Bot moi thay kenh.
  - Gui Embed don dang ky vao kenh ticket.
  - Ping Admin de xet duyet.
  - Tra ve nut nhay den kenh ticket.

#### 3. Xet duyet (TicketAdminView)
- **Admin** bam nut:
  - **Dong Y:** Dang bai gioi thieu cua khach len kenh `PARTNER_CHANNEL_ID`. **Tu dong cap role `PARTNER_ROLE_ID`** cho nguoi dang ky. Gui lai bai gioi thieu cua Royal City de khach dang len server ho. Cac nut bi khoa.
  - **Tu Choi:** Thong bao tu choi, khoa nut.

#### 4. Dong kenh (CloseTicketView)
- Nut **Dong Kenh**: Chi Admin duoc bam. Xoa kenh sau 5 giay.

#### 5. Persistent Views
- Tat ca views (`PartnerView`, `TicketAdminView`, `CloseTicketView`) deu co `timeout=None` de hoat dong vinh vien ngay ca khi restart bot. Duoc dang ky trong `__init__` cua Cog.

---

## 16. PHAN HE TIEN ICH (utilities.py)

### Lenh (Hybrid - ca Slash va Prefix)

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/healing` hoac `!healing` | Nhan mot loi chua lanh am ap tu Royal City | Khong co |
| `/goidem` hoac `!goidem` | Loi thi tham danh rieng cho cu dan song ve dem | Khong co |
| `/serverinfo` hoac `!serverinfo` | Xem thong tin chi tiet cua Royal City | Khong co |

### Chi tiet `/healing`

- Random 1 trong 6 cau chua lanh ngot ngao.
- Embed mau hong pastel.
- Kem thumbnail GIF bong hoa de thuong.

### Chi tiet `/goidem`

- **Chi hoat dong tu 23h den 5h sang.**
- Random 1 trong 5 cau thi tham ban dem.
- Embed mau xanh dem tham.
- Ngoai khung gio: tra ve thong bao vui ve.

### Chi tiet `/serverinfo`

- Thong tin: Ten server, chu so huu, ngay thanh lap, tong thanh vien.
- So kenh text/voice, tong role.
- Cap do Boost, tong so Boost.
- Muc do bao mat.

---

## 17. PHAN HE CONG DONG (community.py)

### Lenh Slash

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/confess` | Mo bang gui tam su an danh | Khong co |
| `/nhangui` | Gui loi nhan ngot ngao bi mat toi ai do | `user` (Member): Nguoi nhan, `message` (string): Noi dung thu, `an_danh` (bool, mac dinh False): True de an danh |
| `/view_conf` | Xem lich su confession (Chi Admin ID: 1119820359500304396) | `limit` (int, mac dinh 5): So luong confession gan nhat |

### Chi tiet `/confess`

- Hien thi nut **"Viet Loi Tam Su (An Danh)"**.
- Bam nut mo Modal `ConfessionModal` (toi da 2000 ky tu).
- Khi submit:
  - Luu vao database (bao gom `user_id` cua nguoi gui - nhung khong hien thi cong khai).
  - Gui Embed an danh len kenh `CONFESSION_CHANNEL_ID` (ID: `1523960669324574750`).

### Chi tiet `/nhangui`

- Khong the tu nhan cho chinh minh.
- Hai che do: **an danh** (an ten nguoi gui) hoac **cong khai** (hien mention).
- Gui qua DM (Direct Message). Neu nguoi nhan khoa DM, se gui cong khai ra kenh chat.
- Kem thumbnail GIF buc thu tinh yeu.

### Chi tiet `/view_conf`

- Chi Admin duoc dung (kiem tra cung ID: `1119820359500304396`).
- Hien thi `limit` confession gan nhat.
- Hien thi ca ID/mention nguoi gui (chi Admin thay).
- Ephemeral (chi nguoi goi lenh thay).

---

## 18. PHAN HE GAME DIEP VIEN NAM VUNG (spyfall.py)

### Lenh (Hybrid - ca Slash va Prefix)

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/diepvien` hoac `!diepvien` | Mo mot phong cho choi game Diep Vien Nam Vung (Spyfall) | Khong co |

### Lua choi

1. **Nguoi choi toi thieu:** 3 nguoi.
2. **12 dia diem bi mat** duoc chon ngau nhien: Tram Khong Gian, Bai Bien Royal, Rap Xiec Trung Uong, Benh Vien Tam Than, Khach San 5 Sao, Nha Hang Phap, Truong Hoc, Can Cu Quan Su, Tau Ngam Hat Nhan, San Bay Quoc Te, Dao Hoang Ky, Phim Truong Hollywood.

### Cac giai doan

#### Phong cho (`SpyfallJoinView`)
- Chu phong tao game.
- Nguoi choi bam **Tham Gia** de dang ky.
- Co the **Roi Phong**.
- Chu phong bam **Bat Dau** khi du 3 nguoi.
- Timeout 180 giay.

#### Mat thu DM
- Khi bat dau, moi nguoi choi nhan mat thu qua DM:
  - **Diep Vien (Spy):** Khong biet dia diem. Nhan danh sach goi y cac dia diem de "chem gio".
  - **Cu Dan:** Biet dia diem bi mat. Nhiem vu: hoi cac cau hoi lien quan de tim Spy.
- Neu nguoi choi khoa DM: canh bao cong khai.

#### Thao luan va To giac
- Giao dien `SpyfallGameView` co dropdown menu de chon nguoi nghi ngo.
- Moi nguoi choi chi duoc bo phieu 1 lan.
- Khi tat ca da bo phieu: tu dong cong bo ket qua.

#### Ket qua
- **Da so phieu trung Spy:** Cu dan chien thang.
- **Da so phieu khong trung (chia re hoac sai):** Spy chien thang.
- Hien thi bang tong sap phieu bau, dia diem bi mat.

---

## 19. PHAN HE KICH CHAT (chat_reviver.py)

### Event Listener

| Listener | Mo ta |
|----------|-------|
| `on_message` | Cap nhat moc thoi gian tin nhan cuoi cung khi co nguoi chat (khong phai bot) tai kenh chi dinh |

### Co che hoat dong

- **Kenh muc tieu:** ID `1503825245671395368`.
- **Thoi gian im lang:** 300 giay (5 phut).
- **Khoang quet:** 15 giay/lan (`@tasks.loop(seconds=15)`).
- Neu kenh khong co tin nhan moi trong 5 phut: bot gui 1 cau ngau nhien tu kho thoai kich chat.
- Co **6 cau thoai vui nhon**, nhu "Ua moi nguoi oi, tu dung im ang the? Dang ban tron di ngu het roi a?".
- Bot tu reset moc thoi gian sau khi gui tin nhan kich chat de tranh spam lien tuc.

### Luu y

- Chi gui 1 tin kich chat, khong spam lien tuc trong khoang thoi gian im lang keo dai (vi da reset `last_message_time`).

---

## 20. PHAN HE HO SO CU DAN (server_profile.py)

### Bang du lieu

Su dung bang `royal_profiles` trong database de quan ly ho so cu dan voi cac truong:
- ID tu tang (so ho so `#XXX`)
- Bio, gender, birthday, location, bg_url
- spouuse_id, marriage_date (hon nhan)

### Lenh Slash

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/afk` | Thiet lap trang thai treo may ban ron | `ly_do` (string, mac dinh: "Treo may khong ly do.") |
| `/nhac_nho` | Thiet lap chuong bao hen gio nhac viec | `thoi_gian` (string): VD "30s", "15m", "2h", "1d". `noi_dung` (string) |
| `/poll` | Khoi tao cuoc khao sat lay y kien bang nut bam | `cau_hoi` (string), `lua_chon_1` (string), `lua_chon_2` (string) |
| `/qrcode` | Bien link/van ban thanh ma QR Code | `link_hoac_van_ban` (string) |
| `/marry` | Cau hon mot cu dan khac de ket doi tri ky | `user` (Member) |
| `/ly_hon` | Xoa bo trang thai ket doi | Khong co |
| `/sua_hoso` | Chinh sua thong tin the cu dan | `tieu_su` (string, tuy chon), `gioi_tinh` (string, tuy chon), `ngay_sinh` (string, tuy chon), `den_tu` (string, tuy chon), `tai_anh_tu_may` (Attachment, tuy chon), `link_anh_ngoai` (string, tuy chon) |
| `/cap_hoso` | Cap so hieu ho so cho thanh vien (Chi Admin) | `user` (Member) |
| `/ban` | True xuat thanh vien pha hoai (Chi Admin) | `user` (Member), `thoi_gian_phut` (int), `xoa_tin_nhan` (Choice: 0/5/10/15/30/50), `ly_do` (string) |
| `/unban` | Go lenh cam true xuat (Chi Admin) | `user_id` (string): ID Discord |
| `/doi_so_hoso` | Hoan doi so ho so giua 2 cu dan (Chi Admin) | `nguoi_a` (Member), `nguoi_b` (Member) |
| `/reset_hoso` | Xoa trang ho so cua mot nguoi (Chi Admin) | `user` (Member) |

### Lenh Prefix (Text Commands)

| Lenh | Mo ta |
|------|-------|
| `!so` | Xem ho so cu dan (cua minh hoac nguoi khac) |
| `!so <ten>` | Tim kiem ho so theo ten nguoi dung |
| `!so <@user>` | Tim kiem ho so theo mention |
| `!so <so>` | Tim kiem ho so theo ma so (VD: `!so 9`) |
| `!vohuy` | Xem ho so cu dan co ma so #009 |

### Event Listener

| Listener | Mo ta |
|----------|-------|
| `on_message` | Kiem tra AFK: go AFK khi nguoi dung chat, canh bao khi mention nguoi dang AFK. Bat prefix `!so` va `!vohuy`. |

### Background Tasks

| Task | Tan suat | Mo ta |
|------|----------|-------|
| `check_unbans` | 1 phut | Kiem tra va tu dong unban nguoi dung khi het thoi han cấm |
| `check_reminders` | 5 giay | Kiem tra va gui thong bao nhac nho khi den thoi gian hen |

### Chi tiet cac tinh nang

#### AFK
- Khi dung `/afk`: bot gui thong bao cong khai va `ephemeral` xac nhan.
- Khi nguoi AFK chat: tu dong go AFK va gui Embed chao mung quay tro lai.
- Khi mention nguoi AFK: bot canh bao nguoi do dang treo may + hien ly do + thoi gian bat dau.

#### Nhac nho
- Ho tro cac don vi thoi gian: `s` (giay), `m` (phut), `h` (gio), `d` (ngay).
- Khi den thoi gian: bot ping nguoi dung + gui noi dung nhac viec.

#### Poll (Khao sat)
- Giao dien `PollView`: 2 nut bam "Lua chon 1" va "Lua chon 2".
- Hien thi % tung lua chon + thanh tien trinh do hoa.
- Cho phep thay doi binh chon.
- Timeout 300 giay (5 phut), sau do khoa.

#### QR Code
- Su dung API `https://api.qrserver.com` de tao anh QR.
- Ket qua duoc gui duoi dang file `royal_qrcode.png`.

#### Ket Hon / Ly Hon
- `/marry @nguoiay`: Gui loi cau hon kem nut **Dong Y** / **Tu Choi**. Chi nguoi duoc cau hon moi duoc bam.
- Sau khi dong y: cap nhat `spouse_id` cho ca hai.
- `/ly_hon`: Xoa quan he hon nhan cua ca hai ben.
- Dieu kien: Ca hai phai co ho so, chua ket hon voi ai.

#### Ban / Unban
- `/ban`: Yeu cau Admin. Co the xoa tin nhan cua nguoi bi ban (Choice 0/5/10/15/30/50). Ho tro ban co thoi han (tu dong unban) hoac ban vinh vien (thoi_gian_phut = 0).
- `/unban`: Go ban bang cach nhap ID Discord.

#### Ho so cu dan (`!so`, `!vohuy`)
- Khi go `!so`: xem ho so cua chinh minh.
- `!so <ten>`: Tim theo ten hoac display_name.
- `!so <@user>`: Tim theo mention.
- `!so <so>`: Tim theo ma so ho so.
- `!vohuy`: Xem ho so so #009 (co dinh).
- Hien thi the dinh danh Royal City: So ho so, ten, tri ky, gioi tinh, sinh nhat, dia diem, tieu su, anh nen (banner). Neu khong tu chinh banner, su dung anh thanh pho dem mac dinh.

---

## 21. PHAN HE XAC MINH THANH VIEN (verification.py)

### Lenh Slash

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/setup_verification` | Khoi tao bang nut bam xac minh tuy chinh noi dung (Chi Admin) | Khong co (mo Modal) |

### Quy trinh xac minh

#### 1. Cai dat bang xac minh
- Admin dung `/setup_verification` mo Modal `VerificationSetupModal`.
- Co the tuy chinh:
  - Tieu de bang cong khai
  - Noi dung huong dan
  - Dong chu nho chan trang
  - Ma mau Embed (Hex)
- Sau khi submit, mot Embed + nut **"Bat dau xac minh"** duoc gui ra kenh.

#### 2. Luong xac minh

**Buoc 1:** Cu dan bam nut **"Bat dau xac minh"** tu bang cong khai.
- Nhan tin nhan Ephemeral (chi minh thay) voi loi chao mung + cau hoi dau tien.

**Buoc 2:** Tra loi 3 cau hoi trac nghiem qua dropdown menu:
1. **Cau 1:** Hoi ve hanh vi bi cam o Royal City (dap an dung: C - Spam/doc hai/xuc pham)
2. **Cau 2:** Toan hoc co ban 5+3=? (dap an dung: C - Bang 8)
3. **Cau 3:** Huong dan partner (dap an dung: A - Ok)

**Buoc 3:** Ket qua:
- **Dung 3/3:** Tu dong cap `VERIFIED_ROLE_ID` (ID: `1524357636286578718`). **Tu dong tao ho so cu dan** trong `royal_profiles`. Hien thi Embed thanh cong.
- **Sai:** Hien thi Embed that bai kem nut **"Thu Lam Lai Bai Kiem Tra"** de lam lai.

#### Persistent View
- `VerificationLandingView` co `timeout=None`, duoc dang ky trong `__init__` Cog de hoat dong vinh vien.

---

## 22. PHAN HE VAI TRO TU CHON (self_roles.py)

### Lenh Slash

| Lenh | Mo ta | Tham so |
|------|-------|---------|
| `/setup_roles` | Khoi tao bang nhan danh hieu/role tu dong (Chi Admin) | Khong co |

### Bang vai tro (`SelfRolesPersistentView`)

Gom 3 menu tha xuong (Dropdown Select Menu) hoat dong vinh vien:

#### Menu 1 - Game (`GameRoleSelect`)
Chon nhieu game cung luc (multi-select):
- Khong choi game
- Valorant
- Roblox
- Lien Quan Mobile
- Minecraft
- Dau Truong Chan Ly (TFT)
- Free Fire
- CS:GO / CS2
- Game khac...

#### Menu 2 - Gioi Tinh (`GenderRoleSelect`)
Chon 1 (single select):
- He / Him
- She / Her

#### Menu 3 - Tinh Trang Moi Quan He (`StatusRoleSelect`)
Chon 1 (single select):
- Doc than
- Trong mot moi quan he
- Moi quan he phuc tap
- Lop du phong

### Co che hoat dong

- Chon lan dau de **nhan** role.
- Chon lai lan nua de **go bo** role.
- Multi-select (Game): Bat/tat nhieu role cung luc.
- Single-select (Gioi Tinh, Trang Thai): Chi giu 1 role tai mot thoi diem.
- Tat ca cac menu deu la **Persistent** (`timeout=None`), duoc dang ky lai khi bot khoi dong.

---

## 23. DANH SACH 30 DANH HIEU RNG (roles.json)

| # | Ten | Emoji | Ty le | Rank | Mau Embed |
|---|-----|-------|-------|------|-----------|
| 01 | Common | ⚪ | 1/2 | 1 | Xam (#CCCCCC) |
| 02 | Uncommon | 🟢 | 1/4 | 2 | Xanh la (#4CAF50) |
| 03 | Rare | 🔵 | 1/8 | 3 | Xanh duong (#2196F3) |
| 04 | Epic | 🟣 | 1/16 | 4 | Tim (#9C27B0) |
| 05 | Legendary | 🟡 | 1/50 | 5 | Vang (#FFEB3B) |
| 06 | Mythic | 🔴 | 1/100 | 6 | Hong (#E91E63) |
| 07 | Divine | ✨ | 1/250 | 7 | Xanh Cyan (#00BCD4) |
| 08 | Celestial | 🌌 | 1/500 | 8 | Xanh nhat (#03A9F4) |
| 09 | Cosmic | 🌠 | 1/1,000 | 9 | Xanh cham (#3F51B5) |
| 10 | Astral | 🌟 | 1/2,500 | 10 | Tim dam (#673AB7) |
| 11 | Eternal | ⏳ | 1/5,000 | 11 | Nau (#795548) |
| 12 | Transcendent | 👁️ | 1/10,000 | 12 | Xanh luc dam (#009688) |
| 13 | Infernal | 🔥 | 1/25,000 | 13 | Cam (#FF5722) |
| 14 | Frostborn | ❄️ | 1/50,000 | 14 | Xanh bang (#00E5FF) |
| 15 | Nature | 🌿 | 1/75,000 | 15 | Xanh la nhat (#8BC34A) |
| 16 | Solar | ☀️ | 1/100,000 | 16 | Cam vang (#FF9800) |
| 17 | Lunar | 🌙 | 1/150,000 | 17 | Xam xanh (#90A4AE) |
| 18 | Stellar | ☄️ | 1/250,000 | 18 | Hong dam (#FF4081) |
| 19 | Galactic | 🌀 | 1/500,000 | 19 | Tim dien (#7C4DFF) |
| 20 | Prismatic | 🌈 | 1/1,000,000 | 20 | Xanh neon (#00FF87) |
| 21 | Void | 🖤 | 1/2,500,000 | 21 | Den (#111111) |
| 22 | Abyss | 🔱 | 1/5,000,000 | 22 | Xanh bien (#0D47A1) |
| 23 | Phantom | 👻 | 1/10,000,000 | 23 | Xam bac (#B0BEC5) |
| 24 | Reaper | ☠️ | 1/25,000,000 | 24 | Xam den (#263238) |
| 25 | Seraph | 👼 | 1/50,000,000 | 25 | Vang (#FFD700) |
| 26 | Dragon | 🐉 | 1/100,000,000 | 26 | Do (#DD2C00) |
| 27 | Omniscient | 👁️‍🗨️ | 1/250,000,000 | 27 | Xanh la neon (#00E676) |
| 28 | Omega | Ω | 1/500,000,000 | 28 | Tim dien (#D500F9) |
| 29 | Genesis | 🌌 | 1/1,000,000,000 | 29 | Xanh gradient (#29B6F6) |
| 30 | Secret | 👑 | 1/5,000,000,000 | 30 | Hong deep (#FF1493) |

### He thong Rank

- **Rank 1-18:** Tang Luck +1% sau moi lan roll (khong trung Galactic+).
- **Rank 19 (Galactic) tro len:** Luck reset ve 0% sau khi roll trung.
- **Rank 19+:** Kich hoat thong bao cong khai:
  - Rank 19-24: `🌀 SUC MANH VU TRU`
  - Rank 25-29: `👼 THAN THOAI GIANG LAM` (+ @everyone)
  - Rank 30 (Secret): `👑 DANH HIEU TOI MAT` (+ @everyone + GIF)

---

## 24. CAC LENH PREFIX (TEXT COMMANDS)

Bot su dung tien to `!` va `@mention`. Day la danh sach toan bo lenh prefix duoc dang ky:

### Lenh co san (dang ky qua hybrid command)

| Lenh | Cog | Mo ta |
|------|-----|-------|
| `!ping` | ping.py | Kiem tra do tre (khong co, ping la slash-only) |
| `!roll` | roll.py | Quay thuong (khong co, roll la slash-only) |
| `!partner` | partner.py | Mo chuong trinh Doi Tac |
| `!healing` | utilities.py | Nhan loi chua lanh |
| `!goidem` | utilities.py | Loi thi tham ban dem |
| `!serverinfo` | utilities.py | Thong tin server |
| `!diepvien` | spyfall.py | Mo phong choi game Diep Vien |

### Lenh prefix lang nghe qua `on_message`

| Lenh | Cog | Mo ta |
|------|-----|-------|
| `!so` | server_profile.py | Xem ho so cu dan |
| `!so <ten>` | server_profile.py | Tim ho so theo ten |
| `!so <@user>` | server_profile.py | Tim ho so theo mention |
| `!so <so>` | server_profile.py | Tim ho so theo ma so |
| `!vohuy` | server_profile.py | Xem ho so #009 |

---

## PHU LUC: SO DO CAC THANH PHAN CHINH

```
main.py
├── ConfigService (Singleton)
│   ├── config/config.json
│   └── data/roles.json
├── DatabaseManager
│   └── database/rng.db (SQLite)
│       ├── players
│       ├── collections
│       ├── history
│       ├── seasons
│       ├── roll_inventory
│       ├── daily_missions
│       ├── confessions
│       ├── royal_profiles
│       ├── royal_bans
│       ├── royal_afk
│       └── royal_reminders
├── RNGEngine (quay thuong)
├── PlayerService (CRUD nguoi choi)
├── CooldownService (hoi chieu)
├── RoleManager (Discord Role)
├── AnnouncementService (thong bao)
├── LeaderboardService (bang xep hang)
├── SeasonService (quan ly mua giai)
└── Cogs (18 cog)
    ├── PingCog (/ping)
    ├── RollCog (/roll, /pick, /inventory)
    ├── ProfileCog (/profile)
    ├── CollectionCog (/collection)
    ├── HistoryCog (/history)
    ├── LeaderboardCog (/leaderboard rarity|collection|lucky|rolls)
    ├── AdminCog (/admin reload|stats|backup|restore|reset-player|reset-season|config|checkperms|resetall, /admintest)
    ├── MissionsCog (/missions, on_message, on_voice_state_update)
    ├── BoostCog (/equipslot)
    ├── AvatarCog (/avatar)
    ├── PartnerCog (/partner/!partner)
    ├── UtilitiesCog (/healing, /goidem, /serverinfo)
    ├── CommunityCog (/confess, /nhangui, /view_conf)
    ├── SpyfallCog (/diepvien)
    ├── ChatReviverCog (on_message, background loop)
    ├── ServerProfileCog (/afk, /nhac_nho, /poll, /qrcode, /marry, /ly_hon, /sua_hoso, /cap_hoso, /ban, /unban, /doi_so_hoso, /reset_hoso, !so, !vohuy, check_unbans, check_reminders)
    ├── VerificationCog (/setup_verification, persistent view)
    └── SelfRolesCog (/setup_roles, persistent view)
```

---

## PHU LUC: CAC ID CO DINH QUAN TRONG

| Thanh phan | ID | Mo ta |
|------------|-----|------|
| ADMIN_ID (chinh) | 1119820359500304396 | Admin toi cao |
| ADMIN_ID (test) | 819822563588964383 | Admin thu nghiem |
| ANNOUNCEMENT_CHANNEL | 1523335043064402094 | Kenh thong bao roll |
| PARTNER_CHANNEL_ID | 1504447095216803841 | Kenh dang bai Doi Tac |
| PARTNER_ROLE_ID | 1504447660130828399 | Role Doi Tac |
| BOOST_ROLE_ID | 1505505891225567334 | Role Booster |
| VERIFIED_ROLE_ID | 1524357636286578718 | Role da xac minh |
| CONFESSION_CHANNEL_ID | 1523960669324574750 | Kenh confession |
| CHAT_REVIVER_TARGET | 1503825245671395368 | Kenh kich chat tu dong |
| ADMIN_ROLE_IDS (Partner) | [1503824832075268386, 1503824851046236161] | Role xet duyet Partner |

---

*Tai lieu duoc tao du tren phan tich toan bo ma nguon Bot Discord RNG Royal City, phien ban 1.0.0.*
