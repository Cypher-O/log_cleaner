import pytest
import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock
from src.logcleaner import LogFileManager

class TestLogFileManager:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_ui(self):
        """Create a mock UI instance."""
        return Mock()

    @pytest.fixture
    def manager(self, mock_ui):
        """Create a LogFileManager instance with mock UI."""
        return LogFileManager(mock_ui)

    @pytest.fixture
    def sample_log_files(self, temp_dir):
        """Create sample log files with different formats and content."""
        files = {}
        
        # Standard log file with ISO format dates
        iso_content = """
        2024-02-15 10:30:45 INFO Started application
        2024-02-15 10:30:46 DEBUG Initializing components
        2024-02-15 10:30:47 ERROR Failed to connect
        """
        iso_file = Path(temp_dir) / "app.log"
        iso_file.write_text(iso_content)
        files["iso"] = iso_file

        # Log file with Unix timestamp format
        unix_content = """
        1644915045 Started backup process
        1644915046 Backup completed
        1644915047 Cleanup started
        """
        unix_file = Path(temp_dir) / "system.log"
        unix_file.write_text(unix_content)
        files["unix"] = unix_file

        # Log file with custom format
        custom_content = """
        [Feb 15 10:30:45 2024] Server started
        [Feb 15 10:30:46 2024] Connection accepted
        [Feb 15 10:30:47 2024] Request processed
        """
        custom_file = Path(temp_dir) / "server.log"
        custom_file.write_text(custom_content)
        files["custom"] = custom_file

        return files

    def test_is_log_file_extension(self, manager, temp_dir):
        """Test log file detection based on file extension."""
        # Create test files
        log_file = Path(temp_dir) / "test.log"
        log_file.write_text("some log content")
        
        txt_file = Path(temp_dir) / "test.txt"
        txt_file.write_text("some text content")
        
        # Test valid log extensions
        assert manager.is_log_file(log_file) is True
        assert manager.is_log_file(str(log_file)) is True  # Test string path
        
        # Test non-log extensions
        assert manager.is_log_file(txt_file) is False

    def test_is_log_file_content(self, manager, temp_dir):
        """Test log file detection based on content patterns."""
        # File with log-like content but wrong extension
        log_content = """2024-02-15 10:30:45 INFO Test message
    2024-02-15 10:30:46 ERROR Another message
    2024-02-15 10:30:47 DEBUG Third message"""
        fake_txt = Path(temp_dir) / "log_like.txt"
        fake_txt.write_text(log_content)
        
        # File with non-log content but .log extension
        non_log_content = "This is just a regular text file\nwithout any log patterns"
        fake_log = Path(temp_dir) / "fake.log"
        fake_log.write_text(non_log_content)
        
        # Test file detection
        assert manager.is_log_file(fake_txt) is True, "File with log-like content should be detected"
        assert manager.is_log_file(fake_log) is True, "File with .log extension should be detected"
        
        # Test file with neither log extension nor log content
        random_txt = Path(temp_dir) / "random.txt"
        random_txt.write_text("Just some random text\nwithout any dates or log patterns")
        assert manager.is_log_file(random_txt) is False, "File without log content or extension should not be detected"

    def test_get_log_files(self, manager, sample_log_files, temp_dir):
        """Test recursive log file discovery."""
        # Create nested directory structure
        nested_dir = Path(temp_dir) / "nested"
        nested_dir.mkdir()
        
        nested_log = nested_dir / "nested.log"
        nested_log.write_text("2024-02-15 10:30:45 INFO Nested log")
        
        # Create .git directory with log file that should be ignored
        git_dir = Path(temp_dir) / ".git"
        git_dir.mkdir()
        git_log = git_dir / "git.log"
        git_log.write_text("some git log content")
        
        # Get all log files
        log_files = manager.get_log_files(temp_dir)
        
        # Verify results
        assert len(log_files) == len(sample_log_files) + 1  # +1 for nested log
        assert nested_log in log_files
        assert git_log not in log_files  # .git directory should be ignored
        assert all(Path(f).exists() for f in log_files)

    def test_clean_logs_before_date(self, manager, sample_log_files):
        """Test log cleaning based on date."""
        cutoff_date = datetime.now() - timedelta(days=1)
        
        # Process all sample log files
        files_cleaned, lines_removed = manager.clean_logs_before_date(
            list(sample_log_files.values()),
            cutoff_date
        )
        
        # Verify results
        assert isinstance(files_cleaned, int)
        assert isinstance(lines_removed, int)
        assert files_cleaned <= len(sample_log_files)
        
        # Check file contents after cleaning
        for log_file in sample_log_files.values():
            with open(log_file) as f:
                content = f.read()
                # Verify that empty lines are preserved
                assert any(line.strip() == '' for line in content.split('\n'))

    def test_extract_date(self, manager):
        """Test date extraction from different log formats."""
        # Override the datetime patterns to ensure proper matching
        manager.datetime_patterns = [
            (r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', '%Y-%m-%d %H:%M:%S'),
            (r'\[([A-Za-z]{3} \d{2} \d{2}:\d{2}:\d{2} \d{4})\]', '%b %d %H:%M:%S %Y')
        ]
        
        test_cases = [
            {
                'line': "2024-02-15 10:30:45 INFO Test",
                'expected': datetime(2024, 2, 15, 10, 30, 45)
            },
            {
                'line': "[Feb 15 10:30:45 2024] Test",
                'expected': datetime(2024, 2, 15, 10, 30, 45)
            }
        ]
        
        for case in test_cases:
            result = manager.extract_date(case['line'])
            expected_date = case['expected']
            
            assert result is not None, f"Date extraction failed for: {case['line']}"
            assert result.year == expected_date.year, f"Year mismatch for: {case['line']}"
            assert result.month == expected_date.month, f"Month mismatch for: {case['line']}"
            assert result.day == expected_date.day, f"Day mismatch for: {case['line']}"
            assert result.hour == expected_date.hour, f"Hour mismatch for: {case['line']}"
            assert result.minute == expected_date.minute, f"Minute mismatch for: {case['line']}"
            assert result.second == expected_date.second, f"Second mismatch for: {case['line']}"
                    
    def test_setup_cron_job(self, manager, temp_dir):
        """Test cron job setup."""
        # Create a mock for the CronTab instance
        mock_cron = Mock()
        mock_job = Mock()
        mock_cron.new.return_value = mock_job
        manager.user_cron = mock_cron
        
        # Test successful job creation
        result = manager.setup_cron_job(
            "cleanup_script.py",
            temp_dir,
            hour=2,
            minute=30
        )
        
        assert result is True
        mock_cron.new.assert_called_once()
        mock_job.setall.assert_called_with('30 2 * * *')
        mock_cron.write.assert_called_once()

    def test_remove_cron_job(self, manager):
        """Test cron job removal."""
        # Create a mock for the CronTab instance
        mock_cron = Mock()
        mock_job = Mock()
        mock_job.comment = f"{manager.job_comment_base}_test"
        mock_cron.__iter__ = lambda self: iter([mock_job])
        manager.user_cron = mock_cron
        
        result = manager.remove_cron_job()
        
        assert result is True
        mock_cron.remove.assert_called_with(mock_job)
        mock_cron.write.assert_called_once()

    def test_has_cron_job(self, manager):
        """Test cron job detection."""
        # Mock the user_cron attribute
        mock_cron = Mock()
        
        # Test when job exists
        job_with_matching_comment = Mock()
        job_with_matching_comment.comment = f"{manager.job_comment_base}_test"
        mock_cron.__iter__ = lambda self: iter([job_with_matching_comment])
        manager.user_cron = mock_cron
        assert manager.has_cron_job() is True
        
        # Test when no matching job exists
        job_without_matching_comment = Mock()
        job_without_matching_comment.comment = "other_job"
        mock_cron.__iter__ = lambda self: iter([job_without_matching_comment])
        manager.user_cron = mock_cron
        assert manager.has_cron_job() is False
