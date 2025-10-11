# Python Project Instructions

This is a Python project with a basic structure for development.

## Project Structure

- `main.py` - Main entry point
- `src/` - Source code directory  
- `tests/` - Test directory
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore file
- `README.md` - Project documentation

## Virtual Environment activiation
Activate the virtual environment with:
```bash
source .venv/bin/activate
```

## Running the Project

Use the VS Code task "Run Python Project" or run from terminal:
```bash
/home/orlando/Projects/syfi-ai/.venv/bin/python main.py
```

## Testing

Run tests with:
```bash
/home/orlando/Projects/syfi-ai/.venv/bin/python -m pytest tests/ -v
```

Work through each checklist item systematically.
Keep communication concise and focused.
Follow development best practices.
Utilize Gang of Four design patterns where applicable.
Apply the Don't Repeat Yourself (DRY) principle to avoid code duplication.
Adhere to Core Principles of software design, including: Separation of Concerns, Single Responsibility Principle, and Interface Segregation Principle, Open/Closed Principle, and Dependency Inversion Principle, Liskov Substitution Principle.


Code changes should be tested and verified using existing test suites. If a test suite does not exist for the changed code, create one.

## Web Application Design Guidelines

### Design Philosophy
SyFi AI is a professional financial data generation tool. All web interfaces must reflect the trustworthy, sophisticated aesthetic of a modern fintech serving financial institutions using the established Radar Blue color palette.

### Visual Design Standards

#### Color Palette (Radar Blue Theme)
Use CSS custom properties from `base.css`:
- **Primary Colors**:
  - `var(--radar-blue-primary)`: `#b6c8e4` (main brand blue)
  - `var(--radar-blue-dark)`: `#1a2e5c` (headers, emphasis)
  - `var(--radar-blue-medium)`: `#7494ca` (accents, links)
  - `var(--radar-blue-light)`: `#e8eef7` (backgrounds)
  - `var(--radar-blue-lighter)`: `#f8fafc` (page backgrounds)
  - `var(--radar-accent)`: `#9bb2d9` (subtle accents)
- **Text Colors**:
  - Primary: `var(--text-primary)` (`#2c3e50`)
  - Secondary: `var(--text-secondary)` (`#64748b`)
- **Status Colors**:
  - Success: `var(--success)` (`#10b981`)
  - Warning: `var(--warning)` (`#f59e0b`)
  - Danger: `var(--danger)` (`#ef4444`)
- **Card Backgrounds**: `rgba(255, 255, 255, 0.95)` with backdrop-filter blur

#### Typography
- **Font Stack**: `'Montserrat', 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif`
- **Font Imports**: Always include Montserrat from Google Fonts
- **Preconnect**: Include `preconnect` links for performance
- **Hierarchy**: 
  - Page titles: `2.25rem, font-weight: 300`
  - Section titles: `1.25rem, font-weight: 600`
  - Body text: `1rem, line-height: 1.6`
  - Small text: `0.875rem`
- **Code/Data**: Use monospace font for database names, file paths, technical identifiers

#### Layout Principles
- **Clean Grid**: Use Bootstrap's 12-column grid consistently
- **White Space**: Generous padding and margins for readability
- **Card-Based**: Group related content in subtle bordered cards
- **Professional Spacing**: 
  - Section padding: `2rem 0`
  - Card padding: `2rem`
  - Element margins: `1rem` to `1.5rem`

### Component Standards

#### Cards and Content Containers
```css
.card, .search-card, .builder-card {
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
    border: none;
    border-radius: 8px;
    overflow: hidden;
    backdrop-filter: blur(10px);
    background: rgba(255, 255, 255, 0.95);
}

.card-header {
    border: none;
    font-weight: 600;
    letter-spacing: -0.3px;
}

.card-header.bg-primary {
    background: var(--radar-blue-dark) !important;
    color: white;
}
```

#### Navigation and Tab Patterns
- Use Bootstrap nav-tabs with Font Awesome icons
- Structure: `<i class="fas fa-icon me-2"></i>Tab Label`
- Active states use radar blue colors
- Tab content in `.tab-content` containers

#### Status Indicators and Badges
- Database connection status with colored indicators
- Success states: `var(--success)` green
- Warning states: `var(--warning)` amber
- Error states: `var(--danger)` red
- Icons: Font Awesome with consistent sizing (`me-2` spacing)

#### Forms and Inputs
- Bootstrap form classes with custom focus styles
- Consistent `border-radius: 8px`
- Proper label hierarchy and required field indicators

### Interactive Elements

#### Buttons
- **Primary Actions**: Bootstrap `btn-primary` 
- **Secondary Actions**: `btn-outline-secondary`
- **Subtle Actions**: Custom styled links with hover effects
- **No Flashy Effects**: Minimal transitions (0.2s ease maximum)

#### Hover States
- Subtle elevation: `translateY(-2px)`
- Soft shadows: `rgba(0, 0, 0, 0.08)`
- Color changes should be minimal and professional

### Responsive Design
- **Mobile First**: Design for mobile, enhance for desktop
- **Breakpoints**: Follow Bootstrap's standard breakpoints
- **Hide Complexity**: Hide detailed stats on mobile, show essential info only
- **Touch Targets**: Minimum 44px for interactive elements

### Content Guidelines

#### Language and Tone
- **Professional**: Use banking/financial terminology appropriately
- **Clear**: Avoid jargon, explain technical concepts
- **Concise**: Short descriptions, bullet points over paragraphs
- **Action-Oriented**: Use verbs for buttons and links ("Manage", "View", "Export")

#### Data Display
- **Consistent Formatting**: Numbers, dates, and currencies
- **Loading States**: Show shimmer effects or spinners for async content
- **Empty States**: Provide helpful guidance when no data exists
- **Error States**: Clear, actionable error messages

### Forbidden Design Elements
❌ **Avoid These**:
- Bright gradients or flashy colors
- Complex animations or transitions
- Busy backgrounds or patterns  
- Multiple competing call-to-action buttons
- Inconsistent icon styles or sizes
- Comic or casual fonts
- Neon or high-contrast color schemes

### Page Structure Templates

#### Standard Page Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Title - SyFi AI Database Browser</title>
    
    <!-- Font and CSS imports -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/shared_navigation_styles.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/page-specific.css') }}">
</head>
<body class="bg-light">
    {% include 'shared_navigation.html' %}
    
    <div class="container mt-4">
        <!-- Main card container -->
        <div class="card">
            <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                <h4 class="mb-0">
                    <i class="fas fa-icon me-2"></i>Page Title
                </h4>
            </div>
            <div class="card-body">
                <!-- Page content -->
            </div>
        </div>
    </div>
</body>
</html>
```

#### Tabbed Interface Pattern
```html
<!-- Tab Navigation -->
<ul class="nav nav-tabs nav-fill" id="mainTabs" role="tablist">
    <li class="nav-item" role="presentation">
        <button class="nav-link active" id="tab1" data-bs-toggle="tab" data-bs-target="#content1" type="button" role="tab">
            <i class="fas fa-icon me-2"></i>Tab Name
        </button>
    </li>
</ul>

<!-- Tab Content -->
<div class="tab-content" id="tabsContent">
    <div class="tab-pane fade show active" id="content1" role="tabpanel">
        <!-- Tab content -->
    </div>
</div>
```

### Implementation Notes
- Always include proper semantic HTML
- Ensure WCAG 2.1 AA accessibility compliance
- Test responsiveness on mobile devices
- Validate CSS for cross-browser compatibility
- Use consistent class naming conventions
- Include focus states for keyboard navigation