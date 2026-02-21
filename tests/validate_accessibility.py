#!/usr/bin/env python3
"""
Validate Frontend Accessibility Implementation
Checks panel-heimdall.js for required WCAG 2.1 AA compliance and responsive design
"""

import re
import sys

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def check_pattern(content, pattern, description):
    """Check if pattern exists in content"""
    if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description}")
        return False

def main():
    panel_file = "/home/dshanaghy/src/github.com/declanshanaghy/heimdall-battery-sentinel/custom_components/heimdall_battery_sentinel/www/panel-heimdall.js"
    
    try:
        content = read_file(panel_file)
    except FileNotFoundError:
        print(f"❌ File not found: {panel_file}")
        return 1
    
    print("🧪 Validating Frontend Accessibility Implementation\n")
    print("=" * 60)
    
    checks = [
        # HIGH Priority: ARIA Attributes
        (r'aria-sort="', "HIGH-1.1: aria-sort attributes on table headers"),
        (r'aria-label=["\'].*Sort', "HIGH-1.2: aria-label on sort buttons"),
        (r'aria-label=["\'].*table', "HIGH-1.3: aria-label on table"),
        (r'role=["\']status["\'].*aria-live=["\']polite', "HIGH-1.4: Live regions with role=status"),
        (r'role=["\'](status|grid)["\']', "HIGH-1.5: Status and grid roles"),
        
        # HIGH Priority: Focus Indicators
        (r':focus-visible\s*\{[^}]*outline:[^}]*\}', "HIGH-2.1: :focus-visible styles defined"),
        (r'\.tab-btn:focus-visible', "HIGH-2.2: Focus styles on tab buttons"),
        (r'th:focus-visible', "HIGH-2.3: Focus styles on table headers"),
        (r'a:focus-visible', "HIGH-2.4: Focus styles on links"),
        
        # HIGH Priority: Responsive Design
        (r'@media\s*\(\s*max-width:\s*768px\s*\)', "HIGH-3.1: Tablet media query (768px)"),
        (r'@media\s*\(\s*max-width:\s*375px\s*\)', "HIGH-3.2: Mobile media query (375px)"),
        (r'hidden-tablet', "HIGH-3.3: hidden-tablet class defined"),
        (r'hidden-mobile', "HIGH-3.4: hidden-mobile class defined"),
        
        # MEDIUM Priority: Colors
        (r'#F44336', "MEDIUM-1.1: Red severity color spec (#F44336)"),
        (r'#FF9800', "MEDIUM-1.2: Orange severity color spec (#FF9800)"),
        (r'#FFEB3B', "MEDIUM-1.3: Yellow severity color spec (#FFEB3B)"),
        (r'\.severity-red\s*\{\s*color:\s*#F44336', "MEDIUM-1.4: Red color applied correctly"),
        (r'\.severity-orange\s*\{\s*color:\s*#FF9800', "MEDIUM-1.5: Orange color applied correctly"),
        (r'\.severity-yellow\s*\{\s*color:\s*#FFEB3B', "MEDIUM-1.6: Yellow color applied correctly"),
        
        # MEDIUM Priority: Typography Tokens
        (r'--typography-h6', "MEDIUM-2.1: H6 typography token"),
        (r'--typography-subtitle1', "MEDIUM-2.2: Subtitle1 typography token"),
        (r'--typography-body1', "MEDIUM-2.3: Body1 typography token"),
        (r'--typography-caption', "MEDIUM-2.4: Caption typography token"),
        
        # MEDIUM Priority: Sort Indicator Size
        (r'\.sort-icon\s*\{[^}]*font-size:\s*(13|14|15|16)px', "MEDIUM-3.1: Sort icon font-size >= 13px"),
        (r'aria-hidden=["\']true["\']', "MEDIUM-3.2: aria-hidden on sort icons"),
        
        # MEDIUM Priority: Live Regions
        (r'aria-live=["\']polite["\']', "MEDIUM-4.1: aria-live regions marked"),
        
        # Bonus: Reduced Motion Support
        (r'@media\s*\(\s*prefers-reduced-motion:\s*reduce\s*\)', "BONUS: Reduced motion support"),
    ]
    
    print("\n🔍 Code Pattern Checks:\n")
    passed = 0
    failed = 0
    
    for pattern, description in checks:
        if check_pattern(content, pattern, description):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    print(f"Total: {passed + failed} checks\n")
    
    if failed == 0:
        print("✨ All accessibility requirements validated!")
        return 0
    else:
        print(f"⚠️  {failed} check(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
