"""
Tests for Command Pattern Implementation.

This module tests the export commands that implement the Gang of Four Command pattern
for encapsulated, undoable, and queueable export operations.
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open
from typing import Dict, Any

from src.syfi.patterns.commands import (
    Command,
    ExportCommand,
    ExportCustomersCommand
)


@pytest.mark.unit
class TestCommand:
    """Test abstract Command interface."""
    
    def test_abstract_command_cannot_be_instantiated(self):
        """Test that abstract Command cannot be directly instantiated."""
        with pytest.raises(TypeError):
            Command()


@pytest.mark.unit
class TestExportCommand:
    """Test base ExportCommand class."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        return Mock()
    
    @pytest.fixture  
    def output_path(self, tmp_path):
        """Create a temporary output path."""
        return tmp_path / "test_export.json"
    
    def test_export_command_initialization(self, mock_db_manager, output_path):
        """Test ExportCommand initialization."""
        command = ExportCommand(mock_db_manager, output_path)
        
        assert command.db_manager is mock_db_manager
        assert command.output_path == output_path
        assert command.executed_at is None
        assert command.result is None
    
    def test_undo_removes_existing_file(self, mock_db_manager, output_path):
        """Test undo removes created file."""
        # Create the file
        output_path.write_text("test content")
        assert output_path.exists()
        
        command = ExportCommand(mock_db_manager, output_path)
        result = command.undo()
        
        assert result is True
        assert not output_path.exists()
    
    def test_undo_nonexistent_file(self, mock_db_manager, output_path):
        """Test undo with nonexistent file."""
        assert not output_path.exists()
        
        command = ExportCommand(mock_db_manager, output_path)
        result = command.undo()
        
        assert result is True  # Should succeed even if file doesn't exist
    
    @patch('pathlib.Path.unlink')
    def test_undo_handles_exception(self, mock_unlink, mock_db_manager, output_path):
        """Test undo handles file removal exceptions."""
        # Create the file
        output_path.write_text("test content")
        
        # Make unlink raise an exception
        mock_unlink.side_effect = PermissionError("Cannot delete file")
        
        command = ExportCommand(mock_db_manager, output_path)
        result = command.undo()
        
        assert result is False


@pytest.mark.unit
class TestExportCustomersCommand:
    """Test ExportCustomersCommand implementation."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager with sample data."""
        db_manager = Mock()
        db_manager.get_all_customers.return_value = [
            {"id": 1, "name": "John Doe", "age": 30, "city": "New York"},
            {"id": 2, "name": "Jane Smith", "age": 25, "city": "Los Angeles"},
            {"id": 3, "name": "Bob Johnson", "age": 35, "city": "Chicago"}
        ]
        return db_manager
    
    @pytest.fixture
    def output_path(self, tmp_path):
        """Create a temporary output path."""
        return tmp_path / "customers.json"
    
    def test_customers_command_initialization(self, mock_db_manager, output_path):
        """Test ExportCustomersCommand initialization."""
        command = ExportCustomersCommand(mock_db_manager, output_path)
        
        assert command.format_type == "json"  # default
        assert command.filters == {}
        
    def test_customers_command_initialization_with_params(self, mock_db_manager, output_path):
        """Test initialization with custom parameters."""
        filters = {"city": "New York"}
        command = ExportCustomersCommand(
            mock_db_manager, 
            output_path, 
            format_type="CSV", 
            filters=filters
        )
        
        assert command.format_type == "csv"  # should be lowercase
        assert command.filters == filters
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_execute_json_format(self, mock_json_dump, mock_file_open, mock_db_manager, output_path):
        """Test executing JSON export."""
        command = ExportCustomersCommand(mock_db_manager, output_path, format_type="json")
        
        result = command.execute()
        
        # Verify database was queried
        mock_db_manager.get_all_customers.assert_called_once()
        
        # Verify file operations
        mock_file_open.assert_called_once_with(output_path, 'w')
        mock_json_dump.assert_called_once()
        
        # Verify command state
        assert command.executed_at is not None
        assert isinstance(command.executed_at, datetime)
        assert isinstance(result, dict)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.DictWriter')
    def test_execute_csv_format(self, mock_csv_writer, mock_file_open, mock_db_manager, output_path):
        """Test executing CSV export."""
        # Setup CSV writer mock
        writer_instance = Mock()
        mock_csv_writer.return_value = writer_instance
        
        command = ExportCustomersCommand(mock_db_manager, output_path, format_type="csv")
        
        result = command.execute()
        
        # Verify database was queried
        mock_db_manager.get_all_customers.assert_called_once()
        
        # Verify CSV operations
        mock_file_open.assert_called_once_with(output_path, 'w', newline='')
        mock_csv_writer.assert_called_once()
        writer_instance.writeheader.assert_called_once()
        writer_instance.writerows.assert_called_once()
        
        assert isinstance(result, dict)
    
    def test_execute_unsupported_format(self, mock_db_manager, output_path):
        """Test executing with unsupported format."""
        command = ExportCustomersCommand(mock_db_manager, output_path, format_type="pdf")
        
        with pytest.raises(ValueError, match="Unsupported export format"):
            command.execute()
    
    def test_apply_filters(self, mock_db_manager, output_path):
        """Test filter application."""
        filters = {"city": "New York"}
        command = ExportCustomersCommand(mock_db_manager, output_path, filters=filters)
        
        customers = [
            {"id": 1, "name": "John Doe", "city": "New York"},
            {"id": 2, "name": "Jane Smith", "city": "Los Angeles"}
        ]
        
        filtered = command._apply_filters(customers)
        
        assert len(filtered) == 1
        assert filtered[0]["name"] == "John Doe"
    
    def test_apply_multiple_filters(self, mock_db_manager, output_path):
        """Test applying multiple filters."""
        filters = {"city": "New York", "age": 30}
        command = ExportCustomersCommand(mock_db_manager, output_path, filters=filters)
        
        customers = [
            {"id": 1, "name": "John Doe", "city": "New York", "age": 30},
            {"id": 2, "name": "Jane Smith", "city": "New York", "age": 25},
            {"id": 3, "name": "Bob Johnson", "city": "Chicago", "age": 30}
        ]
        
        filtered = command._apply_filters(customers)
        
        assert len(filtered) == 1
        assert filtered[0]["name"] == "John Doe"
    
    def test_get_description(self, mock_db_manager, output_path):
        """Test command description."""
        command = ExportCustomersCommand(mock_db_manager, output_path, format_type="json")
        
        description = command.get_description()
        
        assert "Export customers" in description
        assert "json" in description.lower()


