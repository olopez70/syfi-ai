"""
Tests for Observer Pattern Implementation.

This module tests the progress tracking and event handling system that implements 
the Gang of Four Observer pattern for decoupled notification of generation events.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from src.syfi.patterns.observers import (
    GenerationEvent,
    GenerationEventData,
    Observer,
    Subject
)


@pytest.mark.unit
class TestGenerationEvent:
    """Test GenerationEvent enumeration."""
    
    def test_generation_event_values(self):
        """Test that all expected event types exist."""
        expected_events = [
            "profile_created",
            "customers_generated", 
            "accounts_generated",
            "transactions_generated",
            "generation_completed",
            "error_occurred"
        ]
        
        for event_name in expected_events:
            # Find the enum member with this value
            found = False
            for event in GenerationEvent:
                if event.value == event_name:
                    found = True
                    break
            assert found, f"Event {event_name} not found in GenerationEvent"


@pytest.mark.unit
class TestGenerationEventData:
    """Test GenerationEventData class."""
    
    def test_event_data_initialization(self):
        """Test event data initialization."""
        data = {"count": 10, "source": "test_generator"}
        event_data = GenerationEventData(GenerationEvent.CUSTOMERS_GENERATED, data)
        
        assert event_data.event_type == GenerationEvent.CUSTOMERS_GENERATED
        assert event_data.data == data
        assert event_data.source == "test_generator"
        assert isinstance(event_data.timestamp, datetime)
    
    def test_event_data_with_custom_timestamp(self):
        """Test event data with custom timestamp."""
        custom_time = datetime(2023, 1, 15, 10, 30, 0)
        data = {"count": 5}
        
        event_data = GenerationEventData(
            GenerationEvent.PROFILE_CREATED, 
            data, 
            timestamp=custom_time
        )
        
        assert event_data.timestamp == custom_time
    
    def test_event_data_default_source(self):
        """Test event data with default source."""
        data = {"count": 3}
        event_data = GenerationEventData(GenerationEvent.ACCOUNTS_GENERATED, data)
        
        assert event_data.source == "unknown"
    
    def test_event_data_string_representation(self):
        """Test string representation of event data."""
        data = {"count": 10, "source": "test"}
        event_data = GenerationEventData(GenerationEvent.CUSTOMERS_GENERATED, data)
        
        str_repr = str(event_data)
        
        assert "customers_generated" in str_repr
        assert "count" in str_repr
        assert str(event_data.timestamp) in str_repr


@pytest.mark.unit
class TestObserver:
    """Test abstract Observer interface."""
    
    def test_observer_cannot_be_instantiated(self):
        """Test that abstract Observer cannot be directly instantiated."""
        with pytest.raises(TypeError):
            Observer()


@pytest.mark.unit
class TestSubject:
    """Test abstract Subject class."""
    
    @pytest.fixture
    def subject(self):
        """Create a concrete Subject implementation for testing."""
        class ConcreteSubject(Subject):
            def notify(self, event_data: GenerationEventData):
                for observer in self._observers:
                    observer.update(event_data)
        
        return ConcreteSubject()
    
    @pytest.fixture
    def mock_observer(self):
        """Create a mock observer."""
        return Mock(spec=Observer)
    
    def test_subject_initialization(self, subject):
        """Test subject initialization."""
        assert len(subject._observers) == 0
    
    def test_attach_observer(self, subject, mock_observer):
        """Test attaching an observer."""
        subject.attach(mock_observer)
        
        assert len(subject._observers) == 1
        assert mock_observer in subject._observers
    
    def test_attach_same_observer_twice(self, subject, mock_observer):
        """Test attaching the same observer twice."""
        subject.attach(mock_observer)
        subject.attach(mock_observer)
        
        # Should only be attached once
        assert len(subject._observers) == 1
    
    def test_detach_observer(self, subject, mock_observer):
        """Test detaching an observer."""
        subject.attach(mock_observer)
        subject.detach(mock_observer)
        
        assert len(subject._observers) == 0
        assert mock_observer not in subject._observers
    
    def test_detach_nonexistent_observer(self, subject, mock_observer):
        """Test detaching an observer that wasn't attached."""
        subject.detach(mock_observer)  # Should not raise error
        assert len(subject._observers) == 0
    
    def test_notify_observers(self, subject, mock_observer):
        """Test notifying attached observers."""
        subject.attach(mock_observer)
        
        event_data = GenerationEventData(
            GenerationEvent.CUSTOMERS_GENERATED,
            {"count": 5}
        )
        
        subject.notify(event_data)
        
        mock_observer.update.assert_called_once_with(event_data)


