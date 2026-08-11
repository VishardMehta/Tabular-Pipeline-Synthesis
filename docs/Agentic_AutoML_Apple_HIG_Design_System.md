# Apple-Inspired Human Interface Design System

## Design specification for the Agentic AutoML web application

**Purpose:** A practical, implementation-ready design guide for building
a polished web application inspired by Apple's Human Interface
Guidelines (HIG), while adapting the principles to a desktop/web
data-science product.

**Source basis:** Apple's current Human Interface Guidelines and Apple
Design Resources, researched August 2026. This document summarizes and
operationalizes Apple's guidance; it is not a reproduction of Apple's
copyrighted documentation.

**Primary official references** - Human Interface Guidelines:
https://developer.apple.com/design/human-interface-guidelines/ - Apple
Design Resources: https://developer.apple.com/design/resources/ - Apple
design principles:
https://developer.apple.com/design/human-interface-guidelines/design-principles -
Layout:
https://developer.apple.com/design/human-interface-guidelines/layout -
Typography:
https://developer.apple.com/design/human-interface-guidelines/typography -
Color:
https://developer.apple.com/design/human-interface-guidelines/color -
Materials:
https://developer.apple.com/design/human-interface-guidelines/materials -
Dark Mode:
https://developer.apple.com/design/human-interface-guidelines/dark-mode -
Search fields:
https://developer.apple.com/design/human-interface-guidelines/search-fields -
Sidebars:
https://developer.apple.com/design/human-interface-guidelines/sidebars -
Menus:
https://developer.apple.com/design/human-interface-guidelines/menus - SF
Symbols:
https://developer.apple.com/design/human-interface-guidelines/sf-symbols -
SF Symbols product page: https://developer.apple.com/sf-symbols/ - Apple
fonts: https://developer.apple.com/fonts/

------------------------------------------------------------------------

# 1. Design north star

The design should feel:

-   **Clear:** users immediately understand what is happening and what
    they can do next.
-   **Calm:** avoid visual noise, excessive borders, unnecessary
    gradients, and competing calls to action.
-   **Precise:** data and technical information should feel trustworthy
    and deliberate.
-   **Hierarchical:** primary content should visually dominate secondary
    metadata.
-   **Responsive:** the interface should adapt rather than merely
    shrink.
-   **Human:** use concise language, meaningful feedback, and
    predictable interactions.
-   **Premium:** polish comes from spacing, typography, consistency,
    motion, and restraint---not decoration.

Apple's current design principles emphasize **Purpose, Flexibility,
Simplicity, Craft, and Delight**. Apply these as decision criteria
rather than as a visual theme.

For this product:

> Purpose = help a user move from raw CSV to an understandable ML
> pipeline.
>
> Flexibility = work across desktop widths and different data sizes.
>
> Simplicity = expose only the information needed for the current
> decision.
>
> Craft = make every state, transition, warning, and code interaction
> deliberate.
>
> Delight = make technically complex ML work feel approachable.

------------------------------------------------------------------------

# 2. Do not "make it look like Apple"

The goal is not to copy Apple's product UI.

Do not blindly copy: - Apple's exact app layouts - proprietary artwork -
Apple product screenshots - Apple logos - Apple trademarks - exact
component styling where it has no functional reason

Instead, use the underlying principles:

1.  strong information hierarchy
2.  semantic color
3.  generous but purposeful spacing
4.  adaptive layout
5.  system-like typography
6.  restrained materials
7.  familiar controls
8.  accessibility
9.  meaningful motion
10. progressive disclosure

The resulting application should look like **a premium native-quality
data product**, not an Apple clone.

------------------------------------------------------------------------

# 3. Design language for Agentic AutoML

## 3.1 Product personality

The application should feel like:

> **Apple-level clarity + modern developer tooling + scientific
> precision.**

Avoid making it resemble: - a generic AI chatbot - a dashboard
overloaded with cards - an enterprise BI product from 2015 - a neon "AI"
landing page - a crypto dashboard - a conventional AutoML leaderboard

The product should communicate:

**"This system understands my data and explains what it is doing."**

------------------------------------------------------------------------

# 4. Design tokens

Create a token layer before writing components.

Suggested token structure:

``` css
:root {
  /* Surfaces */
  --color-bg: ...;
  --color-surface: ...;
  --color-surface-secondary: ...;
  --color-surface-elevated: ...;

  /* Text */
  --color-text-primary: ...;
  --color-text-secondary: ...;
  --color-text-tertiary: ...;
  --color-text-disabled: ...;

  /* Semantic */
  --color-accent: ...;
  --color-success: ...;
  --color-warning: ...;
  --color-error: ...;
  --color-info: ...;

  /* Borders */
  --color-separator: ...;
  --color-border: ...;

  /* Radius */
  --radius-small: ...;
  --radius-medium: ...;
  --radius-large: ...;

  /* Shadows */
  --shadow-small: ...;
  --shadow-medium: ...;

  /* Spacing */
  --space-1: ...;
  --space-2: ...;
  --space-3: ...;
  --space-4: ...;
  --space-5: ...;
  --space-6: ...;
  --space-8: ...;
  --space-10: ...;
  --space-12: ...;

  /* Motion */
  --duration-fast: ...;
  --duration-normal: ...;
  --duration-slow: ...;
}
```

