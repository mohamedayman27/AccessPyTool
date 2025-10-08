from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import locale
from database import DatabaseManager

def format_currency(amount: float, currency: str = "ج.م") -> str:
    """تنسيق المبلغ كعملة"""
    if amount is None:
        return f"0.00 {currency}"
    return f"{amount:,.2f} {currency}"

def format_number(number: int) -> str:
    """تنسيق الرقم بفواصل الآلاف"""
    if number is None:
        return "0"
    return f"{number:,}"

def format_date(date_obj: date, format_type: str = "arabic") -> str:
    """تنسيق التاريخ"""
    if date_obj is None:
        return ""
    
    if format_type == "arabic":
        months = {
            1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل",
            5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس",
            9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
        }
        return f"{date_obj.day} {months[date_obj.month]} {date_obj.year}"
    else:
        return date_obj.strftime("%Y-%m-%d")

def format_datetime(datetime_obj: datetime, format_type: str = "arabic") -> str:
    """تنسيق التاريخ والوقت"""
    if datetime_obj is None:
        return ""
    
    date_part = format_date(datetime_obj.date(), format_type)
    time_part = datetime_obj.strftime("%H:%M")
    return f"{date_part} - {time_part}"

def get_low_stock_products(db: DatabaseManager, threshold: Optional[int] = None) -> List[Dict[str, Any]]:
    """الحصول على المنتجات ذات المخزون المنخفض"""
    if threshold is None:
        # استخدام الحد الأدنى المحدد لكل منتج
        query = 'SELECT * FROM products WHERE quantity <= min_stock AND quantity > 0 ORDER BY quantity ASC'
        return db.execute_query(query)
    else:
        # استخدام حد موحد
        query = 'SELECT * FROM products WHERE quantity <= ? AND quantity > 0 ORDER BY quantity ASC'
        return db.execute_query(query, (threshold,))

def get_out_of_stock_products(db: DatabaseManager) -> List[Dict[str, Any]]:
    """الحصول على المنتجات غير المتوفرة"""
    query = 'SELECT * FROM products WHERE quantity = 0 ORDER BY name'
    return db.execute_query(query)

def calculate_customer_balance(db: DatabaseManager, customer_id: int) -> float:
    """حساب رصيد العميل المستحق"""
    query = 'SELECT COALESCE(SUM(remaining_amount), 0) as balance FROM invoices WHERE customer_id = ?'
    result = db.execute_query(query, (customer_id,), fetch_one=True)
    return result['balance'] if result else 0.0