@pytest.mark.unit
class TestProgressObserver:
    """Test ProgressObserver implementation."""
    
    @pytest.fixture
    def progress_observer(self):
        """Create a ProgressObserver instance."""
        try:
            from src.syfi.patterns.observers import ProgressObserver
            return ProgressObserver()
        except ImportError:
            pytest.skip("ProgressObserver not implemented yet")
    
    def test_progress_observer_initialization(self, progress_observer):
        """Test progress observer initialization."""
        assert isinstance(progress_observer, Observer)
        assert progress_observer.total_steps == 0
        assert progress_observer.completed_steps == 0
    
    @patch('builtins.print')
    def test_update_with_progress_event(self, mock_print, progress_observer):
        """Test update with progress-related event."""
        event_data = GenerationEventData(
            GenerationEvent.CUSTOMERS_GENERATED,
            {"count": 10, "total": 100, "source": "test_generator"}
        )
        
        progress_observer.update(event_data)
        
        # Should print progress information
        mock_print.assert_called()
        
        # Check that progress was updated
        assert progress_observer.completed_steps > 0
    
    def test_calculate_progress_percentage(self, progress_observer):
        """Test progress percentage calculation."""
        progress_observer.total_steps = 100
        progress_observer.completed_steps = 25
        
        percentage = progress_observer.get_progress_percentage()
        
        assert percentage == 25.0
    
    def test_calculate_progress_percentage_no_total(self, progress_observer):
        """Test progress percentage when no total steps set."""
        progress_observer.completed_steps = 10
        
        percentage = progress_observer.get_progress_percentage()
        
        assert percentage == 0.0  # Cannot calculate without total


@pytest.mark.unit
class TestLoggingObserver:
    """Test LoggingObserver implementation."""
    
    @pytest.fixture
    def logging_observer(self):
        """Create a LoggingObserver instance."""
        return LoggingObserver()
    
    @patch('src.syfi.patterns.observers.logging')
    def test_update_logs_event(self, mock_logging, logging_observer):
        """Test that update logs the event."""
        event_data = GenerationEventData(
            GenerationEvent.ERROR_OCCURRED,
            {"error": "Test error", "source": "test"}
        )
        
        logging_observer.update(event_data)
        
        # Should log the event
        mock_logging.info.assert_called()
    
    @patch('src.syfi.patterns.observers.logging')
    def test_update_logs_error_event_as_error(self, mock_logging, logging_observer):
        """Test that error events are logged as errors."""
        event_data = GenerationEventData(
            GenerationEvent.ERROR_OCCURRED,
            {"error": "Critical error", "source": "test"}
        )
        
        logging_observer.update(event_data)
        
        # Error events should be logged as errors
        mock_logging.error.assert_called()


@pytest.mark.unit
class TestMetricsObserver:
    """Test MetricsObserver implementation."""
    
    @pytest.fixture
    def metrics_observer(self):
        """Create a MetricsObserver instance."""
        return MetricsObserver()
    
    def test_metrics_observer_initialization(self, metrics_observer):
        """Test metrics observer initialization."""
        assert isinstance(metrics_observer, Observer)
        assert len(metrics_observer.metrics) == 0
    
    def test_update_records_metrics(self, metrics_observer):
        """Test that update records metrics."""
        event_data = GenerationEventData(
            GenerationEvent.CUSTOMERS_GENERATED,
            {"count": 15, "duration": 2.5, "source": "test"}
        )
        
        metrics_observer.update(event_data)
        
        # Should record metrics
        assert len(metrics_observer.metrics) == 1
        recorded_metric = metrics_observer.metrics[0]
        assert recorded_metric['event_type'] == GenerationEvent.CUSTOMERS_GENERATED
        assert recorded_metric['count'] == 15
        assert recorded_metric['duration'] == 2.5
    
    def test_get_metrics_summary(self, metrics_observer):
        """Test getting metrics summary."""
        # Add some test metrics
        events = [
            GenerationEventData(GenerationEvent.CUSTOMERS_GENERATED, {"count": 10}),
            GenerationEventData(GenerationEvent.ACCOUNTS_GENERATED, {"count": 20}),
            GenerationEventData(GenerationEvent.CUSTOMERS_GENERATED, {"count": 15})
        ]
        
        for event in events:
            metrics_observer.update(event)
        
        summary = metrics_observer.get_summary()
        
        # Should summarize by event type
        assert 'customers_generated' in summary
        assert 'accounts_generated' in summary
        assert summary['customers_generated']['total_count'] == 25  # 10 + 15
        assert summary['accounts_generated']['total_count'] == 20