Do not hard-code dozens of unrelated values.

A small token system creates consistency across the entire product.

------------------------------------------------------------------------

# 5. Color system

Apple recommends using color deliberately for communication, hierarchy,
continuity, status, and feedback.

## 5.1 Primary palette

Do not choose a color simply because it "looks Apple."

For this application, use a restrained neutral foundation and one accent
color.

Recommended conceptual palette:

``` text
Background
  near-white / very light neutral

Primary surface
  white

Secondary surface
  very light neutral

Primary text
  near-black

Secondary text
  muted gray

Tertiary text
  lighter gray

Accent
  one strong blue/purple/indigo family

Success
  green

Warning
  amber/orange

Error
  red

Info
  blue
```

The exact hex values should be selected after checking contrast.

## 5.2 Semantic colors

Never use the same color to mean unrelated things.

For example:

``` text
green  = successful / passed
yellow = attention / warning
red    = failure / destructive
blue   = interactive / informational
```

Do not use red merely because it looks attractive.

## 5.3 Color should not be the only signal

Bad:

``` text
[red dot] Failed
```

Better:

``` text
[error icon] Failed
```

with: - icon - label - supporting text

This helps color-blind users and improves comprehension.

## 5.4 Dark mode

Dark mode must not be implemented by simply inverting colors.

Use semantic tokens:

``` text
Light:
background → light
primary text → dark

Dark:
background → dark
primary text → light
```

The semantic role stays the same.

Do not create an app-level "Dark Mode" switch if the product is intended
to behave like a native Apple-style application. Respect the user's
system/browser preference.

For a web implementation:

``` css
@media (prefers-color-scheme: dark) {
  ...
}
```

Use adaptive colors rather than hard-coded assumptions.

Apple's HIG recommends sufficient contrast and notes a minimum contrast
ratio of 4.5:1; for custom foreground/background combinations, it
recommends striving for stronger contrast, particularly for small text.

------------------------------------------------------------------------

# 6. Typography

Typography is one of the biggest contributors to perceived quality.

Apple's system typography centers around San Francisco and its
text-style hierarchy.

For a web application, use:

``` css
font-family:
  -apple-system,
  BlinkMacSystemFont,
  "SF Pro Display",
  "SF Pro Text",
  "Segoe UI",
  sans-serif;
```

If the application is primarily used on Apple hardware, `-apple-system`
gives the browser a native system-font experience.

## 6.1 Typography hierarchy

Do not create 15 arbitrary font sizes.

Use semantic roles:

``` text
Display
Large title
Title
Section heading
Body
Body emphasized
Secondary
Caption
Code
```

Example web token system:

``` text
display       48–56px
large-title   32–40px
title         24–28px
heading       18–20px
body          15–17px
secondary     13–15px
caption       11–13px
```

These are implementation suggestions, not Apple-mandated web values.

## 6.2 Weight

Use weight to create hierarchy, not decoration.

Suggested:

``` text
Display        600
Large title    600
Title          600
Heading        600
Body           400
Emphasized     500/600
Secondary      400
Caption        400/500
```

Avoid making everything bold.

## 6.3 Line height

Body text needs comfortable reading rhythm.

Use approximately:

``` text
Body:      1.45–1.6
Secondary: 1.4–1.5
Headings:  1.15–1.3
```

## 6.4 Text width

Long paragraphs should not span the entire browser window.

For explanatory text:

``` css
max-width: 65ch;
```

This makes technical explanations significantly easier to read.

## 6.5 Code typography

Use a monospaced font for generated Python:

``` css
font-family:
  "SF Mono",
  ui-monospace,
  "Cascadia Code",
  "Roboto Mono",
  monospace;
```

Use code typography only for: - Python - file paths - API routes -
technical identifiers - metric names where appropriate

Do not turn the entire application into a developer terminal.

------------------------------------------------------------------------

# 7. Layout

Apple's HIG emphasizes consistent layouts that adapt to different
contexts.

## 7.1 Core layout principle

Think in layers:

``` text
Window
 ├── Navigation layer
 ├── Toolbar / controls
 └── Content layer
```

Do not treat every element as a card.

## 7.2 Content width

For a desktop web application:

``` text
Full viewport
    ↓
application shell
    ↓
content region
    ↓
readable maximum width
```

Suggested:

``` css
max-width: 1440px;
margin-inline: auto;
padding-inline: 24px–48px;
```

For dense technical screens, allow wider content.

For narrative/strategy content, constrain the text width.

## 7.3 Spacing

Use an 8-point-derived spacing system:

``` text
4
8
12
16
20
24
32
40
48
64
80
96
```

