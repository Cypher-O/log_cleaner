from unittest.mock import Mock
import pytest
import os
import shutil
import tempfile
from pathlib import Path
from src.logcleaner import LogCleaner

class TestLogCleaner:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def cleaner(self):
        """Create a LogCleaner instance."""
        cleaner = LogCleaner()
        yield cleaner

    @pytest.fixture
    def sample_files(self, temp_dir):
        """Create sample files for testing."""
        # JavaScript file with console statements
        js_content = """
        console.log('test');
        function test() {
            console.error('error');
            return true;
        }
        console.warn('warning');
        """
        js_file = Path(temp_dir) / "test.js"
        js_file.write_text(js_content)

        # Python file with logging statements
        py_content = """
        import logging
        logger = logging.getLogger(__name__)
        def test():
            logger.info('test')
            logging.error('error')
            return True
        """
        py_file = Path(temp_dir) / "test.py"
        py_file.write_text(py_content)

        return {"js": js_file, "py": py_file}

    def test_initialization(self, cleaner):
        """Test LogCleaner initialization."""
        assert hasattr(cleaner, 'ui')
        assert hasattr(cleaner, 'console_methods')
        assert hasattr(cleaner, 'python_patterns')
        assert hasattr(cleaner, 'stats')

    def test_should_remove_line_python(self, cleaner):
        """Test Python logging statement detection."""
        assert cleaner.should_remove_line('import logging', '.py')
        assert cleaner.should_remove_line('logger.info("test")', '.py')
        assert cleaner.should_remove_line('logging.error("test")', '.py')
        assert not cleaner.should_remove_line('# logging.info("test")', '.py')  # Commented code
        assert not cleaner.should_remove_line('my_logger("test")', '.py')  # Not a logging statement

    def test_get_statement_type(self, cleaner):
        """Test statement type detection."""
        assert cleaner.get_statement_type('console.log("test");', '.js') == 'console.log'
        assert cleaner.get_statement_type('logger.info("test")', '.py') == 'logger.info'
        assert cleaner.get_statement_type('import logging', '.py') == 'logging_import'

    @pytest.mark.integration
    def test_process_files_js(self, cleaner, sample_files, temp_dir):
        """Test processing of JavaScript files."""
        # Setup
        cleaner.source_path = str(temp_dir)
        cleaner.selected_types = ['.js']
        
        # Process files
        cleaner.process_files()
        
        # Verify
        with open(sample_files['js']) as f:
            content = f.read()
            assert 'console.log' not in content
            assert 'console.error' not in content
            assert 'console.warn' not in content
            assert 'function test()' in content
            assert 'return true;' in content

    @pytest.mark.integration
    def test_process_files_python(self, cleaner, sample_files, temp_dir):
        """Test processing of Python files."""
        # Setup
        cleaner.source_path = str(temp_dir)
        cleaner.selected_types = ['.py']
        
        # Process files
        cleaner.process_files()
        
        # Verify
        with open(sample_files['py']) as f:
            content = f.read()
            assert 'import logging' not in content
            assert 'logger.info' not in content
            assert 'logging.error' not in content
            assert 'def test():' in content
            assert 'return True' in content

    @pytest.mark.integration
    def test_backup_creation(self, cleaner, sample_files, temp_dir):
        """Test backup functionality."""
        # Setup
        cleaner.should_backup = True
        cleaner.source_path = str(temp_dir)
        cleaner.selected_types = ['.js', '.py']
        
        # Initialize assets directory before creating backup directory
        cleaner.assets_dir = cleaner.get_assets_directory(cleaner.source_path)
        cleaner.create_backup_directory()
        
        # Process files
        cleaner.process_files()
        
        # Verify backup directory and files
        assert os.path.exists(cleaner.current_backup_dir)
        backup_files = list(Path(cleaner.current_backup_dir).glob('**/*'))
        backup_files = [f for f in backup_files if f.is_file()]
        assert len(backup_files) >= 2  # At least original JS and PY files

    def test_initialize_session_complete(self, cleaner, monkeypatch):
        """Test complete initialization session flow."""
        # Mock all UI interactions
        mock_responses = {
            'prompt_choice': [1, 1],  # First for cleaning mode, second for source selection
            'prompt_yes_no': [True, True],  # For file types and backup
            'prompt_input': ['.']  # Directory path
        }
        
        def mock_choice(*args, **kwargs):
            return mock_responses['prompt_choice'].pop(0)
            
        def mock_yes_no(*args, **kwargs):
            return mock_responses['prompt_yes_no'].pop(0)
            
        def mock_input(*args, **kwargs):
            return mock_responses['prompt_input'].pop(0)
        
        monkeypatch.setattr(cleaner.ui, 'prompt_choice', mock_choice)
        monkeypatch.setattr(cleaner.ui, 'prompt_yes_no', mock_yes_no)
        monkeypatch.setattr('builtins.input', mock_input)
        
        assert cleaner.initialize_session() is True

    @pytest.mark.parametrize("file_content,file_type,expected_removals", [
        ("console.log('test');\nvalid code;\nconsole.error('test');", '.js', 2),
        ("import logging\nvalid code\nlogger.info('test')", '.py', 2),
    ])
    def test_removal_counting(self, cleaner, temp_dir, file_content, file_type, expected_removals):
        """Test counting of removed statements."""
        # Setup
        test_file = Path(temp_dir) / f"test{file_type}"
        test_file.write_text(file_content)
        
        cleaner.source_path = [str(test_file)]
        cleaner.selected_types = [file_type]
        
        # Process
        cleaner.process_files()
        
        # Verify
        assert cleaner.stats['lines_removed'] == expected_removals
        
    def test_validate_file_type(self, cleaner):
        """Test file type validation."""
        valid_files = [
            'test.js', 'test.jsx', 'test.ts', 'test.tsx', 'test.py',
            '/path/to/test.js', 'C:\\path\\to\\test.py'
        ]
        invalid_files = [
            'test.txt', 'test.css', 'test.html', 'test',
            '/path/to/test.txt', 'C:\\path\\to\\test.doc'
        ]
        
        for file in valid_files:
            assert cleaner.validate_file_type(file) is True
            
        for file in invalid_files:
            assert cleaner.validate_file_type(file) is False

    def test_should_backup_file(self, cleaner, tmp_path):
        """Test backup decision logic."""
        # Setup test paths
        cleaner.assets_dir = tmp_path / "lc-cleaned-assets"
        cleaner.assets_dir.mkdir()
        
        test_file = tmp_path / "test.js"
        test_file.touch()
        
        asset_file = cleaner.assets_dir / "asset.js"
        asset_file.touch()
        
        # Test files outside assets directory
        assert cleaner.should_backup_file(test_file) is True
        
        # Test files inside assets directory
        assert cleaner.should_backup_file(asset_file) is False
        
        # Test when assets_dir is not set
        cleaner.assets_dir = None
        assert cleaner.should_backup_file(test_file) is True

    def test_get_statement_type_js(self, cleaner):
        """Test JavaScript statement type detection."""
        test_cases = [
            ('console.log("test");', '.js', 'console.log'),
            ('console.error("test");', '.js', 'console.error'),
            ('console.warn("test");', '.js', 'console.warn'),
            ('console.debug("test");', '.js', 'console.debug'),
            ('not a console statement', '.js', 'unknown'),
        ]
        
        for line, file_type, expected in test_cases:
            assert cleaner.get_statement_type(line, file_type) == expected

    def test_get_statement_type_python(self, cleaner):
        """Test Python statement type detection."""
        test_cases = [
            ('import logging', '.py', 'logging_import'),
            ('logger = logging.getLogger(__name__)', '.py', 'logger_definition'),
            ('logger.info("test")', '.py', 'logger.info'),
            ('logging.error("test")', '.py', 'logging.error'),
            ('_logger.debug("test")', '.py', 'logger.debug'),
            ('not a logging statement', '.py', 'unknown'),
        ]
        
        for line, file_type, expected in test_cases:
            assert cleaner.get_statement_type(line, file_type) == expected

    def test_get_assets_directory(self, cleaner, tmp_path):
        """Test assets directory path generation."""
        # Test with single directory
        dir_path = tmp_path / "source"
        dir_path.mkdir()
        result = cleaner.get_assets_directory(str(dir_path))
        assert result == dir_path / cleaner.ASSETS_DIR_NAME
        
        # Test with multiple files
        file1 = tmp_path / "dir1" / "test1.js"
        file2 = tmp_path / "dir1" / "test2.js"
        file1.parent.mkdir(parents=True)
        file1.touch()
        file2.touch()
        
        result = cleaner.get_assets_directory([str(file1), str(file2)])
        assert result == file1.parent / cleaner.ASSETS_DIR_NAME
        
    def test_setup_automation(self, cleaner, monkeypatch):
        """Test automation setup."""
        mock_responses = {
            'prompt_input': ["2", "30"]  # Hour and minute
        }
        
        def mock_input(*args, **kwargs):
            return mock_responses['prompt_input'].pop(0)
        
        monkeypatch.setattr(cleaner.ui, 'prompt_input', mock_input)
        
        assert cleaner._setup_automation("/test/dir") is True
        
    def test_handle_file_mode(self, cleaner, tmp_path, monkeypatch):
        """Test file mode handling."""
        # Create test files
        js_file = tmp_path / "test.js"
        py_file = tmp_path / "test.py"
        js_file.write_text("console.log('test');")
        py_file.write_text("print('test')")
        
        # Mock file list input
        mock_files = [str(js_file), str(py_file), ""]
        
        def mock_input(*args, **kwargs):
            return mock_files.pop(0) if mock_files else ""
        
        monkeypatch.setattr('builtins.input', mock_input)
        
        assert cleaner._handle_file_mode() is True
        assert len(cleaner.source_path) == 2
        assert cleaner.selected_types == {'.js', '.py'}
        
    def test_handle_directory_mode(self, cleaner, tmp_path, monkeypatch):
        """Test directory mode handling."""
        # Mock UI interactions
        mock_responses = {
            'prompt_yes_no': [True],  # All file types
            'prompt_input': [str(tmp_path)]  # Directory path
        }
        
        def mock_yes_no(*args, **kwargs):
            return mock_responses['prompt_yes_no'].pop(0)
            
        def mock_input(*args, **kwargs):
            return mock_responses['prompt_input'].pop(0)
        
        monkeypatch.setattr(cleaner.ui, 'prompt_yes_no', mock_yes_no)
        monkeypatch.setattr('builtins.input', mock_input)
        
        assert cleaner._handle_directory_mode() is True
        assert cleaner.source_path == str(tmp_path.resolve())
        
    def test_setup_code_cleaning(self, cleaner, monkeypatch):
        """Test code cleaning setup flow."""
        # Mock UI interactions
        mock_responses = {
            'prompt_choice': [1],  # Choose directory mode
            'prompt_yes_no': [True, False],  # All file types, no backup
            'prompt_input': ['.']  # Current directory
        }
        
        def mock_choice(*args, **kwargs):
            return mock_responses['prompt_choice'].pop(0)
            
        def mock_yes_no(*args, **kwargs):
            return mock_responses['prompt_yes_no'].pop(0)
            
        def mock_input(*args, **kwargs):
            return mock_responses['prompt_input'].pop(0)
        
        monkeypatch.setattr(cleaner.ui, 'prompt_choice', mock_choice)
        monkeypatch.setattr(cleaner.ui, 'prompt_yes_no', mock_yes_no)
        monkeypatch.setattr('builtins.input', mock_input)
        
        assert cleaner._setup_code_cleaning() is True

    def test_setup_log_cleaning(self, cleaner, tmp_path, monkeypatch):
        """Test log cleaning setup flow."""
        # Create test log file
        log_file = tmp_path / "test.log"
        log_file.write_text("2024-02-15 Test log")
        
        # Mock UI interactions
        mock_responses = {
            'prompt_choice': [2],  # Choose specify directory
            'prompt_yes_no': [True, False],  # Proceed with cleaning, no automation
            'prompt_input': [str(tmp_path), "7"]  # Directory path, retention days
        }
        
        def mock_choice(*args, **kwargs):
            return mock_responses['prompt_choice'].pop(0)
            
        def mock_yes_no(*args, **kwargs):
            return mock_responses['prompt_yes_no'].pop(0)
            
        def mock_input(*args, **kwargs):
            return mock_responses['prompt_input'].pop(0)
        
        monkeypatch.setattr(cleaner.ui, 'prompt_choice', mock_choice)
        monkeypatch.setattr(cleaner.ui, 'prompt_yes_no', mock_yes_no)
        monkeypatch.setattr('builtins.input', mock_input)
        
        assert cleaner._setup_log_cleaning() is True

    def test_handle_automation_management(self, cleaner, monkeypatch):
        """Test automation management flow."""
        # Mock cron jobs
        mock_job = Mock()
        mock_job.slices.render.return_value = "0 0 * * *"
        mock_job.command = 'python3 "test/dir" --clean-logs'
        
        cleaner.log_manager.get_cron_jobs = Mock(return_value=[mock_job])
        
        # Mock UI interactions
        mock_responses = {
            'prompt_choice': [1, 1],  # First for "Remove specific schedule", second for main menu return
            'prompt_input': ["1"],  # Select first job
        }
        
        def mock_choice(*args, **kwargs):
            return mock_responses['prompt_choice'].pop(0)
            
        def mock_input(*args, **kwargs):
            return mock_responses['prompt_input'].pop(0)
        
        monkeypatch.setattr(cleaner.ui, 'prompt_choice', mock_choice)
        monkeypatch.setattr(cleaner.ui, 'prompt_input', mock_input)
        
        result = cleaner._handle_automation_management()
        assert isinstance(result, int)
        
if __name__ == '__main__':
    pytest.main(['-v'])