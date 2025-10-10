"""
Report generation module for SyFi AI data profiling.

This module handles the generation of various report formats including
HTML, JSON, and markdown reports with banking-specific visualizations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import html

class ProfileReporter:
    """
    Generates comprehensive reports from profiling data.
    
    Supports multiple output formats and provides banking-specific
    report templates and visualizations.
    """
    
    def __init__(self, output_dir: Path):
        """
        Initialize reporter with output directory.
        
        Args:
            output_dir: Directory where reports will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_report(self, profile_data: Dict[str, Any], 
                       format: str = 'html',
                       filename: Optional[str] = None) -> Path:
        """
        Generate a comprehensive report from profile data.
        
        Args:
            profile_data: Complete profiling results dictionary
            format: Output format ('html', 'json', 'markdown')
            filename: Optional custom filename
            
        Returns:
            Path to generated report file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'banking_profile_report_{timestamp}'
        
        if format == 'html':
            return self._generate_html_report(profile_data, filename)
        elif format == 'json':
            return self._generate_json_report(profile_data, filename)
        elif format == 'markdown':
            return self._generate_markdown_report(profile_data, filename)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_html_report(self, data: Dict[str, Any], filename: str) -> Path:
        """Generate comprehensive HTML report."""
        file_path = self.output_dir / f"{filename}.html"
        
        html_content = self._build_html_template(data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return file_path
    
    def _generate_json_report(self, data: Dict[str, Any], filename: str) -> Path:
        """Generate JSON report."""
        file_path = self.output_dir / f"{filename}.json"
        
        # Convert summary object to dict for serialization
        if 'summary' in data and hasattr(data['summary'], 'to_dict'):
            data['summary'] = data['summary'].to_dict()
        
        # Convert table profiles to dicts
        if 'tables' in data:
            for table_name, table_profile in data['tables'].items():
                if hasattr(table_profile, 'to_dict'):
                    data['tables'][table_name] = table_profile.to_dict()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        return file_path
    
    def _generate_markdown_report(self, data: Dict[str, Any], filename: str) -> Path:
        """Generate Markdown report."""
        file_path = self.output_dir / f"{filename}.md"
        
        markdown_content = self._build_markdown_content(data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return file_path
    
    def _build_html_template(self, data: Dict[str, Any]) -> str:
        """Build complete HTML report."""
        summary = data.get('summary')
        tables = data.get('tables', {})
        banking_metrics = data.get('banking_metrics', {})
        relationships = data.get('relationships', {})
        data_quality = data.get('data_quality', {})
        customer_profiles = data.get('customer_profiles', {})
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SyFi AI Banking Data Profile Report</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏦 SyFi AI Banking Data Profile Report</h1>
            <p class="subtitle">Comprehensive analysis of synthetic banking data</p>
        </header>

        {self._build_summary_section(summary)}
        {self._build_banking_metrics_section(banking_metrics)}
        {self._build_customer_profiles_section(customer_profiles)}
        {self._build_relationships_section(relationships)}
        {self._build_data_quality_section(data_quality)}
        {self._build_tables_section(tables)}
        
        <footer>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by SyFi AI Data Profiler</p>
        </footer>
    </div>
</body>
</html>
        """
        
        return html
    
    def _get_css_styles(self) -> str:
        """Return CSS styles for HTML report."""
        return """
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        header {
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        h1 {
            color: #2c3e50;
            margin: 0;
            font-size: 2.5em;
        }
        .subtitle {
            color: #7f8c8d;
            font-size: 1.2em;
            margin: 10px 0;
        }
        h2 {
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-top: 40px;
        }
        h3 {
            color: #2c3e50;
            margin-top: 25px;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        .metric-label {
            color: #7f8c8d;
            font-size: 0.9em;
            text-transform: uppercase;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background: white;
        }
        .data-table th,
        .data-table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        .data-table th {
            background-color: #f2f2f2;
            font-weight: bold;
            color: #2c3e50;
        }
        .data-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .progress-bar {
            background-color: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            height: 20px;
            margin: 5px 0;
        }
        .progress-fill {
            height: 100%;
            background-color: #3498db;
            transition: width 0.3s ease;
        }
        .alert {
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }
        .alert-info {
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
        }
        .alert-warning {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }
        footer {
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #7f8c8d;
        }
        """
    
    def _build_summary_section(self, summary) -> str:
        """Build database summary section."""
        if not summary:
            return ""
        
        return f"""
        def _build_summary_section(self, summary) -> str:
        """Build the summary section with key metrics."""
        # Handle both dataclass and dict formats
        if hasattr(summary, 'to_dict'):
            # It's a dataclass
            db_path = str(summary.database_path)
            total_customers = summary.total_customers
            total_accounts = summary.total_accounts
            total_transactions = summary.total_transactions
            database_size_kb = summary.database_size_kb
            unique_profiles = summary.unique_profiles
            analysis_date = summary.analysis_date
            date_range = summary.date_range
        else:
            # It's a dictionary
            db_path = str(summary.get('database_path', ''))
            total_customers = summary.get('total_customers', 0)
            total_accounts = summary.get('total_accounts', 0)
            total_transactions = summary.get('total_transactions', 0)
            database_size_kb = summary.get('database_size_kb', 0)
            unique_profiles = summary.get('unique_profiles', 0)
            analysis_date = summary.get('analysis_date', datetime.now())
            date_range = summary.get('date_range')
            
            # Parse date if it's a string
            if isinstance(analysis_date, str):
                analysis_date = datetime.fromisoformat(analysis_date)
        
        return f"""
        <section class="summary-section">
            <h2>📊 Database Overview</h2>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{total_customers:,}</div>
                    <div class="metric-label">Total Customers</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{total_accounts:,}</div>
                    <div class="metric-label">Total Accounts</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{total_transactions:,}</div>
                    <div class="metric-label">Total Transactions</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{database_size_kb:.1f} KB</div>
                    <div class="metric-label">Database Size</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{unique_profiles}</div>
                    <div class="metric-label">Unique Profiles</div>
                </div>
            </div>
            
            <div class="alert alert-info">
                <strong>Database:</strong> {html.escape(db_path)}<br>
                <strong>Analysis Date:</strong> {analysis_date.strftime('%Y-%m-%d %H:%M:%S')}
                {f'<br><strong>Transaction Period:</strong> {date_range[0]} to {date_range[1]}' if date_range else ''}
            </div>
        </section>
        """
        """
    
    def _build_banking_metrics_section(self, metrics: Dict[str, Any]) -> str:
        """Build banking metrics section."""
        if not metrics:
            return ""
        
        html = """
        <section>
            <h2>🏪 Banking Metrics</h2>
        """
        
        # Account metrics
        account_metrics = metrics.get('account_metrics', {})
        if account_metrics:
            html += """
            <h3>Account Distribution</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Account Type</th>
                        <th>Count</th>
                        <th>Percentage</th>
                        <th>Avg Balance</th>
                        <th>Total Balance</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            account_dist = account_metrics.get('account_type_distribution', {})
            for acc_type, data in account_dist.items():
                html += f"""
                    <tr>
                        <td>{acc_type.title()}</td>
                        <td>{data['count']:,}</td>
                        <td>{data['percentage']}%</td>
                        <td>${data['avg_balance']:,.2f}</td>
                        <td>${data['total_balance']:,.2f}</td>
                    </tr>
                """
            
            html += "</tbody></table>"
        
        # Customer segments
        segments = metrics.get('customer_segments', {})
        if segments and segments.get('family_composition'):
            html += """
            <h3>Customer Segments</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Family Type</th>
                        <th>Customer Count</th>
                        <th>Avg Income</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for family_type, data in segments['family_composition'].items():
                avg_income = f"${data['avg_income']:,.2f}" if data['avg_income'] else "N/A"
                html += f"""
                    <tr>
                        <td>{family_type}</td>
                        <td>{data['count']:,}</td>
                        <td>{avg_income}</td>
                    </tr>
                """
            
            html += "</tbody></table>"
        
        html += "</section>"
        return html
    
    def _build_customer_profiles_section(self, profiles: Dict[str, Any]) -> str:
        """Build customer profiles analysis section."""
        if not profiles:
            return ""
        
        html = """
        <section>
            <h2>👥 Customer Profiles</h2>
        """
        
        # Profile distribution
        profile_dist = profiles.get('profile_distribution', {})
        if profile_dist:
            html += """
            <h3>Profile Distribution</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Profile Description</th>
                        <th>Customer Count</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for profile_desc, count in profile_dist.items():
                html += f"""
                    <tr>
                        <td>{html.escape(profile_desc)}</td>
                        <td>{count:,}</td>
                    </tr>
                """
            
            html += "</tbody></table>"
        
        # Household composition
        household = profiles.get('household_composition', {})
        if household:
            html += f"""
            <h3>Average Household Composition</h3>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{household['avg_household_size']}</div>
                    <div class="metric-label">Household Size</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{household['avg_adults']}</div>
                    <div class="metric-label">Adults</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{household['avg_children']}</div>
                    <div class="metric-label">Children</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{household['avg_pets']}</div>
                    <div class="metric-label">Pets</div>
                </div>
            </div>
            """
        
        html += "</section>"
        return html
    
    def _build_relationships_section(self, relationships: Dict[str, Any]) -> str:
        """Build relationships analysis section."""
        if not relationships:
            return ""
        
        html = """
        <section>
            <h2>🔗 Data Relationships</h2>
        """
        
        # Customer-Account relationships
        cust_acc = relationships.get('customer_accounts', {})
        if cust_acc:
            html += f"""
            <h3>Customer-Account Relationships</h3>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{cust_acc.get('avg_accounts_per_customer', 0)}</div>
                    <div class="metric-label">Avg Accounts/Customer</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{cust_acc.get('min_accounts', 0)}</div>
                    <div class="metric-label">Min Accounts</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{cust_acc.get('max_accounts', 0)}</div>
                    <div class="metric-label">Max Accounts</div>
                </div>
            </div>
            """
        
        html += "</section>"
        return html
    
    def _build_data_quality_section(self, quality: Dict[str, Any]) -> str:
        """Build data quality section."""
        if not quality:
            return ""
        
        html = """
        <section>
            <h2>✅ Data Quality Assessment</h2>
        """
        
        # Referential integrity
        ref_integrity = quality.get('referential_integrity', {})
        if ref_integrity:
            orphaned_accounts = ref_integrity.get('orphaned_accounts', 0)
            orphaned_transactions = ref_integrity.get('orphaned_transactions', 0)
            
            if orphaned_accounts > 0 or orphaned_transactions > 0:
                alert_class = "alert-warning"
                status = "⚠️ Issues Found"
            else:
                alert_class = "alert-info" 
                status = "✅ No Issues"
            
            html += f"""
            <h3>Referential Integrity</h3>
            <div class="alert {alert_class}">
                <strong>{status}</strong><br>
                Orphaned Accounts: {orphaned_accounts}<br>
                Orphaned Transactions: {orphaned_transactions}
            </div>
            """
        
        # Customer completeness
        completeness = quality.get('customer_completeness', {})
        if completeness:
            html += f"""
            <h3>Customer Data Completeness</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Field</th>
                        <th>Completeness %</th>
                        <th>Progress</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Profile Descriptions</td>
                        <td>{completeness.get('profile_completeness', 0)}%</td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {completeness.get('profile_completeness', 0)}%"></div>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td>Email Addresses</td>
                        <td>{completeness.get('email_completeness', 0)}%</td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {completeness.get('email_completeness', 0)}%"></div>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td>Phone Numbers</td>
                        <td>{completeness.get('phone_completeness', 0)}%</td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {completeness.get('phone_completeness', 0)}%"></div>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
            """
        
        html += "</section>"
        return html
    
    def _build_tables_section(self, tables: Dict[str, Any]) -> str:
        """Build tables analysis section."""
        if not tables:
            return ""
        
        html = """
        <section>
            <h2>📋 Table Details</h2>
        """
        
        for table_name, table_data in tables.items():
            if hasattr(table_data, 'to_dict'):
                table_dict = table_data.to_dict()
            else:
                table_dict = table_data
                
            html += f"""
            <h3>{table_name.title()} Table</h3>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{table_dict.get('row_count', 0):,}</div>
                    <div class="metric-label">Rows</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{table_dict.get('column_count', 0)}</div>
                    <div class="metric-label">Columns</div>
                </div>
            </div>
            """
        
        html += "</section>"
        return html
    
    def _build_markdown_content(self, data: Dict[str, Any]) -> str:
        """Build Markdown report content."""
        summary = data.get('summary')
        
        markdown = f"""# SyFi AI Banking Data Profile Report

Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Database Summary

"""
        
        if summary:
            markdown += f"""
- **Database:** {summary.database_path}
- **Customers:** {summary.total_customers:,}
- **Accounts:** {summary.total_accounts:,}
- **Transactions:** {summary.total_transactions:,}
- **Database Size:** {summary.database_size_kb:.1f} KB
- **Unique Profiles:** {summary.unique_profiles}
"""
            
            if summary.date_range:
                markdown += f"- **Transaction Period:** {summary.date_range[0]} to {summary.date_range[1]}\n"
        
        # Add other sections as needed for markdown format
        banking_metrics = data.get('banking_metrics', {})
        if banking_metrics:
            markdown += "\n## Banking Metrics\n\n"
            # Add banking metrics content
        
        return markdown