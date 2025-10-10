# EXPORT_SCHEMA configuration for SQL database migration
EXPORT_SCHEMA = {
    "name": "database_migration_sql",
    "description": "Export all data as SQL INSERT statements for database migration",
    "version": "1.0",
    "format": "sql",
    "encoding": "utf-8",
    
    "tables": [
        {
            "table_name": "customers",
            "export_name": "customers",
            "sort_by": "customer_id",
            "fields": [
                {
                    "source_field": "customer_id",
                    "target_field": "customer_id",
                    "data_type": "string"
                },
                {
                    "source_field": "first_name",
                    "target_field": "first_name",
                    "data_type": "string"
                },
                {
                    "source_field": "last_name",
                    "target_field": "last_name",
                    "data_type": "string"
                },
                {
                    "source_field": "email",
                    "target_field": "email",
                    "data_type": "string"
                },
                {
                    "source_field": "phone",
                    "target_field": "phone",
                    "data_type": "string"
                },
                {
                    "source_field": "address",
                    "target_field": "address",
                    "data_type": "string"
                },
                {
                    "source_field": "city",
                    "target_field": "city",
                    "data_type": "string"
                },
                {
                    "source_field": "state",
                    "target_field": "state",
                    "data_type": "string"
                },
                {
                    "source_field": "zip_code",
                    "target_field": "zip_code",
                    "data_type": "string"
                },
                {
                    "source_field": "date_of_birth",
                    "target_field": "date_of_birth",
                    "data_type": "date"
                },
                {
                    "source_field": "created_date",
                    "target_field": "created_date",
                    "data_type": "date"
                },
                {
                    "source_field": "profile_description",
                    "target_field": "profile_description",
                    "data_type": "string"
                },
                {
                    "source_field": "profile_metadata",
                    "target_field": "profile_metadata",
                    "data_type": "string"
                },
                {
                    "source_field": "bulk_generation_id",
                    "target_field": "bulk_generation_id",
                    "data_type": "string"
                }
            ]
        },
        {
            "table_name": "accounts",
            "export_name": "accounts",
            "sort_by": "account_id",
            "fields": [
                {
                    "source_field": "account_id",
                    "target_field": "account_id",
                    "data_type": "string"
                },
                {
                    "source_field": "customer_id",
                    "target_field": "customer_id",
                    "data_type": "string"
                },
                {
                    "source_field": "account_type",
                    "target_field": "account_type",
                    "data_type": "string"
                },
                {
                    "source_field": "balance",
                    "target_field": "balance",
                    "data_type": "float"
                },
                {
                    "source_field": "interest_rate",
                    "target_field": "interest_rate",
                    "data_type": "float"
                },
                {
                    "source_field": "is_active",
                    "target_field": "is_active",
                    "data_type": "boolean"
                },
                {
                    "source_field": "created_date",
                    "target_field": "created_date",
                    "data_type": "date"
                },
                {
                    "source_field": "bulk_generation_id",
                    "target_field": "bulk_generation_id",
                    "data_type": "string"
                }
            ]
        },
        {
            "table_name": "transactions",
            "export_name": "transactions",
            "sort_by": "transaction_date",
            "fields": [
                {
                    "source_field": "transaction_id",
                    "target_field": "transaction_id",
                    "data_type": "string"
                },
                {
                    "source_field": "account_id",
                    "target_field": "account_id",
                    "data_type": "string"
                },
                {
                    "source_field": "transaction_type",
                    "target_field": "transaction_type",
                    "data_type": "string"
                },
                {
                    "source_field": "amount",
                    "target_field": "amount",
                    "data_type": "float"
                },
                {
                    "source_field": "description",
                    "target_field": "description",
                    "data_type": "string"
                },
                {
                    "source_field": "transaction_date",
                    "target_field": "transaction_date",
                    "data_type": "date"
                },
                {
                    "source_field": "related_transaction_id",
                    "target_field": "related_transaction_id",
                    "data_type": "string"
                },
                {
                    "source_field": "bulk_generation_id",
                    "target_field": "bulk_generation_id",
                    "data_type": "string"
                }
            ]
        }
    ],
    
    "output_options": {
        "include_create_statements": True,
        "include_comments": True,
        "batch_size": 1000
    }
}