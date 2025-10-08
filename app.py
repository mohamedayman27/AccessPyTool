import streamlit as st
import pandas as pd
from datetime import datetime, date
import sqlite3
from database import DatabaseManager
from models import Customer, Product, Invoice, InvoiceItem
from utils import format_currency, get_low_stock_products, calculate_customer_balance
from export_utils import export_to_excel
import os

# تكوين الصفحة
st.set_page_config(
    page_title="الخليفة - لتجهيزات المطاعم والخدمات الفندقية",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تهيئة قاعدة البيانات
@st.cache_resource
def init_database():
    return DatabaseManager()

db = init_database()

# تهيئة Session State
if 'current_invoice_items' not in st.session_state:
    st.session_state.current_invoice_items = []

# العنوان الرئيسي
st.title("🏨 الخليفة")
st.markdown("### لتجهيزات المطاعم والخدمات الفندقية")
st.markdown("---")

# الشريط الجانبي للتنقل
st.sidebar.title("القوائم الرئيسية")
page = st.sidebar.selectbox(
    "اختر القسم",
    ["الصفحة الرئيسية", "إدارة الفواتير", "إدارة العملاء", "إدارة المخزون", "المرتجعات والمردودات", "التقارير"]
)

# الصفحة الرئيسية
if page == "الصفحة الرئيسية":
    st.header("لوحة التحكم الرئيسية")
    
    # إحصائيات سريعة
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_customers = db.get_total_customers()
        st.metric("إجمالي العملاء", total_customers)
    
    with col2:
        total_products = db.get_total_products()
        st.metric("إجمالي المنتجات", total_products)
    
    with col3:
        monthly_sales = db.get_monthly_sales()
        st.metric("مبيعات الشهر", format_currency(monthly_sales))
    
    with col4:
        pending_payments = db.get_pending_payments()
        st.metric("المدفوعات المعلقة", format_currency(pending_payments))
    
    # تنبيهات المخزون المنخفض
    st.subheader("🔔 تنبيهات المخزون")
    low_stock_products = get_low_stock_products(db)
    
    if low_stock_products:
        st.warning(f"يوجد {len(low_stock_products)} منتج بمخزون منخفض")
        for product in low_stock_products:
            st.write(f"- {product['name']}: {product['quantity']} قطعة متبقية")
    else:
        st.success("جميع المنتجات متوفرة بكميات كافية")
    
    # العملاء المدينون
    st.subheader("💰 العملاء المدينون")
    debtor_customers = db.get_debtor_customers()
    
    if debtor_customers:
        df_debtors = pd.DataFrame(debtor_customers)
        df_debtors['المبلغ المستحق'] = df_debtors['balance'].apply(format_currency)
        st.dataframe(
            df_debtors[['name', 'المبلغ المستحق']], 
            column_config={
                'name': 'اسم العميل',
                'المبلغ المستحق': 'المبلغ المستحق'
            }
        )
    else:
        st.success("لا يوجد عملاء مدينون حالياً")

# إدارة الفواتير
elif page == "إدارة الفواتير":
    st.header("📋 إدارة الفواتير")
    
    tab1, tab2 = st.tabs(["إنشاء فاتورة جديدة", "عرض الفواتير السابقة"])
    
    with tab1:
        st.subheader("إنشاء فاتورة جديدة")
        
        # بيانات العميل
        col1, col2 = st.columns(2)
        
        with col1:
            customers = db.get_all_customers()
            customer_options = {f"{c['name']} - {c['phone']}": c['id'] for c in customers}
            
            if customer_options:
                selected_customer = st.selectbox("اختر العميل", list(customer_options.keys()))
                customer_id = customer_options[selected_customer]
            else:
                st.warning("لا يوجد عملاء مسجلون. يرجى إضافة عميل أولاً.")
                customer_id = None
        
        with col2:
            invoice_date = st.date_input("تاريخ الفاتورة", datetime.now().date())
        
        if customer_id:
            # إضافة منتجات للفاتورة
            st.subheader("إضافة منتجات")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                products = db.get_all_products()
                product_options = {f"{p['name']} - {format_currency(p['price'])}": p for p in products}
                
                if product_options:
                    selected_product_display = st.selectbox("اختر المنتج", list(product_options.keys()))
                    selected_product = product_options[selected_product_display]
            
            with col2:
                if product_options:
                    max_quantity = selected_product['quantity']
                    quantity = st.number_input("الكمية", min_value=1, max_value=max_quantity, value=1)
                    
                    if quantity > max_quantity:
                        st.error(f"الكمية المتاحة: {max_quantity}")
            
            with col3:
                if product_options:
                    if st.button("إضافة للفاتورة"):
                        if quantity <= selected_product['quantity']:
                            item = {
                                'product_id': selected_product['id'],
                                'product_name': selected_product['name'],
                                'price': selected_product['price'],
                                'quantity': quantity,
                                'total': selected_product['price'] * quantity
                            }
                            st.session_state.current_invoice_items.append(item)
                            st.success(f"تم إضافة {selected_product['name']}")
                            st.rerun()
                        else:
                            st.error("الكمية المطلوبة غير متاحة")
            
            # عرض عناصر الفاتورة الحالية
            if st.session_state.current_invoice_items:
                st.subheader("عناصر الفاتورة")
                
                df_items = pd.DataFrame(st.session_state.current_invoice_items)
                df_items['السعر'] = df_items['price'].apply(format_currency)
                df_items['الإجمالي'] = df_items['total'].apply(format_currency)
                
                st.dataframe(
                    df_items[['product_name', 'quantity', 'السعر', 'الإجمالي']],
                    column_config={
                        'product_name': 'اسم المنتج',
                        'quantity': 'الكمية',
                        'السعر': 'السعر',
                        'الإجمالي': 'الإجمالي'
                    }
                )
                
                # حساب الإجمالي
                total_amount = sum(item['total'] for item in st.session_state.current_invoice_items)
                st.write(f"**إجمالي الفاتورة: {format_currency(total_amount)}**")
                
                # خيارات الدفع
                col1, col2 = st.columns(2)
                
                with col1:
                    paid_amount = st.number_input("المبلغ المدفوع", min_value=0.0, value=0.0, step=0.01)
                
                with col2:
                    remaining_amount = total_amount - paid_amount
                    st.write(f"**المبلغ المتبقي: {format_currency(remaining_amount)}**")
                
                # حفظ الفاتورة
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("حفظ الفاتورة", type="primary"):
                        invoice_data = {
                            'customer_id': customer_id,
                            'date': invoice_date,
                            'total_amount': total_amount,
                            'paid_amount': paid_amount,
                            'remaining_amount': remaining_amount
                        }
                        
                        invoice_id = db.create_invoice(invoice_data, st.session_state.current_invoice_items)
                        
                        if invoice_id:
                            st.success(f"تم حفظ الفاتورة برقم: {invoice_id}")
                            st.session_state.current_invoice_items = []
                            st.rerun()
                        else:
                            st.error("خطأ في حفظ الفاتورة")
                
                with col2:
                    if st.button("مسح الفاتورة"):
                        st.session_state.current_invoice_items = []
                        st.rerun()
    
    with tab2:
        st.subheader("الفواتير السابقة")
        
        # فلاتر البحث
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_customer = st.text_input("البحث بالعميل")
        
        with col2:
            start_date = st.date_input("من تاريخ")
        
        with col3:
            end_date = st.date_input("إلى تاريخ", datetime.now().date())
        
        # عرض الفواتير
        invoices = db.get_invoices_with_filters(search_customer, start_date, end_date)
        
        if invoices:
            df_invoices = pd.DataFrame(invoices)
            df_invoices['المبلغ الإجمالي'] = df_invoices['total_amount'].apply(format_currency)
            df_invoices['المبلغ المدفوع'] = df_invoices['paid_amount'].apply(format_currency)
            df_invoices['المبلغ المتبقي'] = df_invoices['remaining_amount'].apply(format_currency)
            
            st.dataframe(
                df_invoices[['id', 'customer_name', 'date', 'المبلغ الإجمالي', 'المبلغ المدفوع', 'المبلغ المتبقي']],
                column_config={
                    'id': 'رقم الفاتورة',
                    'customer_name': 'اسم العميل',
                    'date': 'التاريخ',
                    'المبلغ الإجمالي': 'الإجمالي',
                    'المبلغ المدفوع': 'المدفوع',
                    'المبلغ المتبقي': 'المتبقي'
                }
            )
            
            # خيارات التصدير والطباعة
            st.subheader("📥 تصدير وطباعة")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # تصدير Excel
                excel_data = export_to_excel(invoices, "invoices.xlsx")
                st.download_button(
                    label="📊 تصدير Excel",
                    data=excel_data,
                    file_name=f"invoices_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            with col2:
                # اختيار فاتورة لطباعة PDF
                selected_invoice_id = st.selectbox(
                    "اختر فاتورة للطباعة",
                    options=[inv['id'] for inv in invoices],
                    format_func=lambda x: f"فاتورة رقم {x}"
                )
            
            with col3:
                if selected_invoice_id:
                    # الحصول على بيانات الفاتورة المحددة
                    selected_inv = next(inv for inv in invoices if inv['id'] == selected_invoice_id)
                    invoice_items = db.get_invoice_items(selected_invoice_id)
                    
                    # تصدير تفاصيل الفاتورة كـ Excel
                    invoice_excel_data = export_to_excel(invoice_items, f"invoice_{selected_invoice_id}.xlsx")
                    st.download_button(
                        label="📄 تصدير تفاصيل الفاتورة",
                        data=invoice_excel_data,
                        file_name=f"invoice_{selected_invoice_id}_details.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.info("لا توجد فواتير للعرض")

# إدارة العملاء
elif page == "إدارة العملاء":
    st.header("👥 إدارة العملاء")
    
    tab1, tab2 = st.tabs(["إضافة عميل جديد", "عرض العملاء"])
    
    with tab1:
        st.subheader("إضافة عميل جديد")
        
        with st.form("add_customer_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("اسم العميل *")
                phone = st.text_input("رقم الهاتف *")
            
            with col2:
                email = st.text_input("البريد الإلكتروني")
                company = st.text_input("اسم الشركة")
            
            address = st.text_area("العنوان")
            notes = st.text_area("ملاحظات")
            
            submitted = st.form_submit_button("إضافة العميل")
            
            if submitted:
                if name and phone:
                    customer_data = {
                        'name': name,
                        'phone': phone,
                        'email': email,
                        'company': company,
                        'address': address,
                        'notes': notes
                    }
                    
                    if db.add_customer(customer_data):
                        st.success("تم إضافة العميل بنجاح")
                    else:
                        st.error("خطأ في إضافة العميل")
                else:
                    st.error("يرجى ملء الحقول المطلوبة (*)")
    
    with tab2:
        st.subheader("قائمة العملاء")
        
        # البحث
        search_term = st.text_input("البحث في العملاء")
        
        customers = db.search_customers(search_term) if search_term else db.get_all_customers()
        
        if customers:
            for customer in customers:
                with st.expander(f"{customer['name']} - {customer['phone']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**الهاتف:** {customer['phone']}")
                        st.write(f"**البريد الإلكتروني:** {customer['email'] or 'غير محدد'}")
                        st.write(f"**الشركة:** {customer['company'] or 'غير محدد'}")
                    
                    with col2:
                        balance = calculate_customer_balance(db, customer['id'])
                        st.write(f"**الرصيد المستحق:** {format_currency(balance)}")
                        st.write(f"**تاريخ التسجيل:** {customer['created_at']}")
                    
                    if customer['address']:
                        st.write(f"**العنوان:** {customer['address']}")
                    
                    if customer['notes']:
                        st.write(f"**ملاحظات:** {customer['notes']}")
        else:
            st.info("لا يوجد عملاء مسجلون")

# إدارة المخزون
elif page == "إدارة المخزون":
    st.header("📦 إدارة المخزون")
    
    tab1, tab2 = st.tabs(["إضافة منتج جديد", "عرض المخزون"])
    
    with tab1:
        st.subheader("إضافة منتج جديد")
        
        with st.form("add_product_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("اسم المنتج *")
                category = st.text_input("الفئة")
                price = st.number_input("سعر البيع *", min_value=0.01, step=0.01)
                cost_price = st.number_input("سعر التكلفة", min_value=0.0, step=0.01, value=0.0)
            
            with col2:
                sku = st.text_input("رمز المنتج (SKU)")
                quantity = st.number_input("الكمية *", min_value=0, step=1)
                min_stock = st.number_input("الحد الأدنى للمخزون", min_value=0, value=10, step=1)
            
            description = st.text_area("وصف المنتج")
            
            submitted = st.form_submit_button("إضافة المنتج")
            
            if submitted:
                if name and price >= 0 and quantity >= 0:
                    product_data = {
                        'name': name,
                        'sku': sku,
                        'category': category,
                        'price': price,
                        'cost_price': cost_price,
                        'quantity': quantity,
                        'min_stock': min_stock,
                        'description': description
                    }
                    
                    if db.add_product(product_data):
                        st.success("تم إضافة المنتج بنجاح")
                    else:
                        st.error("خطأ في إضافة المنتج")
                else:
                    st.error("يرجى ملء الحقول المطلوبة (*)")
    
    with tab2:
        st.subheader("المخزون الحالي")
        
        # البحث والفلاتر
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("البحث في المنتجات")
        
        with col2:
            category_filter = st.selectbox("فلترة بالفئة", ["الكل"] + db.get_categories())
        
        with col3:
            stock_filter = st.selectbox("حالة المخزون", ["الكل", "مخزون منخفض", "غير متوفر"])
        
        # عرض المنتجات
        products = db.get_products_with_filters(search_term, category_filter, stock_filter)
        
        if products:
            df_products = pd.DataFrame(products)
            df_products['السعر'] = df_products['price'].apply(format_currency)
            
            # تلوين الصفوف حسب حالة المخزون
            def color_stock_status(row):
                if row['quantity'] == 0:
                    return ['background-color: #ffebee'] * len(row)  # أحمر فاتح
                elif row['quantity'] <= row['min_stock']:
                    return ['background-color: #fff3e0'] * len(row)  # برتقالي فاتح
                else:
                    return [''] * len(row)
            
            styled_df = df_products[['name', 'sku', 'category', 'السعر', 'quantity', 'min_stock']].style.apply(
                color_stock_status, axis=1
            )
            
            st.dataframe(
                styled_df,
                column_config={
                    'name': 'اسم المنتج',
                    'sku': 'رمز المنتج',
                    'category': 'الفئة',
                    'السعر': 'السعر',
                    'quantity': 'الكمية المتاحة',
                    'min_stock': 'الحد الأدنى'
                }
            )
            
            # تحديث المخزون
            st.subheader("تحديث المخزون")
            
            product_to_update = st.selectbox(
                "اختر المنتج لتحديث المخزون",
                options=[(p['name'], p['id']) for p in products],
                format_func=lambda x: x[0]
            )
            
            if product_to_update:
                col1, col2 = st.columns(2)
                
                with col1:
                    new_quantity = st.number_input("الكمية الجديدة", min_value=0, step=1)
                
                with col2:
                    if st.button("تحديث المخزون"):
                        if db.update_product_quantity(product_to_update[1], new_quantity):
                            st.success("تم تحديث المخزون بنجاح")
                            st.rerun()
                        else:
                            st.error("خطأ في تحديث المخزون")
        else:
            st.info("لا توجد منتجات في المخزون")

# المرتجعات والمردودات
elif page == "المرتجعات والمردودات":
    st.header("🔄 إدارة المرتجعات والمردودات")
    
    tab1, tab2 = st.tabs(["إنشاء مرتجع جديد", "عرض المرتجعات"])
    
    with tab1:
        st.subheader("إنشاء مرتجع جديد")
        
        # اختيار الفاتورة
        col1, col2 = st.columns(2)
        
        with col1:
            # عرض الفواتير الحديثة
            recent_invoices = db.get_invoices_with_filters("", None, None)
            if recent_invoices:
                invoice_options = {f"فاتورة #{inv['id']} - {inv['customer_name']} - {format_currency(inv['total_amount'])}": inv for inv in recent_invoices[:50]}
                selected_invoice_display = st.selectbox("اختر الفاتورة للمرتجع", list(invoice_options.keys()))
                selected_invoice = invoice_options[selected_invoice_display]
            else:
                st.warning("لا توجد فواتير متاحة")
                selected_invoice = None
        
        with col2:
            return_date = st.date_input("تاريخ المرتجع", datetime.now().date())
        
        if selected_invoice:
            # عرض معلومات الفاتورة
            st.info(f"**العميل:** {selected_invoice['customer_name']} | **إجمالي الفاتورة:** {format_currency(selected_invoice['total_amount'])}")
            
            # الحصول على عناصر الفاتورة
            invoice_items = db.get_invoice_items(selected_invoice['id'])
            
            if invoice_items:
                # اختيار المنتجات للمرتجع
                st.subheader("اختر المنتجات للمرتجع")
                
                if 'return_items' not in st.session_state:
                    st.session_state.return_items = []
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    product_options = {f"{item['product_name']} - {item['quantity']} قطعة": item for item in invoice_items}
                    selected_product_display = st.selectbox("اختر المنتج", list(product_options.keys()))
                    selected_product = product_options[selected_product_display]
                
                with col2:
                    max_return_qty = selected_product['quantity']
                    return_quantity = st.number_input("الكمية المرتجعة", min_value=1, max_value=max_return_qty, value=1)
                
                with col3:
                    if st.button("إضافة للمرتجع"):
                        item = {
                            'product_id': selected_product['product_id'],
                            'product_name': selected_product['product_name'],
                            'price': selected_product['price'],
                            'quantity': return_quantity,
                            'total': selected_product['price'] * return_quantity
                        }
                        st.session_state.return_items.append(item)
                        st.success(f"تم إضافة {selected_product['product_name']}")
                        st.rerun()
                
                # عرض عناصر المرتجع
                if st.session_state.return_items:
                    st.subheader("عناصر المرتجع")
                    
                    df_return = pd.DataFrame(st.session_state.return_items)
                    df_return['السعر'] = df_return['price'].apply(format_currency)
                    df_return['الإجمالي'] = df_return['total'].apply(format_currency)
                    
                    st.dataframe(
                        df_return[['product_name', 'quantity', 'السعر', 'الإجمالي']],
                        column_config={
                            'product_name': 'اسم المنتج',
                            'quantity': 'الكمية',
                            'السعر': 'السعر',
                            'الإجمالي': 'الإجمالي'
                        }
                    )
                    
                    # حساب الإجمالي
                    total_return = sum(item['total'] for item in st.session_state.return_items)
                    st.write(f"**إجمالي المرتجع: {format_currency(total_return)}**")
                    
                    # تفاصيل المرتجع
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        refund_amount = st.number_input("المبلغ المسترد", min_value=0.0, max_value=float(total_return), value=float(total_return), step=0.01)
                        reason = st.text_input("سبب المرتجع")
                    
                    with col2:
                        status = st.selectbox("حالة المرتجع", ["معلق", "مقبول", "مرفوض"])
                        notes = st.text_area("ملاحظات")
                    
                    # حفظ المرتجع
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("حفظ المرتجع", type="primary"):
                            return_data = {
                                'invoice_id': selected_invoice['id'],
                                'customer_id': selected_invoice['customer_id'],
                                'return_date': return_date,
                                'total_amount': total_return,
                                'refund_amount': refund_amount,
                                'status': status,
                                'reason': reason,
                                'notes': notes
                            }
                            
                            return_id = db.create_return(return_data, st.session_state.return_items)
                            
                            if return_id:
                                st.success(f"تم حفظ المرتجع برقم: {return_id}")
                                st.session_state.return_items = []
                                st.rerun()
                            else:
                                st.error("خطأ في حفظ المرتجع")
                    
                    with col2:
                        if st.button("مسح المرتجع"):
                            st.session_state.return_items = []
                            st.rerun()
            else:
                st.warning("لا توجد عناصر في هذه الفاتورة")
    
    with tab2:
        st.subheader("المرتجعات السابقة")
        
        returns = db.get_all_returns()
        
        if returns:
            df_returns = pd.DataFrame(returns)
            df_returns['المبلغ الإجمالي'] = df_returns['total_amount'].apply(format_currency)
            df_returns['المبلغ المسترد'] = df_returns['refund_amount'].apply(format_currency)
            
            st.dataframe(
                df_returns[['id', 'invoice_number', 'customer_name', 'return_date', 'المبلغ الإجمالي', 'المبلغ المسترد', 'status', 'reason']],
                column_config={
                    'id': 'رقم المرتجع',
                    'invoice_number': 'رقم الفاتورة',
                    'customer_name': 'العميل',
                    'return_date': 'تاريخ المرتجع',
                    'المبلغ الإجمالي': 'المبلغ الإجمالي',
                    'المبلغ المسترد': 'المبلغ المسترد',
                    'status': 'الحالة',
                    'reason': 'السبب'
                }
            )
            
            # تصدير تقرير المرتجعات
            st.subheader("📥 تصدير تقرير المرتجعات")
            excel_data = export_to_excel(returns, "returns_report.xlsx")
            st.download_button(
                label="📊 تصدير Excel",
                data=excel_data,
                file_name=f"returns_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("لا توجد مرتجعات مسجلة")

# التقارير
elif page == "التقارير":
    st.header("📊 التقارير")
    
    tab1, tab2, tab3, tab4 = st.tabs(["تقارير المبيعات", "تقارير المخزون", "تقارير العملاء", "التقارير المالية"])
    
    with tab1:
        st.subheader("تقارير المبيعات")
        
        # فلاتر التاريخ
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("من تاريخ", datetime.now().replace(day=1).date())
        
        with col2:
            end_date = st.date_input("إلى تاريخ", datetime.now().date())
        
        # إحصائيات المبيعات
        sales_data = db.get_sales_report(start_date, end_date)
        
        if sales_data['invoices']:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("عدد الفواتير", sales_data['total_invoices'])
            
            with col2:
                st.metric("إجمالي المبيعات", format_currency(sales_data['total_sales']))
            
            with col3:
                st.metric("المتحصلات", format_currency(sales_data['total_paid']))
            
            # جدول الفواتير
            st.subheader("تفاصيل الفواتير")
            df_sales = pd.DataFrame(sales_data['invoices'])
            df_sales['المبلغ الإجمالي'] = df_sales['total_amount'].apply(format_currency)
            df_sales['المبلغ المدفوع'] = df_sales['paid_amount'].apply(format_currency)
            
            st.dataframe(
                df_sales[['id', 'customer_name', 'date', 'المبلغ الإجمالي', 'المبلغ المدفوع']],
                column_config={
                    'id': 'رقم الفاتورة',
                    'customer_name': 'العميل',
                    'date': 'التاريخ',
                    'المبلغ الإجمالي': 'الإجمالي',
                    'المبلغ المدفوع': 'المدفوع'
                }
            )
            
            # أزرار التصدير
            st.subheader("📥 تصدير التقرير")
            col1, col2 = st.columns(2)
            
            with col1:
                # تصدير Excel
                excel_data = export_to_excel(sales_data['invoices'], "sales_report.xlsx")
                st.download_button(
                    label="📊 تصدير Excel",
                    data=excel_data,
                    file_name=f"sales_report_{start_date}_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            with col2:
                # معلومات التقرير
                st.info(f"📊 التقرير يحتوي على {sales_data['total_invoices']} فاتورة")
        else:
            st.info("لا توجد مبيعات في هذه الفترة")
    
    with tab2:
        st.subheader("تقارير المخزون")
        
        # تقرير المخزون المنخفض
        st.write("**المنتجات ذات المخزون المنخفض:**")
        low_stock = db.get_low_stock_report()
        
        if low_stock:
            df_low_stock = pd.DataFrame(low_stock)
            st.dataframe(
                df_low_stock[['name', 'quantity', 'min_stock']],
                column_config={
                    'name': 'اسم المنتج',
                    'quantity': 'الكمية الحالية',
                    'min_stock': 'الحد الأدنى'
                }
            )
        else:
            st.success("جميع المنتجات متوفرة بكميات كافية")
        
        # تقرير قيمة المخزون
        inventory_value = db.get_inventory_value()
        st.metric("إجمالي قيمة المخزون", format_currency(inventory_value))
        
        # أزرار التصدير
        st.subheader("📥 تصدير تقرير المخزون")
        col1, col2 = st.columns(2)
        
        all_products = db.get_all_products()
        
        with col1:
            # تصدير Excel
            if all_products:
                excel_data = export_to_excel(all_products, "inventory_report.xlsx")
                st.download_button(
                    label="📊 تصدير Excel",
                    data=excel_data,
                    file_name=f"inventory_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col2:
            # معلومات المخزون
            if all_products:
                total_items = sum(p['quantity'] for p in all_products)
                st.info(f"📦 إجمالي القطع في المخزون: {total_items}")
    
    with tab3:
        st.subheader("تقارير العملاء")
        
        # العملاء المدينون
        st.write("**العملاء المدينون:**")
        debtors = db.get_debtor_customers()
        
        if debtors:
            df_debtors = pd.DataFrame(debtors)
            df_debtors['المبلغ المستحق'] = df_debtors['balance'].apply(format_currency)
            
            st.dataframe(
                df_debtors[['name', 'phone', 'المبلغ المستحق']],
                column_config={
                    'name': 'اسم العميل',
                    'phone': 'الهاتف',
                    'المبلغ المستحق': 'المبلغ المستحق'
                }
            )
            
            total_debt = sum(customer['balance'] for customer in debtors)
            st.metric("إجمالي الديون المستحقة", format_currency(total_debt))
            
            # تصدير تقرير العملاء المدينين
            excel_data = export_to_excel(debtors, "debtors_report.xlsx")
            st.download_button(
                label="📊 تصدير تقرير الديون Excel",
                data=excel_data,
                file_name=f"debtors_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.success("لا يوجد عملاء مدينون")
        
        # أفضل العملاء
        st.write("**أفضل العملاء (بحسب المشتريات):**")
        top_customers = db.get_top_customers()
        
        if top_customers:
            df_top = pd.DataFrame(top_customers)
            df_top['إجمالي المشتريات'] = df_top['total_purchases'].apply(format_currency)
            
            st.dataframe(
                df_top[['name', 'phone', 'إجمالي المشتريات', 'invoice_count']],
                column_config={
                    'name': 'اسم العميل',
                    'phone': 'الهاتف',
                    'إجمالي المشتريات': 'إجمالي المشتريات',
                    'invoice_count': 'عدد الفواتير'
                }
            )
    
    with tab4:
        st.subheader("التقارير المالية المتقدمة")
        
        # فترة التقرير
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("من تاريخ", datetime.now().replace(day=1).date(), key="financial_start")
        
        with col2:
            end_date = st.date_input("إلى تاريخ", datetime.now().date(), key="financial_end")
        
        # تقرير الأرباح والخسائر
        st.subheader("📈 تقرير الأرباح والخسائر")
        
        profit_loss = db.get_profit_loss_report(start_date, end_date)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("إجمالي المبيعات", format_currency(profit_loss['total_sales']))
        
        with col2:
            st.metric("التكلفة", format_currency(profit_loss['total_cost']))
        
        with col3:
            st.metric("الربح الصافي", format_currency(profit_loss['net_profit']),
                     delta=f"{profit_loss['profit_margin']:.1f}%" if profit_loss['profit_margin'] > 0 else None)
        
        with col4:
            st.metric("هامش الربح", f"{profit_loss['profit_margin']:.2f}%")
        
        # معلومات إضافية
        with st.expander("📊 تفاصيل التقرير المالي"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**إجمالي المتحصلات:** {format_currency(profit_loss['total_revenue'])}")
                st.write(f"**المرتجعات والمردودات:** {format_currency(profit_loss['total_returns'])}")
            
            with col2:
                st.write(f"**الربح الإجمالي:** {format_currency(profit_loss['gross_profit'])}")
                st.write(f"**الربح الصافي:** {format_currency(profit_loss['net_profit'])}")
        
        # تقرير التدفق النقدي
        st.subheader("💰 تقرير التدفق النقدي")
        
        cashflow = db.get_cashflow_report(start_date, end_date)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("المتحصلات النقدية", format_currency(cashflow['total_inflow']))
        
        with col2:
            st.metric("المبالغ المستردة", format_currency(cashflow['total_outflow']))
        
        with col3:
            st.metric("صافي التدفق النقدي", format_currency(cashflow['net_cashflow']))
        
        # أفضل المنتجات مبيعاً مع الأرباح
        st.subheader("🏆 أفضل المنتجات مبيعاً")
        
        top_products = db.get_top_selling_products_report(start_date, end_date)
        
        if top_products:
            df_top_products = pd.DataFrame(top_products)
            df_top_products['الإيرادات'] = df_top_products['total_revenue'].apply(format_currency)
            df_top_products['التكلفة'] = df_top_products['total_cost'].apply(format_currency)
            df_top_products['الربح'] = df_top_products['total_profit'].apply(format_currency)
            
            st.dataframe(
                df_top_products[['name', 'category', 'total_sold', 'الإيرادات', 'التكلفة', 'الربح']],
                column_config={
                    'name': 'المنتج',
                    'category': 'الفئة',
                    'total_sold': 'الكمية المباعة',
                    'الإيرادات': 'الإيرادات',
                    'التكلفة': 'التكلفة',
                    'الربح': 'الربح'
                }
            )
        else:
            st.info("لا توجد بيانات في هذه الفترة")
        
        # أداء الفئات
        st.subheader("📦 أداء الفئات")
        
        categories = db.get_category_performance_report(start_date, end_date)
        
        if categories:
            df_categories = pd.DataFrame(categories)
            df_categories['الإيرادات'] = df_categories['total_revenue'].apply(format_currency)
            df_categories['الأرباح'] = df_categories['total_profit'].apply(format_currency)
            
            st.dataframe(
                df_categories[['category', 'product_count', 'total_sold', 'الإيرادات', 'الأرباح']],
                column_config={
                    'category': 'الفئة',
                    'product_count': 'عدد المنتجات',
                    'total_sold': 'الكمية المباعة',
                    'الإيرادات': 'الإيرادات',
                    'الأرباح': 'الأرباح'
                }
            )
        else:
            st.info("لا توجد بيانات للفئات")
        
        # تصدير التقارير المالية
        st.subheader("📥 تصدير التقارير المالية")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if top_products:
                excel_data = export_to_excel(top_products, "financial_report.xlsx")
                st.download_button(
                    label="📊 تصدير تقرير المنتجات Excel",
                    data=excel_data,
                    file_name=f"financial_products_{start_date}_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col2:
            if categories:
                excel_data = export_to_excel(categories, "categories_report.xlsx")
                st.download_button(
                    label="📊 تصدير تقرير الفئات Excel",
                    data=excel_data,
                    file_name=f"categories_{start_date}_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
