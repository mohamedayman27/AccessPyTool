from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal

@dataclass
class Customer:
    """نموذج العميل"""
    id: Optional[int] = None
    name: str = ""
    phone: str = ""
    company: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def display_name(self) -> str:
        """اسم العرض للعميل"""
        return f"{self.name} - {self.phone}"
    
    def to_dict(self) -> dict:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'company': self.company,
            'address': self.address,
            'notes': self.notes,
            'created_at': self.created_at
        }

@dataclass
class Product:
    """نموذج المنتج"""
    id: Optional[int] = None
    name: str = ""
    sku: Optional[str] = None
    category: Optional[str] = None
    price: float = 0.0
    quantity: int = 0
    min_stock: int = 10
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    @property
    def is_low_stock(self) -> bool:
        """هل المخزون منخفض؟"""
        return self.quantity <= self.min_stock
    
    @property
    def is_out_of_stock(self) -> bool:
        """هل المنتج غير متوفر؟"""
        return self.quantity == 0
    
    @property
    def stock_status(self) -> str:
        """حالة المخزون"""
        if self.is_out_of_stock:
            return "غير متوفر"
        elif self.is_low_stock:
            return "مخزون منخفض"
        else:
            return "متوفر"
    
    @property
    def total_value(self) -> float:
        """القيمة الإجمالية للمخزون"""
        return self.price * self.quantity
    
    @property
    def display_name(self) -> str:
        """اسم العرض للمنتج"""
        return f"{self.name} - {self.price:.2f} ج.م"
    
    def can_sell(self, requested_quantity: int) -> bool:
        """هل يمكن بيع الكمية المطلوبة؟"""
        return self.quantity >= requested_quantity
    
    def to_dict(self) -> dict:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'category': self.category,
            'price': self.price,
            'quantity': self.quantity,
            'min_stock': self.min_stock,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

@dataclass
class InvoiceItem:
    """نموذج عنصر الفاتورة"""
    id: Optional[int] = None
    invoice_id: Optional[int] = None
    product_id: int = 0
    product_name: str = ""
    quantity: int = 1
    price: float = 0.0
    total_amount: float = 0.0
    
    def __post_init__(self):
        if self.total_amount == 0.0:
            self.total_amount = self.quantity * self.price
    
    @property
    def unit_price(self) -> float:
        """سعر الوحدة"""
        return self.price
    
    @property
    def line_total(self) -> float:
        """إجمالي السطر"""
        return self.total_amount
    
    def to_dict(self) -> dict:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'price': self.price,
            'total_amount': self.total_amount
        }

@dataclass
class Invoice:
    """نموذج الفاتورة"""
    id: Optional[int] = None
    customer_id: int = 0
    customer_name: str = ""
    date: date = None
    total_amount: float = 0.0
    paid_amount: float = 0.0
    remaining_amount: float = 0.0
    status: str = "active"
    notes: Optional[str] = None
    items: List[InvoiceItem] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.date is None:
            self.date = date.today()
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.items is None:
            self.items = []
        if self.remaining_amount == 0.0:
            self.remaining_amount = self.total_amount - self.paid_amount
    
    @property
    def is_fully_paid(self) -> bool:
        """هل الفاتورة مدفوعة بالكامل؟"""
        return self.remaining_amount <= 0
    
    @property
    def is_partially_paid(self) -> bool:
        """هل الفاتورة مدفوعة جزئياً؟"""
        return 0 < self.paid_amount < self.total_amount
    
    @property
    def is_unpaid(self) -> bool:
        """هل الفاتورة غير مدفوعة؟"""
        return self.paid_amount == 0
    
    @property
    def payment_status(self) -> str:
        """حالة الدفع"""
        if self.is_fully_paid:
            return "مدفوعة بالكامل"
        elif self.is_partially_paid:
            return "مدفوعة جزئياً"
        else:
            return "غير مدفوعة"
    
    @property
    def payment_percentage(self) -> float:
        """نسبة الدفع"""
        if self.total_amount == 0:
            return 0
        return (self.paid_amount / self.total_amount) * 100
    
    def add_item(self, item: InvoiceItem):
        """إضافة عنصر للفاتورة"""
        self.items.append(item)
        self.recalculate_total()
    
    def remove_item(self, item_id: int):
        """حذف عنصر من الفاتورة"""
        self.items = [item for item in self.items if item.id != item_id]
        self.recalculate_total()
    
    def recalculate_total(self):
        """إعادة حساب الإجمالي"""
        self.total_amount = sum(item.total_amount for item in self.items)
        self.remaining_amount = self.total_amount - self.paid_amount
    
    def make_payment(self, amount: float):
        """تسجيل دفعة"""
        self.paid_amount += amount
        self.remaining_amount = self.total_amount - self.paid_amount
        
        if self.remaining_amount < 0:
            self.remaining_amount = 0
    
    def to_dict(self) -> dict:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'date': self.date,
            'total_amount': self.total_amount,
            'paid_amount': self.paid_amount,
            'remaining_amount': self.remaining_amount,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at,
            'items': [item.to_dict() for item in self.items] if self.items else []
        }

