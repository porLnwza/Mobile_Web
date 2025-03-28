import pyodbc

# ฟังก์ชันสำหรับเชื่อมต่อกับฐานข้อมูล
def connection_database():
    try:
        conn = pyodbc.connect(
            "Driver={SQL Server};"
            "Server=GBSUPGRADE20220;"
            "Database=istockcoop;"
            "Trusted_Connection=yes;"
        )
        return conn
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

# ฟังก์ชันสำหรับเรียกใช้งานคำสั่ง SQL
def execute_data(query):
    try:
        with connection_database() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                return rows
    except Exception as e:
        print(f"Query execution failed: {e}")
        return None

# ฟังก์ชันดึงข้อมูลการสั่งซื้อทั้งหมด
def get_all_orders():
    conn = connection_database()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM tbOrderMobileSale")  # ตรวจสอบ SQL Query ว่าถูกต้อง
                rows = cursor.fetchall()

                columns = [column[0] for column in cursor.description]
                orders = []

                for row in rows:
                    order = dict(zip(columns, row))
                    orders.append({
                        'customerName': order['OrderName'],
                        'model': order['OrderMobileName'],
                        'network': order['OrderMobileGrp'],
                        'customerGroup': order['OrderPeople'],
                        'quantity': order['OrderNameMobile'],  # ตรวจสอบว่า 'OrderNameMobile' คือจำนวนสินค้าใช่หรือไม่
                        'phone': order['Orderphone']
                    })
                return orders
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
    return []

# ฟังก์ชันสำหรับการเพิ่มคำสั่งซื้อ
def add_order_to_database(customer_name, model, network, customer_group, quantity, phone):
    conn = connection_database()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(''' 
                    INSERT INTO tbOrderMobileSale 
                    (OrderName, OrderMobileName, OrderMobileGrp, OrderPeople, OrderNameMobile, Orderphone)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (customer_name, model, network, customer_group, quantity, phone))

                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding order: {e}")
            return False
    return False

# ฟังก์ชันสำหรับการอัปเดตข้อมูลการสั่งซื้อ
def update_order(order_name, model, network, customer_group, quantity, phone):
    conn = connection_database()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE tbOrderMobileSale
                    SET OrderName = ?, OrderMobileName = ?, OrderMobileGrp = ?, OrderPeople = ?, OrderNameMobile = ?, Orderphone = ?
                    WHERE OrderName = ?
                """, (order_name, model, network, customer_group, quantity, phone, order_name))  # แก้ไขตำแหน่งให้ถูกต้อง
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating order: {e}")
            return False
    return False

# ฟังก์ชันสำหรับลบข้อมูลการสั่งซื้อ
def delete_order(order_id):
    conn = connection_database()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute('DELETE FROM tbOrderMobileSale WHERE OrderID = ?', (order_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting order: {e}")
            return False
    return False

# ฟังก์ชันสำหรับการอัปเดตสถานะการสั่งซื้อ
def update_order_status(order_id, status):
    conn = connection_database()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE tbOrderMobileSale SET OrderStatus = ? WHERE OrderID = ?", (status, order_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    return False

# ฟังก์ชันสำหรับการดึงข้อมูลลูกค้าจากฐานข้อมูล
def get_customer_data():
    try:
        conn = connection_database()  # ใช้การเชื่อมต่อฐานข้อมูลจากฟังก์ชันที่คุณสร้างขึ้น
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM tbCustomer")  # หรือเปลี่ยนชื่อ table ให้เหมาะสม
                rows = cursor.fetchall()

                # ใช้ cursor.description เพื่อดึงชื่อคอลัมน์
                columns = [column[0] for column in cursor.description]
                customers = []

                for row in rows:
                    customer = dict(zip(columns, row))  # สร้าง dictionary จากชื่อคอลัมน์และข้อมูลใน row
                    customers.append(customer)
                
                return customers  # ส่งกลับข้อมูลลูกค้าในรูปแบบ list ของ dictionary
    except Exception as e:
        print(f"Error fetching customer data: {e}")
        return []
