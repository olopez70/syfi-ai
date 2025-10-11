/**
 * Home Page JavaScript
 * Handles database connection and status display on the home page
 */

let currentDatabase = null;

// Load current database status and available databases
async function loadDatabaseInfo() {
    try {
        // Get current database
        const currentResponse = await fetch('/api/current-database');
        const currentData = await currentResponse.json();
        
        if (currentData.success && currentData.connected) {
            currentDatabase = currentData.database;
            document.getElementById('current-db-name').textContent = currentData.database;
            document.getElementById('db-status').className = 'badge bg-success ms-2';
            document.getElementById('db-status').textContent = 'Connected';
            const dbAlert = document.getElementById('db-alert');
            if (dbAlert) {
                dbAlert.style.display = 'none';
            }
        } else {
            currentDatabase = null;
            document.getElementById('current-db-name').textContent = 'No Database';
            document.getElementById('db-status').className = 'badge bg-danger ms-2';
            document.getElementById('db-status').textContent = 'Disconnected';
            const dbAlert = document.getElementById('db-alert');
            if (dbAlert) {
                dbAlert.style.display = 'block';
            }
        }

        // Get available databases
        const dbResponse = await fetch('/api/databases');
        const dbData = await dbResponse.json();
        
        const select = document.getElementById('database-select');
        if (select) {
            select.innerHTML = '<option value="">Select Database...</option>';
            
            dbData.databases.forEach(db => {
                const option = document.createElement('option');
                option.value = db.name;
                option.textContent = db.name;
                if (db.name === currentDatabase) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        }
        
    } catch (error) {
        console.error('Error loading database info:', error);
    }
}

// Connect to database
async function connectDatabase() {
    const select = document.getElementById('database-select');
    if (!select) return;
    
    const selectedDb = select.value;
    if (!selectedDb) return;

    try {
        const response = await fetch(`/connect/${selectedDb}`);
        const data = await response.json();
        
        if (data.success) {
            loadDatabaseInfo();
        } else {
            alert('Failed to connect to database: ' + data.error);
        }
    } catch (error) {
        console.error('Error connecting to database:', error);
        alert('Error connecting to database');
    }
}

// Initialize event listeners
function initializeEventListeners() {
    // Connect button
    const connectBtn = document.getElementById('connect-btn');
    if (connectBtn) {
        connectBtn.addEventListener('click', connectDatabase);
    }
    
    // Refresh databases button
    const refreshBtn = document.getElementById('refresh-databases');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadDatabaseInfo);
    }
}

// Load entity statistics for multi-entity banking demo
async function loadEntityOverview() {
    try {
        const response = await fetch('/api/entity-stats');
        const data = await response.json();
        
        const container = document.getElementById('entityOverview');
        if (!container) return;
        
        if (data.success && data.entities) {
            container.innerHTML = '';
            
            // Sort entities by transaction volume
            const sortedEntities = Object.entries(data.entities).sort((a, b) => 
                b[1].total_volume - a[1].total_volume
            );
            
            sortedEntities.forEach(([entityType, entityData]) => {
                const entityCard = createEntityCard(entityType, entityData);
                container.appendChild(entityCard);
            });
            
            // If no entities found, show message
            if (sortedEntities.length === 0) {
                container.innerHTML = `
                    <div class="col-12 text-center">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle me-2"></i>
                            No entity data available in current database
                        </div>
                    </div>
                `;
            }
        } else {
            container.innerHTML = `
                <div class="col-12 text-center">
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Could not load entity statistics: ${data.error || 'Unknown error'}
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading entity overview:', error);
        const container = document.getElementById('entityOverview');
        if (container) {
            container.innerHTML = `
                <div class="col-12 text-center">
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Error loading entity data
                    </div>
                </div>
            `;
        }
    }
}

// Create entity card HTML
function createEntityCard(entityType, entityData) {
    const div = document.createElement('div');
    div.className = 'col-md-6 col-lg-3';
    
    const customerCount = entityData.customers.length;
    const avgVolume = customerCount > 0 ? entityData.total_volume / customerCount : 0;
    
    div.innerHTML = `
        <div class="card h-100 border-${entityData.color}">
            <div class="card-header bg-${entityData.color} text-white">
                <h6 class="card-title mb-0">
                    <span style="font-size: 1.2em;">${entityData.icon}</span>
                    ${entityType}
                </h6>
            </div>
            <div class="card-body">
                <div class="row text-center">
                    <div class="col-6">
                        <div class="small text-muted">Customers</div>
                        <div class="fw-bold">${customerCount}</div>
                    </div>
                    <div class="col-6">
                        <div class="small text-muted">Accounts</div>
                        <div class="fw-bold">${entityData.total_accounts}</div>
                    </div>
                </div>
                <hr class="my-2">
                <div class="row text-center">
                    <div class="col-12">
                        <div class="small text-muted">Total Volume</div>
                        <div class="fw-bold text-${entityData.color}">$${entityData.total_volume.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0})}</div>
                    </div>
                </div>
                <div class="row text-center mt-2">
                    <div class="col-12">
                        <div class="small text-muted">Transactions</div>
                        <div class="fw-bold">${entityData.total_transactions.toLocaleString()}</div>
                    </div>
                </div>
            </div>
            <div class="card-footer">
                <button class="btn btn-outline-${entityData.color} btn-sm w-100" onclick="viewEntityDetails('${entityType}')">
                    <i class="fas fa-eye me-1"></i>View Details
                </button>
            </div>
        </div>
    `;
    
    return div;
}

// View entity details (redirect to customers page with filter)
function viewEntityDetails(entityType) {
    // For now, just redirect to customers page
    // TODO: Add entity filtering to customers page
    window.location.href = '/customers';
}

// Initialize page when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    loadDatabaseInfo();
    loadEntityOverview();
    initializeEventListeners();
});