def get_customer_purchase_history(db: DatabaseManager, customer_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """الحصول على تاريخ مشتريات العميل"""
    query = '''
        SELECT * FROM invoices 
        WHERE customer_id = ? 
        ORDER BY date DESC, id DESC 
        LIMIT ?
    '''
    return db.execute_query(query, (customer_id, limit))

def calculate_product_sales(db: DatabaseManager, product_id: int, days: int = 30) -> Dict[str, Any]:
    """حساب مبيعات المنتج خلال فترة معينة"""
    start_date = datetime.now().date() - timedelta(days=days)
    
    query = '''
        SELECT 
            COALESCE(SUM(ii.quantity), 0) as total_sold,
            COALESCE(SUM(ii.total_amount), 0) as total_revenue,
            COUNT(DISTINCT i.id) as invoice_count
        FROM invoice_items ii
        JOIN invoices i ON ii.invoice_id = i.id
        WHERE ii.product_id = ? AND i.date >= ?
    '''
    
    result = db.execute_query(query, (product_id, start_date), fetch_one=True)
    
    return {
        'total_sold': result['total_sold'] if result else 0,
        'total_revenue': result['total_revenue'] if result else 0.0,
        'invoice_count': result['invoice_count'] if result else 0,
        'period_days': days
    }

def get_sales_trend(db: DatabaseManager, days: int = 30) -> List[Dict[str, Any]]:
    """الحصول على اتجاه المبيعات اليومية"""
    start_date = datetime.now().date() - timedelta(days=days)
    
    query = '''
        SELECT 
            date,
            COUNT(*) as invoice_count,
            SUM(total_amount) as daily_sales,
            SUM(paid_amount) as daily_payments
        FROM invoices
        WHERE date >= ?
        GROUP BY date
        ORDER BY date
    '''
    
    return db.execute_query(query, (start_date,))

def validate_phone_number(phone: str) -> bool:
    """التحقق من صحة رقم الهاتف"""
    if not phone:
        return False
    
    # إزالة المسافات والرموز
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # التحقق من أن الرقم يحتوي على أرقام فقط وطوله مناسب
    if not phone.isdigit():
        return False
    
    # التحقق من الطول (10-15 رقم)
    return 10 <= len(phone) <= 15

def validate_email(email: str) -> bool:
    """التحقق من صحة البريد الإلكتروني"""
    if not email:
        return True  # البريد الإلكتروني اختياري
    
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_sku(product_name: str, category: str = None) -> str:
    """توليد رمز SKU للمنتج"""
    import re
    
    # أخذ أول 3 أحرف من اسم المنتج
    name_part = re.sub(r'[^a-zA-Z0-9]', '', product_name)[:3].upper()
    
    # أخذ أول حرفين من الفئة إن وجدت
    category_part = ""
    if category:
        category_part = re.sub(r'[^a-zA-Z0-9]', '', category)[:2].upper()
    
    # إضافة الوقت الحالي
    time_part = datetime.now().strftime("%m%d%H%M")[-4:]
    
    return f"{name_part}{category_part}{time_part}"

def calculate_payment_due_date(invoice_date: date, payment_terms: int = 30) -> date:
    """حساب تاريخ استحقاق الدفع"""
    return invoice_date + timedelta(days=payment_terms)

def get_payment_status_color(remaining_amount: float, total_amount: float) -> str:
    """الحصول على لون حالة الدفع"""
    if remaining_amount <= 0:
        return "green"  # مدفوع بالكامل
    elif remaining_amount == total_amount:
        return "red"    # غير مدفوع
    else:
        return "orange" # مدفوع جزئياً

def format_payment_status(paid_amount: float, total_amount: float) -> str:
    """تنسيق حالة الدفع"""
    remaining = total_amount - paid_amount
    
    if remaining <= 0:
        return "✅ مدفوع بالكامل"
    elif paid_amount == 0:
        return "❌ غير مدفوع"
    else:
        percentage = (paid_amount / total_amount) * 100
        return f"🟡 مدفوع جزئياً ({percentage:.0f}%)"

def get_stock_status_emoji(quantity: int, min_stock: int) -> str:
    """الحصول على رمز تعبيري لحالة المخزون"""
    if quantity == 0:
        return "🔴"  # غير متوفر
    elif quantity <= min_stock:
        return "🟡"  # مخزون منخفض
    else:
        return "🟢"  # متوفر

def calculate_profit_margin(selling_price: float, cost_price: float) -> float:
    """حساب هامش الربح"""
    if cost_price == 0:
        return 0
    return ((selling_price - cost_price) / cost_price) * 100

def get_top_selling_products(db: DatabaseManager, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
    """الحصول على أكثر المنتجات مبيعاً"""
    start_date = datetime.now().date() - timedelta(days=days)
    
    query = '''
        SELECT 
            p.id,
            p.name,
            p.price,
            COALESCE(SUM(ii.quantity), 0) as total_sold,
            COALESCE(SUM(ii.total_amount), 0) as total_revenue
        FROM products p
        LEFT JOIN invoice_items ii ON p.id = ii.product_id
        LEFT JOIN invoices i ON ii.invoice_id = i.id
        WHERE i.date >= ? OR i.date IS NULL
        GROUP BY p.id, p.name, p.price
        HAVING total_sold > 0
        ORDER BY total_sold DESC
        LIMIT ?
    '''
    
    return db.execute_query(query, (start_date, limit))

def backup_database(db: DatabaseManager, backup_path: str = None) -> bool:
    """عمل نسخة احتياطية من قاعدة البيانات"""
    import shutil
    
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"backup_hotel_equipment_store_{timestamp}.db"
    
    try:
        shutil.copy2(db.db_path, backup_path)
        return True
    except Exception as e:
        print(f"Backup error: {e}")
        return False

def export_data_to_excel(data: List[Dict[str, Any]], filename: str, sheet_name: str = "البيانات") -> bool:
    """تصدير البيانات إلى ملف Excel"""
    try:
        import pandas as pd
        
        df = pd.DataFrame(data)
        df.to_excel(filename, sheet_name=sheet_name, index=False, engine='openpyxl')
        return True
    except ImportError:
        print("pandas or openpyxl not installed. Cannot export to Excel.")
        return False
    except Exception as e:
        print(f"Export error: {e}")
        return False

def import_data_from_excel(filename: str, sheet_name: str = None) -> Optional[List[Dict[str, Any]]]:
    """استيراد البيانات من ملف Excel"""
    try:
        import pandas as pd
        
        df = pd.read_excel(filename, sheet_name=sheet_name, engine='openpyxl')
        return df.to_dict('records')
    except ImportError:
        print("pandas or openpyxl not installed. Cannot import from Excel.")
        return None
    except Exception as e:
        print(f"Import error: {e}")
        return None

def search_products_advanced(db: DatabaseManager, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """البحث المتقدم في المنتجات"""
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    
    if search_criteria.get('name'):
        query += " AND name LIKE ?"
        params.append(f"%{search_criteria['name']}%")
    
    if search_criteria.get('category'):
        query += " AND category = ?"
        params.append(search_criteria['category'])
    
    if search_criteria.get('min_price'):
        query += " AND price >= ?"
        params.append(search_criteria['min_price'])
    
    if search_criteria.get('max_price'):
        query += " AND price <= ?"
        params.append(search_criteria['max_price'])
    
    if search_criteria.get('low_stock'):
        query += " AND quantity <= min_stock"
    
    if search_criteria.get('out_of_stock'):
        query += " AND quantity = 0"
    
    query += " ORDER BY name"
    return db.execute_query(query, tuple(params))

def generate_invoice_number(db: DatabaseManager) -> str:
    """توليد رقم فاتورة فريد"""
    # الحصول على آخر رقم فاتورة
    query = "SELECT MAX(id) as max_id FROM invoices"
    result = db.execute_query(query, fetch_one=True)
    
    next_id = (result['max_id'] or 0) + 1
    current_year = datetime.now().year
    
    return f"INV-{current_year}-{next_id:06d}"

def calculate_age_of_debt(invoice_date: date) -> int:
    """حساب عمر الدين بالأيام"""
    return (datetime.now().date() - invoice_date).days

def categorize_debt_by_age(db: DatabaseManager) -> Dict[str, List[Dict[str, Any]]]:
    """تصنيف الديون حسب العمر"""
    query = '''
        SELECT i.*, c.name as customer_name, c.phone
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.remaining_amount > 0
        ORDER BY i.date
    '''
    
    invoices = db.execute_query(query)
    
    categories = {
        'current': [],      # أقل من 30 يوم
        'overdue_30': [],   # 30-60 يوم
        'overdue_60': [],   # 60-90 يوم
        'overdue_90': []    # أكثر من 90 يوم
    }
    
    for invoice in invoices:
        age = calculate_age_of_debt(datetime.strptime(invoice['date'], '%Y-%m-%d').date())
        
        if age < 30:
            categories['current'].append(invoice)
        elif age < 60:
            categories['overdue_30'].append(invoice)
        elif age < 90:
            categories['overdue_60'].append(invoice)
        else:
            categories['overdue_90'].append(invoice)
    
    return categories