Not every spacing value needs to be used.

A practical hierarchy:

``` text
4–8px    icon/text relationships
8–16px   related controls
16–24px  component internal spacing
24–32px  component groups
32–48px  sections
64–96px  major page transitions
```

## 7.4 Negative space

Whitespace is not empty.

Use it to: - separate conceptual groups - emphasize important
information - slow down dense screens - make decisions easier

Do not fill every available pixel with cards.

------------------------------------------------------------------------

# 8. Safe areas and responsive behavior

Apple's concept of safe areas maps to web design as avoiding content
being obscured by: - fixed navigation - browser overlays - mobile
notches - sticky controls - keyboard/input overlays - responsive
navigation

On the web, use:

``` css
padding:
  max(24px, env(safe-area-inset-left))
  ...
```

where appropriate for mobile/PWA contexts.

For responsive breakpoints, design around content constraints rather
than device names.

Suggested:

``` text
< 640px     compact
640–1024    tablet / small desktop
1024–1440   desktop
> 1440      wide desktop
```

Do not simply scale every component down.

------------------------------------------------------------------------

# 9. Application shell

For Agentic AutoML, the shell should be quiet.

Suggested desktop structure:

``` text
┌─────────────────────────────────────────────────────────┐
│ App identity        Dataset / Project        Actions    │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│ Navigation   │              Main content                │
│              │                                          │
│ Dataset      │                                          │
│ Profile      │                                          │
│ Strategy     │                                          │
│ Pipeline     │                                          │
│              │                                          │
└──────────────┴──────────────────────────────────────────┘
```

But do not force a sidebar if the current workflow is linear.

For the initial upload experience, a centered full-width composition is
better.

Once a dataset exists, a sidebar can become useful.

------------------------------------------------------------------------

# 10. Sidebar

Apple describes a sidebar as navigation between major areas or top-level
collections.

Use it for:

``` text
Workspace
 ├── Current Dataset
 ├── Profile
 ├── Strategy
 └── Pipeline

Workspace
 ├── New Dataset
 └── History
```

Do not put every action into the sidebar.

A sidebar should represent **information architecture**, not a dumping
ground for buttons.

For your application:

``` text
AutoML
────────────────
Current Dataset

Overview
Profile
Strategy
Pipeline

────────────────
New Dataset
History
```

The selected item should have: - clear background treatment - strong
text/icon - enough contrast - obvious active state

Do not rely solely on color.

On narrow widths, collapse to a compact navigation pattern rather than
squeezing the sidebar.

------------------------------------------------------------------------

# 11. Navigation

Navigation should answer:

> "Where am I?"

and:

> "Where can I go next?"

Your core workflow already provides a natural progression:

``` text
Upload
  ↓
Target
  ↓
Profile
  ↓
Strategy
  ↓
Pipeline
```

Show progress subtly.

Do not create a giant wizard with five glowing circles.

A compact progress indicator can be:

``` text
01 Upload  →  02 Profile  →  03 Strategy  →  04 Pipeline
```

Completed stages can be visually quieter than the current stage.

------------------------------------------------------------------------

# 12. Search fields

Apple's current HIG describes search fields as editable fields with a
search affordance, clear control, and placeholder text.

For this product, search is useful on: - column lists - generation
history - datasets - code - possibly documentation

Use placeholder text that tells users what can be searched.

Bad:

``` text
Search...
```

Better:

``` text
Search columns
```

or:

``` text
Search generations
```

or:

``` text
Find in pipeline
```

Search should be contextual.

If the user is looking at columns, search should search columns---not
unexpectedly search the entire application.

For a large column table:

``` text
[ 🔍 Search columns... ]       24 columns
```

Keep the search field above the content it filters.

------------------------------------------------------------------------

# 13. Scroll views

Scrolling content should remain visually connected to the application
shell.

For the generated code:

``` text
┌───────────────────────────────┐
│ pipeline.py          Copy     │
├───────────────────────────────┤
│                               │
│  01 import pandas as pd       │
│  02 ...                       │
│  03 ...                       │
│                               │
│             ↕ scroll          │
└───────────────────────────────┘
```

Do not put the entire application inside a nested scrolling nightmare.

Prefer: - one primary page scroll - localized scrolling only where
content is naturally long - sticky headers where useful - scroll
shadows/edge cues when necessary

For code, localized scrolling is appropriate.

For tables, localized horizontal scrolling may be appropriate.

------------------------------------------------------------------------

# 14. Cards

Cards should group information that belongs together.

Use cards for:

``` text
Metric recommendation
Data quality summary
Candidate model
Validation result
```

Do not wrap every tiny item in a card.

Bad:

``` text
[card]
Rows

[card]
Columns

[card]
Target

[card]
Task
```

Better:

``` text
Dataset overview

18,432 rows     24 columns     2.4 MB
Target: churn  |  Binary classification
```

Use grouping and whitespace first.

------------------------------------------------------------------------

# 15. Buttons