@dataclass
class SalesReport:
    """نموذج تقرير المبيعات"""
    start_date: date
    end_date: date
    total_invoices: int = 0
    total_sales: float = 0.0
    total_paid: float = 0.0
    total_pending: float = 0.0
    invoices: List[Invoice] = None
    
    def __post_init__(self):
        if self.invoices is None:
            self.invoices = []
        if self.total_pending == 0.0:
            self.total_pending = self.total_sales - self.total_paid
    
    @property
    def average_invoice_value(self) -> float:
        """متوسط قيمة الفاتورة"""
        if self.total_invoices == 0:
            return 0
        return self.total_sales / self.total_invoices
    
    @property
    def payment_rate(self) -> float:
        """معدل الدفع"""
        if self.total_sales == 0:
            return 0
        return (self.total_paid / self.total_sales) * 100
    
    def to_dict(self) -> dict:
        """تحويل إلى قاموس"""
        return {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'total_invoices': self.total_invoices,
            'total_sales': self.total_sales,
            'total_paid': self.total_paid,
            'total_pending': self.total_pending,
            'average_invoice_value': self.average_invoice_value,
            'payment_rate': self.payment_rate,
            'invoices': [invoice.to_dict() for invoice in self.invoices]
        }

@dataclass
class InventoryReport:
    """نموذج تقرير المخزون"""
    total_products: int = 0
    total_quantity: int = 0
    total_value: float = 0.0
    low_stock_products: List[Product] = None
    out_of_stock_products: List[Product] = None
    products_by_category: dict = None
    
    def __post_init__(self):
        if self.low_stock_products is None:
            self.low_stock_products = []
        if self.out_of_stock_products is None:
            self.out_of_stock_products = []
        if self.products_by_category is None:
            self.products_by_category = {}
    
    @property
    def low_stock_count(self) -> int:
        """عدد المنتجات ذات المخزون المنخفض"""
        return len(self.low_stock_products)
    
    @property
    def out_of_stock_count(self) -> int:
        """عدد المنتجات غير المتوفرة"""
        return len(self.out_of_stock_products)
    
    @property
    def average_product_value(self) -> float:
        """متوسط قيمة المنتج"""
        if self.total_products == 0:
            return 0
        return self.total_value / self.total_products
    
    def to_dict(self) -> dict:
        """تحويل إلى قاموس"""
        return {
            'total_products': self.total_products,
            'total_quantity': self.total_quantity,
            'total_value': self.total_value,
            'low_stock_count': self.low_stock_count,
            'out_of_stock_count': self.out_of_stock_count,
            'average_product_value': self.average_product_value,
            'low_stock_products': [product.to_dict() for product in self.low_stock_products],
            'out_of_stock_products': [product.to_dict() for product in self.out_of_stock_products],
            'products_by_category': self.products_by_category
        }
