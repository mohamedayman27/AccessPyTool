# Overview

This is a restaurant and hotel equipment management system called "الخليفة" (Al-Khalifa) built with Streamlit. The application provides comprehensive business management features including invoice management, customer relationship management, inventory control, returns processing, and reporting capabilities. The system is designed for Arabic-speaking users in the hospitality industry, featuring bilingual support and localized formatting.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture

**Framework**: Streamlit web framework
- **Rationale**: Streamlit provides rapid development of data-driven applications with minimal frontend code
- **Multi-page navigation**: Sidebar-based navigation system with sections for Dashboard, Invoices, Customers, Inventory, Returns, and Reports
- **State Management**: Uses Streamlit's session_state for managing temporary data like current invoice items
- **Caching Strategy**: Implements `@st.cache_resource` for database connections to optimize performance

**UI Design Patterns**:
- Wide layout configuration for better data visualization
- Column-based layouts for statistics and forms
- Right-to-left (RTL) text support for Arabic language
- Responsive design with expandable sidebar

## Backend Architecture

**Core Components**:
1. **Models Layer** (`models.py`): Data classes using Python dataclasses
   - Customer, Product, Invoice, InvoiceItem entities
   - Built-in validation and data transformation methods
   - Dictionary conversion for database operations

2. **Database Layer** (`database.py`): DatabaseManager class
   - Abstraction layer for SQLite operations
   - Handles CRUD operations for all entities
   - Query execution and connection management

3. **Business Logic** (`utils.py`): Utility functions
   - Currency and number formatting (Arabic locale support)
   - Date/time formatting with Arabic month names
   - Stock level calculations and alerts
   - Customer balance calculations

4. **Export Layer** (`export_utils.py`): Document generation
   - Excel export using pandas and openpyxl
   - PDF generation with ReportLab for invoices
   - Arabic text rendering support
   - Custom styling for professional documents

## Data Storage

**Database**: SQLite
- **Choice Rationale**: Lightweight, serverless database suitable for small to medium businesses
- **Schema Design**: Relational structure with entities for customers, products, invoices, and invoice items
- **Benefits**: Zero configuration, file-based storage, ACID compliance
- **Considerations**: Single-user access, suitable for desktop deployment

**Data Models**:
- Customer tracking with contact information and company details
- Product inventory with SKU, pricing, and stock levels
- Invoice system with line items and customer associations
- Minimum stock levels for inventory alerts

## Authentication and Authorization

Currently no authentication system implemented. The application appears to be designed for single-user or trusted environment usage.

## External Dependencies

**Core Framework**:
- **Streamlit**: Web application framework for Python
- **Purpose**: Provides UI components and application structure

**Data Processing**:
- **Pandas**: Data manipulation and Excel export
- **Purpose**: DataFrame operations and structured data handling

**Document Generation**:
- **ReportLab**: PDF generation library
- **Purpose**: Creating professional invoices and reports with Arabic support
- **openpyxl**: Excel file handling
- **Purpose**: Excel export functionality

**Database**:
- **SQLite3**: Built-in Python database
- **Purpose**: Persistent data storage

**Date/Time Handling**:
- **datetime**: Python standard library
- **Purpose**: Date and time operations with locale support

**Numeric Operations**:
- **decimal.Decimal**: Precision arithmetic
- **Purpose**: Accurate financial calculations