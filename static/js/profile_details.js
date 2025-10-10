/**
 * Profile Details Management JavaScript
 * Handles profile search and filtering functionality
 */

// Initialize page when DOM is ready
document.addEventListener('DOMContentLoaded', async function() {
    console.log('=== PAGE INITIALIZATION START ===');
    
    initializeEventListeners();
    
    // Check for URL parameters to pre-filter by template
    const urlParams = new URLSearchParams(window.location.search);
    const templateId = urlParams.get('template_id');
    const templateName = urlParams.get('template_name');
    
    console.log('URL Parameters detected:');
    console.log('  template_id:', templateId);
    console.log('  template_name:', templateName);
    console.log('  Full URL:', window.location.href);
    
    // Load template options first
    console.log('Loading template options...');
    await loadTemplateOptions();
    console.log('Template options loaded successfully');
    
    if (templateId && templateName) {
        console.log('Template context detected - setting up filters');
        
        // Add a header showing the template context
        addTemplateContextHeader(templateName);
        
        // Pre-select the template filter now that options are loaded
        const templateFilter = document.getElementById('template-filter');
        console.log('Template filter element before setting:', templateFilter);
        console.log('Available options in dropdown:');
        for (let option of templateFilter.options) {
            console.log(`  Option: value="${option.value}", text="${option.text}"`);
        }
        
        templateFilter.value = templateId;
        
        // Debug: verify the value was set
        console.log('AFTER setting template filter:');
        console.log('  Intended value:', templateId);
        console.log('  Actual dropdown value:', templateFilter.value);
        console.log('  Selected index:', templateFilter.selectedIndex);
        console.log('  Selected option text:', templateFilter.options[templateFilter.selectedIndex]?.text);
        
        // Double-check that the value was actually set (sometimes browsers need a moment)
        if (templateFilter.value !== templateId) {
            console.warn('Template filter value not set properly, trying alternative approach');
            // Try finding and setting by index
            for (let i = 0; i < templateFilter.options.length; i++) {
                if (templateFilter.options[i].value === templateId) {
                    templateFilter.selectedIndex = i;
                    console.log('Set template filter using selectedIndex:', i);
                    break;
                }
            }
        }
        
        // Final verification
        console.log('FINAL verification:');
        console.log('  Final dropdown value:', templateFilter.value);
        console.log('  Final selected index:', templateFilter.selectedIndex);
        
        // Search with the template filter applied
        console.log('Triggering initial search with template filter...');
        // Small delay to ensure DOM has fully updated
        setTimeout(() => {
            console.log('Delayed search execution - checking template value one more time:');
            console.log('  Template filter value at search time:', document.getElementById('template-filter').value);
            searchProfiles();
        }, 100);
    } else {
        console.log('No template context - waiting for user to click search');
        // Don't auto-load profiles, wait for user to click search
    }
    
    console.log('=== PAGE INITIALIZATION COMPLETE ===');
});

// Initialize event listeners
function initializeEventListeners() {
    // Profile search form
    document.getElementById('profile-search-form').addEventListener('submit', function(e) {
        e.preventDefault();
        searchProfiles();
    });
}

