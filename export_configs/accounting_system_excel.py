# EXPORT_SCHEMA configuration for accounting system import
EXPORT_SCHEMA = {
    "name": "accounting_system_excel",
    "description": "Export financial data in Excel format for accounting system import",
    "version": "1.0",
    "format": "excel",
    "encoding": "utf-8",
    "include_headers": True,
    
    "tables": [
        {
            "table_name": "customers",
            "export_name": "Customers",
            "sort_by": "customer_id",
            "fields": [
                {
                    "source_field": "customer_id",
                    "target_field": "Customer_ID",
                    "data_type": "string"
                },
                {
                    "source_field": "first_name",
                    "target_field": "First_Name", 
                    "data_type": "string"
                },
                {
                    "source_field": "last_name",
                    "target_field": "Last_Name",
                    "data_type": "string"
                },
                {
                    "source_field": "email",
                    "target_field": "Email_Address",
                    "data_type": "string"
                },
                {
                    "source_field": "created_date",
                    "target_field": "Registration_Date",
                    "data_type": "date",
                    "format": "%Y-%m-%d"
                }
            ]
        },
        {
            "table_name": "accounts",
            "export_name": "Accounts",
            "sort_by": "account_id",
            "fields": [
                {
                    "source_field": "account_id",
                    "target_field": "Account_ID",
                    "data_type": "string"
                },
                {
                    "source_field": "customer_id", 
                    "target_field": "Customer_ID",
                    "data_type": "string"
                },
                {
                    "source_field": "account_type",
                    "target_field": "Account_Type",
                    "data_type": "string",
                    "transform": "uppercase"
                },
                {
                    "source_field": "balance",
                    "target_field": "Current_Balance",
                    "data_type": "float"
                },
                {
                    "source_field": "created_date",
                    "target_field": "Opened_Date",
                    "data_type": "date",
                    "format": "%Y-%m-%d"
                }
            ]
        },
        {
            "table_name": "transactions",
            "export_name": "Transactions",
            "sort_by": "transaction_date DESC",
            "filters": {
                "transaction_date": ">=2024-01-01"  # Only current year
            },
            "fields": [
                {
                    "source_field": "transaction_id",
                    "target_field": "Transaction_ID",
                    "data_type": "string"
                },
                {
                    "source_field": "account_id",
                    "target_field": "Account_ID", 
                    "data_type": "string"
                },
                {
                    "source_field": "transaction_type",
                    "target_field": "Transaction_Type",
                    "data_type": "string",
                    "transform": "uppercase"
                },
                {
                    "source_field": "amount",
                    "target_field": "Amount",
                    "data_type": "float"
                },
                {
                    "source_field": "description",
                    "target_field": "Description", 
                    "data_type": "string"
                },
                {
                    "source_field": "transaction_date",
                    "target_field": "Transaction_Date",
                    "data_type": "date",
                    "format": "%Y-%m-%d"
                }
            ]
        }
    ],
    
    "output_options": {
        "worksheet_colors": True,
        "auto_column_width": True,
        "freeze_headers": True
    }
}