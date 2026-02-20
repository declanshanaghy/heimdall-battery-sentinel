# UX Design Specification: Heimdall Battery Sentinel

## 1. Design Principles

1. **Clarity First**: Provide immediate, unambiguous visibility into battery health and device availability without overwhelming the user.
2. **Native Cohesion**: Seamlessly integrate with Home Assistant's Material Design-inspired UI while maintaining distinct identity for the battery monitoring features.
3. **Responsive Resilience**: Maintain consistent functionality and legibility across all viewing contexts.
4. **Action-Oriented**: Highlight critical information and provide clear paths to address issues.
5. **Accessible Insight**: Ensure all users can understand and interact with the information.

## 2. Design Tokens

### Color Palette
- **Primary**: `#4285F4`
- **Secondary**: `#34A853`
- **Semantic**: 
  - Critical: `#EA4335`
  - Warning: `#FBBC05`
  - Informational: `#4285F4`
- **Light Mode**: 
  - Surface: `#FFFFFF`
  - Cards: `#F8F9FA`
- **Dark Mode**: 
  - Surface: `#202124`
  - Cards: `#303134`

### Typography Scale
- **H1**: 24px (semibold)
- **H2**: 20px (semibold)
- **Body**: 16px (regular)
- **Caption**: 14px (regular)

### Spacing System
- **XS**: 4px
- **S**: 8px
- **M**: 16px
- **L**: 24px
- **XL**: 32px

### Border Radii
- **Small**: 4px
- **Medium**: 8px
- **Large**: 12px

### Shadows
- **Low**: 0 1px 2px rgba(0,0,0,0.1)
- **Medium**: 0 2px 6px rgba(0,0,0,0.15)
- **High**: 0 4px 12px rgba(0,0,0,0.2)

### Animation Timing
- **Micro-interactions**: 200ms
- **Page Transitions**: 300ms
- **Data Loading**: 500ms (eased)

## 3. Component Library

### Battery Severity Indicator
- **Critical**: Red + mdi:battery-alert
- **Warning**: Orange + mdi:battery-30
- **Low**: Yellow + mdi:battery-50

### Entity Row States
- **Default**: Neutral
- **Hover**: Light blue tint
- **Active**: Subtle elevation
- **Disabled**: 50% opacity
- **Error**: Red border left

### Table Component
- **Header**: Light grey bg
- **Sort**: Primary color arrow
- **Striping**: Zebra pattern

## 4. Page Layouts

### Main Page
```
[ Tabs: Low Battery | Unavailable ]
[ Search ] [ Threshold Slider ]
----------------------------------
| Name      | Device    | Area   |
----------------------------------
| Entity 1  | Model     | Area   |
| Entity 2  | Model     | Area   |
| Loading...                    |
| End of list                   |
----------------------------------
```

**Responsive**:
- Mobile: 1 column
- Tablet: 2 columns
- Desktop: Full table

## 5. Interaction Patterns

### Threshold Adjustment
1. User moves slider
2. Loading spinner appears
3. Backend processes
4. UI updates dynamically
5. Success indicator pulses

### Data Loading
1. Initial: Skeleton screens
2. Pagination: "Loading..."
3. Error: Red border + retry
4. Empty: Message + illustration

## 6. Accessibility

- **Contrast**: Min 4.5:1 ratio
- **Focus**: Clear visual states
- **Screen Readers**: ARIA labels
- **Keyboard**: Full tab support
- **Reduced Motion**: Disable animations
- **Dark Mode**: Full support
