# UX Design Specification: Heimdall Battery Sentinel

## Design Principles

1. **Clarity First**: Prioritize clear information hierarchy to quickly identify critical issues (low batteries, unavailable entities)
2. **Native Integration**: Seamlessly match Home Assistant's Material Design aesthetic while adding distinctive battery-focused visual language
3. **Progressive Disclosure**: Show essential information first, with details available on interaction
4. **Responsive Resilience**: Ensure consistent experience across mobile, tablet, and desktop views
5. **Accessible by Default**: Meet or exceed WCAG 2.1 AA standards for all components

## Design Tokens

### Color Palette
```mermaid
graph LR
    subgraph Base Colors
        Primary["Primary\n#03A9F4"]:::swatch_primary
        Accent["Accent\n#FF9800"]:::swatch_accent
        Error["Error\n#F44336"]:::swatch_error
    end

    subgraph Light Mode
        LM_BG["Background\n#FFFFFF"]:::swatch_lm_bg
        LM_Surface["Surface\n#F5F5F5"]:::swatch_lm_surface
        LM_Text["Text\n#212121"]:::swatch_lm_text
        LM_Secondary["Secondary Text\n#757575"]:::swatch_lm_secondary
    end

    subgraph Dark Mode
        DM_BG["Background\n#121212"]:::swatch_dm_bg
        DM_Surface["Surface\n#1E1E1E"]:::swatch_dm_surface
        DM_Text["Text\n#E0E0E0"]:::swatch_dm_text
        DM_Secondary["Secondary Text\n#9E9E9E"]:::swatch_dm_secondary
    end

    subgraph Severity
        Critical["Critical\n#F44336"]:::swatch_critical
        Warning["Warning\n#FF9800"]:::swatch_warning
        Notice["Notice\n#FFEB3B"]:::swatch_notice
    end

    classDef swatch_primary fill:#03A9F4,color:#000000,stroke:#03A9F4
    classDef swatch_accent fill:#FF9800,color:#000000,stroke:#FF9800
    classDef swatch_error fill:#F44336,color:#FFFFFF,stroke:#F44336
    classDef swatch_lm_bg fill:#FFFFFF,color:#000000,stroke:#DDDDDD
    classDef swatch_lm_surface fill:#F5F5F5,color:#000000,stroke:#CCCCCC
    classDef swatch_lm_text fill:#212121,color:#FFFFFF,stroke:#212121
    classDef swatch_lm_secondary fill:#757575,color:#FFFFFF,stroke:#757575
    classDef swatch_dm_bg fill:#121212,color:#FFFFFF,stroke:#333333
    classDef swatch_dm_surface fill:#1E1E1E,color:#FFFFFF,stroke:#333333
    classDef swatch_dm_text fill:#E0E0E0,color:#000000,stroke:#E0E0E0
    classDef swatch_dm_secondary fill:#9E9E9E,color:#000000,stroke:#9E9E9E
    classDef swatch_critical fill:#F44336,color:#FFFFFF,stroke:#F44336
    classDef swatch_warning fill:#FF9800,color:#000000,stroke:#FF9800
    classDef swatch_notice fill:#FFEB3B,color:#000000,stroke:#FFEB3B
```

### Typography Scale
```mermaid
pie
    title Typography Scale
    "H6: 1.25rem" : 20
    "Subtitle1: 1rem" : 30
    "Body1: 0.875rem" : 40
    "Caption: 0.75rem" : 10
```

### Spacing System
```mermaid
flowchart TD
    Space[4px Base Unit]
    Space --> XS[4px]
    Space --> S[8px]
    Space --> M[16px]
    Space --> L[24px]
    Space --> XL[32px]
```

### Other Tokens
- Border Radii: 4px
- Shadows: 0 2px 4px rgba(0,0,0,0.1)
- Animation Timing: 200ms for micro-interactions, 300ms for transitions

## Component Library

