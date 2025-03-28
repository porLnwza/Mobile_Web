from flask import Flask, render_template, redirect ,url_for,request,flash
from connection import connection_database, execute_data ,add_order_to_database, get_all_orders, update_order,get_customer_data,cancel_order
import pyodbc
import requests



# กำหนดการตั้งค่า Flask
app = Flask(__name__, template_folder="template", static_folder="static")
app.secret_key = 'your_secret_key_here'  # ใช้สำหรับการแสดงผล Flash messages

# ตัวแปรจำลองฐานข้อมูลสินค้า
product = []

# ฟังก์ชันสำหรับการเชื่อมต่อฐานข้อมูล
def get_all_orders():
    try:
        conn = pyodbc.connect("DRIVER={SQL Server};SERVER=GBSUPGRADE20220;DATABASE=istockcoop;Trusted_Connection=yes")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tbOrderMobileSale")
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")
        return []
    finally:
        conn.close()

# ฟังก์ชันสำหรับค้นหาคำสั่งซื้อ
def search_orders(search_order):
    try:
        conn = pyodbc.connect("DRIVER={SQL Server};SERVER=GBSUPGRADE20220;DATABASE=istockcoop;Trusted_Connection=yes")
        cursor = conn.cursor()
        sql = """SELECT * FROM tbOrderMobileSale 
                 WHERE OrderName LIKE ? OR Orderphone LIKE ?"""
        cursor.execute(sql, ('%' + search_order + '%', '%' + search_order + '%'))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")
        return []
    finally:
        conn.close()

# ฟังก์ชันหลักที่แสดงหน้าแรก
@app.route('/', methods=['GET', 'POST'])
def home():
    search_order = request.form.get('search_order', '')  # รับค่าจากฟอร์ม
    all_orders = get_all_orders()  # เริ่มต้นโดยดึงข้อมูลทั้งหมดจากฐานข้อมูล

    if search_order:  # ถ้ามีการค้นหาคำสั่งซื้อ
        all_orders = search_orders(search_order)  # ค้นหาตามคำค้น

    # ดึงข้อมูลจากฐานข้อมูลทุกครั้งที่โหลดหน้า
    data_Customer = execute_data("SELECT * FROM tbCustomer") or []
    data_Customer_grp = execute_data("SELECT * FROM tbCustomerGrp") or []
    data_stock = execute_data("SELECT * FROM tbStock") or []
    all_orders = get_all_orders() or []  # เช็คว่า get_all_orders() ส่งข้อมูลจริงๆ
        
    select_value = ""
    selected_customer = None
    customer_real_name = ""
    selected_phone = ""
    customer_group = ""
    select_stock = ""

    # ตรวจสอบว่ามีการกดปุ่มค้นหาหรือไม่
    if "button_search" in request.form:
        select_value = request.form.get("customer_real_name", "")  # ดึงค่าจากฟอร์ม
        selected_phone = request.form.get("selected_phone", "")
        customer_group = request.form.get("customer_group", "")
        select_stock = request.form.get("select_stock", "")

    # หากเลือกชื่อลูกค้า ให้ดึงข้อมูลจากฐานข้อมูล
    if select_value:
        for row in data_Customer:
            if row[0] == select_value:
                selected_customer = row[0]  
                customer_real_name = row[3]  # สมมติว่าชื่อจริงอยู่ในคอลัมน์ที่ 3
                selected_phone = row[5]  
                customer_group = row[1]  
                select_stock = row[4]  
                break

    if request.method == 'POST':
        if 'button_add' in request.form:
            customer_name = request.form.get('customer_real_name')
            model = request.form.get('select_stock')
            network = request.form.get('network')
            customer_group = request.form.get('customer_group')
            quantity = request.form.get('quantity')
            phone = request.form.get('selected_phone')

            if not all([customer_name, model, network, customer_group, quantity, phone]):
                flash('กรุณากรอกข้อมูลให้ครบถ้วน', 'error')
                return redirect(url_for('home'))

            customer_real_name = ""
            for row in data_Customer:
                if row[0] == customer_name:
                    customer_real_name = row[3]  # สมมติว่า column ที่ 2 คือชื่อจริง
                    break

            add_order_to_database(customer_real_name, model, network, customer_group, quantity, phone)
            flash('เพิ่มข้อมูลการสั่งซื้อสำเร็จ', 'success')

            # ✅ ส่งข้อความผ่าน Line Notify
            url = "https://notify-api.line.me/api/notify"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                "Authorization": "Bearer DxjRgaf2lch2M1LwOFysWq3aLuHoKtVIaDyvOT56jbN"
            }
            message_text = (f"ร้านมือถือ Dekkapo （￣︶￣）↗📱\n"
                f"ชื่อลูกค้า👤: {customer_real_name}\n"
                f"สินค้าที่สั่ง🛒: {model}\n"
                f"เครือข่าย🌏: {network}\n"
                f"ประเภทลูกค้า🫂: {customer_group}\n"
                f"จำนวน📱🛒: {quantity}\n"
                f"เบอร์โทร🤙: {phone}"
            )
            message = {"message": message_text}
            requests.post(url, headers=headers, data=message)

            return redirect(url_for('home'))
        else:
            flash('เกิดข้อผิดพลาดในการบันทึกข้อมูล', 'error')

    return render_template(
        "home/home.html",
        data_Customer=data_Customer,
        data_Customer_grp=data_Customer_grp,
        data_stock=data_stock,
        selected_customer=selected_customer,    
        selected_phone=selected_phone,
        customer_group=customer_group,
        select_stock=select_stock,
        all_orders=all_orders,
        search_order=search_order 
    )

