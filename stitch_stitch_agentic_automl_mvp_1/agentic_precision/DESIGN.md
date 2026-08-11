---
name: Agentic Precision
colors:
  surface: '#f9f9ff'
  surface-dim: '#d3daea'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eefe'
  surface-container-high: '#e2e8f8'
  surface-container-highest: '#dce2f3'
  on-surface: '#151c27'
  on-surface-variant: '#424656'
  inverse-surface: '#2a313d'
  inverse-on-surface: '#ebf1ff'
  outline: '#727687'
  outline-variant: '#c2c6d8'
  surface-tint: '#0054d6'
  primary: '#0050cb'
  on-primary: '#ffffff'
  primary-container: '#0066ff'
  on-primary-container: '#f8f7ff'
  inverse-primary: '#b3c5ff'
  secondary: '#5b5e69'
  on-secondary: '#ffffff'
  secondary-container: '#e0e2ef'
  on-secondary-container: '#61646f'
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
  secondary-fixed: '#e0e2ef'
  secondary-fixed-dim: '#c4c6d2'
  on-secondary-fixed: '#181b24'
  on-secondary-fixed-variant: '#444651'
  tertiary-fixed: '#ffdbd0'
  tertiary-fixed-dim: '#ffb59d'
  on-tertiary-fixed: '#390c00'
  on-tertiary-fixed-variant: '#832600'
  background: '#f9f9ff'
  on-background: '#151c27'
  surface-variant: '#dce2f3'
  surface-background: '#F7F8FB'
  surface-card: '#FFFFFF'
  status-warning: '#FACC15'
  border-subtle: '#E5E7EB'
  data-mono: '#1D4ED8'
typography:
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  data-display:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: -0.01em
  data-code:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base-unit: 4px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 32px
  container-max: 1440px
---

## Brand & Style

This design system is engineered for **Agentic AutoML**, a high-performance platform where automated intelligence meets data science rigor. The brand personality is "The Expert Assistant"—highly capable, hyper-precise, and friction-free. It targets data scientists and ML engineers who require a "Pro" environment that balances executive-level clarity with technical depth.

The aesthetic follows a **Modern Minimalist** movement infused with **Technical Precision**. It prioritizes extreme legibility, a sophisticated use of "logical whitespace," and a monochromatic foundation that allows the primary blue accent to signal action and focus. The experience should feel like a high-end IDE—efficient, automated, and authoritative.

## Colors

The palette is strictly functional. We utilize a "High-Definition Neutral" base where `#F7F8FB` serves as the canvas, creating a soft contrast against pure white cards. 

- **Primary Blue (#0066FF):** Reserved exclusively for primary actions, active states, and automated progress indicators. It represents "The Agent" in motion.
- **Deep Slate (#151821):** Used for primary typography and heavy structural elements (like sidebars) to ground the interface.
- **Functional Accents:** Warning yellows are used sparingly for model drift or data quality alerts. 

The system operates primarily in a light mode that mimics professional white-paper reports, though the structure is architected to support a "Dim" high-contrast mode for long-duration technical tasks.

## Typography

Typography is used to distinguish between **Narrative** (Hanken Grotesk) and **Logic** (JetBrains Mono). 

- **Hanken Grotesk:** Applied to all UI controls, headings, and explanatory text. It provides a contemporary, approachable feel to complex operations.
- **JetBrains Mono:** Used for all data-driven elements, including model parameters, logs, code snippets, and table cell values. This visual separation allows users to instantly scan for technical data versus interface navigation.
- **Hierarchy:** Use bold weights for headers to maintain a strong information skeleton against the generous whitespace.

## Layout & Spacing

This design system employs a **Fixed-Fluid Hybrid Grid**. Sidebars and property panels are fixed-width to ensure tool consistency, while the central stage (the "Workbench") is fluid.

- **Grid:** A 12-column grid is used for dashboards, while a 4-column sub-grid handles form layouts.
- **Rhythm:** An 8px linear scale (4px, 8px, 16px, 24px, 32px, 48px, 64px) governs all padding and margins. 
- **Logical Grouping:** Use wide margins (32px+) between major sections to reduce cognitive load during complex ML workflows. On mobile, the grid collapses to a single column with a 16px safety margin.

## Elevation & Depth

We avoid heavy shadows in favor of **Tonal Layering** and **Micro-Borders**.

- **Surface 0 (Background):** #F7F8FB.
- **Surface 1 (Cards/Panels):** #FFFFFF with a 1px solid border (#E5E7EB).
- **Elevation:** Shadows are reserved for ephemeral elements only (dropdowns, modals). Use a "Natural Ambient" shadow: `0px 4px 12px rgba(0, 0, 0, 0.05)`.
- **Interactive Depth:** On hover, cards do not lift; instead, the border color transitions to the Primary Blue or a darker neutral. This maintains the "Precision" feel—stability over motion.

## Shapes

The shape language is **Soft-Geometric**. We use a 4px (0.25rem) standard radius for buttons and inputs to maintain a crisp, professional edge. Larger containers like cards may use up to 8px (0.5rem) to feel modern, but never "bubbly."

- **Inputs/Buttons:** 4px radius.
- **Cards/Modals:** 8px radius.
- **Data Tags:** 2px radius (near-sharp) to emphasize technical precision.

## Components

- **Buttons:** Primary buttons use a solid #0066FF fill with white Hanken Grotesk text. Secondary buttons use a ghost style with a subtle border.
- **Data Inputs:** Modern, "Elixai-inspired" inputs. Use a transition where the label floats or the border thickens on focus. Use JetBrains Mono for the input text itself.
- **Status Chips:** Small, square-edged tags for "Training," "Deployed," or "Failed." Use a light-tint background of the status color with high-contrast text.
- **Monospace Tables:** Data tables are the core of the tool. Use subtle zebra-striping and JetBrains Mono for all cell content. Headers remain Hanken Grotesk Bold.
- **Progress Indicators:** Use thin, high-precision loading bars in Primary Blue. Avoid playful animations; use smooth, linear transitions that suggest mechanical efficiency.
- **Model Cards:** Use a consistent header layout with the model name in Hanken Grotesk and its accuracy metrics in JetBrains Mono.