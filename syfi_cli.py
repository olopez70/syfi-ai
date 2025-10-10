#!/usr/bin/env python3
"""
SyFi AI CLI - Command Line Interface for Synthetic Banking Data Generation

This module provides a comprehensive CLI for executing banking data generation
steps independently, including database operations and data export.
"""

import sys
import click
from pathlib import Path
from datetime import datetime, date
from typing import Optional
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from syfi.database import DatabaseManager
from syfi.generators import CustomerGenerator, TransactionEngine
from syfi.exporters import DataExporter

# Initialize rich console for beautiful CLI output
console = Console()

@click.group()
@click.version_option(version="0.1.0", prog_name="SyFi AI")
def cli():
    """
    🏦 SyFi AI - Synthetic Banking Data Generation CLI
    
    Generate realistic synthetic banking data with independent workflow steps.
    Execute initialization, customer creation, transaction generation, and data export.
    """
    pass

@cli.command()
@click.option('--database', '-db', default='data/syfi_banking.db', 
              help='SQLite database filename (default: data/syfi_banking.db)')
@click.option('--force', '-f', is_flag=True, 
              help='Force initialization, overwriting existing database')
def init(database: str, force: bool):
    """
    Step 0: Initialize SyFi AI database and setup.
    
    Creates a new SQLite database with proper schema for customers, 
    accounts, and transactions.
    """
    console.print(Panel.fit("🚀 [bold blue]Step 0: Initialization and Setup[/bold blue]"))
    
    db_path = Path(database)
    
    # Check if database exists
    if db_path.exists() and not force:
        console.print(f"❌ Database '{database}' already exists. Use --force to overwrite.")
        return
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing database schema...", total=None)
            
            # Initialize database
            db_manager = DatabaseManager(database)
            db_manager.initialize_schema()
            
            progress.update(task, description="✅ Database initialized successfully")
        
        console.print(f"✅ [green]Database '{database}' created successfully![/green]")
        console.print(f"📍 Location: {db_path.absolute()}")
        
        # Show schema info
        table = Table(title="Database Schema Created")
        table.add_column("Table", style="cyan")
        table.add_column("Description", style="white")
        
        table.add_row("customers", "Customer personal information and profiles")
        table.add_row("accounts", "Bank accounts linked to customers") 
        table.add_row("transactions", "Banking transactions and transfers")
        table.add_row("metadata", "Generation metadata and configuration")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ [red]Error initializing database: {e}[/red]")
        sys.exit(1)

@cli.command()
@click.option('--database', '-db', default='data/syfi_banking.db',
              help='SQLite database filename')
@click.option('--customers', '-c', default=100, type=int,
              help='Number of customers to create (default: 100)')
@click.option('--accounts-per-customer', '-a', default=2, type=int,
              help='Average accounts per customer (default: 2)')