Buttons communicate actions.

Use three levels:

## Primary

One dominant action per context.

Examples:

``` text
Generate Strategy
Generate Pipeline
Continue
```

## Secondary

Important but non-dominant:

``` text
Back
Copy
Download
Regenerate
```

## Tertiary

Low emphasis:

``` text
View details
Learn more
```

Do not make every button filled.

A screen should make the next action obvious.

------------------------------------------------------------------------

# 16. Button wording

Use verbs.

Good:

``` text
Generate Pipeline
Upload Dataset
Copy Code
Download Python
Retry Generation
Change Target
```

Avoid:

``` text
Submit
Process
Action
Continue
Click Here
```

unless the action is genuinely obvious.

------------------------------------------------------------------------

# 17. Inputs

Inputs should have:

``` text
Label
Input
Optional supporting text
Validation state
```

Example:

``` text
Target column

[ customer_churn             ▾ ]

The column the model will predict.
```

Do not rely on placeholder text as the label.

Placeholder text disappears and is not a substitute for labeling.

------------------------------------------------------------------------

# 18. Select / target selector

This is a critical component in your application.

Use:

``` text
Target column
┌───────────────────────────────────┐
│ customer_churn                 ▾ │
└───────────────────────────────────┘

Binary classification
High confidence
```

The dropdown/list should display useful metadata:

``` text
customer_churn
categorical · 2 unique · 3.2% missing
```

This helps users make the decision without leaving the screen.

------------------------------------------------------------------------

# 19. Tables

Use tables when relationships between rows and columns matter.

Your column profile table:

``` text
Column          Type          Missing      Unique       Flags
──────────────────────────────────────────────────────────────
age             Numeric       2.1%         71           —
income          Numeric       0.0%         14,232        ID-like
country         Categorical   0.3%         41           —
customer_id     Numeric       0.0%         18,432       ID-like
```

Use: - aligned numeric values - readable column names - concise badges -
sticky header when useful - row hover only when it helps - sorting where
meaningful

Do not overdecorate tables with borders on every cell.

------------------------------------------------------------------------

# 20. Status badges

Use semantic labels:

``` text
PASS
WARN
FAIL
HIGH CONFIDENCE
AMBIGUOUS
PROFILED
GENERATING
```

A badge should communicate status, not become decoration.

Good:

``` text
✓ Passed
⚠ Warning
× Failed
```

------------------------------------------------------------------------

# 21. Progress and loading

Never show an unexplained spinner for a 30-second operation.

For generation:

``` text
Generating pipeline

✓ Reading dataset profile
✓ Selecting preprocessing strategy
● Generating pipeline
○ Running static checks
```

Only display steps that actually correspond to backend work.

Do not fake progress.

For long operations, tell the user: - what is happening - what has
completed - what is next

------------------------------------------------------------------------

# 22. Empty states

An empty state should explain:

1.  what is missing
2.  why it matters
3.  what the user should do

Example:

``` text
No dataset loaded

Upload a CSV to analyze its structure,
identify a prediction target, and generate
an ML pipeline.

[ Upload CSV ]
```

Do not show a blank page.

------------------------------------------------------------------------

# 23. Error states

Errors should be: - specific - actionable - calm - human-readable

Bad:

``` text
500 Internal Server Error
```

Better:

``` text
We couldn't generate the pipeline.

The model provider timed out before returning
a complete strategy.

[ Try Again ]
```

If retryable:

``` text
Retry
```

If not:

``` text
Change target
```

or:

``` text
Upload another dataset
```

Never expose raw stack traces to the user.

------------------------------------------------------------------------

# 24. Data quality presentation

The Profile screen should make complex statistics understandable.

Use a hierarchy:

``` text
Dataset quality

Good
────────────────────────────

Missing values          3.2%
Duplicate rows          14
Constant columns        1
ID-like columns         2
Possible leakage        1
```

Then show details only when needed.

This is progressive disclosure.

------------------------------------------------------------------------

# 25. Metric recommendation component

This should be one of the most visually important components.

``` text
Recommended metric

        F1 Score

Why?
The minority class is substantially underrepresented,
so accuracy may hide poor minority-class performance.

[ Change metric ]
```

Do not say:

``` text
AI recommends F1
```

The recommendation is generated deterministically by Python.

The UI should communicate that.

Better:

``` text
Recommended by dataset analysis
```

This reinforces the product's core architecture.

------------------------------------------------------------------------

# 26. Strategy screen

The Strategy screen should feel like a decision document.

Suggested hierarchy:

``` text
Recommended ML Strategy

Problem
Binary classification

Primary metric
F1

────────────────────────

Preprocessing

✓ Median imputation
✓ One-hot encoding
✓ Standard scaling

────────────────────────

Candidate models

Random Forest
Why: robust baseline...

XGBoost
Why: strong performance...

────────────────────────

Validation

Stratified 5-fold cross-validation

────────────────────────

Risks

⚠ Possible leakage in income-derived feature
```

