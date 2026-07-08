import aiosqlite
import asyncio
import os

async def debug_database():
    # 1. Đường dẫn file đúng của cậu là database/rng.db
    db_path = 'database/rng.db' 
    
    if not os.path.exists(db_path):
        print(f"❌ Lỗi: Không tìm thấy file database tại: {db_path}")
        return

    print(f"✅ Đã tìm thấy file database: {db_path}")
    
    async with aiosqlite.connect(db_path) as db:
        # 2. Liệt kê tất cả các bảng có trong database để cậu chọn
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table';") as cursor:
            tables = await cursor.fetchall()
            print("\n📂 Các bảng (table) hiện có trong database:")
            for table in tables:
                print(f"   - {table[0]}")
        
        # 3. Thử đọc dữ liệu từ bảng confessions (nếu có)
        table_to_read = 'confessions'
        print(f"\n🔍 Đang thử đọc bảng '{table_to_read}'...")
        
        try:
            async with db.execute(f"SELECT * FROM {table_to_read} ORDER BY id DESC LIMIT 10") as cursor:
                rows = await cursor.fetchall()
                if not rows:
                    print("   => Bảng này trống hoặc không có dữ liệu.")
                else:
                    for row in rows:
                        print(f"   => {row}")
        except Exception as e:
            print(f"   => Không thể đọc bảng '{table_to_read}'. Có vẻ tên bảng khác? Hãy kiểm tra danh sách bảng ở trên.")

if __name__ == "__main__":
    asyncio.run(debug_database())