@click.option('--seed', '-s', type=int, help='Random seed for reproducible generation')
@click.option('--profile', '-p', type=str, help='Customer profile description (e.g., "Two income households with 2 adults, 1-4 children")')
def create_customers(database: str, customers: int, accounts_per_customer: int, seed: Optional[int], profile: Optional[str]):
    """
    Step 1: Create synthetic customers and accounts dataset.
    
    Generates realistic customer profiles with associated bank accounts
    and saves them to the SQLite database.
    """
    console.print(Panel.fit("👥 [bold blue]Step 1: Create Customers and Accounts[/bold blue]"))
    
    db_path = Path(database)
    if not db_path.exists():
        console.print(f"❌ Database '{database}' not found. Run 'init' first.")
        return
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Initialize components
            task1 = progress.add_task("Connecting to database...", total=None)
            db_manager = DatabaseManager(database)
            
            progress.update(task1, description="Initializing customer generator...")
            customer_gen = CustomerGenerator(seed=seed)
            
            # Generate customers and accounts
            progress.update(task1, description=f"Generating {customers} customers...")
            if profile:
                generated_customers, generated_accounts = customer_gen.generate_customers(
                    customers, accounts_per_customer, profile_description=profile
                )
            else:
                generated_customers, generated_accounts = customer_gen.generate_customers(
                    customers, accounts_per_customer
                )
            
            # Save to database
            progress.update(task1, description="Saving customers to database...")
            customer_ids = db_manager.insert_customers(generated_customers)
            
            progress.update(task1, description="Saving accounts to database...")
            account_ids = db_manager.insert_accounts(generated_accounts)
            
            progress.update(task1, description="✅ Generation completed successfully")
        
        # Show results
        console.print(f"✅ [green]Successfully created {len(customer_ids)} customers and {len(account_ids)} accounts![/green]")
        
        # Summary table
        table = Table(title="Generation Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="white", justify="right")
        
        table.add_row("Customers Created", str(len(customer_ids)))
        table.add_row("Accounts Created", str(len(account_ids)))
        table.add_row("Avg Accounts/Customer", f"{len(account_ids)/len(customer_ids):.1f}")
        table.add_row("Database Size", f"{db_path.stat().st_size / 1024:.1f} KB")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ [red]Error creating customers: {e}[/red]")
        sys.exit(1)

@cli.command()
@click.option('--database', '-db', default='data/syfi_banking.db',
              help='SQLite database filename')
@click.option('--start-date', '-s', required=True,
              help='Start date for transactions (YYYY-MM-DD)')
@click.option('--end-date', '-e', required=True, 
              help='End date for transactions (YYYY-MM-DD)')
@click.option('--transactions-per-day', '-t', default=50, type=int,
              help='Average transactions per day (default: 50)')
@click.option('--seed', type=int, help='Random seed for reproducible generation')
def generate_transactions(database: str, start_date: str, end_date: str, 
                         transactions_per_day: int, seed: Optional[int]):
    """
    Step 2 & 4: Generate synthetic transactions for specified period.
    
    Creates realistic banking transactions for existing customers and accounts
    within the specified date range.
    """
    console.print(Panel.fit("💳 [bold blue]Generate Transactions[/bold blue]"))
    
    db_path = Path(database)
    if not db_path.exists():
        console.print(f"❌ Database '{database}' not found. Run 'init' first.")
        return
    
    try:
        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if start >= end:
            console.print("❌ Start date must be before end date.")
            return
        
        days = (end - start).days + 1
        estimated_transactions = days * transactions_per_day
        
        console.print(f"📅 Period: {start_date} to {end_date} ({days} days)")
        console.print(f"🎯 Target: ~{estimated_transactions} transactions")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Initialize components
            task = progress.add_task("Connecting to database...", total=None)
            db_manager = DatabaseManager(database)
            
            progress.update(task, description="Loading existing accounts...")
            accounts = db_manager.get_all_accounts()
            
            if not accounts:
                console.print("❌ No accounts found in database. Run 'create-customers' first.")
                return
            
            progress.update(task, description="Initializing transaction engine...")
            tx_engine = TransactionEngine(seed=seed)
            
            progress.update(task, description=f"Generating transactions for {days} days...")
            transactions = tx_engine.generate_transactions_for_period(
                accounts, start, end, transactions_per_day
            )
            
            progress.update(task, description="Saving transactions to database...")
            tx_ids = db_manager.insert_transactions(transactions)
            
            progress.update(task, description="✅ Transaction generation completed")
        
        # Show results
        console.print(f"✅ [green]Successfully generated {len(tx_ids)} transactions![/green]")
        
        # Summary table
        table = Table(title="Transaction Generation Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white", justify="right")
        
        table.add_row("Period", f"{start_date} to {end_date}")
        table.add_row("Days", str(days))
        table.add_row("Transactions Generated", str(len(tx_ids)))
        table.add_row("Avg Transactions/Day", f"{len(tx_ids)/days:.1f}")
        table.add_row("Total Accounts Used", str(len(accounts)))
        
        console.print(table)
        
    except ValueError as e:
        console.print(f"❌ [red]Invalid date format. Use YYYY-MM-DD: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ [red]Error generating transactions: {e}[/red]")
        sys.exit(1)

@cli.command()
@click.option('--database', '-db', default='data/syfi_banking.db',
              help='SQLite database filename')
@click.option('--customers', '-c', default=50, type=int,
              help='Number of additional customers (default: 50)')
@click.option('--accounts-per-customer', '-a', default=2, type=int,
              help='Average accounts per customer (default: 2)')
@click.option('--seed', type=int, help='Random seed for reproducible generation')
@click.option('--profile', '-p', type=str, help='Customer profile description (e.g., "Two income households with 2 adults, 1-4 children")')
def add_customers(database: str, customers: int, accounts_per_customer: int, seed: Optional[int], profile: Optional[str]):
    """
    Step 3: Add more customers and accounts to existing database.
    
    Generates additional customer profiles and accounts without affecting 
    existing data.
    """
    console.print(Panel.fit("➕ [bold blue]Step 3: Add Additional Customers[/bold blue]"))
    
    db_path = Path(database)
    if not db_path.exists():
        console.print(f"❌ Database '{database}' not found. Run 'init' first.")
        return
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Get current stats
            task = progress.add_task("Checking existing database...", total=None)
            db_manager = DatabaseManager(database)
            
            existing_customers = db_manager.count_customers()
            existing_accounts = db_manager.count_accounts()
            
            progress.update(task, description="Generating additional customers...")
            customer_gen = CustomerGenerator(seed=seed)
            
            # Generate new customers and accounts
            if profile:
                new_customers, new_accounts = customer_gen.generate_customers(
                    customers, accounts_per_customer, profile_description=profile
                )
            else:
                new_customers, new_accounts = customer_gen.generate_customers(
                    customers, accounts_per_customer
                )
            
            # Save to database
            progress.update(task, description="Saving new customers...")
            customer_ids = db_manager.insert_customers(new_customers)
            
            progress.update(task, description="Saving new accounts...")
            account_ids = db_manager.insert_accounts(new_accounts)
            
            progress.update(task, description="✅ Additional customers added successfully")
        
        # Show results
        console.print(f"✅ [green]Successfully added {len(customer_ids)} customers and {len(account_ids)} accounts![/green]")
        
        # Summary table
        table = Table(title="Database Growth Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Before", style="yellow", justify="right")
        table.add_column("Added", style="green", justify="right")
        table.add_column("Total", style="white", justify="right")
        
        table.add_row("Customers", str(existing_customers), str(len(customer_ids)), 
                     str(existing_customers + len(customer_ids)))
        table.add_row("Accounts", str(existing_accounts), str(len(account_ids)), 
                     str(existing_accounts + len(account_ids)))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ [red]Error adding customers: {e}[/red]")
        sys.exit(1)

@cli.command()
@click.option('--database', '-db', default='data/syfi_banking.db',
              help='SQLite database filename')
@click.option('--output-dir', '-o', default='./exports',
              help='Output directory for exported files (default: ./exports)')
@click.option('--format', '-f', type=click.Choice(['pipe', 'csv', 'json']), 
              default='pipe', help='Export format (default: pipe-delimited)')
@click.option('--schema', type=click.Choice(['standard', 'banking', 'audit']),
              default='standard', help='Export schema format')
def export(database: str, output_dir: str, format: str, schema: str):
    """
    Step 5: Export banking data to files.
    
    Extracts all banking data (customers, accounts, transactions) 
    to pipe-delimited or other format files.
    """
    console.print(Panel.fit("📤 [bold blue]Step 5: Export Banking Data[/bold blue]"))
    
    db_path = Path(database)
    if not db_path.exists():
        console.print(f"❌ Database '{database}' not found.")
        return
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Connecting to database...", total=None)
            db_manager = DatabaseManager(database)
            
            progress.update(task, description="Initializing data exporter...")
            exporter = DataExporter(db_manager, output_path)
            
            # Export each table
            progress.update(task, description="Exporting customers...")
            customers_file = exporter.export_customers(format=format, schema=schema)
            
            progress.update(task, description="Exporting accounts...")
            accounts_file = exporter.export_accounts(format=format, schema=schema)
            
            progress.update(task, description="Exporting transactions...")
            transactions_file = exporter.export_transactions(format=format, schema=schema)
            
            # Generate summary report
            progress.update(task, description="Generating export summary...")
            summary_file = exporter.generate_export_summary()
            
            progress.update(task, description="✅ Export completed successfully")
        
        # Show results
        console.print(f"✅ [green]Data exported successfully to {output_path.absolute()}![/green]")
        
        # File summary table
        table = Table(title="Exported Files")
        table.add_column("File", style="cyan")
        table.add_column("Records", style="white", justify="right")
        table.add_column("Size", style="yellow", justify="right")
        
        for file_path, record_count in [
            (customers_file, db_manager.count_customers()),
            (accounts_file, db_manager.count_accounts()),
            (transactions_file, db_manager.count_transactions()),
            (summary_file, 1)
        ]:
            if file_path and file_path.exists():
                size_kb = file_path.stat().st_size / 1024
                table.add_row(file_path.name, str(record_count), f"{size_kb:.1f} KB")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ [red]Error exporting data: {e}[/red]")
        sys.exit(1)

@cli.command()
@click.option('--database', '-db', default='data/syfi_banking.db',
              help='SQLite database filename')
def status(database: str):
    """
    Show current database status and statistics.
    
    Displays information about customers, accounts, transactions,
    and database size.
    """
    console.print(Panel.fit("📊 [bold blue]Database Status[/bold blue]"))
    
    db_path = Path(database)
    if not db_path.exists():
        console.print(f"❌ Database '{database}' not found.")
        return
    
    try:
        db_manager = DatabaseManager(database)
        
        # Get statistics
        customers_count = db_manager.count_customers()
        accounts_count = db_manager.count_accounts()
        transactions_count = db_manager.count_transactions()
        db_size = db_path.stat().st_size / 1024  # KB
        
        # Get date range of transactions
        date_range = db_manager.get_transaction_date_range()
        
        # Status table
        table = Table(title=f"Database: {database}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white", justify="right")
        
        table.add_row("Customers", str(customers_count))
        table.add_row("Accounts", str(accounts_count))
        table.add_row("Transactions", str(transactions_count))
        table.add_row("Database Size", f"{db_size:.1f} KB")
        
        if date_range:
            table.add_row("Transaction Period", f"{date_range[0]} to {date_range[1]}")
        
        if customers_count > 0:
            table.add_row("Avg Accounts/Customer", f"{accounts_count/customers_count:.1f}")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ [red]Error checking database status: {e}[/red]")

@cli.command()
@click.option('--database', '-db', default='data/syfi_banking.db',
              help='SQLite database filename')
@click.option('--output-dir', '-o', default='./reports',
              help='Output directory for reports (default: ./reports)')
@click.option('--format', '-f', type=click.Choice(['html', 'json', 'markdown']), default='html',
              help='Report format (default: html)')
@click.option('--filename', type=str, help='Custom filename for report')
def profile(database: str, output_dir: str, format: str, filename: Optional[str]):
    """
    Step 6: Generate comprehensive banking data profile report.
    
    Analyzes the synthetic banking database and generates detailed reports
    with banking-specific metrics, customer segmentation, and data quality assessment.
    """
    console.print(Panel.fit("📊 [bold blue]Step 6: Data Profiling Analysis[/bold blue]"))
    
    db_path = Path(database)
    if not db_path.exists():
        console.print(f"❌ Database '{database}' not found. Run 'init' and generate some data first.")
        return
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Initialize profiler
            task = progress.add_task("Initializing data profiler...", total=None)
            
            from src.syfi.profiling import BankingDataProfiler, ProfileReporter
            
            progress.update(task, description="Analyzing database schema...")
            with BankingDataProfiler(database) as profiler:
                # Generate comprehensive profile
                progress.update(task, description="Calculating banking metrics...")
                profile_data = profiler.generate_full_profile()
                
                progress.update(task, description="Analyzing customer segments...")
                # Profile data is already complete from generate_full_profile()
                
                progress.update(task, description="Assessing data quality...")
                # Quality assessment is included in the full profile
                
                # Generate report
                progress.update(task, description="Generating report...")
                reporter = ProfileReporter(Path(output_dir))
                report_path = reporter.generate_report(profile_data, format, filename)
                
                progress.update(task, description="✅ Profiling completed successfully")
        
        # Show summary
        summary = profile_data['summary']
        console.print(f"✅ [green]Banking data profile generated successfully![/green]")
        
        # Summary table
        table = Table(title="Profiling Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white", justify="right")
        
        table.add_row("Database", str(summary.database_path))
        table.add_row("Total Customers", f"{summary.total_customers:,}")
        table.add_row("Total Accounts", f"{summary.total_accounts:,}")
        table.add_row("Total Transactions", f"{summary.total_transactions:,}")
        table.add_row("Database Size", f"{summary.database_size_kb:.1f} KB")
        table.add_row("Unique Profiles", str(summary.unique_profiles))
        table.add_row("Report Format", format.upper())
        table.add_row("Report Location", str(report_path))
        
        console.print(table)
        
        # Banking insights
        banking_metrics = profile_data.get('banking_metrics', {})
        account_metrics = banking_metrics.get('account_metrics', {})
        
        if account_metrics:
            console.print("\n[bold cyan]🏪 Key Banking Insights[/bold cyan]")
            
            # Account distribution
            account_dist = account_metrics.get('account_type_distribution', {})
            if account_dist:
                insights_table = Table()
                insights_table.add_column("Account Type", style="yellow")
                insights_table.add_column("Count", justify="right")
                insights_table.add_column("Percentage", justify="right")
                insights_table.add_column("Avg Balance", justify="right")
                
                for acc_type, data in account_dist.items():
                    insights_table.add_row(
                        acc_type.title(),
                        str(data['count']),
                        f"{data['percentage']}%",
                        f"${data['avg_balance']:,.2f}"
                    )
                
                console.print(insights_table)
        
        # Customer profile insights
        customer_profiles = profile_data.get('customer_profiles', {})
        profile_dist = customer_profiles.get('profile_distribution', {})
        
        if profile_dist:
            console.print("\n[bold cyan]👥 Customer Profile Distribution[/bold cyan]")
            
            profile_table = Table()
            profile_table.add_column("Profile Description", style="green")
            profile_table.add_column("Customer Count", justify="right")
            
            for profile_desc, count in profile_dist.items():
                # Truncate long descriptions for display
                display_desc = profile_desc[:50] + "..." if len(profile_desc) > 50 else profile_desc
                profile_table.add_row(display_desc, str(count))
            
            console.print(profile_table)
        
        console.print(f"\n📄 [bold]Full report available at:[/bold] [link=file://{report_path}]{report_path}[/link]")
        
    except Exception as e:
        console.print(f"❌ [red]Error generating profile: {e}[/red]")
        sys.exit(1)

if __name__ == '__main__':
    cli()