Avoid a chatbot-style interface.

The model is not "talking."

It is producing a structured technical artifact.

------------------------------------------------------------------------

# 27. Generated code viewer

The code screen should be treated as a serious technical artifact.

Structure:

``` text
Generated pipeline
──────────────────────────────────────

pipeline.py                    [Copy] [Download]

Static checks
✓ Syntax valid
✓ Imports allowed
✓ Columns verified
✓ Target verified
✓ Metric verified

──────────────────────────────────────

01 | import pandas as pd
02 | from sklearn...
03 | ...
```

Use: - syntax highlighting - line numbers - monospace font - subtle line
hover - copy action - download action - optional find-in-code

Do not put the code inside a huge floating glass container.

The code itself is the content.

------------------------------------------------------------------------

# 28. Materials and glass

Apple's current HIG distinguishes **Liquid Glass** from standard
materials.

For this web application, interpret the principle---not the exact Apple
implementation.

Use translucent/blurred material only for: - floating navigation -
sticky toolbars - overlays - transient controls

Do not use glass for: - every card - every panel - code blocks - data
tables - the entire background

Apple explicitly recommends using Liquid Glass as a functional layer for
controls/navigation rather than the content layer, and recommends using
it sparingly.

For web CSS, if appropriate:

``` css
backdrop-filter: blur(...);
background: color-mix(...);
```

But the effect must remain subtle.

A premium interface is not "glass everywhere."

------------------------------------------------------------------------

# 29. Shadows

Use shadows to communicate elevation.

Suggested hierarchy:

``` text
No shadow
  normal content

Small shadow
  raised control / card

Medium shadow
  popover / dropdown

Strong shadow
  modal / major overlay
```

Avoid: - huge diffuse shadows - colored shadows - glowing neon shadows

Borders and background contrast often work better than shadows.

------------------------------------------------------------------------

# 30. Corner radius

Use a small number of radii.

Suggested:

``` text
Small       8px
Medium      12px
Large       16px
Pill        999px
```

Use larger radii for: - major surfaces - upload zones - prominent
controls

Use smaller radii for: - inputs - buttons - code blocks - compact
elements

Do not make everything a pill.

------------------------------------------------------------------------

# 31. Icons

Apple's SF Symbols are designed to integrate with San Francisco and
provide consistent weights and scales.

For a web app, use a consistent icon library with a similar principle.

If using SF Symbols specifically, verify Apple's current SF Symbols
terms and platform requirements before shipping. Do not use symbols as a
product logo or trademark-like branding.

Recommended semantic icons:

``` text
Upload          arrow.up
Search          magnifyingglass
Settings        gear
Profile         chart.bar
Strategy        wand / lightbulb
Pipeline        chevron.left.forwardslash.chevron.right
Success         checkmark.circle
Warning         exclamationmark.triangle
Error           xmark.circle
Download        arrow.down
Copy            doc.on.doc
```

Use icons to reinforce labels, not replace them everywhere.

------------------------------------------------------------------------

# 32. Motion

Motion should explain state changes.

Good uses: - page transitions - dropdown appearance - button state
changes - progress transitions - sidebar collapse - code copy
confirmation

Avoid: - constant floating animations - particles - glowing AI effects -
excessive bouncing - animated backgrounds

Suggested durations:

``` text
micro interaction    100–160ms
normal transition    180–250ms
large transition     250–350ms
```

Respect:

``` css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

------------------------------------------------------------------------

# 33. Accessibility

Accessibility is not an afterthought.

Minimum requirements:

-   keyboard navigation
-   visible focus states
-   semantic HTML
-   proper labels
-   sufficient contrast
-   no color-only status
-   screen-reader-friendly controls
-   meaningful button labels
-   logical tab order
-   reduced-motion support
-   resizable text/layout
-   accessible error messages

For interactive components:

``` text
button → button
input → input
navigation → nav
main content → main
section → section
```

Do not build everything from clickable `<div>` elements.

------------------------------------------------------------------------

# 34. Focus states

Never remove the browser focus indicator without replacing it with a
stronger one.

Bad:

``` css
outline: none;
```

unless replaced by a visible accessible focus treatment.

Recommended conceptual behavior:

``` text
default
  subtle

hover
  slightly emphasized

focus
  obvious high-contrast ring

pressed
  compressed/subtle state

disabled
  reduced emphasis
```

------------------------------------------------------------------------

# 35. Forms and validation

Validate close to the source of the error.

Example:

``` text
Target column

[ — select — ]

⚠ Select a target column before continuing.
```

Do not wait until the final generation request to tell the user.

------------------------------------------------------------------------

# 36. Tooltips

Tooltips are secondary.

Do not hide critical information in tooltips.

If the metric rationale matters, show it directly.

Use tooltips for: - uncommon technical terminology - icon-only
controls - additional context - secondary explanations

Not for: - primary instructions - required information - error messages

------------------------------------------------------------------------

# 37. Menus

Apple recommends familiar menu behavior and logical grouping.

For the web application:

``` text
Dataset
 ├── Rename
 ├── Download profile
 ├────────────
 └── Delete
