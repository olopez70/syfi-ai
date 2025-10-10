/**
 * Profile Templates Page JavaScript
 * Handles loading and displaying profile templates
 */

let profileTemplates = [];
let selectedTemplate = null;

// Load profile templates from API
async function loadProfileTemplates() {
    try {
        showLoading(true);
        
        const response = await fetch('/api/profile-templates');
        const data = await response.json();
        
        if (data.success) {
            profileTemplates = data.templates;
            displayProfileTemplates();
            showLoading(false);
        } else {
            showError('Failed to load profile templates: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error loading profile templates:', error);
        showError('Error loading profile templates: ' + error.message);
    }
}

// Display profile templates in the grid
function displayProfileTemplates() {
    const container = document.getElementById('templatesContainer');
    container.innerHTML = '';
    
    profileTemplates.forEach(template => {
        const templateCard = createTemplateCard(template);
        container.appendChild(templateCard);
    });
    
    container.classList.remove('d-none');
}

// Create a template card element
function createTemplateCard(template) {
    const col = document.createElement('div');
    col.className = 'col-md-6 col-lg-4';
    
    col.innerHTML = `
        <div class="card profile-template-card border-${template.color}" onclick="showTemplateDetails('${template.id}')">
            <div class="card-header bg-${template.color} text-white">
                <div class="template-header">
                    <span class="template-icon">${template.icon}</span>
                    <div>
                        <h6 class="card-title mb-1">${template.name}</h6>
                        <small class="opacity-75">${template.entity_type}</small>
                    </div>
                </div>
            </div>
            <div class="card-body">
                <div class="template-description">
                    ${template.description.substring(0, 200)}${template.description.length > 200 ? '...' : ''}
                </div>
                
                <div class="template-tags">
                    ${template.tags.map(tag => `<span class="template-tag">${tag}</span>`).join('')}
                </div>
                
                <div class="template-stats">
                    <div class="row text-center">
                        <div class="col-6">
                            <div class="stat-item">
                                <div class="stat-value">${template.complexity_level}</div>
                                <div class="stat-label">Complexity</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="stat-item">
                                <div class="stat-value">${template.category}</div>
                                <div class="stat-label">Category</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card-footer text-center">
                <small class="text-muted">
                    <i class="fas fa-dollar-sign me-1"></i>${template.typical_income_range}
                </small>
            </div>
        </div>
    `;
    
    return col;
}

// Show template details by navigating to dedicated page
function showTemplateDetails(templateId) {
    const template = profileTemplates.find(t => t.id === templateId);
    if (!template) {
        console.error('Template not found:', templateId);
        return;
    }

    // Navigate to dedicated template details page
    window.location.href = `/profile-template/${encodeURIComponent(templateId)}`;
}

// Get complexity badge color
function getComplexityColor(complexity) {
    switch(complexity.toLowerCase()) {
        case 'low': return 'success';
        case 'medium': return 'warning';
        case 'high': return 'danger';
        default: return 'secondary';
    }
}

// View profiles generated from template
function viewProfiles() {
    if (!selectedTemplate) return;
    
    // Redirect to profile-details page with template filter
    const url = `/profile-details?template_id=${encodeURIComponent(selectedTemplate.id)}&template_name=${encodeURIComponent(selectedTemplate.name)}`;
    window.location.href = url;
}



// Show/hide loading state
function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    const container = document.getElementById('templatesContainer');
    const errorAlert = document.getElementById('errorAlert');
    
    if (show) {
        spinner.classList.remove('d-none');
        container.classList.add('d-none');
        errorAlert.classList.add('d-none');
    } else {
        spinner.classList.add('d-none');
    }
}

// Show error message
function showError(message) {
    const spinner = document.getElementById('loadingSpinner');
    const container = document.getElementById('templatesContainer');
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');
    
    spinner.classList.add('d-none');
    container.classList.add('d-none');
    errorMessage.textContent = message;
    errorAlert.classList.remove('d-none');
}

// Initialize event listeners
function initializeEventListeners() {
    // View profiles button in modal
    const viewProfilesBtn = document.getElementById('viewProfilesBtn');
    if (viewProfilesBtn) {
        viewProfilesBtn.addEventListener('click', viewProfiles);
    }
}

// Initialize page when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    loadProfileTemplates();
    initializeEventListeners();
});