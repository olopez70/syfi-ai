/* Shared Navigation JavaScript */

// Load available databases
async function loadDatabases() {
    try {
        const response = await fetch('/api/databases');
        const data = await response.json();
        
        // Update both old and new selects (for backward compatibility)
        const selects = [
            document.getElementById('header-database-select'),
            document.getElementById('modal-database-select')
        ];
        
        selects.forEach(select => {
            if (select) {
                select.innerHTML = '<option value="">Select Database...</option>';
                data.databases.forEach(db => {
                    const option = document.createElement('option');
                    option.value = db.name;
                    option.textContent = `${db.name} (${formatFileSize(db.size)})`;
                    select.appendChild(option);
                });
            }
        });
    } catch (error) {
        console.error('Failed to load databases:', error);
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Sidebar functionality
function initializeSidebar() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const body = document.body;
    
    // Toggle sidebar
    function toggleSidebar() {
        const isOpen = sidebar.classList.contains('open');
        
        if (isOpen) {
            sidebar.classList.remove('open');
            overlay.classList.remove('show');
            body.classList.remove('sidebar-open');
        } else {
            sidebar.classList.add('open');
            overlay.classList.add('show');
            body.classList.add('sidebar-open');
        }
    }
    
    // Sidebar toggle button
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }
    
    // Overlay click to close
    if (overlay) {
        overlay.addEventListener('click', toggleSidebar);
    }
    

    
    // Close sidebar on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('open')) {
            toggleSidebar();
        }
    });
    
    // Responsive behavior
    function handleResize() {
        if (window.innerWidth > 768) {
            overlay.classList.remove('show');
            if (!sidebar.classList.contains('open')) {
                body.classList.add('sidebar-open');
                sidebar.classList.add('open');
            }
        } else {
            body.classList.remove('sidebar-open');
        }
    }
    
    // Initialize on load
    if (window.innerWidth > 768) {
        sidebar.classList.add('open');
        body.classList.add('sidebar-open');
    }
    
    window.addEventListener('resize', handleResize);
}

// Connect to database
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded event fired');
    
    // Initialize sidebar functionality
    initializeSidebar();
    
    // Load databases and current database status on page load
    loadDatabases();
    
    // Call immediately
    loadCurrentDatabase();
    
    // Also call with delay as backup
    setTimeout(() => {
        console.log('Timeout callback - calling loadCurrentDatabase again');
        loadCurrentDatabase();
    }, 500);

    // Modal Connect button functionality
    const modalConnectBtn = document.getElementById('modal-connect-btn');
    if (modalConnectBtn) {
        modalConnectBtn.addEventListener('click', async () => {
            const select = document.getElementById('modal-database-select');
            const dbName = select.value;
            
            if (!dbName) {
                alert('Please select a database first');
                return;
            }

            try {
                modalConnectBtn.disabled = true;
                modalConnectBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Connecting...';

                const response = await fetch(`/connect/${dbName}`);
                const data = await response.json();
                
                if (data.success) {
                    // Refresh current database info to get the display name
                    loadCurrentDatabase();
                    
                    // Close the modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('changeDatabaseModal'));
                    if (modal) {
                        modal.hide();
                    }
                    
                    // Trigger any page-specific database connection handlers
                    if (typeof onDatabaseConnected === 'function') {
                        onDatabaseConnected(dbName);
                    }
                } else {
                    alert(`Failed to connect to database: ${data.error}`);
                }
            } catch (error) {
                console.error('Database connection failed:', error);
                alert('Failed to connect to database. Please try again.');
            } finally {
                modalConnectBtn.disabled = false;
                modalConnectBtn.innerHTML = '<i class="fas fa-plug me-2"></i>Connect';
            }
        });
    }

    // Modal Create database functionality
    const modalCreateDbBtn = document.getElementById('modal-create-database-btn');
    if (modalCreateDbBtn) {
        modalCreateDbBtn.addEventListener('click', async () => {
            const nameInput = document.getElementById('modal-new-database-name');
            const templateSelect = document.getElementById('modal-database-template');
            const dbName = nameInput.value.trim();
            const template = templateSelect.value;
            
            if (!dbName) {
                alert('Please enter a database name');
                return;
            }

            // Validate database name
            if (!/^[a-zA-Z0-9_-]+$/.test(dbName)) {
                alert('Database name can only contain letters, numbers, underscores, and hyphens');
                return;
            }

            try {
                modalCreateDbBtn.disabled = true;
                modalCreateDbBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creating...';

                const response = await fetch('/api/create-database', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name: dbName,
                        template: template
                    })
                });

                const data = await response.json();

                if (data.success) {
                    alert(`Database "${dbName}.db" created successfully!`);
                    nameInput.value = '';
                    templateSelect.value = 'empty';
                    
                    // Refresh database list
                    await loadDatabases();
                    
                    // Close the modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('createDatabaseModal'));
                    if (modal) {
                        modal.hide();
                    }
                    
                    // Auto-connect to the new database
                    if (data.database_path) {
                        const connectResponse = await fetch(`/connect/${dbName}.db`);
                        const connectData = await connectResponse.json();
                        if (connectData.success) {
                            loadCurrentDatabase();
                            if (typeof onDatabaseConnected === 'function') {
                                onDatabaseConnected(`${dbName}.db`);
                            }
                        }
                    }
                } else {
                    alert(`Failed to create database: ${data.error}`);
                }
            } catch (error) {
                console.error('Database creation failed:', error);
                alert('Failed to create database. Please try again.');
            } finally {
                modalCreateDbBtn.disabled = false;
                modalCreateDbBtn.innerHTML = '<i class="fas fa-plus me-2"></i>Create Database';
            }
        });
    }

    // Modal Refresh databases functionality
    const modalRefreshBtn = document.getElementById('modal-refresh-databases');
    if (modalRefreshBtn) {
        modalRefreshBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            modalRefreshBtn.disabled = true;
            modalRefreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Refreshing...';
            
            await loadDatabases();
            
            setTimeout(() => {
                modalRefreshBtn.disabled = false;
                modalRefreshBtn.innerHTML = '<i class="fas fa-refresh me-2"></i>Refresh Databases';
            }, 500);
        });
    }

    // Modal event handlers to load databases when opened
    const changeDatabaseModal = document.getElementById('changeDatabaseModal');
    if (changeDatabaseModal) {
        changeDatabaseModal.addEventListener('show.bs.modal', function (event) {
            loadDatabases();
        });
    }
});