# ฟังก์ชันสำหรับการแก้ไขข้อมูล
@app.route('/edit_product', methods=['POST'])
def edit_product():
    data_Customer = execute_data("SELECT * FROM tbCustomer") or []
    customer_name = request.form.get('edit_customerName')
    model = request.form.get('edit_model')
    network = request.form.get('edit_network')
    customer_group = request.form.get('edit_customergrp')
    quantity = request.form.get('edit_quantity')
    phone = request.form.get('edit_phone')

    # ตรวจสอบข้อมูล
    if not all([customer_name, model, network, customer_group, quantity, phone]):
        flash('กรุณากรอกข้อมูลให้ครบถ้วน', 'error')
        return redirect(url_for('home'))


    customer_real_name = ""
    for row in data_Customer:
                if row[0] == customer_name:
                    customer_real_name = row[3]  # สมมติว่า column ที่ 2 คือชื่อจริง
                    break
    customer_data = get_customer_data()  # เรียกใช้ฟังก์ชัน get_customer_data จาก connect.py

    for row in customer_data:
        print(row)  # ตรวจสอบข้อมูลในแต่ละ row
        if row.get('OrderName') == customer_name:  # ตรวจสอบว่า 'OrderName' มีใน row และค่าตรงกับ customer_name หรือไม่
            customer_real_name = row.get('RealName', '')  # ใช้ get() เพื่อป้องกัน KeyError
            break

    # อัปเดตข้อมูลการสั่งซื้อ
    try:
        update_order(customer_name, model, network, customer_group, quantity, phone)
        flash('แก้ไขข้อมูลการสั่งซื้อสำเร็จ', 'success')

        # หากต้องการส่งข้อความผ่าน Line Notify
        url = "https://notify-api.line.me/api/notify"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            "Authorization": "Bearer DxjRgaf2lch2M1LwOFysWq3aLuHoKtVIaDyvOT56jbN"
        }
        message_text = (f"ร้านมือถือ Dekkapo （￣︶￣）↗📱\n"
                        f"แก้ไขข้อมูลลูกค้าคนใหม่🛠️ : ( •̀ ω •́ )✧\n"
                        f"\nชื่อลูกค้า👤: {customer_real_name}\n"
                        f"สินค้าที่แก้ไข🛒: {model}\n"
                        f"เครือข่าย🌏: {network}\n"
                        f"ประเภทลูกค้า🫂: {customer_group}\n"
                        f"จำนวน📱🛒: {quantity} เครื่อง\n"
                        f"เบอร์โทร🤙: {phone}"
        )
        message = {"message": message_text}
        requests.post(url, headers=headers, data=message)

    except Exception as e:
        flash(f"เกิดข้อผิดพลาด: {str(e)}", 'danger')

    return redirect(url_for('home'))



