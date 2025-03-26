import pyodbc

# ฟังก์ชันสำหรับเชื่อมต่อกับฐานข้อมูล
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
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            return rows
    except Exception as e:
        print(f"Query execution failed: {e}")
        return None
    


def get_all_orders():
    conn = connection_database()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tbOrderMobileSale")  # ตรวจสอบ SQL Query ว่าถูกต้อง
            rows = cursor.fetchall()
            
            # ใช้ cursor.description เพื่อดึงชื่อคอลัมน์
            columns = [column[0] for column in cursor.description]
            orders = []

            for row in rows:
                order = dict(zip(columns, row))  # สร้าง dictionary จากชื่อคอลัมน์และข้อมูลใน row
                orders.append({
                    'customerName': order['OrderName'],
                    'model': order['OrderMobileName'],
                    'network': order['OrderMobileGrp'],
                    'customerGroup': order['OrderPeople'],
                    'quantity': order['OrderNameMobile'],
                    'phone': order['Orderphone']
                })
            cursor.close()
            conn.close()
            return orders
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
    return []


# ฟังก์ชันเพิ่มคำสั่งซื้อและส่งข้อความผ่าน Line Notify
def add_order_to_database(customer_name, model, network, customer_group, quantity, phone):
    conn = connection_database()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(''' 
                INSERT INTO tbOrderMobileSale 
                (OrderName, OrderMobileName, OrderMobileGrp, OrderPeople, OrderNameMobile, Orderphone)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (customer_name, model, network, customer_group, quantity, phone))

            conn.commit()
            cursor.close()
            conn.close()

            return True
        except Exception as e:
            print(f"Error adding order: {e}")
            return False
    return False

# ฟังก์ชันสำหรับแก้ไขข้อมูลการสั่งซื้อ
def update_order(order_id, customer_name, model, network, customer_group, quantity, phone):
    conn = connection_database()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tbOrderMobileSale
                SET OrderName = ?, OrderMobileName = ?, OrderMobileGrp = ?, 
                    OrderPeople = ?, OrderNameMobile = ?, Orderphone = ?
                WHERE OrderID = ?
            ''', (customer_name, model, network, customer_group, quantity, phone, order_id))
            
            conn.commit()
            cursor.close()
            conn.close()
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
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tbOrderMobileSale WHERE OrderID = ?', (order_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting order: {e}")
            return False
    return False



# ฟังก์ชันสำหรับการอัปเดตสถานะการสั่งซื้อ (เช่น การยกเลิก)
def update_order_status(product_id, status):
    conn = connection_database()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE tbOrderMobileSale SET OrderStatus = ? WHERE OrderID = ?", (status, product_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False



# # ฟังก์ชันสำหรับการลบข้อมูลการสั่งซื้อ
# @app.route('/cancel_product', methods=['POST'])
# def cancel_product():
#     product_id = request.form.get('product_id')
#     if not product_id or not product_id.isdigit():
#         flash('ข้อมูล product_id ไม่ถูกต้อง', 'error')
#         return redirect(url_for('home'))

#     product_id = int(product_id)
#     if update_order_status(product_id, 'canceled'):
#         flash('สินค้าถูกยกเลิกแล้ว', 'success')
#     else:
#         flash('เกิดข้อผิดพลาดในการยกเลิกสินค้า', 'error')

#     return redirect(url_for('home'))
