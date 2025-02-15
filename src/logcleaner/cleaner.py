import os
from pathlib import Path
import re
from datetime import datetime, timedelta
import logging
import shutil
import sys
from typing import Dict, List, Optional, Set, Union
from .file_manager import LogFileManager
from .console import ConsoleUI
from .exit import GracefulExit

class LogCleaner:
    """
    Utility class for cleaning log statements from various programming files (JavaScript, TypeScript, Python).
    
    Features:
        - Cleans log statements and creates backups
        - Manages user interactions
        - Generates reports on the cleaning process

    Attributes:
        ASSETS_DIR_NAME (str): Directory for cleaned assets
        SUPPORTED_EXTENSIONS (Dict[str, str]): Supported file extensions and their descriptions

    Args:
        testing (bool): Flag for test mode during initialization

    Example:
        cleaner = LogCleaner()
        if cleaner.initialize_session():
            print("Session initialized successfully")
    """
    ASSETS_DIR_NAME = 'lc-cleaned-assets'
    
    SUPPORTED_EXTENSIONS: Dict[str, str] = {
        '.js': 'JavaScript files',
        '.jsx': 'React JavaScript files',
        '.ts': 'TypeScript files',
        '.tsx': 'React TypeScript files',
        '.py': 'Python files'
    }
    
    def __init__(self, testing: bool = False):
        """
        Initializes the LogCleaner class by setting up the user interface (UI), exit handling, and default settings.
        
        This constructor prepares the necessary attributes and configurations for subsequent operations. It also displays the logo
        of the application and sets initial values for the source path, assets directory, selected file types, and logging settings.
        
        Args:
        testing (bool): Flag to indicate if running in test mode
        """
        self.ui = ConsoleUI()
        self.ui.print_logo()
        
        self.exit_handler = GracefulExit(self.ui, testing=testing)
        self.exit_handler.register_cleanup(self.cleanup)
        self.log_manager = LogFileManager(self.ui)
        
        self.should_backup = False
        
        self.source_path: Optional[Union[str, List[str]]] = None
        self.assets_dir: Optional[Path] = None
        
        self.selected_types: Set[str] = set()
        
        self.console_methods = [
            'log', 'error', 'warn', 'info', 'debug', 
            'trace', 'dir', 'dirxml', 'table', 'count',
            'countReset', 'assert', 'clear', 'group', 
            'groupEnd', 'groupCollapsed', 'time', 'timeEnd',
            'timeLog', 'profile', 'profileEnd'
        ]

        self.python_patterns = [
            r'import\s+logging\s*(?:as\s+\w+)?\s*',
            r'from\s+logging\s+import\s+.*',
            r'_?logger\s*=\s*logging\.getLogger\([^)]*\)',
            r'logging\.[a-zA-Z]+\([^)]*\)',
            r'_?logger\.[a-zA-Z]+\([^)]*\)',
            r'logging\.[a-zA-Z]+\s*\(\s*(?:[^()]*?\s*\+?\s*)*[^()]*?\)',
            r'_?logger\.[a-zA-Z]+\s*\(\s*(?:[^()]*?\s*\+?\s*)*[^()]*?\)'
        ]
        
        methods_pattern = '|'.join(self.console_methods)
        self.console_pattern = rf'\bconsole\.({methods_pattern})\s*\(\s*(?:[^;]*?\s*\+?\s*)*[^;]*?\);?'
        
        self.compiled_python_patterns = [
            re.compile(pattern, re.MULTILINE | re.DOTALL) 
            for pattern in self.python_patterns
        ]
        self.compiled_console_pattern = re.compile(
            self.console_pattern, 
            re.MULTILINE | re.DOTALL
        )
        
        self.stats = {
            'files_processed': 0,
            'lines_removed': 0,
            'removed_statements': {},
            'file_types_processed': {}
        }
        
    def initialize_session(self) -> bool:
        """
        Initializes the cleanup session interactively, guiding the user through the process
        of selecting files or directories for cleaning.

        Returns:
            bool: True if the session is initialized successfully; False otherwise.
        """
        try:
            while True:
                mode_choice = self._get_cleaning_mode()
                
                if mode_choice in [1, 3]:  # Code files or both
                    if not self._setup_code_cleaning():
                        if not self._prompt_continue():
                            return False
                        continue

                if mode_choice in [2, 3]:  # Log files or both
                    if not self._setup_log_cleaning():
                        if not self._prompt_continue():
                            return False
                        continue

                if mode_choice == 2:
                    if not self._prompt_continue():
                        return False
                    continue

                return True

        except KeyboardInterrupt:
            self.cleanup()
            return False
        except Exception as e:
            self.ui.print_error(f"Error during initialization: {str(e)}")
            self.cleanup()
            return False

    def _handle_existing_cron(self) -> bool:
        """
        Handles removal of existing cron jobs if present.

        This method checks for any active automated cleaning schedules and prompts the user to remove them.
        
        Returns:
            bool: True if the user decides to continue; False if cleaning should be aborted.
        """
        if self.log_manager.has_cron_job():
            self.ui.print_info("An automated log cleaning schedule is currently active")
            if self.ui.prompt_yes_no("Would you like to remove the automated cleaning schedule?"):
                if self.log_manager.remove_cron_job():
                    self.ui.print_success("Automated cleaning schedule removed")
                    return self._prompt_continue()
        return True
    
    def _get_cleaning_mode(self) -> int:
        """
        Prompts user for cleaning mode selection.

        This method allows the user to choose between cleaning log statements in code files, cleaning log files, or both.

        Returns:
            int: The selected cleaning mode.
        """
        self.ui.print_step("Select cleaning mode", 4, 1)
        
        choices = ["Log statements in code files", "Log files", "Both"]
        
        if self.log_manager.has_cron_job():
            choices.append("Manage automated cleaning")
        
        mode_choice = self.ui.prompt_choice(
            "What would you like to do?",
            choices
        )
    
        if mode_choice == 4:
            return self._handle_automation_management()
            
        return mode_choice

    def _handle_automation_management(self) -> int:
        """
        Manages automated cleaning schedule options.

        This method presents the user with options to view, remove, or manage existing automated cleaning schedules.

        Returns:
            int: The mode selected after managing automation.
        """
        self.ui.print_step("Automation Management", 4, 1)
        
        jobs = list(self.log_manager.get_cron_jobs())
        
        if not jobs:
            self.ui.print_info("No automated cleaning schedules found")
            return self._get_cleaning_mode() 
            
        self.ui.print_info("\nCurrent automation schedules:")
        for i, job in enumerate(jobs, 1):
            schedule = job.slices.render()
            directory = job.command.split('"')[1]  
            self.ui.print_info(f"{i}. Directory: {directory}")
            self.ui.print_info(f"   Schedule: {schedule}")
            
        choices = ["Remove specific schedule", "Remove all schedules", "Return to main menu"]
        action = self.ui.prompt_choice("What would you like to do?", choices)
        
        if action == 1: 
            if len(jobs) == 1:
                job_to_remove = jobs[0]
            else:
                job_num = int(self.ui.prompt_input(f"Enter schedule number to remove (1-{len(jobs)})"))
                job_to_remove = jobs[job_num - 1]
                
            self.log_manager.remove_specific_cron_job(job_to_remove)
            self.ui.print_success("Schedule removed successfully")
            
        elif action == 2:  
            self.log_manager.remove_cron_job()
            self.ui.print_success("All automation schedules removed")
            
        return self._get_cleaning_mode()

    def _setup_code_cleaning(self) -> bool:
        """
        Sets up configuration for cleaning code files.

        This method guides the user through selecting source files and configuring backup options.

        Returns:
            bool: True if setup is successful; False otherwise.
        """
        
        self.ui.print_step("Select source", 3, 1)
        source_choice = self.ui.prompt_choice(
            "Where are the files you want to clean?",
            ["Select a directory", "Select specific files"]
        )

        self.ui.print_step("Specify location", 3, 2)
        if source_choice == 1:
            if not self._handle_directory_mode():
                return False
        else:
            if not self._handle_file_mode():
                return False

        return self._setup_assets_and_backup()

    def _handle_directory_mode(self) -> bool:
        """
        Handles directory selection for code files.

        This method allows the user to specify a directory for cleaning, validating the path and selecting file types.

        Returns:
            bool: True if the directory is valid and files are selected; False otherwise.
        """
        while True:
            try:
                path = input(f"{self.ui.BOLD}Enter directory path (or '.' for current directory): {self.ui.END}")
                if not os.path.isdir(path):
                    self.ui.print_error("Invalid directory path")
                    continue

                self.source_path = os.path.abspath(path)
                self._display_supported_types()
                
                if not self._select_file_types():
                    return False
                    
                return True

            except KeyboardInterrupt:
                raise
            except Exception as e:
                self.ui.print_error(f"Error: {str(e)}")
                return False

    def _handle_file_mode(self) -> bool:
        """
        Handles individual file selection for cleaning.

        This method allows the user to select specific files for cleaning, validating each file's existence and type.

        Returns:
            bool: True if valid files are selected; False otherwise.
        """
        self._display_supported_types()
        files = self._get_file_list()
        
        if not files:
            self.ui.print_error("No files specified")
            return False

        valid_files, invalid_files = self.validate_files(files)
        
        if invalid_files:
            self.ui.print_error("\nThe following files cannot be processed:")
            for file in invalid_files:
                self.ui.print_error(f"  - {file}")

        if not valid_files:
            self.ui.print_error("No valid files to process")
            return False

        self.source_path = valid_files
        self.selected_types = {Path(f).suffix.lower() for f in valid_files}
        return True

    def _setup_log_cleaning(self) -> bool:
        """
        Sets up configuration for cleaning log files.

        This method prompts the user to specify how log files will be selected for cleaning.

        Returns:
            bool: True if log cleaning setup is successful; False otherwise.
        """
        self.ui.print_step("Log file cleaning", 4, 2)
        
        source_choice = self.ui.prompt_choice(
            "How would you like to specify the log files location?",
            ["Current directory (.)", "Specify directory path", "Select specific log files"]
        )
        
        log_files = []
        log_dir = ""
        
        if source_choice == 1: 
            log_dir = str(Path('.').resolve())
            self.ui.print_info(f"Searching for log files in current directory: {log_dir}")
            log_files = self.log_manager.get_log_files(Path(log_dir))
            if not log_files:
                self.ui.print_error("No log files found in the current directory")
                return False
                
        elif source_choice == 2: 
            while True:
                log_dir = input(f"{self.ui.BOLD}Enter directory path: {self.ui.END}")
                
                if os.path.isfile(log_dir):
                    self.ui.print_error("Please enter a directory path, not a file path")
                    continue
                    
                if not os.path.isdir(log_dir):
                    self.ui.print_error("Invalid directory path. Please try again")
                    continue
                        
                self.ui.print_info(f"Searching for log files in: {log_dir}")
                log_files = self.log_manager.get_log_files(Path(log_dir))
                
                if not log_files:
                    self.ui.print_error(f"No log files found in: {log_dir}")
                    if not self.ui.prompt_yes_no("Would you like to try another directory?"):
                        return False
                    continue

                break
                
        else: 
            self.ui.print_warning("\nEnter log file paths one by one. Press Enter twice when done.")
            while True:
                file_path = input(f"{self.ui.BOLD}Enter log file path (or press Enter to finish): {self.ui.END}")
                if not file_path and log_files:
                    break
                if not file_path:
                    continue
                    
                if not os.path.isfile(file_path):
                    self.ui.print_error(f"Invalid file path: {file_path}")
                    continue
                    
                file_path = Path(file_path)
                if not file_path.exists():
                    self.ui.print_error(f"File does not exist: {file_path}")
                    continue

                if not self.log_manager.is_log_file(file_path):
                    self.ui.print_warning(f"File may not be a log file: {file_path}")
                    if not self.ui.prompt_yes_no("Include this file anyway?"):
                        continue

                log_files.append(file_path)
                if not log_dir:
                    log_dir = str(file_path.parent)
                    
            if not log_files:
                self.ui.print_error("No valid log files specified")
                return False
            
        return self._configure_log_retention(log_files, log_dir)

    def _configure_log_retention(self, log_files: list, log_dir: str) -> bool:
        """
        Configures log retention period and automation settings.

        This method allows the user to specify how long logs should be retained and optionally sets up automation.

        Returns:
            bool: True if configuration is successful; False otherwise.
        """
        self.ui.print_info(f"\nFound {len(log_files)} log files")
        
        if len(log_files) <= 10:
            self.ui.print_info("\nLog files found:")
            for file in log_files:
                self.ui.print_info(f"  - {file}")
        
        if not self.ui.prompt_yes_no("\nProceed with log cleaning?"):
            return False
        
        self.ui.print_step("Set retention period", 4, 3)
        days = self._get_retention_days()
        if days is None:
            return False

        cutoff_date = datetime.now() - timedelta(days=days)
        files_cleaned, lines_removed = self.log_manager.clean_logs_before_date(log_files, cutoff_date)
        self.ui.print_success(f"Cleaned {files_cleaned} log files")
        if files_cleaned > 0:
            self.ui.print_info(f"Total lines removed: {lines_removed}")

        self.ui.print_step("Automation setup", 4, 4)
        if self.ui.prompt_yes_no("Would you like to automate log cleaning?"):
            if not self._setup_automation(log_dir):
                return False
        
        self.ui.print_info("\nLog Cleaning Summary:")
        self.ui.print_info(f"  Directory: {log_dir}")
        self.ui.print_info(f"  Files processed: {len(log_files)}")
        self.ui.print_info(f"  Files cleaned: {files_cleaned}")
        if files_cleaned > 0:
            self.ui.print_info(f"  Lines removed: {lines_removed}")
        self.ui.print_info(f"  Retention period: {days} days")
        
        return True

    def _get_retention_days(self) -> Optional[int]:
        """
        Prompts user for log retention period in days.

        This method ensures the user provides a valid number of days for log retention.

        Returns:
            Optional[int]: The number of days to retain logs, or None if input is invalid.
        """
        while True:
            try:
                days = int(self.ui.prompt_input("Enter number of days to retain logs"))
                if days < 0:
                    self.ui.print_error("Please enter a positive number")
                    continue
                return days
            except ValueError:
                self.ui.print_error("Please enter a valid number")

    def _setup_automation(self, log_dir: str) -> bool:
        """
        Sets up automated log cleaning schedule.

        This method prompts the user to specify the time for daily automated cleaning.

        Returns:
            bool: True if automation setup is successful; False otherwise.
        """
        while True:
            try:
                hour = int(self.ui.prompt_input("Enter hour for daily cleaning (0-23)"))
                if not 0 <= hour <= 23:
                    self.ui.print_error("Hour must be between 0 and 23")
                    continue
                    
                minute = int(self.ui.prompt_input("Enter minute (0-59)"))
                if not 0 <= minute <= 59:
                    self.ui.print_error("Minute must be between 0 and 59")
                    continue

                script_path = os.path.abspath(sys.argv[0])
                if self.log_manager.setup_cron_job(script_path, log_dir, hour, minute):
                    self.ui.print_success(f"Automated cleaning scheduled for {hour:02d}:{minute:02d} daily")
                    return True
                return False

            except ValueError:
                self.ui.print_error("Please enter valid numbers")
                return False

    def _prompt_continue(self) -> bool:
        """
        Asks user if they want to perform another operation.

        This method prompts the user for confirmation to continue with additional tasks.

        Returns:
            bool: True if the user wants to continue; False otherwise.
        """
        return self.ui.prompt_yes_no("Would you like to perform another operation?")

    def _display_supported_types(self):
        """
        Displays types of files supported for cleaning.

        This method informs the user of all file types that can be cleaned by the utility.
        """
        self.ui.print_info("\nSupported file types:")
        for ext, desc in self.SUPPORTED_EXTENSIONS.items():
            self.ui.print_info(f"  {ext} - {desc}")

    def _select_file_types(self) -> bool:
        """
        Handles selection of specific file types for cleaning.

        This method allows the user to choose which file types they wish to include in the cleaning process.

        Returns:
            bool: True if file types are selected successfully; False otherwise.
        """
        self.ui.print_step("Select file types", 3, 3)
        if self.ui.prompt_yes_no("Would you like to clean all supported file types? (*)"):
            self.selected_types = set(self.SUPPORTED_EXTENSIONS.keys())
            self.ui.print_success("Selected all file types")
            return True

        self.ui.print_info("Select specific file types:")
        for ext, desc in self.SUPPORTED_EXTENSIONS.items():
            if self.ui.prompt_yes_no(f"Include {ext} ({desc})?"):
                self.selected_types.add(ext)

        if not self.selected_types:
            self.ui.print_error("No file types selected")
            return False
        return True

    def _get_file_list(self) -> list:
        """
        Gets a list of file paths from user input.

        This method collects file paths specified by the user for cleaning.

        Returns:
            list: A list of file paths entered by the user.
        """
        files = []
        self.ui.print_warning("\nEnter file paths one by one. Press Enter twice when done.")
        
        while True:
            file = input(f"{self.ui.BOLD}Enter file path (or press Enter to finish): {self.ui.END}")
            if not file and files:
                break
            if not file:
                continue
            files.append(file)
        
        return files

    def _setup_assets_and_backup(self) -> bool:
        """
        Sets up asset directory and backup configuration.

        This method configures the directory for cleaned assets and prompts for backup options.

        Returns:
            bool: True if asset setup is successful; False otherwise.
        """
        self.assets_dir = self.get_assets_directory(self.source_path)
        self.should_backup = self.ui.prompt_yes_no("Create backup of modified files?")
        
        if self.should_backup:
            self.create_backup_directory()
            self.setup_logging()
            self.ui.print_info("\nBackup Configuration:")
            self.ui.print_info(f"Assets Directory: {self.assets_dir}")
            self.ui.print_info(f"Backup Location: {self.current_backup_dir}")
        
        return True

    def get_assets_directory(self, source_path: Union[str, List[str]]) -> Path:
        """
        Determines the appropriate location for the 'lc-cleaned-assets' directory based on the specified source path.

        This method identifies the most logical directory structure for storing cleaned assets. If cleaning specific files,
        it finds the common parent directory. If cleaning a directory, it uses that directory directly.

        Args:
            source_path (Union[str, List[str]]): The path to the source file(s) or directory being cleaned.

        Returns:
            Path: A Path object pointing to the determined assets directory.
        """
        if isinstance(source_path, list):
            paths = [Path(p).resolve() for p in source_path]
            common_parent = os.path.commonpath([str(p.parent) for p in paths])
            base_dir = Path(common_parent)
        else:
            base_dir = Path(source_path).resolve()
            
        return base_dir / self.ASSETS_DIR_NAME
    
    def create_backup_directory(self) -> None:
        """
        Creates a timestamped backup directory under the 'lc-cleaned-assets' directory.

        This method ensures that backups of original files are stored in an organized manner, allowing for easy retrieval
        in case the user needs to restore the original files. The directory is created with a unique timestamp to avoid conflicts.
        """
        if not self.assets_dir:
            raise RuntimeError("Assets directory not initialized")
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.assets_dir / 'backups'
        self.current_backup_dir = backup_dir / f'backup_{timestamp}'
        self.current_backup_dir.mkdir(parents=True, exist_ok=True)
    
    def setup_logging(self) -> None:
        """
        Configures the logging settings for the LogCleaner class.

        This method establishes a logging system to track the application's operations, including session starts, file processing,
        and any errors encountered. The logs are saved in a dedicated directory within the assets directory, allowing for
        easy access and review.

        Raises:
            RuntimeError: If the assets directory is not initialized.
        """
        if not self.assets_dir:
            raise RuntimeError("Assets directory not initialized")
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        logs_dir = self.assets_dir / 'logs'
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = logs_dir / f'cleanup_log_{timestamp}.log'

        file_handler = logging.FileHandler(str(self.log_file))

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        
        self.logger.info(f"Started new cleanup session. Log file: {self.log_file}")
    
    def validate_file_type(self, file_path: Union[str, Path]) -> bool:
        """
        Checks if the specified file has a supported extension.

        This method evaluates the file's extension against a predefined list of supported types. It is used to ensure that only
        files compatible with the cleaning process are processed.

        Args:
            file_path (Union[str, Path]): The path to the file to be checked.

        Returns:
            bool: True if the file type is supported; False otherwise.
        """
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS
    
        
    def validate_files(self, files: List[str]) -> tuple[List[str], List[str]]:
        """
        Validates a list of file paths, categorizing them into valid and invalid files.

        This method checks each file's existence and type, providing feedback to the user on any files that cannot be processed.

        Args:
            files (List[str]): A list of file paths to validate.

        Returns:
            tuple: A tuple containing two lists: valid_files and invalid_files.
        """
        valid_files = []
        invalid_files = []
        
        for file in files:
            path = Path(file)
            if not path.is_file():
                invalid_files.append(f"{file} (not a file)")
            elif not self.validate_file_type(file):
                invalid_files.append(f"{file} (unsupported type)")
            else:
                valid_files.append(str(path.resolve()))
                
        return valid_files, invalid_files
    
    def should_backup_file(self, file_path: Path) -> bool:
        """
        Determines if a given file should be backed up based on its location relative to the assets directory.

        This method checks if the provided file path lies within the assets directory. Files outside this directory are eligible
        for backup to prevent redundant backups of already cleaned files.

        Args:
            file_path (Path): The path to the file being considered for backup.

        Returns:
            bool: True if the file should be backed up; False otherwise.
        """
        if not self.assets_dir:
            return True
            
        try:
            file_path.relative_to(self.assets_dir)
            return False 
        except ValueError:
            return True  
    
    def process_files(self):
        """
        Initiates the file processing based on the selected source type (specific files or directory).

        This method handles the logic for processing files based on whether the user selected specific files or a directory,
        delegating the actual processing to the appropriate method.
        """
        try:
            if isinstance(self.source_path, list):
                for file_path in self.source_path:
                    self.remove_logging_statements(file_path)
            else:
                self.process_directory(self.source_path)
        except KeyboardInterrupt:
            self.cleanup()
        except Exception as e:
            self.ui.print_error(f"Error during processing: {str(e)}")
            self.cleanup()

    def process_directory(self, directory: str):
        """
        Recursively processes all files within a specified directory.

        This method traverses the directory structure, applying the cleaning process only to files with supported extensions.
        It skips any files that are located within the assets directory to prevent modifications to cleaned files.

        Args:
            directory (str): The path to the directory to process.
        """
        spinner = self.ui.spinner("Processing files")
        
        for root, _, files in os.walk(directory):
            if self.assets_dir and Path(root).is_relative_to(self.assets_dir):
                continue
                
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in self.selected_types:
                    spinner()
                    self.remove_logging_statements(str(file_path))
                    sys.stdout.write('\r' + self.ui.CLEAR_LINE)

    def remove_logging_statements(self, file_path: str):
        """
        Removes logging statements from the specified file and tracks the removed lines.

        This method reads the contents of the file, identifies lines containing logging statements, and removes them. It also
        logs the removals and updates the statistics regarding processed files and removed lines.

        Args:
            file_path (str): The path to the file from which logging statements should be removed.
        """
        try:
            file_type = os.path.splitext(file_path)[1]
            
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            removed_lines = []
            cleaned_lines = []
            file_modified = False
            
            for line_num, line in enumerate(lines, 1):
                if self.should_remove_line(line, file_type):
                    statement_type = self.get_statement_type(line, file_type)
                    self.stats['removed_statements'][statement_type] = \
                        self.stats['removed_statements'].get(statement_type, 0) + 1
                    removed_lines.append((line_num, line.strip()))
                    self.stats['lines_removed'] += 1
                    file_modified = True

                    if hasattr(self, 'logger'):
                        self.logger.info(f"Removed {statement_type} from {file_path} at line {line_num}: {line.strip()}")
                else:
                    cleaned_lines.append(line)

            if file_modified:
                if self.should_backup:
                    backup_path = self.make_backup(file_path)
                    if hasattr(self, 'logger'):
                        self.logger.info(f"Created backup at: {backup_path}")
                
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.writelines(cleaned_lines)
                
                self.stats['files_processed'] += 1
                self.stats['file_types_processed'][file_type] = \
                    self.stats['file_types_processed'].get(file_type, 0) + 1
                
                if isinstance(self.source_path, list):
                    base_dir = os.path.dirname(self.source_path[0])
                else:
                    base_dir = self.source_path
                    
                rel_path = os.path.relpath(file_path, start=base_dir)
                self.ui.print_success(f"Cleaned: {rel_path} ({len(removed_lines)} lines removed)")
                
        except Exception as e:
            error_msg = f"Error processing {file_path}: {str(e)}"
            self.ui.print_error(error_msg)
            if hasattr(self, 'logger'):
                self.logger.error(error_msg)

    def should_remove_line(self, line: str, file_type: str) -> bool:
        """
        Determines if a specific line should be removed based on its content and file type.

        This method evaluates the line against predefined patterns for JavaScript and Python logging statements to decide
        whether it should be removed during the cleaning process.

        Args:
            line (str): The line of code to evaluate.
            file_type (str): The type of the file (e.g., '.js', '.py').

        Returns:
            bool: True if the line should be removed; False otherwise.
        """
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith('#'):
            return False
        
        if file_type in ['.js', '.jsx', '.ts', '.tsx']:
            return bool(self.compiled_console_pattern.search(line))
        elif file_type in ['.py']:
            return any(pattern.search(line) for pattern in self.compiled_python_patterns)
        return False

    def get_statement_type(self, line: str, file_type: str) -> str:
        """
        Identifies the type of logging statement present in a given line of code.

        This method analyzes the line's content and returns a string representing the type of logging statement,
        facilitating the tracking of removed statements in the statistics.

        Args:
            line (str): The line of code to analyze.
            file_type (str): The type of the file (e.g., '.js', '.py').

        Returns:
            str: A string indicating the type of logging statement (e.g., 'console.log', 'logging.info').
        """
        if file_type in ['.js', '.jsx', '.ts', '.tsx']:
            match = re.search(r'console\.(\w+)', line)
            if match:
                return f"console.{match.group(1)}"
        elif file_type in ['.py']:
            if 'import logging' in line:
                return 'logging_import'
            elif 'getLogger' in line:
                return 'logger_definition'
            elif '_logger.' in line or 'logger.' in line:
                match = re.search(r'_?logger\.(\w+)', line)
                return f"logger.{match.group(1)}" if match else 'logger_statement'
            elif 'logging.' in line:
                match = re.search(r'logging\.(\w+)', line)
                return f"logging.{match.group(1)}" if match else 'logging_statement'
        return 'unknown'
    
    def make_backup(self, file_path: Union[str, Path]) -> Optional[Path]:
        """
        Creates a backup of the original file while maintaining its relative directory structure.

        This method ensures that backups are made before any modifications occur, allowing users to restore their original files
        if needed. It skips backing up files located within the assets directory.

        Args:
            file_path (Union[str, Path]): The path to the file being backed up.

        Returns:
            Optional[Path]: The path to the backup file if backup is enabled; None otherwise.
        """
        if not self.should_backup or not self.current_backup_dir:
            return None
            
        file_path = Path(file_path).resolve()
        
        if not self.should_backup_file(file_path):
            return None
            
        if isinstance(self.source_path, list):
            source_base = Path(os.path.commonpath([str(Path(p).parent) for p in self.source_path]))
        else:
            source_base = Path(self.source_path)
        
        try:
            rel_path = file_path.relative_to(source_base)
        except ValueError:
            rel_path = Path(file_path.name)
            
        backup_path = self.current_backup_dir / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(str(file_path), str(backup_path))
        
        if hasattr(self, 'logger'):
            self.logger.info(f"Created backup: {backup_path}")
            
        return backup_path
    
    def print_summary(self):
        """
        Outputs a summary of the cleanup session, including details such as the number of files processed, lines removed,
        and types of statements removed.

        This method provides users with a comprehensive overview of the operations performed during the session,
        including asset locations and backup details if applicable.
        """
        summary = f"""
{self.ui.CYAN}╔══════════════════════════════════════════╗
║  {self.ui.BOLD}{self.ui.WHITE}Cleanup Summary{self.ui.END}{self.ui.CYAN}                        ║
╚══════════════════════════════════════════╝{self.ui.END}

{self.ui.BOLD}{self.ui.BLUE}Operation Details:{self.ui.END}
{self.ui.CYAN}• Mode:{self.ui.END} {'Directory scan' if isinstance(self.source_path, str) else 'Specific files'}
{self.ui.CYAN}• Location:{self.ui.END} {self.source_path if isinstance(self.source_path, str) else 'Multiple files'}
{self.ui.CYAN}• File Types:{self.ui.END} {', '.join(sorted(self.selected_types))}

{self.ui.BOLD}{self.ui.BLUE}Statistics:{self.ui.END}
{self.ui.CYAN}• Files Processed:{self.ui.END} {self.stats['files_processed']}
{self.ui.CYAN}• Lines Removed:{self.ui.END} {self.stats['lines_removed']}

{self.ui.BOLD}{self.ui.BLUE}Files processed by type:{self.ui.END}"""

        for file_type, count in self.stats['file_types_processed'].items():
            summary += f"\n{self.ui.CYAN}• {file_type}:{self.ui.END} {count}"

        summary += f"\n\n{self.ui.BOLD}{self.ui.BLUE}Removed statements by type:{self.ui.END}"
        for statement, count in self.stats['removed_statements'].items():
            summary += f"\n{self.ui.CYAN}• {statement}:{self.ui.END} {count}"

        if self.should_backup:
            summary += f"\n\n{self.ui.BOLD}{self.ui.BLUE}Asset Locations:{self.ui.END}"
            summary += f"\n{self.ui.CYAN}• Assets Directory:{self.ui.END} {self.assets_dir}"
            summary += f"\n{self.ui.CYAN}• Backup Location:{self.ui.END} {self.current_backup_dir}"
            summary += f"\n{self.ui.CYAN}• Log File:{self.ui.END} {getattr(self, 'log_file', 'Not configured')}"

        print(summary)
    
    def cleanup(self):
        """
        Performs necessary cleanup operations before the application exits.

        This method is responsible for closing any logging handlers, clearing the user interface, and printing a final message
        to inform the user that the cleanup session has ended.
        """
        try:
            if hasattr(self, 'logger'):
                self.logger.info("Cleanup session terminated by user")
                for handler in self.logger.handlers[:]:
                    handler.close()
                    self.logger.removeHandler(handler)
            
            self.ui.clear_line()
            
            self.ui.print_warning("Cleanup session ended.")
            
        except Exception as e:
            self.ui.print_error(f"Error during cleanup: {str(e)}")
        