```

Keep dangerous actions separated.

Do not create deep nested menus.

One submenu level is usually enough.

------------------------------------------------------------------------

# 38. Modals and sheets

Use a modal only when the user needs to focus on a decision.

Good examples: - delete dataset confirmation - advanced metric
selection - generation error details

Bad examples: - every small piece of information - simple column
information - routine status messages

Prefer inline content when possible.

------------------------------------------------------------------------

# 39. Notifications

Use transient feedback for completed small actions:

``` text
✓ Pipeline copied
```

Do not use notifications for important failures that require action.

Important errors belong in context.

------------------------------------------------------------------------

# 40. Data visualization

Charts should communicate actual information, not decorate the
interface.

For Profile:

### Class distribution

Use a horizontal bar chart.

### Missingness

Use a compact ranked bar chart.

Avoid: - 3D charts - decorative gradients - excessive legends -
unnecessary pie charts - charts without labels

Use consistent axis formatting.

------------------------------------------------------------------------

# 41. Chart hierarchy

Example:

``` text
Class distribution

Churned       ███████████████ 82%
Not churned   ███             18%
```

The user should understand the data before reading a tooltip.

------------------------------------------------------------------------

# 42. Responsive desktop behavior

At wide desktop:

``` text
Sidebar | Content
```

At medium width:

``` text
Compact sidebar | Content
```

At small width:

``` text
Top navigation
Content
```

Do not keep a 280px sidebar on a 700px screen.

------------------------------------------------------------------------

# 43. The Upload screen

This should be visually simple.

``` text
Analyze your dataset

Turn a CSV into an explainable ML pipeline.

┌─────────────────────────────────────────┐
│                                         │
│              ↑                          │
│                                         │
│       Drop your CSV here                │
│       or choose a file                  │
│                                         │
│       CSV · max 50 MB                   │
│                                         │
└─────────────────────────────────────────┘

Try a sample dataset
[ Titanic ] [ Wine ] [ California Housing ]
```

The upload target should be the primary visual focus.

------------------------------------------------------------------------

# 44. Target screen

After upload:

``` text
Choose what you want to predict

Dataset
customer_data.csv

Target column

[ customer_churn                    ▾ ]

Detected task

Binary classification
High confidence

[ Continue ]
```

Do not overwhelm the user with every statistic yet.

------------------------------------------------------------------------

# 45. Profile screen

Recommended layout:

``` text
Dataset Profile

18,432 rows · 24 columns · 2.4 MB

─────────────────────────────────────

Overview
[Rows] [Columns] [Missing] [Duplicates]

─────────────────────────────────────

Data quality
Missingness
Duplicate rows
Constant columns
ID-like columns

─────────────────────────────────────

Target
customer_churn
Binary classification

Class balance
██████████████ 82%
███            18%

─────────────────────────────────────

Recommended metric

F1 Score

Reason...
```

------------------------------------------------------------------------

# 46. Strategy screen

Use a document-like structure rather than cards everywhere.

``` text
ML Strategy

Binary classification
Target: customer_churn

Primary metric
F1

Preprocessing
...

Models
...

Validation
...

Risks
...
```

This should feel like the user is receiving an expert technical
recommendation.

------------------------------------------------------------------------

# 47. Pipeline screen

Make it feel like an IDE-lite, not a chat window.

``` text
Pipeline

pipeline.py

[Copy] [Download]

Validation
✓ Syntax
✓ Imports
✓ Columns
✓ Target
✓ Metric

────────────────────────────

CODE
```

This is probably the most technically impressive screen in the MVP.

------------------------------------------------------------------------

# 48. AI language

Avoid anthropomorphism.

Bad:

``` text
Claude thinks...
The AI believes...
AI is confused...
```

Better:

``` text
Dataset analysis recommends...
The generated strategy uses...
The validator detected...
Generation failed because...
```

The system should feel like an engineering tool.

------------------------------------------------------------------------

# 49. Loading language

Instead of:

``` text
AI is thinking...
```

Use real system states:

``` text
Analyzing dataset
Generating strategy
Generating pipeline
Running static checks
```

This is both more honest and more professional.

------------------------------------------------------------------------

# 50. Error language

Use:

``` text
What happened
Why it happened
What you can do
```

Example:

``` text
Pipeline generation timed out

The model provider did not return a complete
pipeline within the allowed time.

Your dataset profile is محفوظ and can be reused.

[Retry generation]
```

Never make the user start from zero when the failure is recoverable.

------------------------------------------------------------------------

# 51. Information architecture

Recommended:

``` text
Workspace
│
├── Dataset
│   ├── Overview
│   ├── Profile
│   └── Data quality
│
├── Modeling
│   ├── Strategy
│   └── Pipeline
│
└── History
    └── Generations
