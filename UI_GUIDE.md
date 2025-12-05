# Visual UI Guide - Facturas Pro Modern Dashboard

## Layout Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Facturas Pro - Dashboard Moderno                                      │
├──────────┬──────────────────────────────────────────────────────────────┤
│          │  Archivo  Reportes  Herramientas  Opciones                  │
├──────────┼──────────────────────────────────────────────────────────────┤
│          │                                                              │
│ SIDEBAR  │  HEADER:  Resumen Financiero        [+ Nueva Factura]       │
│ (250px)  │                                                              │
│          ├──────────────────────────────────────────────────────────────┤
│ F        │                                                              │
│ Facturas │  FILTERS:  [Mes: Octubre ▼] [Año: 2025 ▼]                  │
│ Pro      │            [Aplicar Filtro]  [Ver Todo]                     │
│          │                                                              │
│ ┌──────┐ ├──────────────────────────────────────────────────────────────┤
│ │EMPRESA│ │                                                              │
│ │ACTIVA │ │  KPI CARDS (4 cards in a row):                             │
│ └──────┘ │                                                              │
│          │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐
│ Zoec     │  │ TOTAL       │ │ TOTAL       │ │ ITBIS       │ │ A PAGAR  │
│ Civil ▼  │  │ INGRESOS    │ │ GASTOS      │ │ NETO        │ │ ESTIMADO │
│          │  │             │ │             │ │             │ │          │
│ ┌──────┐ │  │ RD$ 1.2M    │ │ RD$ 450K    │ │ RD$ 144K    │ │ RD$ 144K │
│ │📊     │ │  │ ITBIS: 225K │ │ ITBIS: 81K  │ │ Diferencia  │ │ Input    │
│ │Dashbo-│ │  └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘
│ │ard   ││                                                              │
│ └──────┘ ├──────────────────────────────────────────────────────────────┤
│          │                                                              │
│ ┌──────┐ │  TRANSACTIONS TABLE:                                         │
│ │💰     │ │  Transacciones Recientes    [Todos] [Ingresos] [Gastos]    │
│ │Ingre- │ │                                                              │
│ │sos   ││  ┌──────────┬────────┬────────────┬─────────┬────────┬──────┐
│ └──────┘ │  │ Fecha    │ Tipo   │ No. Fact.  │ Empresa │ ITBIS  │Total │
│          │  ├──────────┼────────┼────────────┼─────────┼────────┼──────┤
│ ┌──────┐ │  │2025-10-14│INGRESO │E3100000239 │Barnhouse│ 12,000 │78,000│
│ │🛒     │ │  │2025-10-12│ GASTO  │B0100005512 │Ferretería│  450  │2,950 │
│ │Gastos││  │2025-10-10│INGRESO │E3100000238 │Cliente  │ 9,000  │59,000│
│ └──────┘ │  └──────────┴────────┴────────────┴─────────┴────────┴──────┘
│          │                                                              │
│ ┌──────┐ │                                                              │
│ │💹     │ │                                                              │
│ │Calc.  │ │                                                              │
│ │Impues-│ │                                                              │
│ │tos   ││                                                              │
│ └──────┘ │                                                              │
│          │                                                              │
│ ┌──────┐ │                                                              │
│ │📈     │ │                                                              │
│ │Report-│ │                                                              │
│ │es    ││                                                              │
│ └──────┘ │                                                              │
│          │                                                              │
│ ─────────│                                                              │
│          │                                                              │
│ ┌──────┐ │                                                              │
│ │⚙️     │ │                                                              │
│ │Config-│ │                                                              │
│ │uracio │ │                                                              │
│ └──────┘ │                                                              │
└──────────┴──────────────────────────────────────────────────────────────┘
```

## Color Scheme

### Sidebar (Dark Theme)
- **Background:** `#1E293B` (Slate 900)
- **Text:** `#FFFFFF` (White)
- **Hover:** `#334155` (Slate 700)
- **Active:** `#3B82F6` (Blue 500)
- **Dropdown:** `#334155` (Slate 700)

### Content Area (Light Theme)
- **Background:** `#F8F9FA` (Gray 50)
- **Cards:** `#FFFFFF` (White)
- **Border:** `#E2E8F0` (Gray 200)
- **Text Primary:** `#1E293B` (Slate 900)
- **Text Secondary:** `#64748B` (Slate 500)

### Accent Colors
- **Primary Button:** `#1E293B` → `#334155` (hover)
- **Income Badge:** `#10B981` (Green 500) on `#DCFCE7` (Green 100)
- **Expense Badge:** `#EF4444` (Red 500) on `#FEE2E2` (Red 100)
- **ITBIS Neto:** `#3B82F6` (Blue 500)
- **A Pagar:** `#F59E0B` (Orange 500)

## Components Detail

### Sidebar Navigation Buttons

```
┌────────────────────┐
│ 📊  Dashboard      │  ← Active (Blue background)
├────────────────────┤
│ 💰  Ingresos       │  ← Hover (Dark gray)
├────────────────────┤
│ 🛒  Gastos         │  ← Normal (Transparent)
├────────────────────┤
│ 💹  Calc. Impuestos│
├────────────────────┤
│ 📈  Reportes       │
└────────────────────┘
```