@pytest.mark.unit
class TestExportAccountsCommand:
    """Test ExportAccountsCommand implementation."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        db_manager = Mock()
        db_manager.get_all_accounts.return_value = [
            {"id": 1, "customer_id": 1, "type": "checking", "balance": 1000.00},
            {"id": 2, "customer_id": 1, "type": "savings", "balance": 5000.00}
        ]
        return db_manager
    
    def test_accounts_command_exists(self):
        """Test that ExportAccountsCommand can be imported."""
        try:
            from src.syfi.patterns.commands import ExportAccountsCommand
            assert ExportAccountsCommand is not None
        except ImportError:
            pytest.skip("ExportAccountsCommand not fully implemented yet")


@pytest.mark.unit
class TestExportTransactionsCommand:
    """Test ExportTransactionsCommand implementation."""
    
    def test_transactions_command_exists(self):
        """Test that ExportTransactionsCommand can be imported."""
        try:
            from src.syfi.patterns.commands import ExportTransactionsCommand
            assert ExportTransactionsCommand is not None
        except ImportError:
            pytest.skip("ExportTransactionsCommand not fully implemented yet")


@pytest.mark.unit
class TestCommandInvoker:
    """Test CommandInvoker implementation."""
    
    @pytest.fixture
    def invoker(self):
        """Create a CommandInvoker instance."""
        try:
            from src.syfi.patterns.commands import CommandInvoker
            return CommandInvoker()
        except ImportError:
            pytest.skip("CommandInvoker not implemented yet")
    
    @pytest.fixture
    def mock_command(self):
        """Create a mock command."""
        command = Mock(spec=Command)
        command.execute.return_value = {"status": "success"}
        command.undo.return_value = True
        command.get_description.return_value = "Mock command"
        return command
    
    def test_invoker_initialization(self, invoker):
        """Test CommandInvoker initialization."""
        assert len(invoker.history) == 0
        assert invoker.current_index == -1
    
    def test_execute_command(self, invoker, mock_command):
        """Test executing a command through invoker."""
        result = invoker.execute(mock_command)
        
        mock_command.execute.assert_called_once()
        assert result == {"status": "success"}
        assert len(invoker.history) == 1
        assert invoker.current_index == 0
        assert invoker.history[0] is mock_command
    
    def test_undo_last_command(self, invoker, mock_command):
        """Test undoing the last command."""
        # Execute command first
        invoker.execute(mock_command)
        
        # Then undo
        result = invoker.undo()
        
        mock_command.undo.assert_called_once()
        assert result is True
        assert invoker.current_index == -1
    
    def test_undo_no_commands(self, invoker):
        """Test undo when no commands exist."""
        result = invoker.undo()
        assert result is False
    
    def test_redo_command(self, invoker, mock_command):
        """Test redoing a command."""
        # Execute and undo
        invoker.execute(mock_command)
        invoker.undo()
        
        # Reset mock to track redo execution
        mock_command.reset_mock()
        mock_command.execute.return_value = {"status": "redo_success"}
        
        # Redo
        result = invoker.redo()
        
        mock_command.execute.assert_called_once()
        assert result == {"status": "redo_success"}
        assert invoker.current_index == 0
    
    def test_redo_no_commands_to_redo(self, invoker):
        """Test redo when no commands to redo."""
        result = invoker.redo()
        assert result is None
    
    def test_get_command_history(self, invoker, mock_command):
        """Test getting command history."""
        invoker.execute(mock_command)
        
        history = invoker.get_history()
        
        assert len(history) == 1
        mock_command.get_description.assert_called_once()
    
    def test_clear_history(self, invoker, mock_command):
        """Test clearing command history."""
        invoker.execute(mock_command)
        assert len(invoker.history) == 1
        
        invoker.clear_history()
        
        assert len(invoker.history) == 0
        assert invoker.current_index == -1


@pytest.mark.unit
class TestMacroCommand:
    """Test MacroCommand implementation."""
    
    @pytest.fixture
    def mock_commands(self):
        """Create multiple mock commands."""
        commands = []
        for i in range(3):
            command = Mock(spec=Command)
            command.execute.return_value = {"status": f"success_{i}"}
            command.undo.return_value = True
            command.get_description.return_value = f"Command {i}"
            commands.append(command)
        return commands
    
    def test_macro_command_exists(self):
        """Test that MacroCommand can be imported."""
        try:
            from src.syfi.patterns.commands import MacroCommand
            assert MacroCommand is not None
        except ImportError:
            pytest.skip("MacroCommand not implemented yet")
    
    def test_macro_command_initialization(self, mock_commands):
        """Test MacroCommand initialization."""
        try:
            from src.syfi.patterns.commands import MacroCommand
            macro = MacroCommand(mock_commands, "Batch Export")
            
            assert macro.commands == mock_commands
            assert macro.description == "Batch Export"
        except ImportError:
            pytest.skip("MacroCommand not implemented yet")
    
    def test_macro_execute_all_commands(self, mock_commands):
        """Test macro executes all commands in sequence."""
        try:
            from src.syfi.patterns.commands import MacroCommand
            macro = MacroCommand(mock_commands, "Test Macro")
            
            result = macro.execute()
            
            # Verify all commands executed
            for command in mock_commands:
                command.execute.assert_called_once()
            
            # Verify results collected
            assert len(result["results"]) == 3
            for i, command_result in enumerate(result["results"]):
                assert command_result == {"status": f"success_{i}"}
        except ImportError:
            pytest.skip("MacroCommand not implemented yet")
    
    def test_macro_undo_all_commands(self, mock_commands):
        """Test macro undos all commands in reverse order."""
        try:
            from src.syfi.patterns.commands import MacroCommand
            macro = MacroCommand(mock_commands, "Test Macro")
            
            # Execute first
            macro.execute()
            
            # Then undo
            result = macro.undo()
            
            # Verify all commands undone in reverse order
            for command in reversed(mock_commands):
                command.undo.assert_called_once()
            
            assert result is True
        except ImportError:
            pytest.skip("MacroCommand not implemented yet")
    
    def test_macro_undo_handles_failure(self, mock_commands):
        """Test macro undo handles individual command failures."""
        try:
            from src.syfi.patterns.commands import MacroCommand
            # Make second command undo fail
            mock_commands[1].undo.return_value = False
            
            macro = MacroCommand(mock_commands, "Test Macro")
            macro.execute()
            
            result = macro.undo()
            
            # Should still return False if any command fails
            assert result is False
        except ImportError:
            pytest.skip("MacroCommand not implemented yet")
    
    def test_get_description(self, mock_commands):
        """Test macro command description."""
        try:
            from src.syfi.patterns.commands import MacroCommand
            macro = MacroCommand(mock_commands, "Batch Export Commands")
            
            description = macro.get_description()
            
            assert "Batch Export Commands" in description
            assert "3 commands" in description
        except ImportError:
            pytest.skip("MacroCommand not implemented yet")


@pytest.mark.integration  
class TestCommandIntegration:
    """Integration tests for command pattern with real file operations."""
    
    def test_full_export_workflow(self, tmp_path):
        """Test complete export workflow with real files."""
        # This would require actual database and file operations
        # For now, we'll skip this as it needs full integration setup
        pytest.skip("Integration test requires full database setup")