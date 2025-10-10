"""
Observer Pattern Implementation for Progress Tracking and Event Handling

Allows decoupled notification of data generation progress and events.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class GenerationEvent(Enum):
    """Types of generation events."""
    PROFILE_CREATED = "profile_created"
    CUSTOMERS_GENERATED = "customers_generated"
    ACCOUNTS_GENERATED = "accounts_generated"
    TRANSACTIONS_GENERATED = "transactions_generated"
    GENERATION_COMPLETED = "generation_completed"
    ERROR_OCCURRED = "error_occurred"


class GenerationEventData:
    """Data associated with a generation event."""
    
    def __init__(self, event_type: GenerationEvent, data: Dict[str, Any], 
                 timestamp: Optional[datetime] = None):
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.now()
        self.source = data.get('source', 'unknown')
    
    def __str__(self):
        return f"{self.event_type.value} at {self.timestamp}: {self.data}"


class Observer(ABC):
    """Abstract observer interface."""
    
    @abstractmethod
    def update(self, event_data: GenerationEventData) -> None:
        """Handle notification of an event."""
        pass


class Subject(ABC):
    """Abstract subject interface."""
    
    def __init__(self):
        self._observers: List[Observer] = []
    
    def attach(self, observer: Observer) -> None:
        """Attach an observer."""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer: Observer) -> None:
        """Detach an observer."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify(self, event_data: GenerationEventData) -> None:
        """Notify all observers of an event."""
        for observer in self._observers:
            observer.update(event_data)


# Concrete Observers