@app.route('/cancel_product', methods=['POST'])
def cancel_product():
    # รับค่า OrderID จากฟอร์ม
    order_id = request.form.get('order_id')
    
    # เรียกใช้ฟังก์ชัน cancel_order เพื่ออัปเดตสถานะเป็น "ยกเลิก"
    if cancel_order(order_id):
        flash('ยกเลิกสินค้าเรียบร้อยแล้ว', 'success')
    else:
        flash('เกิดข้อผิดพลาดในการยกเลิกสินค้า', 'danger')
    
    return redirect(url_for('home'))  # กลับไปยังหน้า home

# หน้าแสดงข้อมูลลูกค้า
@app.route('/customer_name')
def customer_name():
    query = "SELECT * FROM tbCustomer"
    result_customer = execute_data(query)

    if result_customer:
        customer_text = result_customer
        conn_text = "Successful"
    else:
        customer_text = []
        conn_text = "ไม่พบข้อมูลในตาราง tbCustomer (┬┬﹏┬┬)"

    return render_template("customer_name/customer_name.html", customer_text=customer_text, conn_text=conn_text)

# เส้นทางสำหรับกลุ่มลูกค้า
@app.route('/mobile_version')
def mobile_version():
    query = "SELECT * FROM tbCustomerGrp"
    result_customer = execute_data(query)

    if result_customer:
        customer_text = result_customer
        conn_text = "Successful"
    else:
        customer_text = []
        conn_text = "ไม่พบข้อมูลในตาราง tbCustomerGrp (┬┬﹏┬┬)"
   
    return render_template('mobile_version/mobile_version.html', customer_text=customer_text, conn_text=conn_text)

# เส้นทางสำหรับข้อมูลสินค้า (Stock)
@app.route('/stock')
def stock():
    query = "SELECT * FROM tbStock"
    result_customer = execute_data(query)

    if result_customer:
        customer_text = result_customer
        conn_text = "Successful"
    else:
        customer_text = []
        conn_text = "ไม่พบข้อมูลในตาราง tbStock (┬┬﹏┬┬)"

    return render_template('stock/stock.html', customer_text=customer_text, conn_text=conn_text)

# เส้นทางสำหรับกลุ่มสินค้า
@app.route('/stockgrp')
def stockgrp():
    query = "SELECT * FROM tbStockGrp"
    result_customer = execute_data(query)

    if result_customer:
        customer_text = result_customer
        conn_text = "Successful"
    else:
        customer_text = []
        conn_text = "ไม่พบข้อมูลในตาราง tbStockGrp (┬┬﹏┬┬)"

    return render_template('stockgrp/stockgrp.html', customer_text=customer_text, conn_text=conn_text)

# เส้นทางสำหรับประเภทการขาย (Sale Type)
@app.route('/sale')
def sale():
    query = "SELECT * FROM tbSaleType"
    result_customer = execute_data(query)

    if result_customer:
        customer_text = result_customer
        conn_text = "Successful"
    else:
        customer_text = []
        conn_text = "ไม่พบข้อมูลในตาราง tbSaleType (┬┬﹏┬┬)"

    return render_template('sale/sale.html', customer_text=customer_text, conn_text=conn_text)

# เริ่มต้นการรันแอปพลิเคชัน Flask
if __name__ == '__main__':
    app.run(debug=True)


# เริ่มต้นการรันแอปพลิเคชัน Flask
if __name__ == '__main__':
    app.run(debug=True)
