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

    def test_initialize_session(self, cleaner, monkeypatch):
        """Test session initialization."""
        # Setup mock responses
        responses = {
            'prompt_choice': 1,
            'prompt_yes_no': [True, False, False, False, False, True]
        }
        
        def mock_prompt_choice(*args, **kwargs):
            return responses['prompt_choice']
            
        def mock_prompt_yes_no(*args, **kwargs):
            return responses['prompt_yes_no'].pop(0)
            
        monkeypatch.setattr(cleaner.ui, 'prompt_choice', mock_prompt_choice)
        monkeypatch.setattr(cleaner.ui, 'prompt_yes_no', mock_prompt_yes_no)
        monkeypatch.setattr('builtins.input', lambda _: '.')
        
        # Execute
        result = cleaner.initialize_session()
        
        # Verify
        assert result is True
        assert hasattr(cleaner, 'source_path')
        assert hasattr(cleaner, 'selected_types')
        assert hasattr(cleaner, 'should_backup')

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
        
if __name__ == '__main__':
    pytest.main(['-v'])
        
# import pytest
# import os
# import shutil
# import tempfile
# from pathlib import Path

# from src.logcleaner import LogCleaner

# class TestLogCleaner:
#     @pytest.fixture
#     def temp_dir(self):
#         """Create a temporary directory for test files"""
#         temp_dir = tempfile.mkdtemp()
#         yield temp_dir
#         shutil.rmtree(temp_dir)

#     @pytest.fixture
#     def cleaner(self):
#         """Create a LogCleaner instance"""
#         cleaner = LogCleaner()
#         yield cleaner

#     @pytest.fixture
#     def sample_files(self, temp_dir):
#         """Create sample files for testing"""
#         # JavaScript file with console statements
#         js_content = """
#         console.log('test');
#         function test() {
#             console.error('error');
#             return true;
#         }
#         console.warn('warning');
#         """
#         js_file = Path(temp_dir) / "test.js"
#         js_file.write_text(js_content)

#         # Python file with logging statements
#         py_content = """
#         import logging
#         logger = logging.getLogger(__name__)
#         def test():
#             logger.info('test')
#             logging.error('error')
#             return True
#         """
#         py_file = Path(temp_dir) / "test.py"
#         py_file.write_text(py_content)

#         return {"js": js_file, "py": py_file}

#     def test_initialization(self, cleaner):
#         """Test LogCleaner initialization"""
#         assert hasattr(cleaner, 'ui')
#         assert hasattr(cleaner, 'console_methods')
#         assert hasattr(cleaner, 'python_patterns')
#         assert hasattr(cleaner, 'stats')
    
#     def should_remove_line(self, line: str, file_type: str) -> bool:
#         if file_type in ['.js', '.jsx', '.ts', '.tsx']:
#             match = self.compiled_console_pattern.search(line)
#             print(f"JS Line: {line.strip()} - Should Remove: {bool(match)}")
#             return bool(match)
#         elif file_type in ['.py']:
#             for pattern in self.compiled_python_patterns:
#                 match = pattern.search(line)
#                 print(f"Python Line: {line.strip()} - Should Remove: {bool(match)}")
#                 if match:
#                     return True
#         return False

#     def test_should_remove_line_python(self, cleaner):
#         """Test Python logging statement detection"""
#         assert cleaner.should_remove_line('import logging', '.py')
#         assert cleaner.should_remove_line('logger.info("test")', '.py')
#         assert cleaner.should_remove_line('logging.error("test")', '.py')
#         assert not cleaner.should_remove_line('# logging.info("test")', '.py')  # Commented code
#         assert not cleaner.should_remove_line('my_logger("test")', '.py')  # Not a logging statement

#     def test_get_statement_type(self, cleaner):
#         """Test statement type detection"""
#         assert cleaner.get_statement_type('console.log("test");', '.js') == 'console.log'
#         assert cleaner.get_statement_type('logger.info("test")', '.py') == 'logger.info'
#         assert cleaner.get_statement_type('import logging', '.py') == 'logging_import'

