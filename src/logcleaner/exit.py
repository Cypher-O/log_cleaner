import signal
import sys
from typing import Optional

from .console import ConsoleUI 

class GracefulExit:
    """
    A class to handle graceful termination of the application.

    This class manages the cleanup process when the application receives termination signals.
    It ensures that any necessary cleanup operations are performed before exiting.
    """
    def __init__(self, ui: 'ConsoleUI', testing: bool = False):
        """
        Initializes the GracefulExit class, setting up signal handling for termination.

        This constructor takes a ConsoleUI instance to provide user feedback during the exit process.
        It sets up signal handlers for SIGINT and SIGTERM to manage graceful exits.

        Args:
            ui (ConsoleUI): An instance of ConsoleUI for displaying messages.
            testing (bool): Flag to indicate if running in test mode
        """
        self.ui = ui
        self.killed = False
        self.testing = testing
        
        if not testing:
            signal.signal(signal.SIGINT, self._exit_handler)
            signal.signal(signal.SIGTERM, self._exit_handler)

    def _exit_handler(self, signum, frame: Optional[object]):
        """
        Handles exit signals and manages the cleanup process.

        This method is invoked when the application receives a termination signal. It checks if
        the exit has already been initiated and performs the cleanup operations accordingly.
        
        In testing mode, raises KeyboardInterrupt instead of exiting
        to allow test verification.

        Args:
            signum: The signal number received.
            frame: The current stack frame (unused).
        """
        if self.killed:
            self.ui.print_error("\nForce quitting...")
            if self.testing:
                raise SystemExit(1)
            sys.exit(1)
        
        self.killed = True
        self.ui.print_warning("\nReceived termination signal. Cleaning up...")

        if self.testing:
            raise KeyboardInterrupt
            
        try:
            if hasattr(self, 'cleanup_callback'):
                self.cleanup_callback()
        finally:
            sys.exit(0)
            
    def register_cleanup(self, callback: callable) -> None:
        """
        Register a cleanup function to be called before exit.
        
        Args:
            callback: Function to call during cleanup
        """
        self.cleanup_callback = callback