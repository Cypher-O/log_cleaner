import pytest
from unittest.mock import Mock
import signal
from src.logcleaner import GracefulExit, LogCleaner

class TestGracefulExit:
    @pytest.fixture
    def ui(self):
        """Create a mock ConsoleUI instance."""
        return Mock()

    @pytest.fixture
    def graceful_exit(self, ui):
        """Create a GracefulExit instance in testing mode."""
        return GracefulExit(ui, testing=True)

    def test_exit_handler(self, graceful_exit):
        """Test the exit handler raises KeyboardInterrupt in test mode."""
        with pytest.raises(KeyboardInterrupt):
            graceful_exit._exit_handler(signal.SIGINT, None)
        
        assert graceful_exit.killed is True
        assert graceful_exit.ui.print_warning.called
        warning_msg = graceful_exit.ui.print_warning.call_args[0][0]
        assert "Cleaning up..." in warning_msg

    def test_double_interrupt(self, graceful_exit):
        """Test double interrupt raises SystemExit in test mode."""
        graceful_exit.killed = True
        
        with pytest.raises(SystemExit) as exc_info:
            graceful_exit._exit_handler(signal.SIGINT, None)
            
        assert exc_info.value.code == 1
        assert graceful_exit.ui.print_error.called
        error_msg = graceful_exit.ui.print_error.call_args[0][0]
        assert "Force quitting..." in error_msg
    
    @pytest.fixture
    def cleaner(self):
        """Create a LogCleaner instance in testing mode."""
        return LogCleaner(testing=True)

if __name__ == '__main__':
    pytest.main(['-v'])