**States:**
- **Normal:** Transparent, gray text (#94A3B8)
- **Hover:** Dark background (#334155), white text
- **Active:** Blue background (#3B82F6), white text, bold

### KPI Card Layout

```
┌─────────────────────────┐
│ TOTAL INGRESOS         │  ← Title (uppercase, small, gray)
│                         │
│ RD$ 1,250,000.00       │  ← Value (large, bold, dark)
│                         │
│ ITBIS: RD$ 225,000.00  │  ← Subtitle (small, light gray)
│                         │
│ ▓▓▓▓▓▓▓▓░░░░           │  ← Progress bar (optional)
└─────────────────────────┘
```

**Style:**
- Border: 1px solid #E2E8F0
- Border radius: 12px
- Padding: 20px
- Background: White
- Shadow: subtle (rgba(0,0,0,0.05))

### Transaction Type Badges

**Income Badge:**
```
┌─────────┐
│ INGRESO │  Green text (#166534) on light green (#DCFCE7)
└─────────┘
```

**Expense Badge:**
```
┌───────┐
│ GASTO │  Red text (#991B1B) on light red (#FEE2E2)
└───────┘
```

**Style:**
- Border radius: 12px
- Padding: 4px 12px
- Font weight: 600
- Font size: 11px
- Uppercase

### Table Design

```
┌────────────────────────────────────────────────────────────┐
│ FECHA      │ TIPO    │ NO. FACT.  │ EMPRESA   │ ITBIS │ ... │  ← Header
├────────────┼─────────┼────────────┼───────────┼───────┼─────┤    (Gray bg)
│ 2025-10-14 │ INGRESO │ E310000239 │ Barnhouse │ 12,000│ ... │
├────────────┼─────────┼────────────┼───────────┼───────┼─────┤
│ 2025-10-12 │  GASTO  │ B010000512 │ Ferretería│   450 │ ... │  ← Alternate
└────────────┴─────────┴────────────┴───────────┴───────┴─────┘    (Light gray)
```

**Features:**
- No vertical gridlines
- Horizontal lines only (#F1F5F9)
- Alternating row colors
- Selection: light blue (#EFF6FF)
- Header: uppercase, gray background
- Padding: 12px 16px per cell

## Typography

### Font Family
- **Primary:** "Inter", "Segoe UI", "Roboto", sans-serif
- **Monospace:** "Consolas", "Courier New" (for logs)

### Font Sizes
- **Logo:** 20px, bold
- **App Name:** 18px, semi-bold
- **Page Title:** 20px, bold
- **Section Title:** 14px, semi-bold
- **KPI Title:** 12px, medium, uppercase
- **KPI Value:** 24px, bold
- **KPI Subtitle:** 11px
- **Table Header:** 12px, semi-bold, uppercase
- **Table Cell:** 14px
- **Button:** 13-14px, medium
- **Nav Button:** 14px

### Font Weights
- **Light:** 300
- **Regular:** 400
- **Medium:** 500
- **Semi-bold:** 600
- **Bold:** 700

## Spacing

### Padding
- **Sidebar:** 20px top/bottom, 16px sides
- **Content:** 32px all sides
- **Cards:** 20px all sides
- **Table cells:** 12px vertical, 16px horizontal
- **Buttons:** 10-12px vertical, 16-20px horizontal

### Margins
- **Between sections:** 24px
- **Between cards:** 16px
- **Between rows:** 4px (nav)

### Border Radius
- **Cards:** 12px
- **Buttons:** 8px
- **Badges:** 12px
- **Inputs:** 8px
- **Logo:** 8px

## Responsive Behavior

### Fixed Widths
- **Sidebar:** 250px (fixed)
- **Header Height:** 70px (fixed)
- **Filter Bar:** Max 60px

### Flexible
- **Content Area:** Expands to fill remaining width
- **KPI Cards:** Flex layout, equal width
- **Table:** 100% width of container

## Icons

### With qtawesome (if installed)
- Dashboard: `fa5s.chart-pie`
- Ingresos: `fa5s.file-invoice-dollar`
- Gastos: `fa5s.shopping-cart`
- Calc. Impuestos: `fa5s.percent`
- Reportes: `fa5s.chart-line`
- Configuración: `fa5s.cog`

### Fallback (emoji)
- Dashboard: 📊
- Ingresos: 💰
- Gastos: 🛒
- Calc. Impuestos: 💹
- Reportes: 📈
- Configuración: ⚙️

## Interactive States

### Buttons
- **Normal:** Background color + border
- **Hover:** Darker background, no delay
- **Active/Pressed:** Slightly darker
- **Disabled:** 50% opacity, no pointer

### Links/Nav Items
- **Normal:** Gray text
- **Hover:** White text, dark background
- **Active:** Blue background, white text

### Table Rows
- **Normal:** White/light gray alternating
- **Hover:** Subtle highlight
- **Selected:** Light blue (#EFF6FF)

## Accessibility

### Contrast Ratios
- **Text on white:** ≥4.5:1 (AA standard)
- **Text on dark sidebar:** ≥7:1 (AAA standard)
- **Badges:** High contrast (6:1+)

### Focus Indicators
- Keyboard navigation supported
- Focus ring on interactive elements
- Tab order logical (top to bottom, left to right)

### Screen Readers
- Semantic HTML structure
- Labels for all inputs
- Alt text for icons (via tooltips)
- ARIA labels where needed

## Animations (Future)

### Current
- **Hover transitions:** 0.2s ease
- **No animations** on data updates (instant)

### Planned (Optional)
- Smooth scrolling
- Card appearance animation
- Progress bar animation
- Toast notifications

---

This guide provides a visual reference for the modern dashboard UI design and can be used for:
- Frontend development
- UI/UX review
- Design consistency checks
- Accessibility audits
- Future enhancements
