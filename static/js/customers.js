/**
 * Customer Management JavaScript
 * Handles customer search, filtering, and display functionality
 */

// Page-specific database connection handler
function onDatabaseConnected(dbName) {
    // Load transaction stats when database is connected
    loadTransactionStats();
}

// Load transaction statistics
async function loadTransactionStats() {
    try {
        const response = await fetch('/api/transaction-stats');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.stats;
            
            // Update transaction type dropdown
            const txTypeSelect = document.getElementById('tx_type');
            // Clear existing options except "All Types"
            txTypeSelect.innerHTML = '<option value="">All Types</option>';
            
            stats.available_types.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type.charAt(0).toUpperCase() + type.slice(1) + 's';
                txTypeSelect.appendChild(option);
            });
            
            // Set default date range if we have data
            if (stats.earliest_date && stats.latest_date) {
                // Set end date to latest transaction date
                document.getElementById('tx_end_date').value = stats.latest_date;
                
                // Set start date to 3 months before latest date, or earliest date if less than 3 months of data
                const latestDate = new Date(stats.latest_date);
                const threeMonthsAgo = new Date(latestDate.getTime() - (90 * 24 * 60 * 60 * 1000));
                const earliestDate = new Date(stats.earliest_date);
                const startDate = threeMonthsAgo > earliestDate ? threeMonthsAgo : earliestDate;
                
                document.getElementById('tx_start_date').value = startDate.toISOString().split('T')[0];
            }
            
            console.log('Transaction stats loaded:', stats);
        }
    } catch (error) {
        console.error('Failed to load transaction stats:', error);
    }
}

// Show/hide loading indicator
function showLoading(show) {
    const loading = document.querySelector('.loading');
    loading.style.display = show ? 'block' : 'none';
}

