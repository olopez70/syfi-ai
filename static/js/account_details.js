/**
 * Account Details JavaScript
 * Handles individual account display and transaction creation
 */

// Initialize transaction creation form
function initializeTransactionCreationForm() {
    const createTransactionBtn = document.getElementById('create-transaction-btn');
    if (createTransactionBtn) {
        createTransactionBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            
            // Get account ID from the page
            const accountIdElement = document.querySelector('[data-account-id]');
            if (!accountIdElement) {
                alert('Account ID not found');
                return;
            }
            
            const accountId = accountIdElement.dataset.accountId;
            
            // Get form data
            const transactionType = document.getElementById('transaction_type').value;
            const amount = parseFloat(document.getElementById('amount').value);
            const description = document.getElementById('description').value;
            const category = document.getElementById('category').value;
            const merchantName = document.getElementById('merchant_name').value;
            
            // Validate amount
            if (isNaN(amount) || amount === 0) {
                alert('Please enter a valid amount');
                return;
            }
            
            // Adjust amount based on transaction type
            let finalAmount = amount;
            if (transactionType === 'debit' && amount > 0) {
                finalAmount = -amount; // Debits should be negative
            } else if (transactionType === 'credit' && amount < 0) {
                finalAmount = -amount; // Credits should be positive
            }
            
            const transactionData = {
                account_id: accountId,
                transaction_type: transactionType,
                amount: finalAmount,
                description: description,
                category: category,
                merchant_name: merchantName,
                currency: 'USD'
            };
            
            try {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creating...';
                this.disabled = true;
                
                const response = await fetch('/api/create-transaction', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(transactionData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('Transaction created successfully!');
                    // Clear the form
                    document.getElementById('transaction-form').reset();
                    // Refresh the page to show the new transaction
                    window.location.reload();
                } else {
                    alert(`Failed to create transaction: ${result.error}`);
                }
            } catch (error) {
                console.error('Error creating transaction:', error);
                alert('Error creating transaction. Please try again.');
            } finally {
                this.innerHTML = '<i class="fas fa-plus me-2"></i>Add Transaction';
                this.disabled = false;
            }
        });
    }
}

// Update transaction type display
function updateTransactionTypeDisplay() {
    const transactionTypeSelect = document.getElementById('transaction_type');
    const amountInput = document.getElementById('amount');
    
    if (transactionTypeSelect && amountInput) {
        transactionTypeSelect.addEventListener('change', function() {
            const amountLabel = document.querySelector('label[for="amount"]');
            if (amountLabel) {
                if (this.value === 'debit') {
                    amountLabel.innerHTML = 'Amount <small class="text-muted">(will be subtracted from account)</small>';
                    amountInput.placeholder = 'Enter positive amount (e.g., 25.50)';
                } else if (this.value === 'credit') {
                    amountLabel.innerHTML = 'Amount <small class="text-muted">(will be added to account)</small>';
                    amountInput.placeholder = 'Enter positive amount (e.g., 1500.00)';
                } else {
                    amountLabel.innerHTML = 'Amount';
                    amountInput.placeholder = 'Enter amount';
                }
            }
        });
    }
}

// Format currency display in transaction table
function formatTransactionAmounts() {
    const amountCells = document.querySelectorAll('.transaction-amount');
    amountCells.forEach(cell => {
        const amount = parseFloat(cell.textContent.replace(/[^-\d.]/g, ''));
        if (!isNaN(amount)) {
            cell.textContent = `$${Math.abs(amount).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            })}`;
            
            // Add color coding
            if (amount >= 0) {
                cell.classList.add('text-success');
            } else {
                cell.classList.add('text-danger');
            }
        }
    });
}

// Initialize page when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeTransactionCreationForm();
    updateTransactionTypeDisplay();
    formatTransactionAmounts();
});