// Load template options for filter dropdown
async function loadTemplateOptions() {
    try {
        const response = await fetch('/api/profile-templates');
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('template-filter');
            // Clear existing options except "All Templates"
            select.innerHTML = '<option value="">All Templates</option>';
            
            data.templates.forEach(template => {
                const option = document.createElement('option');
                option.value = template.template_id;
                option.textContent = template.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load templates:', error);
    }
}

// Search profiles with current form values
async function searchProfiles() {
    try {
        showLoading(true);
        
        const params = new URLSearchParams();
        
        // Get form values directly
        const search = document.getElementById('profile-search').value.trim();
        const profileId = document.getElementById('profile-id-filter').value.trim();
        const templateId = document.getElementById('template-filter').value;
        
        if (search) {
            params.append('search', search);
        }
        if (profileId) {
            params.append('profile_id', profileId);
        }
        if (templateId) {
            params.append('template_id', templateId);
        }
        
        // Debug logging
        console.log('=== SEARCH PROFILES EXECUTION ===');
        console.log('Direct DOM value reading:');
        console.log('  Search input value:', search);
        console.log('  Profile ID filter value:', profileId);
        console.log('  Template dropdown element:', document.getElementById('template-filter'));
        console.log('  Template dropdown value:', templateId);
        console.log('  Template dropdown selected index:', document.getElementById('template-filter').selectedIndex);
        console.log('  Template dropdown options count:', document.getElementById('template-filter').options.length);
        console.log('Constructed parameters:');
        console.log('  search param:', search ? 'YES' : 'NO');
        console.log('  profile_id param:', profileId ? profileId : 'NONE');
        console.log('  template_id param:', templateId ? templateId : 'NONE');
        console.log('Final API URL:', `/api/profiles?${params.toString()}`);
        
        const response = await fetch(`/api/profiles?${params.toString()}`);
        console.log('API Response status:', response.status);
        const data = await response.json();
        console.log('API Response data:', data);
        
        if (data.success) {
            displayProfileResults(data.profiles);
        } else {
            console.error('Search failed:', data.error);
            showNoResults();
        }
    } catch (error) {
        console.error('Failed to search profiles:', error);
        showNoResults();
    } finally {
        showLoading(false);
    }
}

// Display profile search results
function displayProfileResults(profiles) {
    const container = document.getElementById('profile-results');
    const noResults = document.getElementById('profile-no-results');
    const tbody = document.getElementById('profile-results-body');
    const countBadge = document.getElementById('profile-count');
    
    if (!profiles || profiles.length === 0) {
        showNoResults();
        return;
    }
    
    // Update count
    countBadge.textContent = profiles.length;
    
    // Clear previous results
    tbody.innerHTML = '';
    
    profiles.forEach(profile => {
        const row = document.createElement('tr');
        row.style.cursor = 'pointer';
        
        // Format dates
        const createdDate = profile.created_date ? new Date(profile.created_date).toLocaleDateString() : 'N/A';
        
        // Template badge color based on entity type
        let badgeClass = 'bg-secondary';
        switch (profile.entity_type) {
            case 'personal': badgeClass = 'bg-info'; break;
            case 'business': badgeClass = 'bg-success'; break;
            case 'non-profit': badgeClass = 'bg-warning text-dark'; break;
        }
        
        row.innerHTML = `
            <td>
                <div>
                    <strong>${profile.profile_name}</strong>
                    <div class="small text-muted">ID: ${profile.profile_id || 'N/A'}</div>
                    <div class="small text-muted">${profile.description || 'No description'}</div>
                </div>
            </td>
            <td>
                <span class="badge ${badgeClass}">${profile.template_name}</span>
                <div class="small text-muted">${profile.category}</div>
            </td>
            <td>${createdDate}</td>
            <td>
                <button class="btn btn-sm btn-primary view-profile-btn" 
                        data-profile-id="${profile.profile_id}" 
                        data-profile-name="${profile.profile_name}">
                    <i class="fas fa-eye me-1"></i>View
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Add event listeners to view buttons
    tbody.querySelectorAll('.view-profile-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const profileId = this.dataset.profileId;
            const profileName = this.dataset.profileName;
            viewProfileDetails(profileId, profileName);
        });
    });
    
    // Show results
    container.style.display = 'block';
    noResults.style.display = 'none';
}

// Show no results message
function showNoResults() {
    document.getElementById('profile-results').style.display = 'none';
    document.getElementById('profile-no-results').style.display = 'block';
}

// Show/hide loading indicator
function showLoading(show) {
    document.getElementById('profile-loading').style.display = show ? 'block' : 'none';
}

// View detailed information for a specific profile
function viewProfileDetails(profileId, profileName) {
    // For now, we can create a simple modal or navigate to a dedicated page
    // Since no specific route exists yet, let's create a simple alert with profile info
    // This can be enhanced later with a proper profile detail view
    
    // Navigate to a profile detail page (this route would need to be created in the backend)
    window.location.href = `/profile-detail/${encodeURIComponent(profileId)}?name=${encodeURIComponent(profileName)}`;
}

// Debounce function for search input
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Format currency values
function formatCurrency(amount) {
    if (amount === null || amount === undefined || isNaN(amount)) {
        return '0.00';
    }
    return parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Add template context header when navigating from template
function addTemplateContextHeader(templateName) {
    const pageHeader = document.querySelector('h1');
    if (pageHeader) {
        // Add a context breadcrumb
        const contextDiv = document.createElement('div');
        contextDiv.className = 'alert alert-info mb-3';
        contextDiv.innerHTML = `
            <div class="d-flex align-items-center justify-content-between">
                <div>
                    <i class="fas fa-filter me-2"></i>
                    <strong>Filtered View:</strong> Showing profiles generated from template "<strong>${templateName}</strong>"
                </div>
                <div>
                    <a href="/profiles" class="btn btn-sm btn-outline-secondary">
                        <i class="fas fa-arrow-left me-1"></i>Back to All Templates
                    </a>
                    <button onclick="clearTemplateFilter()" class="btn btn-sm btn-secondary ms-2">
                        <i class="fas fa-times me-1"></i>Show All Profiles
                    </button>
                </div>
            </div>
        `;
        pageHeader.parentNode.insertBefore(contextDiv, pageHeader.nextSibling);
    }
}

// Clear template filter and show all profiles
function clearTemplateFilter() {
    // Remove URL parameters
    const url = new URL(window.location);
    url.searchParams.delete('template_id');
    url.searchParams.delete('template_name');
    window.history.pushState({}, '', url);
    
    // Remove context header
    const contextAlert = document.querySelector('.alert-info');
    if (contextAlert) {
        contextAlert.remove();
    }
    
    // Clear template filter dropdown and reload all profiles
    document.getElementById('template-filter').value = '';
    searchProfiles();
}

// Page-specific database connection handler
function onDatabaseConnected(dbName) {
    // Reload profiles when database changes
    loadTemplateOptions();
    setTimeout(() => {
        searchProfiles();
    }, 500);
}