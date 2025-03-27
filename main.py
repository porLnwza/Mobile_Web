from flask import Flask, render_template, redirect ,url_for,request,flash
from connection import connection_database, execute_data ,add_order_to_database, get_all_orders, update_order, delete_order
import pyodbc
import requests



# กำหนดการตั้งค่า Flask
app = Flask(__name__, template_folder="template", static_folder="static")
app.secret_key = 'your_secret_key_here'  # ใช้สำหรับการแสดงผล Flash messages

# ตัวแปรจำลองฐานข้อมูลสินค้า
product = []

# ฟังก์ชันหลักที่แสดงหน้าแรก
@app.route('/', methods=['GET', 'POST'])
def home():
    selected_customer = None
    selected_phone = None
    customer_group = None  
    select_stock = None  

    # ✅ ดึงข้อมูลจากฐานข้อมูลทุกครั้งที่โหลดหน้า
    data_Customer = execute_data("SELECT * FROM tbCustomer") or []
    data_Customer_grp = execute_data("SELECT * FROM tbCustomerGrp") or []
    data_stock = execute_data("SELECT * FROM tbStock") or []
    all_orders = get_all_orders() or []

    select_value = request.form.get('customer')
    selected_phone = request.form.get('selected_phone')
    customer_group = request.form.get('customer_group')
    select_stock = request.form.get('select_stock')

    if select_value:
        for row in data_Customer:
            if row[0] == select_value:
                selected_customer = row[0]  
                customer_real_name = row[3]  # สมมติว่าชื่อจริงอยู่ในคอลัมน์ที่ 2
                selected_phone = row[5]  
                customer_group = row[1]  
                select_stock = row[4]  
                break

    if request.method == 'POST':
        if 'button_add' in request.form:
            customer_name = request.form.get('customer')
            model = request.form.get('select_stock')
            network = request.form.get('network')
            customer_group = request.form.get('customer_group')
            quantity = request.form.get('quantity')
            phone = request.form.get('selected_phone')



            customer_real_name = ""
            for row in data_Customer:
                if row[0] == customer_name:
                    customer_real_name = row[3]  # สมมติว่า column ที่ 2 คือชื่อจริง
                    break

            if not all([customer_name, model, network, customer_group, quantity, phone]):
                flash('กรุณากรอกข้อมูลให้ครบถ้วน', 'error')
                return redirect(url_for('home'))

            add_order_to_database(customer_real_name, model, network, customer_group, quantity, phone)
            flash('เพิ่มข้อมูลการสั่งซื้อสำเร็จ', 'success')

            # ✅ ส่งข้อความผ่าน Line Notify
            url = "https://notify-api.line.me/api/notify"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                "Authorization": "Bearer 7lVpHVzPrquKZ3M4aucCt7SBuXj5tMfw8oWuQSqQTWx"
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
        all_orders=all_orders
    )

# ฟังก์ชันสำหรับการแก้ไขข้อมูล
@app.route('/edit_product', methods=['POST'])
def edit_product():
    # รับ product_id จากฟอร์ม
    product_id = request.form.get('product_id')
    
    if not product_id or not product_id.isdigit():
        flash('ข้อมูล product_id ไม่ถูกต้อง', 'error')
        return redirect(url_for('home'))

    # ดึงข้อมูลที่แก้ไขจากฟอร์ม
    customer_id = request.form.get('edit_customerName')  # รหัสลูกค้า
    model = request.form.get('edit_model')
    network = request.form.get('edit_network')
    customer_group = request.form.get('edit_customerGroup')
    quantity = request.form.get('edit_quantity')
    phone = request.form.get('edit_phone')

    # ค้นหาชื่อจริงของลูกค้าจากฐานข้อมูล
    query = "SELECT CustomerName FROM tbCustomer WHERE CustomerID = ?"
    customer_data = execute_data(query, (customer_id,))

    if customer_data and len(customer_data) > 0:
        customer_real_name = customer_data[0][0]  # ดึงชื่อจริงของลูกค้า
    else:
        flash('ไม่พบข้อมูลลูกค้า', 'error')
        return redirect(url_for('home'))

    # อัปเดตข้อมูลการสั่งซื้อในฐานข้อมูล
    if update_order(product_id, customer_real_name, model, network, customer_group, quantity, phone):
        flash('ข้อมูลถูกอัปเดตสำเร็จ', 'success')
    else:
        flash('เกิดข้อผิดพลาดในการอัปเดตข้อมูล', 'error')

    return redirect(url_for('home'))



# ฟังก์ชันสำหรับการลบข้อมูล
@app.route('/cancel_product', methods=['POST'])
def cancel_product():
    product_id = request.form.get('product_id')
    if not product_id or not product_id.isdigit():
        flash('ข้อมูล product_id ไม่ถูกต้อง', 'error')
        return redirect(url_for('home'))

    product_id = int(product_id)
    if update_order_status(product_id, 'canceled'):
        flash('สินค้าถูกยกเลิกแล้ว', 'success')
    else:
        flash('เกิดข้อผิดพลาดในการยกเลิกสินค้า', 'error')

    return redirect(url_for('home'))

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

@app.route('/orders', methods=['GET', 'POST'])
def orders():
    all_orders = get_all_orders()  # ดึงข้อมูลการสั่งซื้อทั้งหมดจากฐานข้อมูล
    return render_template("orders/orders.html", all_orders=all_orders)


# เริ่มต้นการรันแอปพลิเคชัน Flask
if __name__ == '__main__':  
    app.run(debug=True)