### Table Component
```mermaid
graph TD
    Table[Table] --> Header[Header Row]
    Table --> Body[Body Rows]
    Table --> Footer[Footer]
    
    Header --> Sort[Sort Indicator]
    Header --> Column[Column Title]
    
    Body --> Row[Data Row]
    Row --> States
    States --> Default[Default]
    States --> Hover[Hover: +10% opacity]
    States --> Selected[Selected: Primary 10%]
    States --> Critical[Critical: Red 10%]
    States --> Warning[Warning: Orange 10%]
    States --> Notice[Notice: Yellow 10%]
    
    Footer --> Loading[Loading Indicator]
    Footer --> End[End of List]
    Footer --> Pagination[Page Info]
    
    Accessibility --> Keyboard[Keyboard Navigable]
    Accessibility --> Aria[Aria Roles]
    Accessibility --> Contrast[4.5:1 Contrast]
```

### Threshold Slider
```mermaid
graph LR
    Slider[Slider] --> Track[Track]
    Slider --> Thumb[Thumb]
    
    Track --> Default[Default: Secondary 30%]
    Track --> Active[Active: Secondary]
    
    Thumb --> Default[Default: Secondary]
    Thumb --> Hover[Hover: Secondary +10% lightness]
    Thumb --> Focus[Focus: Primary + Outline]
    
    States --> Disabled[Disabled: 50% opacity]
    
    Accessibility --> Labels[Value Labels]
    Accessibility --> Keyboard[Keyboard Control]
```

## Page Layouts

### Main Page Layout
```mermaid
graph TD
    Page[Heimdall Battery Sentinel] --> Header[Page Header]
    Page --> Tabs[Tabs Container]
    Page --> Content[Content Area]
    
    Header --> Title[Title]
    Header --> Config[Config Button]
    
    Tabs --> Tab1[Low Battery]
    Tabs --> Tab2[Unavailable]
    Tabs --> Count1[Live Count]
    Tabs --> Count2[Live Count]
    
    Content --> Table[Data Table]
    Content --> Footer[Footer Controls]
    
    Footer --> Threshold[Threshold Slider]
    Footer --> Info[Page Info]
```

### Responsive Behavior
```mermaid
graph LR
    Desktop[Desktop] --> 3Col[3 Columns: Name, Device, Area]
    Tablet[Tablet] --> 2Col[2 Columns: Name, Device]
    Mobile[Mobile] --> 1Col[1 Column: Name + Details]
```

## Interaction Patterns

### Threshold Change Flow
```mermaid
sequenceDiagram
    User->>UI: Adjusts Threshold Slider
    UI->>Backend: Threshold Update Event
    Backend->>Backend: Re-evaluate Battery State
    Backend->>UI: Dataset Invalidated
    UI->>UI: Reset to Page 0
    UI->>Backend: Request New Data
    Backend->>UI: Send Updated Rows
    UI->>UI: Render Updated Table
```

### Infinite Scroll
```mermaid
flowchart TD
    Start[User Scrolls] --> Detect[Detect Bottom 20%]
    Detect -->|Visible| Load[Show Loading Indicator]
    Load --> Request[Request Next Page]
    Request -->|Success| Render[Render New Rows]
    Render -->|More Data| Detect
    Render -->|No More| ShowEnd[Show End Indicator]
    Request -->|Error| Error[Show Error State]
```

## Accessibility

- **Color Contrast**: Minimum 4.5:1 for text, 3:1 for UI components
- **Focus Management**: Visible focus indicators for all interactive elements
- **Screen Reader**:
  - ARIA roles for tables (grid, row, cell)
  - Live regions for count updates
  - Status announcements for loading states
- **Keyboard Navigation**:
  - Tab navigation between interactive elements
  - Arrow key navigation within tables
  - Space/Enter to activate controls
- **Reduced Motion**: Respect prefers-reduced-motion for animations
- **Dark Mode**: Full support for HA's dark theme