class ProgressLogger(Observer):
    """Observer that logs progress to console."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
    
    def update(self, event_data: GenerationEventData) -> None:
        """Log the event."""
        if event_data.event_type == GenerationEvent.PROFILE_CREATED:
            profile_name = event_data.data.get('profile_name', 'Unknown')
            print(f"✅ Profile created: {profile_name}")
        
        elif event_data.event_type == GenerationEvent.CUSTOMERS_GENERATED:
            count = event_data.data.get('count', 0)
            profile_name = event_data.data.get('profile_name', 'Unknown')
            print(f"👥 Generated {count} customers for {profile_name}")
        
        elif event_data.event_type == GenerationEvent.ACCOUNTS_GENERATED:
            count = event_data.data.get('count', 0)
            profile_name = event_data.data.get('profile_name', 'Unknown')
            print(f"💳 Generated {count} accounts for {profile_name}")
        
        elif event_data.event_type == GenerationEvent.TRANSACTIONS_GENERATED:
            count = event_data.data.get('count', 0)
            profile_name = event_data.data.get('profile_name', 'Unknown')
            date_range = event_data.data.get('date_range', 'Unknown period')
            print(f"💰 Generated {count} transactions for {profile_name} ({date_range})")
        
        elif event_data.event_type == GenerationEvent.GENERATION_COMPLETED:
            duration = event_data.data.get('duration_seconds', 0)
            total_records = event_data.data.get('total_records', 0)
            print(f"🎉 Generation completed in {duration:.2f}s - {total_records} total records")
        
        elif event_data.event_type == GenerationEvent.ERROR_OCCURRED:
            error = event_data.data.get('error', 'Unknown error')
            print(f"❌ Error: {error}")
        
        if self.verbose and 'details' in event_data.data:
            print(f"   Details: {event_data.data['details']}")


class ProgressBar(Observer):
    """Observer that displays a progress bar."""
    
    def __init__(self, total_steps: int = 100):
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = datetime.now()
    
    def update(self, event_data: GenerationEventData) -> None:
        """Update progress bar."""
        if event_data.event_type in [
            GenerationEvent.PROFILE_CREATED,
            GenerationEvent.CUSTOMERS_GENERATED, 
            GenerationEvent.ACCOUNTS_GENERATED,
            GenerationEvent.TRANSACTIONS_GENERATED
        ]:
            self.current_step += 1
            self._display_progress()
        
        elif event_data.event_type == GenerationEvent.GENERATION_COMPLETED:
            self.current_step = self.total_steps
            self._display_progress()
            print()  # New line after completion
    
    def _display_progress(self):
        """Display the progress bar."""
        progress = min(self.current_step / self.total_steps, 1.0)
        bar_length = 40
        filled_length = int(bar_length * progress)
        
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        percent = progress * 100
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print(f'\r|{bar}| {percent:.1f}% ({self.current_step}/{self.total_steps}) - {elapsed:.1f}s', 
              end='', flush=True)


class MetricsCollector(Observer):
    """Observer that collects performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            'events': [],
            'generation_times': {},
            'record_counts': {},
            'errors': []
        }
        self.start_times: Dict[str, datetime] = {}
    
    def update(self, event_data: GenerationEventData) -> None:
        """Collect metrics from events."""
        self.metrics['events'].append({
            'type': event_data.event_type.value,
            'timestamp': event_data.timestamp.isoformat(),
            'data': event_data.data
        })
        
        if event_data.event_type == GenerationEvent.PROFILE_CREATED:
            profile_name = event_data.data.get('profile_name')
            if profile_name:
                self.start_times[profile_name] = event_data.timestamp
        
        elif event_data.event_type == GenerationEvent.TRANSACTIONS_GENERATED:
            profile_name = event_data.data.get('profile_name')
            if profile_name and profile_name in self.start_times:
                duration = (event_data.timestamp - self.start_times[profile_name]).total_seconds()
                self.metrics['generation_times'][profile_name] = duration
        
        elif event_data.event_type in [
            GenerationEvent.CUSTOMERS_GENERATED,
            GenerationEvent.ACCOUNTS_GENERATED, 
            GenerationEvent.TRANSACTIONS_GENERATED
        ]:
            record_type = event_data.event_type.value.replace('_generated', '')
            count = event_data.data.get('count', 0)
            if record_type not in self.metrics['record_counts']:
                self.metrics['record_counts'][record_type] = 0
            self.metrics['record_counts'][record_type] += count
        
        elif event_data.event_type == GenerationEvent.ERROR_OCCURRED:
            self.metrics['errors'].append({
                'timestamp': event_data.timestamp.isoformat(),
                'error': event_data.data.get('error'),
                'source': event_data.data.get('source')
            })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        total_events = len(self.metrics['events'])
        total_records = sum(self.metrics['record_counts'].values())
        avg_generation_time = (
            sum(self.metrics['generation_times'].values()) / 
            len(self.metrics['generation_times'])
            if self.metrics['generation_times'] else 0
        )
        
        return {
            'total_events': total_events,
            'total_records': total_records,
            'average_generation_time': avg_generation_time,
            'error_count': len(self.metrics['errors']),
            'record_breakdown': self.metrics['record_counts'],
            'generation_times': self.metrics['generation_times']
        }


