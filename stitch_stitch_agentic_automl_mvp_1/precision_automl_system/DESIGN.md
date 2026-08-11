---
name: Precision AutoML System
colors:
  surface: '#fbf9f8'
  surface-dim: '#dbdad9'
  surface-bright: '#fbf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3f3'
  surface-container: '#efeded'
  surface-container-high: '#e9e8e7'
  surface-container-highest: '#e4e2e2'
  on-surface: '#1b1c1c'
  on-surface-variant: '#424656'
  inverse-surface: '#303031'
  inverse-on-surface: '#f2f0f0'
  outline: '#727687'
  outline-variant: '#c2c6d8'
  surface-tint: '#0054d6'
  primary: '#0050cb'
  on-primary: '#ffffff'
  primary-container: '#0066ff'
  on-primary-container: '#f8f7ff'
  inverse-primary: '#b3c5ff'
  secondary: '#425ca0'
  on-secondary: '#ffffff'
  secondary-container: '#9bb4fe'
  on-secondary-container: '#294487'
  tertiary: '#a33200'
  on-tertiary: '#ffffff'
  tertiary-container: '#cc4204'
  on-tertiary-container: '#fff6f4'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae1ff'
  primary-fixed-dim: '#b3c5ff'
  on-primary-fixed: '#001849'
  on-primary-fixed-variant: '#003fa4'
  secondary-fixed: '#dae1ff'
  secondary-fixed-dim: '#b3c5ff'
  on-secondary-fixed: '#001849'
  on-secondary-fixed-variant: '#284386'
  tertiary-fixed: '#ffdbd0'
  tertiary-fixed-dim: '#ffb59d'
  on-tertiary-fixed: '#390c00'
  on-tertiary-fixed-variant: '#832600'
  background: '#fbf9f8'
  on-background: '#1b1c1c'
  surface-variant: '#e4e2e2'
typography:
  headline-sm:
    fontFamily: Hanken Grotesk
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-caps:
    fontFamily: Hanken Grotesk
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 12px
    letterSpacing: 0.05em
  data-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  data-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  max-width: 900px
  gutter: 16px
  margin: 24px
  row-height-compact: 32px
  stack-tight: 4px
  stack-base: 8px
---

## Brand & Style

This design system is engineered for technical rigor, clarity, and auditability. It is optimized for users who prioritize data integrity and systemic transparency over visual flourish. The aesthetic is a fusion of **Minimalism** and **Modern Corporate**, drawing inspiration from developer-centric tools that favor utility and high-information density.

The interface must evoke a sense of absolute precision. Every element exists to serve a functional purpose; there are no decorative illustrations, gradients, or blurs. The emotional response should be one of professional confidence and calm focus, allowing the user to audit complex automated workflows without visual fatigue.

## Colors

The palette is strictly functional, utilizing high contrast to drive legibility.

*   **Primary:** A singular Blue (#0066FF) used exclusively for primary actions and active states.
*   **Neutral:** A range of greys derived from the primary text color. Borders are consistent 1px hairlines using `#E5E5E5`. Secondary text uses `#666666`.
*   **Semantic:** Green, Amber, and Red are used for status indicators (Pass/Warn/Fail). These are applied to text and icons to ensure data auditability is immediate.
*   **Background:** Pure white (#FFFFFF) ensures maximum contrast for small-scale typography.

## Typography

Typography is the primary vehicle for information hierarchy. 

*   **Sans-Serif (Hanken Grotesk):** Used for all prose, labels, and UI controls. It provides a contemporary, sharp feel that remains legible at small scales.
*   **Monospace (JetBrains Mono):** Used for all technical data, including column names, dtypes, row counts, metrics, and code snippets. This separation helps users instantly distinguish between system UI and dataset content.
*   **Scale:** Avoid any font size over 20px. The design relies on weight and color rather than scale to denote importance.

## Layout & Spacing

The layout is a **Fixed Grid** model centered on the screen.

*   **Width:** The main content area is capped at 900px to maintain optimal line lengths for data tables and logs.
*   **Header:** A persistent 56px height header. The product name is left-aligned; a 5-step progress indicator is right-aligned.
*   **Density:** Vertical rhythm is tight. Use 8px increments for general spacing, but 4px for related technical metadata. List rows and table cells should target a 32px height to maximize information density.
*   **Adaptation:** On mobile, margins reduce to 16px, and the 900px container becomes fluid.

## Elevation & Depth

This system avoids traditional shadows and depth. Hierarchy is established through **Tonal Layers** and **Hairline Borders**.

*   **Borders:** All containers, cards, and input fields use a 1px solid border (#E5E5E5). 
*   **Surfaces:** Use a light grey background (#F9F9F9) for secondary containers (like code blocks or sidebars) to distinguish them from the primary white background.
*   **No Shadows:** Do not use box-shadows. Depth is purely architectural, created by the arrangement of bordered panels.

## Shapes

The shape language is conservative and geometric. 

*   **Radius:** All corners are capped at a maximum of 6px (`rounded-lg`). 
*   **Buttons & Inputs:** Use a 4px radius (`rounded-md`) for a sharp, technical appearance.
*   **Strictness:** Never use pill-shaped or fully rounded buttons. Maintain the rectangular integrity of the grid.

## Components

*   **Buttons:** Small padding (8px horizontal, 4px vertical). Primary buttons use #0066FF with white text. Secondary buttons use a white background and 1px hairline border.
*   **Data Tables:** No vertical borders between columns; use subtle horizontal dividers only. Column headers use `label-caps` in grey.
*   **Inputs:** Minimalist 1px borders. Active state is a 1px primary blue border—no outer glow or "halo" effects.
*   **Progress Indicator:** 5 steps shown as small circles or segments in the header. Completed steps are solid #111, the current step is #0066FF, and future steps are #E5E5E5.
*   **Chips/Badges:** Used for dtypes (e.g., `int64`, `float`). These use `data-sm` typography with a light grey background and no border.
*   **Audit Logs:** Monospace font, high density, with timestamps in grey. Successful agent actions are prefixed with a green 2px vertical bar.