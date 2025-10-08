import sqlite3
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Any

class DatabaseManager:
    def __init__(self, db_path: str = "hotel_equipment_store.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """إنشاء قاعدة البيانات والجداول الأساسية"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول العملاء
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                email TEXT,
                company TEXT,
                address TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول المنتجات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT UNIQUE,
                category TEXT,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                min_stock INTEGER DEFAULT 10,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول الفواتير
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                date DATE NOT NULL,
                total_amount REAL NOT NULL,
                paid_amount REAL DEFAULT 0,
                remaining_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # جدول عناصر الفاتورة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                total_amount REAL NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # إنشاء فهارس للتحسين
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_customer_phone ON customers (phone)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_sku ON products (sku)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoice_date ON invoices (date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoice_customer ON invoices (customer_id)')
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = True):
        """تنفيذ استعلام قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            
            if fetch_one:
                result = cursor.fetchone()
                return dict(result) if result else None
            elif fetch_all:
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            print(f"Database error: {e}")
            return None
        finally:
            conn.close()
    
    # =============== إدارة العملاء ===============
    
    def add_customer(self, customer_data: Dict[str, Any]) -> Optional[int]:
        """إضافة عميل جديد"""
        query = '''
            INSERT INTO customers (name, phone, email, company, address, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        params = (
            customer_data['name'],
            customer_data['phone'],
            customer_data.get('email'),
            customer_data.get('company'),
            customer_data.get('address'),
            customer_data.get('notes')
        )
        return self.execute_query(query, params, fetch_all=False)
    
    def get_all_customers(self) -> List[Dict[str, Any]]:
        """الحصول على جميع العملاء"""
        query = 'SELECT * FROM customers ORDER BY name'
        return self.execute_query(query)
    
    def search_customers(self, search_term: str) -> List[Dict[str, Any]]:
        """البحث في العملاء"""
        query = '''
            SELECT * FROM customers 
            WHERE name LIKE ? OR phone LIKE ? OR company LIKE ?
            ORDER BY name
        '''
        term = f'%{search_term}%'
        return self.execute_query(query, (term, term, term))
    
    def get_customer_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على عميل بالمعرف"""
        query = 'SELECT * FROM customers WHERE id = ?'
        return self.execute_query(query, (customer_id,), fetch_one=True)
    
    def get_total_customers(self) -> int:
        """الحصول على إجمالي عدد العملاء"""
        query = 'SELECT COUNT(*) as count FROM customers'
        result = self.execute_query(query, fetch_one=True)
        return result['count'] if result else 0
    
    # =============== إدارة المنتجات ===============
    
    def add_product(self, product_data: Dict[str, Any]) -> Optional[int]:
        """إضافة منتج جديد"""
        query = '''
            INSERT INTO products (name, sku, category, price, quantity, min_stock, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            product_data['name'],
            product_data.get('sku'),
            product_data.get('category'),
            product_data['price'],
            product_data['quantity'],
            product_data.get('min_stock', 10),
            product_data.get('description')
        )
        return self.execute_query(query, params, fetch_all=False)
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """الحصول على جميع المنتجات"""
        query = 'SELECT * FROM products ORDER BY name'
        return self.execute_query(query)
    
    def get_products_with_filters(self, search_term: str = "", category: str = "الكل", stock_status: str = "الكل") -> List[Dict[str, Any]]:
        """الحصول على المنتجات مع الفلاتر"""
        query = 'SELECT * FROM products WHERE 1=1'
        params = []
        
        if search_term:
            query += ' AND (name LIKE ? OR sku LIKE ? OR description LIKE ?)'
            term = f'%{search_term}%'
            params.extend([term, term, term])
        
        if category != "الكل":
            query += ' AND category = ?'
            params.append(category)
        
        if stock_status == "مخزون منخفض":
            query += ' AND quantity <= min_stock AND quantity > 0'
        elif stock_status == "غير متوفر":
            query += ' AND quantity = 0'
        
        query += ' ORDER BY name'
        return self.execute_query(query, tuple(params))
    
    def update_product_quantity(self, product_id: int, new_quantity: int) -> bool:
        """تحديث كمية المنتج"""
        query = 'UPDATE products SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        result = self.execute_query(query, (new_quantity, product_id), fetch_all=False)
        return result is not None
    
    def reduce_product_quantity(self, product_id: int, quantity: int) -> bool:
        """تقليل كمية المنتج (عند البيع)"""
        query = 'UPDATE products SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND quantity >= ?'
        result = self.execute_query(query, (quantity, product_id, quantity), fetch_all=False)
        return result is not None
    
    def get_categories(self) -> List[str]:
        """الحصول على جميع الفئات"""
        query = 'SELECT DISTINCT category FROM products WHERE category IS NOT NULL ORDER BY category'
        results = self.execute_query(query)
        return [row['category'] for row in results]
    
    def get_total_products(self) -> int:
        """الحصول على إجمالي عدد المنتجات"""
        query = 'SELECT COUNT(*) as count FROM products'
        result = self.execute_query(query, fetch_one=True)
        return result['count'] if result else 0
    
    # =============== إدارة الفواتير ===============
    
    def create_invoice(self, invoice_data: Dict[str, Any], items: List[Dict[str, Any]]) -> Optional[int]:
        """إنشاء فاتورة جديدة مع العناصر"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # إنشاء الفاتورة
            cursor.execute('''
                INSERT INTO invoices (customer_id, date, total_amount, paid_amount, remaining_amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                invoice_data['customer_id'],
                invoice_data['date'],
                invoice_data['total_amount'],
                invoice_data['paid_amount'],
                invoice_data['remaining_amount']
            ))
            
            invoice_id = cursor.lastrowid
            
            # إضافة عناصر الفاتورة وتحديث المخزون
            for item in items:
                cursor.execute('''
                    INSERT INTO invoice_items (invoice_id, product_id, quantity, price, total_amount)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    invoice_id,
                    item['product_id'],
                    item['quantity'],
                    item['price'],
                    item['total']
                ))
                
                # تقليل المخزون
                cursor.execute('''
                    UPDATE products SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (item['quantity'], item['product_id']))
            
            conn.commit()
            return invoice_id
            
        except Exception as e:
            conn.rollback()
            print(f"Invoice creation error: {e}")
            return None
        finally:
            conn.close()
    
    def get_invoices_with_filters(self, customer_search: str = "", start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        """الحصول على الفواتير مع الفلاتر"""
        query = '''
            SELECT i.*, c.name as customer_name, c.phone as customer_phone
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            WHERE 1=1
        '''
        params = []
        
        if customer_search:
            query += ' AND c.name LIKE ?'
            params.append(f'%{customer_search}%')
        
        if start_date:
            query += ' AND i.date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND i.date <= ?'
            params.append(end_date)
        
        query += ' ORDER BY i.date DESC, i.id DESC'
        return self.execute_query(query, tuple(params))
    
    def get_invoice_items(self, invoice_id: int) -> List[Dict[str, Any]]:
        """الحصول على عناصر الفاتورة"""
        query = '''
            SELECT ii.*, p.name as product_name, p.sku
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.id
            WHERE ii.invoice_id = ?
        '''
        return self.execute_query(query, (invoice_id,))
    
    # =============== التقارير والإحصائيات ===============
    
    def get_monthly_sales(self) -> float:
        """الحصول على مبيعات الشهر الحالي"""
        query = '''
            SELECT COALESCE(SUM(total_amount), 0) as total
            FROM invoices
            WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
        '''
        result = self.execute_query(query, fetch_one=True)
        return result['total'] if result else 0.0
    
    def get_pending_payments(self) -> float:
        """الحصول على المدفوعات المعلقة"""
        query = 'SELECT COALESCE(SUM(remaining_amount), 0) as total FROM invoices WHERE remaining_amount > 0'
        result = self.execute_query(query, fetch_one=True)
        return result['total'] if result else 0.0
    
    def get_debtor_customers(self) -> List[Dict[str, Any]]:
        """الحصول على العملاء المدينون"""
        query = '''
            SELECT c.id, c.name, c.phone, COALESCE(SUM(i.remaining_amount), 0) as balance
            FROM customers c
            LEFT JOIN invoices i ON c.id = i.customer_id
            GROUP BY c.id, c.name, c.phone
            HAVING balance > 0
            ORDER BY balance DESC
        '''
        return self.execute_query(query)
    
    def get_low_stock_report(self) -> List[Dict[str, Any]]:
        """تقرير المخزون المنخفض"""
        query = 'SELECT * FROM products WHERE quantity <= min_stock ORDER BY quantity ASC'
        return self.execute_query(query)
    
    def get_inventory_value(self) -> float:
        """الحصول على قيمة المخزون الإجمالية"""
        query = 'SELECT COALESCE(SUM(price * quantity), 0) as total FROM products'
        result = self.execute_query(query, fetch_one=True)
        return result['total'] if result else 0.0
    
    def get_sales_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """تقرير المبيعات لفترة معينة"""
        # الحصول على الفواتير
        invoices_query = '''
            SELECT i.*, c.name as customer_name
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            WHERE i.date BETWEEN ? AND ?
            ORDER BY i.date DESC
        '''
        invoices = self.execute_query(invoices_query, (start_date, end_date))
        
        # حساب الإحصائيات
        total_invoices = len(invoices)
        total_sales = sum(inv['total_amount'] for inv in invoices)
        total_paid = sum(inv['paid_amount'] for inv in invoices)
        
        return {
            'invoices': invoices,
            'total_invoices': total_invoices,
            'total_sales': total_sales,
            'total_paid': total_paid
        }
    
    def get_top_customers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """أفضل العملاء بحسب المشتريات"""
        query = '''
            SELECT c.name, c.phone, 
                   COALESCE(SUM(i.total_amount), 0) as total_purchases,
                   COUNT(i.id) as invoice_count
            FROM customers c
            LEFT JOIN invoices i ON c.id = i.customer_id
            GROUP BY c.id, c.name, c.phone
            HAVING total_purchases > 0
            ORDER BY total_purchases DESC
            LIMIT ?
        '''
        return self.execute_query(query, (limit,))