class DatabaseEventLogger(Observer):
    """Observer that logs events to database."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._ensure_events_table()
    
    def _ensure_events_table(self):
        """Ensure events table exists."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generation_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                source TEXT,
                data TEXT,  -- JSON
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    
    def update(self, event_data: GenerationEventData) -> None:
        """Log event to database."""
        import json
        
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO generation_events (event_type, timestamp, source, data)
            VALUES (?, ?, ?, ?)
        """, (
            event_data.event_type.value,
            event_data.timestamp.isoformat(),
            event_data.source,
            json.dumps(event_data.data, default=str)
        ))
        conn.commit()


# Observable Data Generator

class ObservableDataGenerator(Subject):
    """Data generator that notifies observers of progress."""
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
    
    def generate_banking_data(self, profile, start_date, end_date):
        """Generate banking data with progress notifications."""
        from datetime import datetime
        start_time = datetime.now()
        
        try:
            # Notify profile creation
            self.notify(GenerationEventData(
                GenerationEvent.PROFILE_CREATED,
                {
                    'profile_name': profile.name,
                    'profile_id': profile.profile_id,
                    'source': 'ObservableDataGenerator'
                }
            ))
            
            # Generate customers
            customers = self._generate_customers(profile)
            self.notify(GenerationEventData(
                GenerationEvent.CUSTOMERS_GENERATED,
                {
                    'profile_name': profile.name,
                    'count': len(customers),
                    'source': 'ObservableDataGenerator'
                }
            ))
            
            # Generate accounts
            accounts = self._generate_accounts(profile, customers)
            self.notify(GenerationEventData(
                GenerationEvent.ACCOUNTS_GENERATED,
                {
                    'profile_name': profile.name,
                    'count': len(accounts),
                    'source': 'ObservableDataGenerator'
                }
            ))
            
            # Generate transactions
            transactions = self._generate_transactions(profile, accounts, start_date, end_date)
            self.notify(GenerationEventData(
                GenerationEvent.TRANSACTIONS_GENERATED,
                {
                    'profile_name': profile.name,
                    'count': len(transactions),
                    'date_range': f"{start_date} to {end_date}",
                    'source': 'ObservableDataGenerator'
                }
            ))
            
            # Notify completion
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            total_records = len(customers) + len(accounts) + len(transactions)
            
            self.notify(GenerationEventData(
                GenerationEvent.GENERATION_COMPLETED,
                {
                    'profile_name': profile.name,
                    'duration_seconds': duration,
                    'total_records': total_records,
                    'source': 'ObservableDataGenerator'
                }
            ))
            
            return {
                'customers': customers,
                'accounts': accounts,
                'transactions': transactions,
                'profile': profile
            }
            
        except Exception as e:
            # Notify error
            self.notify(GenerationEventData(
                GenerationEvent.ERROR_OCCURRED,
                {
                    'profile_name': getattr(profile, 'name', 'Unknown'),
                    'error': str(e),
                    'source': 'ObservableDataGenerator'
                }
            ))
            raise
    
    def _generate_customers(self, profile):
        """Generate customers from profile data."""
        from ..models import Customer
        
        customers = []
        for customer_data in profile.customers_data:
            customer = Customer(
                first_name=customer_data["first_name"],
                last_name=customer_data["last_name"],
                employment_status=customer_data["employment_status"],
                household_income=profile.household_income,
                household_size=profile.total_members
            )
            customers.append(customer)
        
        # Store in database
        self.db_manager.insert_customers(customers)
        return customers
    
    def _generate_accounts(self, profile, customers):
        """Generate accounts from profile data."""
        from ..models import Account, AccountType
        from decimal import Decimal
        
        accounts = []
        for customer in customers:
            for account_data in profile.accounts_data:
                account = Account(
                    customer_id=customer.customer_id,
                    account_type=AccountType(account_data["account_type"]),
                    balance=Decimal(str(account_data["initial_balance"])),
                    available_balance=Decimal(str(account_data["initial_balance"]))
                )
                accounts.append(account)
        
        # Store in database
        self.db_manager.insert_accounts(accounts)
        return accounts
    
    def _generate_transactions(self, profile, accounts, start_date, end_date):
        """Generate transactions from profile data."""
        # This would use the existing transaction generation logic
        # For now, return empty list as placeholder
        transactions = []
        
        if transactions:
            self.db_manager.insert_transactions(transactions)
        
        return transactions


# Usage Example Factory

class ObserverFactory:
    """Factory for creating common observer configurations."""
    
    @staticmethod
    def create_console_observers(verbose: bool = True) -> List[Observer]:
        """Create observers for console output."""
        return [
            ProgressLogger(verbose=verbose),
            ProgressBar(total_steps=10)
        ]
    
    @staticmethod
    def create_full_monitoring(db_manager, verbose: bool = True) -> List[Observer]:
        """Create full monitoring setup with all observers."""
        return [
            ProgressLogger(verbose=verbose),
            ProgressBar(total_steps=10),
            MetricsCollector(),
            DatabaseEventLogger(db_manager)
        ]
    
    @staticmethod
    def create_metrics_only() -> List[Observer]:
        """Create metrics-only monitoring."""
        return [MetricsCollector()]