// Display search results
function displayResults(customers) {
    const container = document.getElementById('results-container');
    const tbody = document.getElementById('results-tbody');
    const countSpan = document.getElementById('result-count');
    const basicHeader = document.getElementById('results-header-basic');
    const advancedHeader = document.getElementById('results-header-advanced');
    
    tbody.innerHTML = '';
    countSpan.textContent = customers.length;
    
    // Check if this is a transaction-based search
    const hasTransactionData = customers.length > 0 && customers[0].hasOwnProperty('tx_count');
    
    // Toggle headers
    if (hasTransactionData) {
        basicHeader.style.display = 'none';
        advancedHeader.style.display = '';
    } else {
        basicHeader.style.display = '';
        advancedHeader.style.display = 'none';
    }
    
    if (customers.length === 0) {
        const colspan = hasTransactionData ? '8' : '7';
        tbody.innerHTML = `
            <tr>
                <td colspan="${colspan}" class="no-results">
                    <i class="fas fa-search fa-2x mb-2"></i>
                    <br>No customers found matching your search criteria.
                </td>
            </tr>
        `;
    } else {
        customers.forEach(customer => {
            const row = document.createElement('tr');
            
            if (hasTransactionData) {
                // Advanced results with transaction data
                row.innerHTML = `
                    <td><strong>${customer.customer_id}</strong></td>
                    <td>${customer.company_name ? customer.company_name : `${customer.first_name} ${customer.last_name}`}</td>
                    <td>${customer.email || ''}</td>
                    <td><span class="badge bg-info">${customer.tx_count}</span></td>
                    <td class="${customer.tx_net_amount >= 0 ? 'text-success' : 'text-danger'}">
                        <strong>$${formatCurrency(Math.abs(customer.tx_net_amount))}</strong>
                    </td>
                    <td class="text-success">$${formatCurrency(customer.tx_total_credits)}</td>
                    <td class="text-danger">$${formatCurrency(customer.tx_total_debits)}</td>
                    <td>
                        <a href="/customer/${customer.customer_id}" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-eye me-1"></i>View
                        </a>
                    </td>
                `;
            } else {
                // Basic results - show created date if available (for recent customers preset)
                const addressDisplay = `${customer.address || ''}, ${customer.city || ''} ${customer.state || ''}`.trim();
                const finalAddressDisplay = addressDisplay === ', ' || addressDisplay === '' ? '' : addressDisplay;
                
                row.innerHTML = `
                    <td><strong>${customer.customer_id}</strong></td>
                    <td>${customer.company_name ? customer.company_name : `${customer.first_name} ${customer.last_name}`}</td>
                    <td>${customer.email || ''}</td>
                    <td>${customer.phone || ''}</td>
                    <td>${finalAddressDisplay}</td>
                    <td><small>${customer.created_date_display ? 
                        `<i class="fas fa-clock me-1"></i>${customer.created_date_display}` : 
                        (customer.profile_description || 'N/A')}</small></td>
                    <td>
                        <a href="/customer/${customer.customer_id}" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-eye me-1"></i>View
                        </a>
                    </td>
                `;
            }
            
            tbody.appendChild(row);
        });
    }
    
    container.style.display = 'block';
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

// Hide search results
function hideResults() {
    const container = document.getElementById('results-container');
    container.style.display = 'none';
}

// Apply search preset
function applyPreset(preset) {
    // Clear form first
    clearSearchForm();
    
    switch(preset) {
        case 'high-value':
            document.getElementById('tx_min_amount').value = '1000';
            document.getElementById('tx_type').value = '';
            // Set date range to last 6 months
            const sixMonthsAgo = new Date();
            sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
            document.getElementById('tx_start_date').value = sixMonthsAgo.toISOString().split('T')[0];
            document.getElementById('tx_end_date').value = new Date().toISOString().split('T')[0];
            break;
            
        case 'recent-activity':
            // Set date range to last 30 days
            const thirtyDaysAgo = new Date();
            thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
            document.getElementById('tx_start_date').value = thirtyDaysAgo.toISOString().split('T')[0];
            document.getElementById('tx_end_date').value = new Date().toISOString().split('T')[0];
            document.getElementById('tx_min_count').value = '5';
            break;
            
        case 'new-customers':
            // Clear transaction filters and search by recent customer creation
            const lastMonth = new Date();
            lastMonth.setMonth(lastMonth.getMonth() - 1);
            // We'll use the recent customers search which doesn't use transaction filters
            break;
    }
}

// Database status is now handled by shared_navigation.js

// Set high transaction search preset
function setHighTransactionSearch() {
    clearSearchForm();
    
    // Show the advanced search section first
    const advancedSearch = document.getElementById('advanced-search');
    const toggleBtn = document.getElementById('toggle-advanced');
    if (advancedSearch.style.display === 'none') {
        advancedSearch.style.display = 'block';
        toggleBtn.innerHTML = '<i class="fas fa-cog me-1"></i>Hide Advanced';
        toggleBtn.classList.remove('btn-outline-primary');
        toggleBtn.classList.add('btn-primary');
    }
    
    // Set minimum transaction amount to $1000 for high activity
    document.getElementById('tx_total_min').value = '1000';
    
    // Set minimum transaction count to 20 for high activity
    document.getElementById('tx_count_min').value = '20';
    
    // Set date range to last 6 months
    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
    document.getElementById('tx_start_date').value = sixMonthsAgo.toISOString().split('T')[0];
    document.getElementById('tx_end_date').value = new Date().toISOString().split('T')[0];
    
    // Sort by transaction count descending to show most active customers
    document.getElementById('tx_sort_by').value = 'tx_count';
    document.getElementById('tx_sort_order').value = 'DESC';
}

function setHighVolumeSearch() {
    clearSearchForm();
    
    // Show the advanced search section first
    const advancedSearch = document.getElementById('advanced-search');
    const toggleBtn = document.getElementById('toggle-advanced');
    if (advancedSearch.style.display === 'none') {
        advancedSearch.style.display = 'block';
        toggleBtn.innerHTML = '<i class="fas fa-cog me-1"></i>Hide Advanced';
        toggleBtn.classList.remove('btn-outline-primary');
        toggleBtn.classList.add('btn-primary');
    }
    
    // Set minimum transaction amount to $10,000 for high volume
    document.getElementById('tx_total_min').value = '10000';
    
    // Set date range to last 12 months for comprehensive view
    const twelveMonthsAgo = new Date();
    twelveMonthsAgo.setMonth(twelveMonthsAgo.getMonth() - 12);
    document.getElementById('tx_start_date').value = twelveMonthsAgo.toISOString().split('T')[0];
    document.getElementById('tx_end_date').value = new Date().toISOString().split('T')[0];
    
    // Sort by total credits descending to show highest volume customers
    document.getElementById('tx_sort_by').value = 'tx_total_credits';
    document.getElementById('tx_sort_order').value = 'DESC';
}

// Clear search form
function clearSearchForm() {
    document.getElementById('search-form').reset();
    hideResults();
}

// Initialize event listeners
function initializeEventListeners() {
    // Search form submission
    document.getElementById('search-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const searchParams = new URLSearchParams();
        
        for (let [key, value] of formData.entries()) {
            if (value.trim()) {
                searchParams.append(key, value.trim());
            }
        }
        
        showLoading(true);
        
        try {
            const response = await fetch('/search?' + searchParams.toString());
            const data = await response.json();
            
            if (data.success) {
                displayResults(data.customers);
            } else {
                alert(`Search failed: ${data.error}`);
            }
        } catch (error) {
            console.error('Search failed:', error);
            alert('Search failed. Please try again.');
        } finally {
            showLoading(false);
        }
    });

    // Clear form button
    document.getElementById('clear-btn').addEventListener('click', () => {
        clearSearchForm();
    });

    // Advanced search toggle
    document.getElementById('toggle-advanced').addEventListener('click', function() {
        const advancedSearch = document.getElementById('advanced-search');
        const toggleBtn = this;
        const icon = toggleBtn.querySelector('i');
        
        if (advancedSearch.style.display === 'none') {
            advancedSearch.style.display = 'block';
            toggleBtn.innerHTML = '<i class="fas fa-cog me-1"></i>Hide Advanced';
            toggleBtn.classList.remove('btn-outline-primary');
            toggleBtn.classList.add('btn-primary');
        } else {
            advancedSearch.style.display = 'none';
            toggleBtn.innerHTML = '<i class="fas fa-cog me-1"></i>Advanced';
            toggleBtn.classList.remove('btn-primary');
            toggleBtn.classList.add('btn-outline-primary');
        }
    });

    // Preset buttons
    document.getElementById('preset-recent').addEventListener('click', async function(e) {
        e.preventDefault();
        
        try {
            showLoading(true);
            const response = await fetch('/search/preset/recent');
            const data = await response.json();
            
            if (data.success) {
                displayResults(data.customers);
            } else {
                alert(`Failed to load recent customers: ${data.error}`);
            }
        } catch (error) {
            console.error('Failed to load recent customers:', error);
            alert('Failed to load recent customers');
        } finally {
            showLoading(false);
        }
    });

    // Customer form submission
    document.getElementById('customer-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const customerData = {};
        
        for (let [key, value] of formData.entries()) {
            customerData[key] = value;
        }
        
        try {
            const response = await fetch('/api/create-customer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(customerData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('Customer created successfully!');
                this.reset();
                // Optionally refresh the customer list or redirect
            } else {
                alert(`Failed to create customer: ${result.error}`);
            }
        } catch (error) {
            console.error('Error creating customer:', error);
            alert('Error creating customer. Please try again.');
        }
    });
}