#     @pytest.mark.integration
#     def test_process_files_js(self, cleaner, sample_files, temp_dir):
#         """Test processing of JavaScript files"""
#         # Setup
#         cleaner.source_path = str(temp_dir)
#         cleaner.selected_types = ['.js']
        
#         # Process files
#         cleaner.process_files()
        
#         # Verify
#         with open(sample_files['js']) as f:
#             content = f.read()
#             assert 'console.log' not in content
#             assert 'console.error' not in content
#             assert 'console.warn' not in content
#             assert 'function test()' in content
#             assert 'return true;' in content

#     @pytest.mark.integration
#     def test_process_files_python(self, cleaner, sample_files, temp_dir):
#         """Test processing of Python files"""
#         # Setup
#         cleaner.source_path = str(temp_dir)
#         cleaner.selected_types = ['.py']
        
#         # Process files
#         cleaner.process_files()
        
#         # Verify
#         with open(sample_files['py']) as f:
#             content = f.read()
#             assert 'import logging' not in content
#             assert 'logger.info' not in content
#             assert 'logging.error' not in content
#             assert 'def test():' in content
#             assert 'return True' in content

#     @pytest.mark.integration
#     def test_backup_creation(self, cleaner, sample_files, temp_dir):
#         """Test backup functionality"""
#         # Setup
#         cleaner.should_backup = True
#         cleaner.source_path = str(temp_dir)
#         cleaner.selected_types = ['.js', '.py']
#         cleaner.create_backup_directory()
        
#         # Process files
#         cleaner.process_files()
        
#         # Verify backup directory and files
#         assert os.path.exists(cleaner.current_backup_dir)
#         backup_files = list(Path(cleaner.current_backup_dir).glob('**/*'))
#         backup_files = [f for f in backup_files if f.is_file()]
#         assert len(backup_files) >= 2  # At least original JS and PY files

#     def test_initialize_session(self, cleaner, monkeypatch):
#         """Test session initialization"""
#         # Setup mock responses
#         responses = {
#             'prompt_choice': 1,
#             'prompt_yes_no': [True, False, False, False, False, True]
#         }
        
#         def mock_prompt_choice(*args, **kwargs):
#             return responses['prompt_choice']
            
#         def mock_prompt_yes_no(*args, **kwargs):
#             return responses['prompt_yes_no'].pop(0)
            
#         monkeypatch.setattr(cleaner.ui, 'prompt_choice', mock_prompt_choice)
#         monkeypatch.setattr(cleaner.ui, 'prompt_yes_no', mock_prompt_yes_no)
#         monkeypatch.setattr('builtins.input', lambda _: '.')
        
#         # Execute
#         result = cleaner.initialize_session()
        
#         # Verify
#         assert result is True
#         assert hasattr(cleaner, 'source_path')
#         assert hasattr(cleaner, 'selected_types')
#         assert hasattr(cleaner, 'should_backup')

#     @pytest.mark.parametrize("file_content,file_type,expected_removals", [
#         ("console.log('test');\nvalid code;\nconsole.error('test');", '.js', 2),
#         ("import logging\nvalid code\nlogger.info('test')", '.py', 2),
#     ])
#     def test_removal_counting(self, cleaner, temp_dir, file_content, file_type, expected_removals):
#         """Test counting of removed statements"""
#         # Setup
#         test_file = Path(temp_dir) / f"test{file_type}"
#         test_file.write_text(file_content)
        
#         cleaner.source_path = [str(test_file)]
#         cleaner.selected_types = [file_type]
        
#         # Process
#         cleaner.process_files()
        
#         # Verify
#         assert cleaner.stats['lines_removed'] == expected_removals

# if __name__ == '__main__':
#     pytest.main(['-v'])