// Backup - also try window.onload in case DOMContentLoaded doesn't work
window.addEventListener('load', function() {
    console.log('window load event fired - calling loadCurrentDatabase as backup');
    setTimeout(() => {
        loadCurrentDatabase();
    }, 100);
});

// Load current database status
function loadCurrentDatabase() {
    console.log('loadCurrentDatabase() called at:', new Date().toISOString());
    
    const dbStatus = document.getElementById('header-db-status');
    const dbName = document.getElementById('header-db-name');
    
    console.log('Found elements:', {
        dbStatus: !!dbStatus,
        dbName: !!dbName,
        dbStatusId: dbStatus?.id,
        dbNameId: dbName?.id
    });
    
    if (!dbStatus || !dbName) {
        console.error('Database status elements not found in DOM');
        console.log('Available elements with "header" in id:', 
            Array.from(document.querySelectorAll('[id*="header"]')).map(el => el.id)
        );
        return;
    }
    
    console.log('Making API call to /api/current-database');
    fetch('/api/current-database')
        .then(response => {
            console.log('API response received, status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('API data:', data);
            
            // Update header button elements
            if (data.connected && data.database) {
                console.log('Setting connected state');
                dbStatus.innerHTML = 'Connected';
                dbStatus.className = 'badge bg-success ms-2';
                dbName.innerHTML = data.display_name;
                
                // Force style updates
                dbStatus.setAttribute('style', 'background-color: #28a745 !important; color: white !important;');
                
                // Update dropdown content
                const currentDbInfo = document.getElementById('header-current-db-info');
                const noDbInfo = document.getElementById('header-no-db-info');
                const dbFilename = document.getElementById('header-current-db-filename');
                const dbLocation = document.getElementById('header-current-db-location');
                
                if (currentDbInfo && noDbInfo) {
                    currentDbInfo.style.display = 'block';
                    noDbInfo.style.display = 'none';
                }
                
                if (dbFilename) {
                    dbFilename.textContent = data.filename || data.database;
                }
                
                if (dbLocation) {
                    dbLocation.textContent = data.location || '-';
                }
                
                console.log('Updated elements:', {
                    statusText: dbStatus.textContent,
                    nameText: dbName.textContent,
                    statusClass: dbStatus.className,
                    dropdownVisible: currentDbInfo?.style.display
                });
            } else {
                console.log('Setting disconnected state');
                dbStatus.innerHTML = 'No Database';
                dbStatus.className = 'badge bg-danger ms-2';
                dbName.innerHTML = 'No Database';
                
                // Force style updates  
                dbStatus.setAttribute('style', 'background-color: #dc3545 !important; color: white !important;');
                
                // Update dropdown content
                const currentDbInfo = document.getElementById('header-current-db-info');
                const noDbInfo = document.getElementById('header-no-db-info');
                
                if (currentDbInfo && noDbInfo) {
                    currentDbInfo.style.display = 'none';
                    noDbInfo.style.display = 'block';
                }
            }
        })
        .catch(error => {
            console.error('Error loading current database:', error);
            if (dbStatus && dbName) {
                dbStatus.textContent = 'Error';
                dbStatus.className = 'badge bg-danger ms-2';
                dbName.textContent = 'Error';
            }
        });
}