// Check for URL parameters and populate form
function populateFromUrlParameters() {
    const urlParams = new URLSearchParams(window.location.search);
    const bulkGenerationId = urlParams.get('bulk_generation_id');
    const templateCustomers = urlParams.get('template_customers');
    
    if (bulkGenerationId) {
        // Set the bulk generation ID field
        const bulkIdField = document.getElementById('bulk_generation_id');
        if (bulkIdField) {
            bulkIdField.value = bulkGenerationId;
            console.log('Set bulk generation ID to:', bulkGenerationId);
        } else {
            console.error('Bulk generation ID field not found');
        }
        
        // Automatically perform search by submitting the form
        setTimeout(() => {
            const searchForm = document.getElementById('search-form');
            if (searchForm) {
                console.log('Automatically submitting search form');
                searchForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
            } else {
                console.error('Search form not found');
            }
        }, 500); // Small delay to ensure form is ready
    }
    
    if (templateCustomers) {
        // Display customers from template directly
        try {
            const customers = JSON.parse(decodeURIComponent(templateCustomers));
            console.log('Displaying template customers:', customers);
            displayResults(customers);
            
            // Update page title to indicate filtered view
            const pageTitle = document.querySelector('h2');
            if (pageTitle && customers.length > 0) {
                pageTitle.innerHTML = `<i class="fas fa-users me-2"></i>Customers from Profile Template (${customers.length} found)`;
            }
        } catch (error) {
            console.error('Failed to parse template customers:', error);
        }
    }
}

// Initialize page when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Database status is now handled by shared_navigation.js
    initializeEventListeners();
    populateFromUrlParameters();
});