```

For MVP, this can remain mostly linear.

Do not overbuild history/navigation before the core workflow works.

------------------------------------------------------------------------

# 52. Design system component inventory

Build reusable components:

``` text
AppShell
Sidebar
TopBar
Breadcrumbs
ProgressIndicator

Button
IconButton
LinkButton
Dropdown
Select
TextField
SearchField

Card
Section
Divider
Badge
StatusBadge
Callout

DataTable
Stat
MetricCard
Chart
EmptyState
ErrorState
LoadingState

UploadZone
TargetSelector
ProfilePanel
QualitySummary
MetricRecommendation
StrategyPanel
ModelCandidate
ValidationChecklist
CodeViewer

Modal
Popover
Tooltip
Toast
```

Avoid creating components for one-off decorative elements.

------------------------------------------------------------------------

# 53. Component state model

Every interactive component should consider:

``` text
default
hover
focus
pressed
disabled
loading
success
warning
error
```

For async product components:

``` text
idle
loading
success
retryable error
fatal error
```

This is particularly important for:

-   upload
-   generation
-   validation
-   copy
-   download

------------------------------------------------------------------------

# 54. The "Apple test"

Before shipping a screen, ask:

### Purpose

Can I tell what this screen is for within two seconds?

### Simplicity

Can I remove anything without losing functionality?

### Hierarchy

Is the most important information visually dominant?

### Flexibility

Does it work at different widths?

### Craft

Do all states look intentional?

### Delight

Does the interface feel satisfying without being flashy?

If the answer to one is no, fix the design.

------------------------------------------------------------------------

# 55. Anti-patterns

Do NOT use:

``` text
❌ giant gradients
❌ neon purple AI glow
❌ floating particles
❌ excessive glassmorphism
❌ every section inside a card
❌ 10 competing buttons
❌ huge shadows
❌ tiny gray text
❌ color-only warnings
❌ fake progress
❌ chatbot bubbles for technical output
❌ unnecessary animations
❌ fake AI "thinking"
❌ fake confidence scores
❌ fake model metrics
❌ "Best Model" before execution
❌ dense dashboards on the first screen
```

The interface should be quiet enough that the data and generated
strategy become the visual focus.

------------------------------------------------------------------------

# 56. Specific design rules for this project

These are the rules Claude should follow when generating the frontend.

## Rule 1

The application is a **technical product**, not an AI chat application.

## Rule 2

Use whitespace before adding cards.

## Rule 3

Use one primary action per screen.

## Rule 4

Use semantic colors.

## Rule 5

Never fabricate metrics.

## Rule 6

Never call an unexecuted model the "best model."

## Rule 7

Always show whether profiling used the full dataset or a sample.

## Rule 8

Keep technical details accessible but progressively disclosed.

## Rule 9

Use real progress states.

## Rule 10

Respect light/dark system preferences.

## Rule 11

Respect reduced-motion preferences.

## Rule 12

Every destructive operation requires deliberate confirmation.

## Rule 13

Every API failure should map to a useful user-facing state.

## Rule 14

Generated code is a first-class artifact.

## Rule 15

The validation report should be visible before the user copies/downloads
the code.

------------------------------------------------------------------------

# 57. Recommended visual direction

For the actual Agentic AutoML implementation:

### Background

Very light neutral rather than pure white everywhere.

### Content

White or slightly elevated surfaces.

### Accent

One restrained blue/indigo accent.

### Typography

Native system font stack, with SF Pro where licensing/distribution
permits.

### Code

SF Mono/system monospace.

### Borders

Very subtle.

### Radius

8--16px, not everything pill-shaped.

### Shadows

Very restrained.

### Icons

Consistent line-based iconography.

### Motion

Subtle, short, purposeful.

### Layout

Generous whitespace.

### Charts

Minimal and data-first.

### Navigation

Compact sidebar on desktop; adaptive navigation on smaller screens.

------------------------------------------------------------------------

# 58. Apple resources worth actually using

Do not recreate Apple's components from memory.

Start from Apple's official design resources where relevant:

**Apple Design Resources** - official UI kits - Figma templates - Sketch
templates - icon production templates - color guides - product bezels -
fonts

https://developer.apple.com/design/resources/

**SF Symbols** - symbol library - weights - scales - rendering modes -
symbol search

https://developer.apple.com/sf-symbols/

**Fonts** - SF Pro - SF Compact - SF Mono - New York - language-specific
system fonts

https://developer.apple.com/fonts/

Use these as references and resources, but ensure the final web product
follows the relevant licensing and usage terms.

------------------------------------------------------------------------

# 59. Important distinction: Apple HIG vs web implementation

The HIG is designed around Apple platforms, not React/Tailwind.

Therefore:

### Apple concept

``` text
Safe area
```

### Web equivalent

``` text
responsive container + browser viewport + mobile safe-area insets
```

### Apple concept

``` text
SF Symbols
```

### Web equivalent

``` text
consistent icon system
```

### Apple concept

``` text
Liquid Glass
```

### Web equivalent

``` text
limited translucent/blurred functional surfaces
```

### Apple concept

``` text
system text styles
```

### Web equivalent

``` text
semantic typography tokens
```

### Apple concept

``` text
system colors
```

### Web equivalent

``` text
semantic CSS color tokens + prefers-color-scheme
```

Do not force platform-specific APIs into a web application.

------------------------------------------------------------------------

# 60. Final implementation brief for Claude

When Claude builds the frontend, the instruction should effectively be:

> Build a premium technical web application inspired by the principles
> of Apple's Human Interface Guidelines, not a visual clone of Apple.
> Prioritize purpose, simplicity, flexibility, craft, and delight. Use a
> restrained neutral palette, semantic accent/status colors, native
> system typography, strong typographic hierarchy, generous whitespace,
> adaptive layouts, subtle materials, restrained shadows, consistent
> corner radii, familiar controls, accessible focus states, semantic
> HTML, reduced-motion support, and system-aware light/dark appearance.
>
> The application is Agentic AutoML: a deterministic dataset profiler
> followed by structured LLM strategy generation and static code
> validation. It is not a chatbot. The UI must make the workflow feel
> like a high-quality technical instrument: Upload → Target → Profile →
> Strategy → Pipeline.
>
> Do not use neon AI aesthetics, excessive gradients, excessive
> glassmorphism, fake progress, fake metrics, fake confidence, or
> unnecessary cards. Use real backend states and progressive disclosure.
> Make the generated Python pipeline a first-class artifact with syntax
> highlighting, line numbers, copy/download controls, and a visible
> static-validation checklist.
>
> Every important design decision should prioritize information
> hierarchy and clarity over decoration. The interface should feel calm,
> precise, responsive, trustworthy, and native-quality.

------------------------------------------------------------------------

# 61. Final design checklist

Before considering the frontend complete:

## Foundation

-   [ ] Design tokens exist
-   [ ] Typography is centralized
-   [ ] Colors are semantic
-   [ ] Light mode works
-   [ ] Dark mode works
-   [ ] Contrast checked
-   [ ] Spacing system is consistent
-   [ ] Radius system is consistent

## Layout

-   [ ] Responsive desktop layout
-   [ ] Compact layout
-   [ ] Mobile layout
-   [ ] No accidental nested scrolling
-   [ ] Content has readable max width
-   [ ] Navigation does not obscure content

## Components

-   [ ] Buttons have all states
-   [ ] Inputs have labels
-   [ ] Dropdowns are accessible
-   [ ] Search works contextually
-   [ ] Tables are readable
-   [ ] Status badges are semantic
-   [ ] Error states are actionable
-   [ ] Empty states are useful
-   [ ] Loading states show real work

## AutoML workflow

-   [ ] Upload is obvious
-   [ ] Target selection is obvious
-   [ ] Task confidence is visible
-   [ ] Profile facts are clearly labeled
-   [ ] Metric recommendation is explained
-   [ ] Strategy is structured
-   [ ] Generated code is prominent
-   [ ] Static checks are visible
-   [ ] Unexecuted code is clearly labeled

## Accessibility

-   [ ] Keyboard navigation
-   [ ] Visible focus
-   [ ] Screen-reader labels
-   [ ] Color is not the only status signal
-   [ ] Reduced motion
-   [ ] Sufficient contrast
-   [ ] Text can scale

## Product honesty

-   [ ] No fake model metrics
-   [ ] No fake execution state
-   [ ] No "best model" before execution
-   [ ] No fake AI reasoning
-   [ ] No fake progress
-   [ ] Dataset sampling is disclosed

------------------------------------------------------------------------

# 62. Source map

Use these Apple pages as the primary source of truth when a design
decision is disputed.

  Area                 Apple source
  -------------------- ------------------------
  Overall principles   Design principles
  Foundations          HIG Foundations
  Layout               Layout
  Typography           Typography
  Color                Color
  Materials            Materials
  Dark appearance      Dark Mode
  Navigation           Navigation and search
  Search               Search fields
  Sidebars             Sidebars
  Menus                Menus
  Icons                SF Symbols
  Design assets        Apple Design Resources
  Fonts                Apple Fonts
  Accessibility        HIG Accessibility

Apple's HIG is a living resource. Check the current page and its change
log before treating any platform-specific measurement or behavior as
permanent.

------------------------------------------------------------------------

# 63. Bottom line

The design goal is not:

> "Make the AutoML app look like Apple."

The goal is:

> **Make the complexity of AutoML disappear behind an interface that
> feels obvious, calm, precise, and trustworthy.**

The user should never wonder:

-   What do I do next?
-   What is the system doing?
-   Why did it recommend this metric?
-   Is this number real?
-   Did the generated code actually run?
-   Why did something fail?
-   Where am I?

The interface should answer those questions through hierarchy, state,
language, and interaction---not through visual noise.

**Design principle for this project:**

> **Less interface, more understanding.**
