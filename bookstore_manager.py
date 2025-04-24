import sqlite3  # 使用sqlite3模組


DB_NAME = "bookstore.db"  # 資料庫名稱


def connect_db() -> sqlite3.Connection:
    """建立並返回 SQLite 資料庫連線"""
    conn = sqlite3.connect(DB_NAME)  # 建立資料庫連線
    conn.row_factory = sqlite3.Row  # 使結果以類似字典的 sqlite3.Row 物件返回
    return conn


def initialize_db(conn: sqlite3.Connection) -> None:
    """建立資料表並插入初始資料"""
    with conn:
        cursor = conn.cursor()
        cursor.executescript(
            """
        CREATE TABLE IF NOT EXISTS member (
            mid TEXT PRIMARY KEY,
            mname TEXT NOT NULL,
            mphone TEXT NOT NULL,
            memail TEXT
        );
        CREATE TABLE IF NOT EXISTS book (
            bid TEXT PRIMARY KEY,
            btitle TEXT NOT NULL,
            bprice INTEGER NOT NULL,
            bstock INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sale (
            sid INTEGER PRIMARY KEY AUTOINCREMENT,
            sdate TEXT NOT NULL,
            mid TEXT NOT NULL,
            bid TEXT NOT NULL,
            sqty INTEGER NOT NULL,
            sdiscount INTEGER NOT NULL,
            stotal INTEGER NOT NULL
        );

        INSERT OR IGNORE INTO member VALUES ('M001', 'Alice', '0912-345678', 'alice@example.com');
        INSERT OR IGNORE INTO member VALUES ('M002', 'Bob', '0923-456789', 'bob@example.com');
        INSERT OR IGNORE INTO member VALUES ('M003', 'Cathy', '0934-567890', 'cathy@example.com');

        INSERT OR IGNORE INTO book VALUES ('B001', 'Python Programming', 600, 50);
        INSERT OR IGNORE INTO book VALUES ('B002', 'Data Science Basics', 800, 30);
        INSERT OR IGNORE INTO book VALUES ('B003', 'Machine Learning Guide', 1200, 20);

        INSERT OR IGNORE INTO sale (sid, sdate, mid, bid, sqty, sdiscount, stotal)
        VALUES
            (1, '2024-01-15', 'M001', 'B001', 2, 100, 1100),
            (2, '2024-01-16', 'M002', 'B002', 1, 50, 750),
            (3, '2024-01-17', 'M001', 'B003', 3, 200, 3400),
            (4, '2024-01-18', 'M003', 'B001', 1, 0, 600);
        """
        )


def print_menu() -> None:
    """顯示主選單"""
    print("***************選單***************")
    print("1. 新增銷售記錄")
    print("2. 顯示銷售報表")
    print("3. 更新銷售記錄")
    print("4. 刪除銷售記錄")
    print("5. 離開")
    print("**********************************")


def add_sale(conn: sqlite3.Connection) -> None:
    """新增銷售記錄"""
    sdate = input("請輸入銷售日期 (YYYY-MM-DD)：").strip()
    if len(sdate) != 10 or sdate.count("-") != 2:
        print("=> 錯誤：日期格式錯誤")
        return

    mid = input("請輸入會員編號：").strip()
    bid = input("請輸入書籍編號：").strip()

    while True:
        try:
            sqty = int(input("請輸入購買數量：").strip())
            if sqty <= 0:
                print("=> 錯誤：數量必須為正整數，請重新輸入")
                continue
        except ValueError:
            print("=> 錯誤：數量或折扣必須為整數，請重新輸入")
            continue
        break

    while True:
        try:
            sdiscount = int(input("請輸入折扣金額：").strip())
            if sdiscount < 0:
                print("=> 錯誤：折扣金額不能為負數，請重新輸入")
                continue
        except ValueError:
            print("=> 錯誤：數量或折扣必須為整數，請重新輸入")
            continue
        break

    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM member WHERE mid = ?", (mid,))
            member = cursor.fetchone()
            cursor.execute("SELECT * FROM book WHERE bid = ?", (bid,))
            book = cursor.fetchone()

            if not member or not book:
                print("=> 錯誤：會員編號或書籍編號無效")
                return

            if book["bstock"] >= sqty:
                stotal = book["bprice"] * sqty - sdiscount
                cursor.execute(
                    "INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) VALUES (?, ?, ?, ?, ?, ?)",
                    (sdate, mid, bid, sqty, sdiscount, stotal),
                )
                cursor.execute(
                    "UPDATE book SET bstock = bstock - ? WHERE bid = ?", (sqty, bid)
                )
                conn.commit()
                print(f"=> 銷售記錄已新增！(銷售總額: {stotal:,})")
            else:
                print(f"=> 錯誤：書籍庫存不足 (現有庫存: {book['bstock']})")
                return
    except sqlite3.Error as e:
        conn.rollback()
        print(f"=> 錯誤：{e}")