@pytest.mark.unit
class TestEmailNotificationObserver:
    """Test EmailNotificationObserver implementation."""
    
    def test_email_observer_exists(self):
        """Test that EmailNotificationObserver can be imported."""
        try:
            from src.syfi.patterns.observers import EmailNotificationObserver
            observer = EmailNotificationObserver("test@example.com")
            assert isinstance(observer, Observer)
        except ImportError:
            pytest.skip("EmailNotificationObserver not implemented yet")


@pytest.mark.unit
class TestGenerationSubject:
    """Test GenerationSubject implementation."""
    
    @pytest.fixture
    def generation_subject(self):
        """Create a GenerationSubject instance."""
        return GenerationSubject()
    
    @pytest.fixture
    def mock_observer(self):
        """Create a mock observer."""
        return Mock(spec=Observer)
    
    def test_generation_subject_initialization(self, generation_subject):
        """Test GenerationSubject initialization."""
        assert isinstance(generation_subject, Subject)
    
    def test_notify_profile_created(self, generation_subject, mock_observer):
        """Test notifying profile creation."""
        generation_subject.attach(mock_observer)
        
        generation_subject.notify_profile_created("test_profile", {"count": 1})
        
        mock_observer.update.assert_called_once()
        call_args = mock_observer.update.call_args[0][0]
        assert call_args.event_type == GenerationEvent.PROFILE_CREATED
    
    def test_notify_customers_generated(self, generation_subject, mock_observer):
        """Test notifying customers generation."""
        generation_subject.attach(mock_observer)
        
        generation_subject.notify_customers_generated(10, {"source": "test"})
        
        mock_observer.update.assert_called_once()
        call_args = mock_observer.update.call_args[0][0]
        assert call_args.event_type == GenerationEvent.CUSTOMERS_GENERATED
        assert call_args.data["count"] == 10
    
    def test_notify_error(self, generation_subject, mock_observer):
        """Test notifying errors."""
        generation_subject.attach(mock_observer)
        
        error_msg = "Test error occurred"
        generation_subject.notify_error(error_msg, {"context": "test"})
        
        mock_observer.update.assert_called_once()
        call_args = mock_observer.update.call_args[0][0]
        assert call_args.event_type == GenerationEvent.ERROR_OCCURRED
        assert call_args.data["error"] == error_msg


@pytest.mark.unit
class TestDatabaseGenerationTracker:
    """Test DatabaseGenerationTracker implementation."""
    
    def test_database_tracker_exists(self):
        """Test that DatabaseGenerationTracker can be imported."""
        try:
            from src.syfi.patterns.observers import DatabaseGenerationTracker
            tracker = DatabaseGenerationTracker()
            assert isinstance(tracker, Observer)
        except ImportError:
            pytest.skip("DatabaseGenerationTracker not implemented yet")


@pytest.mark.integration
class TestObserverIntegration:
    """Integration tests for observer pattern."""
    
    def test_multiple_observers_with_subject(self):
        """Test multiple observers receiving notifications from same subject."""
        from src.syfi.patterns.observers import GenerationSubject
        
        subject = GenerationSubject()
        
        # Create multiple mock observers
        progress_observer = Mock(spec=Observer)
        logging_observer = Mock(spec=Observer)
        metrics_observer = Mock(spec=Observer)
        
        # Attach all observers
        subject.attach(progress_observer)
        subject.attach(logging_observer)
        subject.attach(metrics_observer)
        
        # Notify an event
        subject.notify_customers_generated(50, {"source": "integration_test"})
        
        # All observers should be notified
        progress_observer.update.assert_called_once()
        logging_observer.update.assert_called_once()
        metrics_observer.update.assert_called_once()
        
        # All should receive the same event data
        progress_call_args = progress_observer.update.call_args[0][0]
        logging_call_args = logging_observer.update.call_args[0][0]
        metrics_call_args = metrics_observer.update.call_args[0][0]
        
        assert progress_call_args.event_type == logging_call_args.event_type == metrics_call_args.event_type
        assert progress_call_args.data == logging_call_args.data == metrics_call_args.data
    
    def test_observer_attachment_and_detachment(self):
        """Test dynamic observer attachment and detachment."""
        from src.syfi.patterns.observers import GenerationSubject
        
        subject = GenerationSubject()
        observer = Mock(spec=Observer)
        
        # Initially no observers
        subject.notify_customers_generated(10, {})
        observer.update.assert_not_called()
        
        # Attach observer
        subject.attach(observer)
        subject.notify_customers_generated(10, {})
        assert observer.update.call_count == 1
        
        # Detach observer  
        subject.detach(observer)
        observer.update.reset_mock()
        subject.notify_customers_generated(10, {})
        observer.update.assert_not_called()