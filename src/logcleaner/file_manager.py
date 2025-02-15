import os
from pathlib import Path
from datetime import datetime
from typing import List
from crontab import CronTab
import re

class LogFileManager:
    """
    Manages log file operations and automated cleaning schedules.

    Features:
        - Identifies and validates log files
        - Discovers log files recursively
        - Cleans entries by date
        - Manages cron jobs for automation

    Attributes:
        datetime_patterns (List[Tuple[str, str]]): Regex patterns for log timestamps
        log_extensions (Set[str]): Recognized log file extensions
        log_patterns (List[str]): Patterns for log file identification
        job_comment_base (str): Base identifier for cron jobs
        user_cron (CronTab): User's crontab interface
        ui (ConsoleUI): User interaction interface

    Example:
        manager = LogFileManager(ui_instance)
        log_files = manager.get_log_files("/path/to/logs")
        cleaned, lines = manager.clean_logs_before_date(log_files, cutoff_date)
        if manager.setup_cron_job(script_path, log_dir, hour=2, minute=30):
            print("Automated cleaning scheduled")
    """
        
    def __init__(self, ui):
        """
        Initializes the LogFileManager.

        Args:
            ui (ConsoleUI): Interface for user interaction and feedback.

        Sets up:
            - User's crontab for automation management.
            - Base identifier for cron jobs.
            - Common datetime patterns for log timestamps.
            - Recognized log file extensions and patterns for validation.
        """
        self.ui = ui
        self.user_cron = CronTab(user=True)
        self.job_comment_base = "log-cleaner-automated"
        
        self.datetime_patterns = [
            (r'(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),
            (r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', '%Y-%m-%d %H:%M:%S'),
            (r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', '%Y-%m-%dT%H:%M:%S'),
            (r'(\d{2}/\d{2}/\d{4})', '%m/%d/%Y'),
            (r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+\-]\d{2}:\d{2})', '%Y-%m-%dT%H:%M:%S%z'),
            (r'([A-Za-z]{3} \d{2} \d{2}:\d{2}:\d{2} \d{4})', '%b %d %H:%M:%S %Y'),
            (r'(\d{10})', '%s'),
            (r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)', '%Y-%m-%dT%H:%M:%S.%fZ'),
            (r'([A-Za-z]{3} [A-Za-z]{3} \d{2} \d{2}:\d{2}:\d{2} \d{4})', '%a %b %d %H:%M:%S %Y'),
            (r'(\d{8})', '%Y%m%d'),
        ]
        
        self.log_extensions = {'.log', '.logs', '.error', '.debug', '.info'}
        self.log_patterns = [
            r'\.log(\.\d+)?$',  # matches .log, .log.1, .log.2, etc.
            r'\.logs$',
            r'\.(error|debug|info)$',
            r'\.log\.[0-9A-Za-z-]+$'  # matches .log.old, .log.backup, etc.
        ]
    
    def is_log_file(self, file_path: str | Path) -> bool:
        """
        Determine if a file is a valid log file through multiple validation methods.

        This method employs a multi-step validation process to identify log files:
        1. Extension check against common log file extensions
        2. Pattern matching against known log file naming conventions
        3. Content analysis for timestamp patterns

        The validation process:
        - First validates file existence and accessibility
        - Checks file extension against known log extensions
        - Matches filename against common log file patterns
        - If previous checks fail, examines file content for log-like structures
        - Handles various file encoding and access issues gracefully

        Args:
            file_path (Union[str, Path]): Path to the file to be checked

        Returns:
            bool: True if the file is determined to be a log file, False otherwise

        Note:
            The method uses a conservative approach, treating files as non-log files
            if they cannot be safely read or don't match any known patterns.
            It handles various error conditions silently, returning False rather
            than raising exceptions.
        """
        try:
            path = Path(file_path)
            
            if not path.is_file():
                return False
                
            if path.suffix.lower() in self.log_extensions:
                return True
                
            file_name = path.name.lower()
            if any(re.search(pattern, file_name) for pattern in self.log_patterns):
                return True
                
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = []
                    for _ in range(5):
                        try:
                            line = next(f)
                            lines.append(line.strip())
                        except StopIteration:
                            break

                for line in lines:
                    for pattern, _ in self.datetime_patterns:
                        if re.search(pattern, line):
                            return True
                            
            except (UnicodeDecodeError, IOError):
                return False
                
            return False
            
        except Exception as e:
            self.ui.print_error(f"Error checking file {file_path}: {str(e)}")
            return False
    
    def get_log_files(self, directory: str | Path) -> List[Path]:
        """
        Recursively discover all log files in a directory while respecting exclusions.

        This method performs a comprehensive directory scan to find log files. It:
        - Traverses the directory structure recursively
        - Applies intelligent filtering to exclude system directories
        - Validates each file against log file criteria
        - Builds a collection of valid log file paths

        Special handling:
        - Skips .git directories for performance
        - Prevents traversal into excluded directories

        Args:
            directory (Union[str, Path]): Root directory to start the search from

        Returns:
            List[Path]: List of Path objects representing discovered log files

        Note:
            Optimized to handle large directory structures by pruning unnecessary paths early.
        """
        directory_path = Path(directory)
        log_files = []
        for root, dirs, files in os.walk(directory_path):
            if '.git' in dirs:
                dirs.remove('.git')  
                
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                if '.git' not in str(file_path) and self.is_log_file(file_path):
                    log_files.append(file_path)
        return log_files

    def clean_logs_before_date(self, log_files: List[Path], cutoff_date: datetime) -> int:
        """
        Clean log files by removing entries older than a specified date.

        This method processes each log file to remove outdated entries while:
        - Preserving file structure and empty lines
        - Maintaining file encoding
        - Only modifying files when necessary
        - Tracking cleaning statistics

        Args:
            log_files (List[Path]): List of log files to process
            cutoff_date (datetime): Date before which entries should be removed

        Returns:
            tuple[int, int]: A tuple containing:
                - Number of files that were cleaned
                - Total number of lines removed across all files

        Note:
            Continues processing even if errors occur with individual files.
        """
        files_cleaned = 0
        total_lines_removed = 0
        
        for log_file in log_files:
            try:
                self.ui.print_info(f"Processing {log_file}")
                modified = False
                lines_removed = 0
                
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                new_lines = []
                
                for line in lines:
                    if not line.strip(): 
                        new_lines.append(line)
                        continue
                        
                    log_date = self.extract_date(line)
                    
                    if log_date is None: 
                        new_lines.append(line)
                    elif log_date >= cutoff_date: 
                        new_lines.append(line)
                    else: 
                        lines_removed += 1
                        modified = True
      
                if modified:
                    with open(log_file, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    files_cleaned += 1
                    total_lines_removed += lines_removed
                    self.ui.print_success(f"Cleaned {log_file.name} - removed {lines_removed} lines")
                else:
                    self.ui.print_info(f"No cleaning needed for {log_file.name}")
                    
            except Exception as e:
                self.ui.print_error(f"Error cleaning {log_file}: {str(e)}")
                continue
                
        return files_cleaned, total_lines_removed

    def extract_date(self, line: str) -> datetime:
        """
        Extract and parse a datetime from a log line using multiple format patterns.

        This method attempts to identify and parse dates in log lines by:
        - Trying multiple common datetime patterns
        - Converting matched strings to datetime objects

        Args:
            line (str): A line of text from a log file

        Returns:
            Optional[datetime]: Datetime object if a valid date was found, None otherwise

        Note:
            Tries patterns in defined order; continues searching even if a pattern fails.
        """
        for pattern, date_format in self.datetime_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    return datetime.strptime(match.group(1), date_format)
                except ValueError:
                    continue
        return None

    def setup_cron_job(self, cleanup_script_path: str | Path, log_dir: str | Path, hour: int = 0, minute: int = 0) -> bool:
        """
        Set up a new automated log cleaning cron job with a unique identifier.

        This method creates a new cron job for automated log cleaning with a timestamp-based unique identifier.
        The job is configured to run at the specified time daily. Each job is created with a unique comment
        that includes a timestamp, allowing for multiple automated cleaning schedules to coexist.

        Args:
            cleanup_script_path (Union[str, Path]): Path to the cleanup script that will be executed
            log_dir (Union[str, Path]): Directory containing the log files to be cleaned
            hour (int, optional): Hour of the day to run the job (0-23). Defaults to 0
            minute (int, optional): Minute of the hour to run the job (0-59). Defaults to 0

        Returns:
            bool: True if the cron job was successfully created and scheduled, False otherwise

        Raises:
            Exception: If there's an error creating or scheduling the cron job
        """
        try:
            script_path = Path(cleanup_script_path)
            log_dir_path = Path(log_dir)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            job_comment = f"{self.job_comment_base}_{timestamp}"
            
            cmd = f'python3 {script_path} --clean-logs "{log_dir_path}"'
            job = self.user_cron.new(command=cmd, comment=job_comment)
            
            job.setall(f'{minute} {hour} * * *')
            
            self.user_cron.write()
            return True
            
        except Exception as e:
            self.ui.print_error(f"Error setting up cron job: {str(e)}")
            return False
        
    def get_cron_jobs(self):
        """
        Retrieve all log cleaner cron jobs currently scheduled.

        This method searches through the user's crontab and yields all jobs that were created
        by the log cleaner application. It identifies these jobs by checking if their comment
        starts with the base identifier used for log cleaner jobs.

        The method uses a generator to efficiently iterate through cron jobs without loading
        all of them into memory at once.

        Returns:
            Generator[CronJob]: A generator yielding CronJob objects for all log cleaner jobs

        Note:
            The jobs are identified by their comment field starting with the log cleaner's
            base identifier, allowing for tracking of multiple cleaning schedules.
        """
        return (job for job in self.user_cron if job.comment.startswith(self.job_comment_base))

    def remove_specific_cron_job(self, job) -> bool:
        """
        Remove a specific automated log cleaning job from the crontab.

        This method removes a single specified cron job from the user's crontab. It is typically
        used when managing multiple automated cleaning schedules and the user wants to remove
        just one specific schedule.

        Args:
            job (CronJob): The specific cron job object to be removed

        Returns:
            bool: True if the job was successfully removed, False if there was an error

        Raises:
            Exception: If there's an error accessing or modifying the crontab
        """
        try:
            self.user_cron.remove(job)
            self.user_cron.write()
            return True
        except Exception as e:
            self.ui.print_error(f"Error removing cron job: {str(e)}")
            return False
            
    def remove_cron_job(self) -> bool:
        """
        Remove all automated log cleaning jobs from the crontab.

        This method searches through the user's crontab and removes all jobs created by the log cleaner application.

        Returns:
            bool: True if all jobs were successfully removed, False if there was an error

        Raises:
            Exception: If there's an error accessing or modifying the crontab
        """
        try:
            for job in self.user_cron:
                if job.comment.startswith(self.job_comment_base):
                    self.user_cron.remove(job)
            self.user_cron.write()
            return True
        except Exception as e:
            self.ui.print_error(f"Error removing cron jobs: {str(e)}")
            return False
            
    def has_cron_job(self) -> bool:
        """
        Check if any automated log cleaning jobs exist in the crontab.

        This method determines if any log cleaner jobs are currently scheduled.

        Returns:
            bool: True if at least one log cleaner job exists, False otherwise
        """
        return any(job.comment.startswith(self.job_comment_base) for job in self.user_cron)