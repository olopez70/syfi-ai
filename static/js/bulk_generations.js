/**
 * Bulk Generations JavaScript
 * Handles bulk generation operations, history, and status tracking
 */

let currentDatabase = null;

// Page-specific database connection handler
function onDatabaseConnected(dbName) {
    currentDatabase = dbName;
    loadBulkGenerations();
}

// Initialize bulk generations page - check database and load data
async function initializeBulkGenerationsPage() {
    try {
        const response = await fetch('/api/current-database');
        const data = await response.json();
        
        if (data.database) {
            currentDatabase = data.database;
            // Database status display is now handled by shared_navigation.js
            if (document.getElementById('db-alert')) {
                document.getElementById('db-alert').style.display = 'none';
            }
            loadBulkGenerations();
        } else {
            // Database status display is now handled by shared_navigation.js
            if (document.getElementById('db-alert')) {
                document.getElementById('db-alert').style.display = 'block';
            }
            if (document.getElementById('generations-table-container')) {
                document.getElementById('generations-table-container').style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error loading current database:', error);
        // Database status display is now handled by shared_navigation.js
    }
}

// Load bulk generations from API
async function loadBulkGenerations() {
    if (!currentDatabase) return;
    
    try {
        const response = await fetch('/api/bulk-generations');
        const data = await response.json();
        
        if (data.success) {
            displayBulkGenerations(data.bulk_generations);
            updateStatsOverview(data.bulk_generations);
        } else {
            console.error('Error loading bulk generations:', data.error);
            showNoDataMessage();
        }
    } catch (error) {
        console.error('Error loading bulk generations:', error);
        showNoDataMessage();
    }
}

// Display bulk generations in table
function displayBulkGenerations(generations) {
    const tbody = document.getElementById('generations-tbody');
    
    if (generations.length === 0) {
        showNoDataMessage();
        return;
    }
    
    document.getElementById('no-data-message').style.display = 'none';
    document.getElementById('generations-table-container').style.display = 'block';
    
    tbody.innerHTML = generations.map(gen => {
        const createdDate = new Date(gen.created_date);
        const formattedDate = createdDate.toLocaleDateString() + ' ' + createdDate.toLocaleTimeString();
        
        let statusBadge = '';
        switch (gen.status) {
            case 'completed':
                statusBadge = '<span class="badge bg-success">Completed</span>';
                break;
            case 'running':
                statusBadge = '<span class="badge bg-warning">Running</span>';
                break;
            case 'failed':
                statusBadge = '<span class="badge bg-danger">Failed</span>';
                break;
            default:
                statusBadge = '<span class="badge bg-secondary">Unknown</span>';
        }
        
        return `
            <tr>
                <td><code>${gen.bulk_id}</code></td>
                <td>${gen.label || '<span class="text-muted">No label</span>'}</td>
                <td><span class="badge bg-info">${gen.operation_type}</span></td>
                <td class="text-truncate" style="max-width: 200px;" title="${gen.profile_description || ''}">${gen.profile_description || '<span class="text-muted">No profile</span>'}</td>
                <td><small>${formattedDate}</small></td>
                <td>
                    <a href="/customers?bulk_generation_id=${gen.bulk_id}" class="btn btn-sm btn-outline-primary" title="View customers from this bulk generation">
                        ${gen.total_customers_created || 0}
                    </a>
                </td>
                <td><span class="badge bg-secondary">${gen.total_accounts_created || 0}</span></td>
                <td><span class="badge bg-secondary">${gen.total_transactions_created || 0}</span></td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-sm btn-outline-info" onclick="showBulkDetails('${gen.bulk_id}')" title="View details">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// Update statistics overview
function updateStatsOverview(generations) {
    if (!generations || generations.length === 0) return;
    
    const totalOperations = generations.length;
    const completedOperations = generations.filter(g => g.status === 'completed').length;
    const totalCustomers = generations.reduce((sum, g) => sum + (g.count || 0), 0);
    
    // Update stats if elements exist
    if (document.getElementById('total-operations')) {
        document.getElementById('total-operations').textContent = totalOperations;
    }
    if (document.getElementById('completed-operations')) {
        document.getElementById('completed-operations').textContent = completedOperations;
    }
    if (document.getElementById('total-customers')) {
        document.getElementById('total-customers').textContent = totalCustomers;
    }
}

// Show no data message
function showNoDataMessage() {
    if (document.getElementById('no-data-message')) {
        document.getElementById('no-data-message').style.display = 'block';
    }
    if (document.getElementById('generations-table-container')) {
        document.getElementById('generations-table-container').style.display = 'none';
    }
}

// Show bulk generation details
async function showBulkDetails(bulkId) {
    try {
        const response = await fetch(`/api/bulk-generation/${bulkId}`);
        const data = await response.json();
        
        if (data.success) {
            displayBulkDetailsModal(data.bulk_generation);
        } else {
            alert(`Failed to load details: ${data.error}`);
        }
    } catch (error) {
        console.error('Error loading bulk details:', error);
        alert('Failed to load bulk generation details');
    }
}

// Display bulk details modal
function displayBulkDetailsModal(data) {
    // Update modal content
    document.getElementById('modal-bulk-id').textContent = data.bulk_id;
    document.getElementById('modal-label').textContent = data.label || 'N/A';
    document.getElementById('modal-operation-type').textContent = data.operation_type || 'N/A';
    document.getElementById('modal-profile-description').textContent = data.profile_description || 'N/A';
    document.getElementById('modal-count').textContent = data.count || '0';
    document.getElementById('modal-created-date').textContent = new Date(data.created_date).toLocaleString();
    document.getElementById('modal-status').textContent = data.status || 'Unknown';
    
    // Update status badge color
    const statusElement = document.getElementById('modal-status');
    statusElement.className = 'badge ';
    switch (data.status) {
        case 'completed':
            statusElement.className += 'bg-success';
            break;
        case 'running':
            statusElement.className += 'bg-warning';
            break;
        case 'failed':
            statusElement.className += 'bg-danger';
            break;
        default:
            statusElement.className += 'bg-secondary';
    }
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('bulkDetailsModal'));
    modal.show();
}

// Search by bulk ID
function searchByBulkId(bulkId) {
    const searchInput = document.getElementById('bulk-id-search');
    if (searchInput) {
        searchInput.value = bulkId;
        
        // Filter table rows
        const tbody = document.getElementById('generations-tbody');
        const rows = tbody.querySelectorAll('tr');
        
        rows.forEach(row => {
            const firstCell = row.cells[0];
            if (firstCell && firstCell.textContent.includes(bulkId)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
}

// Initialize bulk generation form
function initializeBulkForm() {
    const form = document.getElementById('bulk-customer-form');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const bulkData = {};
            
            for (let [key, value] of formData.entries()) {
                bulkData[key] = value;
            }
            
            // Convert count to integer
            bulkData.count = parseInt(bulkData.count);
            bulkData.accounts_per_customer = parseInt(bulkData.accounts_per_customer);
            
            try {
                const submitBtn = this.querySelector('button[type="submit"]');
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Generating...';
                submitBtn.disabled = true;
                
                const response = await fetch('/api/bulk-generate-customers', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(bulkData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(`Bulk generation started! Bulk ID: ${result.bulk_id}`);
                    this.reset();
                    
                    // Refresh the bulk generations list
                    setTimeout(() => {
                        loadBulkGenerations();
                    }, 1000);
                } else {
                    alert(`Failed to start bulk generation: ${result.error}`);
                }
            } catch (error) {
                console.error('Error starting bulk generation:', error);
                alert('Error starting bulk generation. Please try again.');
            } finally {
                const submitBtn = this.querySelector('button[type="submit"]');
                submitBtn.innerHTML = '<i class="fas fa-users me-2"></i>Generate Customers';
                submitBtn.disabled = false;
            }
        });
    }
}

// Initialize tab functionality
function initializeTabs() {
    const historyTab = document.querySelector('a[href="#history"]');
    if (historyTab) {
        historyTab.addEventListener('shown.bs.tab', function (event) {
            loadBulkGenerations();
        });
    }
}

// Navigate to customer search with bulk generation ID filter
function viewBulkCustomers(bulkId) {
    // Navigate to customers page with bulk generation ID parameter
    window.location.href = `/customers?bulk_generation_id=${encodeURIComponent(bulkId)}`;
}

// Initialize page when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeBulkGenerationsPage();
    initializeBulkForm();
    initializeTabs();
});