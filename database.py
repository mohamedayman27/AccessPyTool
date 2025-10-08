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
                cost_price REAL DEFAULT 0,
                quantity INTEGER NOT NULL DEFAULT 0,
                min_stock INTEGER DEFAULT 10,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # إضافة عمود cost_price للجداول الموجودة (migration)
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'cost_price' not in columns:
            cursor.execute('ALTER TABLE products ADD COLUMN cost_price REAL DEFAULT 0')
        
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
        
        # جدول المرتجعات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                return_date DATE NOT NULL,
                total_amount REAL NOT NULL,
                refund_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                reason TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id),
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # جدول عناصر المرتجعات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS return_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                total_amount REAL NOT NULL,
                FOREIGN KEY (return_id) REFERENCES returns (id),
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
            INSERT INTO products (name, sku, category, price, cost_price, quantity, min_stock, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            product_data['name'],
            product_data.get('sku'),
            product_data.get('category'),
            product_data['price'],
            product_data.get('cost_price', 0),
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
    
    # =============== إدارة المرتجعات ===============
    
    def create_return(self, return_data: Dict[str, Any], items: List[Dict[str, Any]]) -> Optional[int]:
        """إنشاء مرتجع جديد مع العناصر"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # إنشاء المرتجع
            cursor.execute('''
                INSERT INTO returns (invoice_id, customer_id, return_date, total_amount, refund_amount, status, reason, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                return_data['invoice_id'],
                return_data['customer_id'],
                return_data['return_date'],
                return_data['total_amount'],
                return_data.get('refund_amount', 0),
                return_data.get('status', 'pending'),
                return_data.get('reason', ''),
                return_data.get('notes', '')
            ))
            
            return_id = cursor.lastrowid
            
            # إضافة عناصر المرتجع وإرجاع المخزون
            for item in items:
                cursor.execute('''
                    INSERT INTO return_items (return_id, product_id, quantity, price, total_amount)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    return_id,
                    item['product_id'],
                    item['quantity'],
                    item['price'],
                    item['total']
                ))
                
                # إرجاع المخزون
                cursor.execute('''
                    UPDATE products SET quantity = quantity + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (item['quantity'], item['product_id']))
            
            # تحديث رصيد العميل (إضافة المبلغ المسترد للفاتورة الأصلية)
            if return_data.get('refund_amount', 0) > 0:
                cursor.execute('''
                    UPDATE invoices 
                    SET remaining_amount = remaining_amount - ?,
                        paid_amount = paid_amount - ?
                    WHERE id = ?
                ''', (
                    return_data['refund_amount'],
                    return_data['refund_amount'],
                    return_data['invoice_id']
                ))
            
            conn.commit()
            return return_id
            
        except Exception as e:
            conn.rollback()
            print(f"Return creation error: {e}")
            return None
        finally:
            conn.close()
    
    def get_all_returns(self) -> List[Dict[str, Any]]:
        """الحصول على جميع المرتجعات"""
        query = '''
            SELECT r.*, c.name as customer_name, c.phone as customer_phone, i.id as invoice_number
            FROM returns r
            JOIN customers c ON r.customer_id = c.id
            JOIN invoices i ON r.invoice_id = i.id
            ORDER BY r.return_date DESC, r.id DESC
        '''
        return self.execute_query(query)
    
    def get_return_items(self, return_id: int) -> List[Dict[str, Any]]:
        """الحصول على عناصر المرتجع"""
        query = '''
            SELECT ri.*, p.name as product_name, p.sku
            FROM return_items ri
            JOIN products p ON ri.product_id = p.id
            WHERE ri.return_id = ?
        '''
        return self.execute_query(query, (return_id,))
    
    def get_returns_by_invoice(self, invoice_id: int) -> List[Dict[str, Any]]:
        """الحصول على المرتجعات الخاصة بفاتورة معينة"""
        query = '''
            SELECT r.*, c.name as customer_name
            FROM returns r
            JOIN customers c ON r.customer_id = c.id
            WHERE r.invoice_id = ?
            ORDER BY r.return_date DESC
        '''
        return self.execute_query(query, (invoice_id,))
    
    def update_return_status(self, return_id: int, status: str) -> bool:
        """تحديث حالة المرتجع"""
        query = 'UPDATE returns SET status = ? WHERE id = ?'
        result = self.execute_query(query, (status, return_id), fetch_all=False)
        return result is not None
    
    # =============== التقارير المالية المتقدمة ===============
    
    def get_profit_loss_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """تقرير الأرباح والخسائر"""
        # حساب إجمالي المبيعات
        sales_query = '''
            SELECT COALESCE(SUM(total_amount), 0) as total_sales,
                   COALESCE(SUM(paid_amount), 0) as total_revenue
            FROM invoices
            WHERE date BETWEEN ? AND ?
        '''
        sales_result = self.execute_query(sales_query, (start_date, end_date), fetch_one=True)
        
        # حساب تكلفة البضاعة المباعة
        cogs_query = '''
            SELECT COALESCE(SUM(ii.quantity * p.cost_price), 0) as total_cost
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.id
            JOIN products p ON ii.product_id = p.id
            WHERE i.date BETWEEN ? AND ?
        '''
        cogs_result = self.execute_query(cogs_query, (start_date, end_date), fetch_one=True)
        
        # حساب المرتجعات
        returns_query = '''
            SELECT COALESCE(SUM(refund_amount), 0) as total_returns
            FROM returns
            WHERE return_date BETWEEN ? AND ?
        '''
        returns_result = self.execute_query(returns_query, (start_date, end_date), fetch_one=True)
        
        total_sales = sales_result['total_sales'] if sales_result else 0
        total_revenue = sales_result['total_revenue'] if sales_result else 0
        total_cost = cogs_result['total_cost'] if cogs_result else 0
        total_returns = returns_result['total_returns'] if returns_result else 0
        
        # حساب الأرباح
        gross_profit = total_sales - total_cost
        net_profit = total_revenue - total_cost - total_returns
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'total_returns': total_returns,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'profit_margin': profit_margin
        }
    
    def get_top_selling_products_report(self, start_date: date, end_date: date, limit: int = 10) -> List[Dict[str, Any]]:
        """تقرير المنتجات الأكثر مبيعاً"""
        query = '''
            SELECT p.id, p.name, p.category, p.price, p.cost_price,
                   SUM(ii.quantity) as total_sold,
                   SUM(ii.total_amount) as total_revenue,
                   SUM(ii.quantity * p.cost_price) as total_cost,
                   SUM(ii.total_amount - (ii.quantity * p.cost_price)) as total_profit
            FROM products p
            JOIN invoice_items ii ON p.id = ii.product_id
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE i.date BETWEEN ? AND ?
            GROUP BY p.id, p.name, p.category, p.price, p.cost_price
            ORDER BY total_sold DESC
            LIMIT ?
        '''
        return self.execute_query(query, (start_date, end_date, limit))
    
    def get_monthly_comparison_report(self, year: int) -> List[Dict[str, Any]]:
        """تقرير المقارنة الشهرية"""
        query = '''
            SELECT strftime('%m', date) as month,
                   COUNT(*) as invoice_count,
                   SUM(total_amount) as total_sales,
                   SUM(paid_amount) as total_revenue,
                   SUM(remaining_amount) as total_pending
            FROM invoices
            WHERE strftime('%Y', date) = ?
            GROUP BY strftime('%m', date)
            ORDER BY month
        '''
        return self.execute_query(query, (str(year),))
    
    def get_category_performance_report(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """تقرير أداء الفئات"""
        query = '''
            SELECT p.category,
                   COUNT(DISTINCT p.id) as product_count,
                   SUM(ii.quantity) as total_sold,
                   SUM(ii.total_amount) as total_revenue,
                   SUM(ii.quantity * p.cost_price) as total_cost,
                   SUM(ii.total_amount - (ii.quantity * p.cost_price)) as total_profit
            FROM products p
            JOIN invoice_items ii ON p.id = ii.product_id
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE i.date BETWEEN ? AND ? AND p.category IS NOT NULL
            GROUP BY p.category
            ORDER BY total_revenue DESC
        '''
        return self.execute_query(query, (start_date, end_date))
    
    def get_cashflow_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """تقرير التدفق النقدي"""
        # المتحصلات النقدية
        inflow_query = '''
            SELECT COALESCE(SUM(paid_amount), 0) as total_inflow
            FROM invoices
            WHERE date BETWEEN ? AND ?
        '''
        inflow_result = self.execute_query(inflow_query, (start_date, end_date), fetch_one=True)
        
        # المبالغ المستردة
        outflow_query = '''
            SELECT COALESCE(SUM(refund_amount), 0) as total_outflow
            FROM returns
            WHERE return_date BETWEEN ? AND ?
        '''
        outflow_result = self.execute_query(outflow_query, (start_date, end_date), fetch_one=True)
        
        total_inflow = inflow_result['total_inflow'] if inflow_result else 0
        total_outflow = outflow_result['total_outflow'] if outflow_result else 0
        net_cashflow = total_inflow - total_outflow
        
        return {
            'total_inflow': total_inflow,
            'total_outflow': total_outflow,
            'net_cashflow': net_cashflow
        }
