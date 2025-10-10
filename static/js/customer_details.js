/**
 * Customer Details JavaScript
 * Handles individual customer display, account charts, and account creation
 */

// Render account chart with analytics data
async function renderAccountChart(accountId) {
    try {
        const chartCanvas = document.getElementById(`chart-${accountId}`);
        if (!chartCanvas) return;
        
        // Fetch real data
        const response = await fetch(`/api/account-analytics/${accountId}`);
        const data = await response.json();
        
        let labels, countData, amountData;
        
        if (data.success && data.chart_data && data.chart_data.months && data.chart_data.months.length > 0) {
            // Use real data
            labels = data.chart_data.months;
            countData = data.chart_data.transaction_counts;
            amountData = data.chart_data.total_amounts;
            console.log(`Using real data for ${accountId}:`, labels);
        } else {
            // Generate dummy data if no real data available
            console.log(`No real data for ${accountId}, using dummy data`);
            labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
            countData = [12, 19, 8, 15, 23, 10];
            amountData = [-1200, 850, -450, 1100, -890, 650];
        }
        
        const ctx = chartCanvas.getContext('2d');
        
        // Destroy existing chart if it exists
        if (window.accountCharts && window.accountCharts[accountId]) {
            window.accountCharts[accountId].destroy();
        }
        
        // Initialize charts storage
        if (!window.accountCharts) {
            window.accountCharts = {};
        }
        
        window.accountCharts[accountId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Transaction Count',
                    data: countData,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    yAxisID: 'y'
                }, {
                    label: 'Net Amount ($)',
                    data: amountData,
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Month'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Transaction Count'
                        },
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Amount ($)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            }
        });
        
    } catch (error) {
        console.error(`Error rendering chart for account ${accountId}:`, error);
        
        // Fallback to test chart with dummy data
        testChartWithDummyData(accountId);
    }
}

// Render all account charts on the page
function renderAllAccountCharts() {
    // Find all chart canvases and render their charts
    const chartCanvases = document.querySelectorAll('canvas[id^="chart-"]');
    chartCanvases.forEach(canvas => {
        const accountId = canvas.id.replace('chart-', '');
        renderAccountChart(accountId);
    });
}

// Test chart with dummy data for fallback
function testChartWithDummyData(accountId) {
    const chartCanvas = document.getElementById(`chart-${accountId}`);
    if (!chartCanvas) return;
    
    const ctx = chartCanvas.getContext('2d');
    
    // Destroy existing chart if it exists
    if (window.accountCharts && window.accountCharts[accountId]) {
        window.accountCharts[accountId].destroy();
    }
    
    // Initialize charts storage
    if (!window.accountCharts) {
        window.accountCharts = {};
    }
    
    window.accountCharts[accountId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Transaction Count',
                data: [5, 8, 3, 12, 6, 9],
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                yAxisID: 'y'
            }, {
                label: 'Net Amount ($)',
                data: [-200, 450, -100, 800, -350, 220],
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Month'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Transaction Count'
                    },
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Amount ($)'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            }
        }
    });
}

// Initialize account creation form
function initializeAccountCreationForm() {
    const createAccountBtn = document.getElementById('create-account-btn');
    if (createAccountBtn) {
        createAccountBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            
            // Get customer ID from the page
            const customerIdElement = document.querySelector('[data-customer-id]');
            if (!customerIdElement) {
                alert('Customer ID not found');
                return;
            }
            
            const customerId = customerIdElement.dataset.customerId;
            
            // Get form data
            const accountType = document.getElementById('account_type').value;
            const initialBalance = parseFloat(document.getElementById('initial_balance').value) || 0;
            
            const accountData = {
                customer_id: customerId,
                account_type: accountType,
                balance: initialBalance,
                available_balance: initialBalance
            };
            
            try {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creating...';
                this.disabled = true;
                
                const response = await fetch('/api/create-account', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(accountData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('Account created successfully!');
                    // Refresh the page to show the new account
                    window.location.reload();
                } else {
                    alert(`Failed to create account: ${result.error}`);
                }
            } catch (error) {
                console.error('Error creating account:', error);
                alert('Error creating account. Please try again.');
            } finally {
                this.innerHTML = '<i class="fas fa-plus me-2"></i>Create Account';
                this.disabled = false;
            }
        });
    }
}

// Initialize page when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Render charts after page loads
    setTimeout(() => {
        renderAllAccountCharts();
    }, 500);
    
    // Initialize account creation form
    initializeAccountCreationForm();
});