def print_sale_report(conn: sqlite3.Connection) -> None:
    """顯示銷售報表"""
    cursor = conn.cursor()
    cursor.execute(
        """
    SELECT s.sid, s.sdate, m.mname, b.btitle, b.bprice, s.sqty, s.sdiscount, s.stotal
    FROM sale s
    JOIN member m ON s.mid = m.mid
    JOIN book b ON s.bid = b.bid
    ORDER BY s.sid
    """
    )
    rows = cursor.fetchall()
    for i, row in enumerate(rows, start=1):
        print(f"\n==================== 銷售報表 ====================")
        print(f"銷售 #{i}")
        print(f"銷售編號: {row['sid']}")
        print(f"銷售日期: {row['sdate']}")
        print(f"會員姓名: {row['mname']}")
        print(f"書籍標題: {row['btitle']}")
        print("-" * 50)
        print("單價\t數量\t折扣\t小計")
        print("-" * 50)
        print(
            f"{row['bprice']:,}\t{row['sqty']}\t{row['sdiscount']:,}\t{row['stotal']:,}"
        )
        print("-" * 50)
        print(f"銷售總額: {row['stotal']:,}")
        print("=" * 50)


def update_sale(conn: sqlite3.Connection) -> None:
    """更新銷售記錄"""
    cursor = conn.cursor()
    cursor.execute(
        """
    SELECT s.sid, m.mname, s.sdate, s.bid, s.sqty
    FROM sale s JOIN member m ON s.mid = m.mid
    ORDER BY s.sid
    """
    )
    sales = cursor.fetchall()
    print("\n======== 銷售記錄列表 ========")
    for i, sale in enumerate(sales, start=1):
        print(
            f"{i}. 銷售編號: {sale['sid']} - 會員: {sale['mname']} - 日期: {sale['sdate']}"
        )
    print("================================")

    sid_input = input("請選擇要更新的銷售編號 (輸入數字或按 Enter 取消): ").strip()
    if not sid_input:
        return
    try:
        choice = int(sid_input)
        if choice < 1 or choice > len(sales):
            print("錯誤：請輸入有效的數字")
            return
    except ValueError:
        print("錯誤：請輸入有效的數字")
        return

    sale = sales[choice - 1]
    try:
        new_discount = int(input("請輸入新的折扣金額：").strip())
        if new_discount < 0:
            print("錯誤：折扣金額不能為負數")
            return
        cursor.execute("SELECT bprice FROM book WHERE bid = ?", (sale["bid"],))
        price = cursor.fetchone()["bprice"]
        new_total = price * sale["sqty"] - new_discount
        cursor.execute(
            "UPDATE sale SET sdiscount = ?, stotal = ? WHERE sid = ?",
            (new_discount, new_total, sale["sid"]),
        )
        conn.commit()
        print(f"=> 銷售編號 {sale['sid']} 已更新！(銷售總額: {new_total:,})")
    except ValueError:
        print("錯誤：請輸入有效的數字")


def delete_sale(conn: sqlite3.Connection) -> None:
    """刪除銷售記錄"""
    cursor = conn.cursor()
    cursor.execute(
        """
    SELECT s.sid, m.mname, s.sdate
    FROM sale s JOIN member m ON s.mid = m.mid
    ORDER BY s.sid
    """
    )
    sales = cursor.fetchall()
    print("\n======== 銷售記錄列表 ========")
    for i, sale in enumerate(sales, start=1):
        print(
            f"{i}. 銷售編號: {sale['sid']} - 會員: {sale['mname']} - 日期: {sale['sdate']}"
        )

    while True:
        print("================================")
        sid_input = input("請選擇要刪除的銷售編號 (輸入數字或按 Enter 取消): ").strip()
        if sid_input == "":
            return
        try:
            choice = int(sid_input)
            if choice < 1 or choice > len(sales):
                print("錯誤：請輸入有效的數字")
                continue
            sid = sales[choice - 1]["sid"]
            cursor.execute("DELETE FROM sale WHERE sid = ?", (sid,))
            conn.commit()
            print(f"=> 銷售編號 {sid} 已刪除")
            break
        except ValueError:
            print("錯誤：請輸入有效的數字")
            continue


def main() -> None:
    """主程式流程"""
    with connect_db() as conn:
        initialize_db(conn)
        while True:
            print_menu()
            choice = input("請選擇操作項目(Enter 離開)：").strip()
            if choice == "1":
                add_sale(conn)
            elif choice == "2":
                print_sale_report(conn)
            elif choice == "3":
                update_sale(conn)
            elif choice == "4":
                delete_sale(conn)
            elif choice == "5" or choice == "":
                break
            else:
                print("=> 請輸入有效的選項（1-5）")


if __name__ == "__main__":  # 避免被其他程式執行
    main()

