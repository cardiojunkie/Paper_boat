---
name: PickPilot
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#3d4947'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#6d7a77'
  outline-variant: '#bcc9c6'
  surface-tint: '#006a61'
  primary: '#00685f'
  on-primary: '#ffffff'
  primary-container: '#008378'
  on-primary-container: '#f4fffc'
  inverse-primary: '#6bd8cb'
  secondary: '#565e74'
  on-secondary: '#ffffff'
  secondary-container: '#dae2fd'
  on-secondary-container: '#5c647a'
  tertiary: '#4d5d73'
  on-tertiary: '#ffffff'
  tertiary-container: '#66768d'
  on-tertiary-container: '#fdfcff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#89f5e7'
  primary-fixed-dim: '#6bd8cb'
  on-primary-fixed: '#00201d'
  on-primary-fixed-variant: '#005049'
  secondary-fixed: '#dae2fd'
  secondary-fixed-dim: '#bec6e0'
  on-secondary-fixed: '#131b2e'
  on-secondary-fixed-variant: '#3f465c'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display-sm:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-xs:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
  mono-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  container-max: 1440px
  sidebar-width: 240px
  gutter: 16px
  cell-padding-x: 12px
  cell-padding-y: 8px
  stack-gap: 20px
---

## Brand & Style
The design system is engineered for high-performance internal operations. It prioritizes clarity, speed of data ingestion, and emotional stability through a "Calm-Dense" aesthetic. The personality is utilitarian and professional, avoiding decorative elements in favor of functional precision.

The style is **Corporate / Modern** with a focus on structural integrity. It utilizes a white-label foundation with a "table-first" philosophy, meaning every component is designed to coexist with complex datasets without adding visual noise. The aesthetic relies on strict alignment, consistent stroke weights, and a restrained use of color to highlight actionable data.

## Colors
The palette is dominated by neutrals to keep the user’s focus on inventory and order data. 

- **Primary (Deep Teal):** Reserved for primary actions, active navigation states, and key progress indicators.
- **Surface Neutrals:** Uses a scale of cool grays. Backgrounds stay at `#FFFFFF` or `#F8FAFC` to maximize contrast with text.
- **Functional Semantic Colors:** Standardized Red (Danger), Amber (Warning), and Emerald (Success) are used exclusively for status pills and destructive actions.
- **Borders:** A consistent `#E2E8F0` is used for all structural divisions to maintain a crisp, organized appearance.

## Typography
This design system uses **Inter** for its neutral, highly legible glyphs, which excel in dense UI environments. 

- **Data Density:** The default body size is 14px, but 13px is used for data tables to increase row capacity.
- **Hierarchy:** Contrast is created through weight (SemiBold/600) rather than large scale jumps to keep the interface compact.
- **Monospacing:** Use JetBrains Mono for SKU numbers, tracking codes, and quantities to ensure character alignment in tables.
- **Labels:** Uppercase is avoided except for very small `label-xs` tags to maintain a calm, readable tone.

## Layout & Spacing
The layout follows a **Fixed-Fluid Hybrid** model. The sidebar remains fixed while the main workspace expands.

- **Desktop (1280px+):** A two-column workspace. The left sidebar is a narrow 240px. The main content area uses a 12-column grid with 16px gutters.
- **Mobile (<768px):** The sidebar collapses into a bottom navigation bar or a hamburger menu. Data tables become horizontally scrollable cards or simplified lists.
- **Information Density:** Vertical rhythm is tight. Component padding follows a 4px baseline, with standard button heights set to 32px or 36px to maximize vertical screen real estate.

## Elevation & Depth
This design system uses **Tonal Layers** and **Low-Contrast Outlines** instead of heavy shadows to maintain a flat, professional look.

- **Level 0 (Base):** `#F8FAFC` background.
- **Level 1 (Panels/Cards):** White (`#FFFFFF`) with a 1px solid border of `#E2E8F0`. 
- **Level 2 (Dropdowns/Modals):** White background with a subtle, tight shadow: `0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)`.
- **Dividers:** Use 1px borders rather than shadows to separate table rows and header sections.

## Shapes
The shape language is **Soft** but disciplined. 

- **Standard Radius:** 4px (`0.25rem`) for buttons, input fields, and small cards. This provides a modern feel without looking "bubbly."
- **Outer Containers:** Larger panels and modals use 8px (`0.5rem`) to provide a clear nesting visual.
- **Status Pills:** Use a fully rounded (capsule) shape to distinguish status indicators from clickable buttons.

## Components
- **Data Tables:** The core of the system. Use 13px text, 8px vertical cell padding, and hover states with a subtle grey background (`#F1F5F9`). Headers are sticky with a bottom border.
- **Buttons:**
    - *Primary:* Solid Deep Teal (#0D9488) with white text.
    - *Secondary:* White background, `#E2E8F0` border, `#475569` text.
    - *Danger:* Solid Red (#DC2626) only used in confirmation modals.
- **Status Pills:** Small, bold labels with low-opacity backgrounds. (e.g., Success: Emerald 100 bg, Emerald 700 text).
- **Input Fields:** 1px `#CBD5E1` border, changing to `#0D9488` on focus. Height is restricted to 32px for dense forms.
- **Filter Bar:** A horizontal strip above tables using "Ghost" buttons for filter triggers and visible "Clear All" text links.
- **Danger Modal:** Centered, white, 8px radius, featuring a prominent warning icon and a primary Red action button.