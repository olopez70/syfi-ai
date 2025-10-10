// Export Page JavaScript Functionality

let currentSchemas = [];
let currentSelectedSchema = null;

// Initialize export page
document.addEventListener('DOMContentLoaded', function() {
    loadExportSchemas();
    loadRecentExports();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    const schemaSelect = document.getElementById('schema-select');
    const previewBtn = document.getElementById('preview-btn');
    const exportForm = document.getElementById('export-form');
    
    // Schema selection change
    schemaSelect.addEventListener('change', handleSchemaSelection);
    
    // Preview button click
    previewBtn.addEventListener('click', handlePreviewExport);
    
    // Export form submission
    exportForm.addEventListener('submit', handleExportSubmission);
    
    // Setup collapsible card animations
    setupCollapseEventListeners();
}

// Setup collapse event listeners for card animations
function setupCollapseEventListeners() {
    // Schema Details collapse
    const schemaDetailsCollapse = document.getElementById('schema-details-collapse');
    if (schemaDetailsCollapse) {
        schemaDetailsCollapse.addEventListener('show.bs.collapse', function() {
            const button = document.querySelector('[data-bs-target="#schema-details-collapse"]');
            button.setAttribute('aria-expanded', 'true');
        });
        
        schemaDetailsCollapse.addEventListener('hide.bs.collapse', function() {
            const button = document.querySelector('[data-bs-target="#schema-details-collapse"]');
            button.setAttribute('aria-expanded', 'false');
        });
    }
    
    // Preview collapse
    const previewCollapse = document.getElementById('preview-collapse');
    if (previewCollapse) {
        previewCollapse.addEventListener('show.bs.collapse', function() {
            const button = document.querySelector('[data-bs-target="#preview-collapse"]');
            button.setAttribute('aria-expanded', 'true');
        });
        
        previewCollapse.addEventListener('hide.bs.collapse', function() {
            const button = document.querySelector('[data-bs-target="#preview-collapse"]');
            button.setAttribute('aria-expanded', 'false');
        });
    }
}

// Load available export schemas
async function loadExportSchemas() {
    try {
        const response = await fetch('/api/export/schemas');
        const data = await response.json();
        
        const schemaSelect = document.getElementById('schema-select');
        
        if (data.success) {
            currentSchemas = data.schemas;
            
            // Clear existing options
            schemaSelect.innerHTML = '<option value="">Select an export schema...</option>';
            
            // Add schema options
            data.schemas.forEach(schema => {
                const option = document.createElement('option');
                option.value = schema.name;
                option.textContent = `${schema.name} - ${schema.description} (${schema.format.toUpperCase()})`;
                schemaSelect.appendChild(option);
            });
            
            // Enable select if we have schemas
            if (data.schemas.length > 0) {
                schemaSelect.disabled = false;
            }
        } else {
            console.error('Failed to load schemas:', data.error);
            schemaSelect.innerHTML = '<option value="">Error loading schemas</option>';
        }
    } catch (error) {
        console.error('Error loading export schemas:', error);
        const schemaSelect = document.getElementById('schema-select');
        schemaSelect.innerHTML = '<option value="">Error loading schemas</option>';
    }
}

// Handle schema selection
async function handleSchemaSelection(event) {
    const schemaName = event.target.value;
    const previewBtn = document.getElementById('preview-btn');
    const exportBtn = document.getElementById('export-btn');
    
    if (!schemaName) {
        currentSelectedSchema = null;
        hideSchemaDescription();
        hideSchemaDetails();
        hidePreviewPanel();
        previewBtn.disabled = true;
        exportBtn.disabled = true;
        return;
    }
    
    try {
        // Load detailed schema information
        const response = await fetch(`/api/export/schema/${schemaName}`);
        const data = await response.json();
        
        if (data.success) {
            currentSelectedSchema = data.schema;
            displaySchemaDescription(data.schema);
            displaySchemaDetails(data.schema);
            hidePreviewPanel();
            previewBtn.disabled = false;
            exportBtn.disabled = false;
        } else {
            console.error('Failed to load schema details:', data.error);
            alert('Failed to load schema details: ' + data.error);
        }
    } catch (error) {
        console.error('Error loading schema details:', error);
        alert('Error loading schema details');
    }
}

// Display schema description
function displaySchemaDescription(schema) {
    const descriptionDiv = document.getElementById('schema-description');
    const descriptionText = document.getElementById('schema-description-text');
    const formatSpan = document.getElementById('schema-format');
    const versionSpan = document.getElementById('schema-version');
    
    descriptionText.textContent = schema.description;
    formatSpan.textContent = schema.format.toUpperCase();
    versionSpan.textContent = schema.version;
    
    descriptionDiv.style.display = 'block';
    descriptionDiv.classList.add('fade-in-up');
}

// Hide schema description
function hideSchemaDescription() {
    const descriptionDiv = document.getElementById('schema-description');
    descriptionDiv.style.display = 'none';
}

// Display schema details
function displaySchemaDetails(schema) {
    const detailsCard = document.getElementById('schema-details-card');
    const tablesInfo = document.getElementById('schema-tables-info');
    
    let html = '';
    
    schema.tables.forEach(table => {
        html += `
            <div class="table-info">
                <h6><i class="fas fa-table me-2"></i>${table.export_name}</h6>
                <div class="small text-muted mb-2">Source: ${table.table_name}</div>
                <div class="field-mappings">
        `;
        
        table.fields.forEach(field => {
            html += `
                <div class="field-mapping">
                    <span class="field-source">${field.source_field}</span>
                    <i class="fas fa-arrow-right field-arrow"></i>
                    <span class="field-target">${field.target_field}</span>
                    ${field.transform ? `<span class="badge bg-secondary ms-2">${field.transform}</span>` : ''}
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    });
    
    tablesInfo.innerHTML = html;
    detailsCard.style.display = 'block';
    detailsCard.classList.add('fade-in-up');
}

// Hide schema details
function hideSchemaDetails() {
    const detailsCard = document.getElementById('schema-details-card');
    detailsCard.style.display = 'none';
}

// Handle preview export
async function handlePreviewExport() {
    if (!currentSelectedSchema) {
        alert('Please select a schema first');
        return;
    }
    
    const previewBtn = document.getElementById('preview-btn');
    const originalText = previewBtn.innerHTML;
    previewBtn.disabled = true;
    previewBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading Preview...';
    
    try {
        const response = await fetch('/api/export/preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                schema_name: currentSelectedSchema.name,
                limit: 10
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayPreviewData(data.preview);
        } else {
            alert('Preview failed: ' + data.error);
        }
    } catch (error) {
        console.error('Error loading preview:', error);
        alert('Error loading preview');
    } finally {
        previewBtn.disabled = false;
        previewBtn.innerHTML = originalText;
    }
}

// Display preview data
function displayPreviewData(previewData) {
    const previewPanel = document.getElementById('preview-panel');
    const previewContent = document.getElementById('preview-content');
    
    let html = '';
    
    for (const [tableName, tableData] of Object.entries(previewData)) {
        html += `
            <div class="mb-4">
                <h6><i class="fas fa-table me-2"></i>${tableName}</h6>
                <div class="text-muted small mb-2">${tableData.total_rows_available} total rows available</div>
        `;
        
        if (tableData.sample_data && tableData.sample_data.length > 0) {
            html += `
                <div class="table-responsive">
                    <table class="table table-sm preview-table">
                        <thead>
                            <tr>
            `;
            
            // Table headers
            tableData.fields.forEach(field => {
                html += `<th>${field}</th>`;
            });
            
            html += `
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            // Table data
            tableData.sample_data.forEach(row => {
                html += '<tr>';
                tableData.fields.forEach(field => {
                    const value = row[field];
                    html += `<td>${value !== null && value !== undefined ? value : ''}</td>`;
                });
                html += '</tr>';
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            html += '<div class="alert alert-info">No data available for preview</div>';
        }
        
        html += '</div>';
    }
    
    previewContent.innerHTML = html;
    previewPanel.style.display = 'block';
    previewPanel.classList.add('fade-in-up');
}

// Hide preview panel
function hidePreviewPanel() {
    const previewPanel = document.getElementById('preview-panel');
    previewPanel.style.display = 'none';
}

// Handle export form submission
async function handleExportSubmission(event) {
    event.preventDefault();
    
    if (!currentSelectedSchema) {
        alert('Please select a schema first');
        return;
    }
    
    const exportBtn = document.getElementById('export-btn');
    const progressDiv = document.getElementById('export-progress');
    const progressText = document.getElementById('progress-text');
    const outputDir = document.getElementById('output-directory').value;
    
    // Show progress
    exportBtn.disabled = true;
    progressDiv.style.display = 'block';
    progressText.textContent = 'Starting export...';
    
    try {
        const response = await fetch('/api/export/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                schema_name: currentSelectedSchema.name,
                output_dir: outputDir
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            progressText.textContent = 'Export completed successfully!';
            setTimeout(() => {
                progressDiv.style.display = 'none';
                displayExportResults(data);
                loadRecentExports(); // Refresh recent exports
            }, 2000);
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Export failed:', error);
        progressText.textContent = 'Export failed: ' + error.message;
        setTimeout(() => {
            progressDiv.style.display = 'none';
        }, 3000);
    } finally {
        exportBtn.disabled = false;
    }
}

// Display export results
function displayExportResults(exportData) {
    const resultsDiv = document.getElementById('export-results');
    const resultsContent = document.getElementById('export-results-content');
    
    let html = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <div>
                <h6>Export completed successfully!</h6>
                <div class="text-muted">Schema: ${exportData.schema} | Format: ${exportData.format.toUpperCase()}</div>
            </div>
            <button class="btn btn-primary" onclick="downloadAllFiles('${exportData.schema}', '${exportData.format}', this)">
                <i class="fas fa-download-alt me-2"></i>Download All (ZIP)
            </button>
        </div>
    `;
    
    exportData.files.forEach(file => {
        html += `
            <div class="export-file-item">
                <div class="file-info">
                    <div class="file-details">
                        <div class="file-name">
                            <i class="fas fa-file me-2"></i>${file.filename}
                        </div>
                        <div class="file-stats">
                            Table: ${file.table} | Rows: ${file.rows.toLocaleString()}
                        </div>
                    </div>
                    <button class="btn download-btn" onclick="downloadFile('${file.filename}')">
                        <i class="fas fa-download me-2"></i>Download
                    </button>
                </div>
            </div>
        `;
    });
    
    resultsContent.innerHTML = html;
    resultsDiv.style.display = 'block';
    resultsDiv.classList.add('fade-in-up');
}

// Download file
function downloadFile(filename) {
    window.open(`/api/export/download/${filename}`, '_blank');
}

// Download all files as ZIP
async function downloadAllFiles(schema, format, buttonElement) {
    try {
        // Get the button to show loading state
        const button = buttonElement || event.target;
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creating ZIP...';
        
        const response = await fetch('/api/export/download-all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                schema: schema,
                format: format
            })
        });
        
        if (response.ok) {
            // Get the ZIP file as blob and download it
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${schema}_export_${format}_${new Date().getTime()}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const errorData = await response.json();
            alert(`Download failed: ${errorData.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error downloading all files:', error);
        alert('Error downloading files. Please try again.');
    } finally {
        // Restore button state
        const button = buttonElement || event.target;
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-download-alt me-2"></i>Download All (ZIP)';
    }
}

// Load recent exports
async function loadRecentExports() {
    const loadingDiv = document.getElementById('recent-exports-loading');
    const contentDiv = document.getElementById('recent-exports-content');
    
    try {
        const response = await fetch('/api/export/files');
        const data = await response.json();
        
        if (data.success) {
            displayRecentExports(data.files);
        } else {
            contentDiv.innerHTML = '<div class="alert alert-warning">Failed to load recent exports</div>';
        }
    } catch (error) {
        console.error('Error loading recent exports:', error);
        contentDiv.innerHTML = '<div class="alert alert-danger">Error loading recent exports</div>';
    } finally {
        loadingDiv.style.display = 'none';
    }
}

// Display recent exports
function displayRecentExports(files) {
    const contentDiv = document.getElementById('recent-exports-content');
    const selectionControls = document.querySelector('.export-selection-controls');
    
    if (files.length === 0) {
        contentDiv.innerHTML = '<div class="text-muted text-center">No export files found</div>';
        selectionControls.style.display = 'none';
        return;
    }
    
    // Show selection controls if there are files
    selectionControls.style.display = 'block';
    
    let html = '';
    
    files.forEach((file, index) => {
        const fileExtension = file.extension.replace('.', '');
        const fileSize = formatFileSize(file.size);
        const modifiedDate = new Date(file.modified).toLocaleString();
        
        html += `
            <div class="recent-export-item" data-filename="${file.filename}">
                <div class="d-flex align-items-center">
                    <div class="form-check me-3">
                        <input class="form-check-input export-file-checkbox" type="checkbox" 
                               value="${file.filename}" id="export-${index}" 
                               onchange="updateSelectionCount()">
                    </div>
                    <div class="export-file-icon ${fileExtension}">
                        <i class="fas fa-file"></i>
                    </div>
                    <div class="export-file-info">
                        <div class="export-file-name">${file.filename}</div>
                        <div class="export-file-meta">
                            ${fileSize} | Modified: ${modifiedDate}
                        </div>
                    </div>
                </div>
                <button class="btn btn-outline-primary btn-sm" onclick="downloadFile('${file.filename}')">
                    <i class="fas fa-download me-1"></i>Download
                </button>
            </div>
        `;
    });
    
    contentDiv.innerHTML = html;
    
    // Setup select all functionality
    setupSelectAllFunctionality();
    
    // Reset selection state
    updateSelectionCount();
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Setup select all functionality
function setupSelectAllFunctionality() {
    const selectAllCheckbox = document.getElementById('select-all-exports');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.export-file-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateSelectionCount();
        });
    }
}

// Update selection count and button state
function updateSelectionCount() {
    const checkboxes = document.querySelectorAll('.export-file-checkbox');
    const selectedCheckboxes = document.querySelectorAll('.export-file-checkbox:checked');
    const selectAllCheckbox = document.getElementById('select-all-exports');
    const downloadSelectedBtn = document.getElementById('download-selected-btn');
    const selectedCountSpan = document.getElementById('selected-count');
    
    const selectedCount = selectedCheckboxes.length;
    const totalCount = checkboxes.length;
    
    // Update selected count display
    if (selectedCountSpan) {
        selectedCountSpan.textContent = selectedCount;
    }
    
    // Update download button state
    if (downloadSelectedBtn) {
        downloadSelectedBtn.disabled = selectedCount === 0;
    }
    
    // Update select all checkbox state
    if (selectAllCheckbox) {
        if (selectedCount === 0) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = false;
        } else if (selectedCount === totalCount) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = true;
        } else {
            selectAllCheckbox.indeterminate = true;
        }
    }
}

// Download selected files
async function downloadSelectedFiles() {
    const selectedCheckboxes = document.querySelectorAll('.export-file-checkbox:checked');
    const selectedFiles = Array.from(selectedCheckboxes).map(cb => cb.value);
    
    if (selectedFiles.length === 0) {
        alert('Please select files to download');
        return;
    }
    
    if (selectedFiles.length === 1) {
        // Single file - use regular download
        downloadFile(selectedFiles[0]);
        return;
    }
    
    // Multiple files - create ZIP
    const downloadBtn = document.getElementById('download-selected-btn');
    const originalText = downloadBtn.innerHTML;
    
    try {
        downloadBtn.disabled = true;
        downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Creating ZIP...';
        
        const response = await fetch('/api/export/download-selected', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                files: selectedFiles
            })
        });
        
        if (response.ok) {
            // Get the ZIP file as blob and download it
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `selected_exports_${new Date().getTime()}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const errorData = await response.json();
            alert(`Download failed: ${errorData.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error downloading selected files:', error);
        alert('Error downloading files. Please try again.');
    } finally {
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = originalText;
    }
}