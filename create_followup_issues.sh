#!/bin/bash

# GitHub Issues Creation Script for Issue #5 Follow-ups
# Run this script to create the follow-up issues after closing Issue #5

echo "🚀 Creating GitHub Issues for Issue #5 Follow-ups..."

# Issue #6: Complete Patterns Module Implementations
echo "📋 Creating Issue #6: Complete Patterns Module Implementations..."
gh issue create \
  --title "Complete Patterns Module Implementations" \
  --body-file "ISSUE_6_PATTERNS_IMPLEMENTATIONS.md" \
  --label "enhancement,patterns,testing,implementation,medium-priority" \
  --milestone "v1.1.0" \
  --assignee "@me"

echo "✅ Issue #6 created successfully!"

# Issue #7: Resolve ProfileTemplate Parameter Compatibility  
echo "📋 Creating Issue #7: Resolve ProfileTemplate Parameter Compatibility..."
gh issue create \
  --title "Resolve ProfileTemplate Parameter Compatibility" \
  --body-file "ISSUE_7_PARAMETER_COMPATIBILITY.md" \
  --label "bug,high-priority,parameters,compatibility,quick-win" \
  --milestone "v1.0.1" \
  --assignee "@me"

echo "✅ Issue #7 created successfully!"

# Issue #8: Fix Web Interface Template Filtering Bug
echo "📋 Creating Issue #8: Fix Web Interface Template Filtering Bug..."
gh issue create \
  --title "Fix Web Interface Template Filtering Bug" \
  --body-file "ISSUE_8_TEMPLATE_FILTERING_BUG.md" \
  --label "bug,critical,web-interface,user-experience,template-filtering" \
  --milestone "v1.0.1" \
  --assignee "@me"

echo "✅ Issue #8 created successfully!"

echo ""
echo "🎉 All follow-up issues created successfully!"
echo ""
echo "📊 Summary:"
echo "  - Issue #6: Patterns implementations (Medium priority)"  
echo "  - Issue #7: Parameter compatibility (High priority)"
echo "  - Issue #8: Template filtering bug (Critical priority)"
echo ""
echo "💡 Recommended next steps:"
echo "  1. Close Issue #5 with ISSUE_5_COMPLETION_SUMMARY.md content"
echo "  2. Prioritize Issue #8 (Critical user experience)"
echo "  3. Address Issue #7 (Quick win for test improvements)" 
echo "  4. Complete Issue #6 (Full patterns module functionality)"