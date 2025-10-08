import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from datetime import datetime
import io
from typing import List, Dict, Any

def export_to_excel(data: List[Dict[str, Any]], filename: str, sheet_name: str = "البيانات") -> bytes:
    """تصدير البيانات إلى ملف Excel"""
    df = pd.DataFrame(data)
    
    # إنشاء ملف Excel في الذاكرة
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    output.seek(0)
    return output.getvalue()

def create_invoice_pdf(invoice_data: Dict[str, Any], items: List[Dict[str, Any]], customer_data: Dict[str, Any]) -> bytes:
    """إنشاء فاتورة PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # العناصر التي ستضاف للـ PDF
    elements = []
    
    # الأنماط
    styles = getSampleStyleSheet()
    
    # نمط للعنوان الرئيسي
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # نمط للنصوص العربية
    arabic_style = ParagraphStyle(
        'Arabic',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_RIGHT,
        fontName='Helvetica'
    )
    
    # العنوان الرئيسي
    elements.append(Paragraph("INVOICE - فاتورة", title_style))
    elements.append(Spacer(1, 12))
    
    # معلومات الفاتورة
    invoice_info = [
        [f"Invoice Number: {invoice_data.get('id', 'N/A')}", f"Date: {invoice_data.get('date', 'N/A')}"],
    ]
    
    invoice_table = Table(invoice_info, colWidths=[3*inch, 3*inch])
    invoice_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 12))
    
    # معلومات العميل
    customer_info = [
        ["Customer Information"],
        [f"Name: {customer_data.get('name', 'N/A')}"],
        [f"Phone: {customer_data.get('phone', 'N/A')}"],
    ]
    
    if customer_data.get('company'):
        customer_info.append([f"Company: {customer_data.get('company')}"])
    
    customer_table = Table(customer_info, colWidths=[6*inch])
    customer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(customer_table)
    elements.append(Spacer(1, 20))
    
    # جدول المنتجات
    items_data = [["Product", "Quantity", "Price", "Total"]]
    
    for item in items:
        items_data.append([
            item.get('product_name', 'N/A'),
            str(item.get('quantity', 0)),
            f"{item.get('price', 0):.2f} EGP",
            f"{item.get('total', 0):.2f} EGP"
        ])
    
    items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 20))
    
    # الإجماليات
    totals_data = [
        ["Total Amount:", f"{invoice_data.get('total_amount', 0):.2f} EGP"],
        ["Paid Amount:", f"{invoice_data.get('paid_amount', 0):.2f} EGP"],
        ["Remaining Amount:", f"{invoice_data.get('remaining_amount', 0):.2f} EGP"],
    ]
    
    totals_table = Table(totals_data, colWidths=[4*inch, 2*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
    ]))
    elements.append(totals_table)
    
    # بناء الـ PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer.getvalue()

def create_sales_report_pdf(sales_data: Dict[str, Any], start_date, end_date) -> bytes:
    """إنشاء تقرير مبيعات PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # العنوان
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    elements.append(Paragraph("Sales Report - تقرير المبيعات", title_style))
    elements.append(Spacer(1, 12))
    
    # فترة التقرير
    period_info = [
        [f"Report Period: {start_date} to {end_date}"],
        [f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
    ]
    
    period_table = Table(period_info, colWidths=[6*inch])
    period_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(period_table)
    elements.append(Spacer(1, 20))
    
    # الإحصائيات الرئيسية
    stats_data = [
        ["Total Invoices", str(sales_data.get('total_invoices', 0))],
        ["Total Sales", f"{sales_data.get('total_sales', 0):.2f} EGP"],
        ["Total Paid", f"{sales_data.get('total_paid', 0):.2f} EGP"],
        ["Pending Amount", f"{sales_data.get('total_sales', 0) - sales_data.get('total_paid', 0):.2f} EGP"],
    ]
    
    stats_table = Table(stats_data, colWidths=[3*inch, 3*inch])
    stats_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f2f6')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 20))
    
    # جدول الفواتير
    if sales_data.get('invoices'):
        invoices_data = [["Invoice #", "Customer", "Date", "Total", "Paid"]]
        
        for invoice in sales_data['invoices']:
            invoices_data.append([
                str(invoice.get('id', '')),
                invoice.get('customer_name', 'N/A'),
                str(invoice.get('date', '')),
                f"{invoice.get('total_amount', 0):.2f}",
                f"{invoice.get('paid_amount', 0):.2f}"
            ])
        
        invoices_table = Table(invoices_data, colWidths=[0.8*inch, 2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        invoices_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(invoices_table)
    
    doc.build(elements)
    
    buffer.seek(0)
    return buffer.getvalue()

def create_inventory_report_pdf(products: List[Dict[str, Any]]) -> bytes:
    """إنشاء تقرير مخزون PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # العنوان
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    elements.append(Paragraph("Inventory Report - تقرير المخزون", title_style))
    elements.append(Spacer(1, 12))
    
    # تاريخ التقرير
    date_info = [[f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}"]]
    date_table = Table(date_info, colWidths=[6*inch])
    date_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
    ]))
    elements.append(date_table)
    elements.append(Spacer(1, 20))
    
    # حساب الإحصائيات
    total_products = len(products)
    total_value = sum(p.get('price', 0) * p.get('quantity', 0) for p in products)
    low_stock = sum(1 for p in products if p.get('quantity', 0) <= p.get('min_stock', 0))
    
    stats_data = [
        ["Total Products", str(total_products)],
        ["Total Inventory Value", f"{total_value:.2f} EGP"],
        ["Low Stock Items", str(low_stock)],
    ]
    
    stats_table = Table(stats_data, colWidths=[3*inch, 3*inch])
    stats_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f2f6')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 20))
    
    # جدول المنتجات
    products_data = [["Product", "SKU", "Category", "Price", "Quantity", "Value"]]
    
    for product in products:
        value = product.get('price', 0) * product.get('quantity', 0)
        products_data.append([
            product.get('name', 'N/A'),
            product.get('sku', 'N/A'),
            product.get('category', 'N/A'),
            f"{product.get('price', 0):.2f}",
            str(product.get('quantity', 0)),
            f"{value:.2f}"
        ])
    
    products_table = Table(products_data, colWidths=[1.8*inch, 0.8*inch, 1*inch, 0.9*inch, 0.8*inch, 0.9*inch])
    products_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(products_table)
    
    doc.build(elements)
    
    buffer.seek(0)
    return buffer.getvalue()
