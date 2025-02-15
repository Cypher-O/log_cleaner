# Log Cleaner Pro

A powerful Python utility that provides comprehensive log management capabilities. This dual-purpose tool helps you maintain clean production code by automatically removing logging statements and console outputs from your codebase, while also efficiently managing your log files through automated cleaning and scheduling. It intelligently handles Python logging statements and JavaScript/TypeScript console outputs, supporting both single-line and multi-line statements, alongside sophisticated log file management features for automated retention and cleanup.

## Features

### Code Cleanup

- **Multi-Language Support**
  - Python (`.py`)
  - JavaScript (`.js`)
  - TypeScript (`.ts`)
  - React files (`.jsx`, `.tsx`)

- **Smart Code Detection**
  - Identifies and removes Python logging statements (`logger.*`, `logging.*`)
  - Catches all console methods in JavaScript/TypeScript
  - Handles multi-line logging statements
  - Preserves code formatting

### Log File Management

- **Intelligent Log Detection**
  - Automatically identifies log files by extension and content
  - Supports multiple log file formats and patterns
  - Handles various timestamp formats
  - Works with rotated log files (e.g., .log.1, .log.2)

- **Automated Cleaning**
  - Remove log entries older than specified date
  - Scheduled cleaning through cron jobs
  - Configurable retention periods
  - Preserves file structure and empty lines

- **Safety Features**
  - Automatic backup creation
  - Detailed logging of all changes
  - Preview of affected files before cleanup
  - Undo capability through backups

- **User Interface**
  - Interactive command-line interface
  - Clear progress indicators
  - Colored output for better visibility
  - Comprehensive summary reports

## Installation

### Using pip (Recommended)

You can install the package directly from GitHub:

```bash
# Install latest version
pip install git+https://github.com/cypher-o/log_cleaner.git

# Or specify a version
pip install git+https://github.com/cypher-o/log_cleaner.git@v1.0.0
```

### From source

1. Clone this repository:

   ```bash
   git clone https://github.com/cypher-o/log_cleaner.git
   cd log_cleaner
   ```

2. Install in development mode:

   ```bash
   pip install -e .
   ```

## Usage

### Basic Command Line Usage

```bash
# Start the interactive tool
log-cleaner

# Or using Python's -m flag
python -m log_cleaner
```

### Code Cleanup Examples

Clean logging statements from a specific directory:

```bash
python log_cleaner.py --clean-code ./my_project
```

Clean specific files:

```bash
python log_cleaner.py --clean-code ./src/main.py ./src/utils.js
```

### Log File Management Examples

Clean old log entries:

```bash
# Clean logs older than 30 days
python log_cleaner.py --clean-logs ./logs --days 30

# Clean logs before specific date
python log_cleaner.py --clean-logs ./logs --before 2024-01-01
```

Set up automated cleaning:

```bash
# Schedule daily cleanup at 2:30 AM
python log_cleaner.py --schedule ./logs --hour 2 --minute 30

# Remove scheduled cleanup
python log_cleaner.py --remove-schedule
```

## Supported Log Formats

The tool supports various log formats including:

- ISO format timestamps:

```bash
2024-02-15 10:30:45 INFO Started application
```

- Unix timestamps:

```bash
1644915045 Started backup process
```

- Custom formats:

```bash
[Feb 15 10:30:45 2024] Server started
```

## Supported Code Patterns

### Python

```python
# Import statements
import logging
from logging import getLogger

# Logger initialization
logger = logging.getLogger(__name__)
_logger = logging.getLogger()

# Logging statements
logger.info("Message")
logger.error(f"Error: {error}")
_logger.warning(
    f"Warning message with "
    "multiple lines"
)
```

### JavaScript/TypeScript

```javascript
// Console statements
console.log("Message");
console.error("Error");
console.warn(
    "Multi-line " +
    "warning message"
);
```

## Backup and Recovery

- Backups are stored in a `backup` directory with timestamps
- Each backup includes:
  - Original files with directory structure preserved
  - Detailed log file of all changes
  - Timestamp-based organization for easy recovery

## Examples

### Basic Usage

Clean a specific directory:

```bash
python log_cleaner.py
# Select "Select a directory"
# Enter: ./my_project
```

### Clean Specific Files

```bash
python log_cleaner.py
# Select "Select specific files"
# Enter files one by one:
# ./src/main.py
# ./src/utils.js
```

## Best Practices

1. Always run on version-controlled code
2. Review changes before confirming
3. Enable backups for important files
4. Test after cleaning
5. Schedule automated cleaning during low-traffic periods
6. Monitor disk space usage
7. Set appropriate retention periods

## Limitations

- Complex string concatenations may require manual review
- Cannot detect logging statements in string literals or comments
- May require adjustment of patterns for custom log formats
- Scheduled cleaning requires cron daemon to be running

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by the need for clean production code
- Built with best practices from Python and JavaScript communities
  
## Support

For issues, questions, or contributions, please:

1. Open an issue in the GitHub repository
2. Include sample code or log files that demonstrate the problem
3. Provide the error message if applicable
4. Describe the expected behavior

## Changelog

### v1.1.0 (2025-02-15)

- Added log file management capabilities
- Automated cleaning with cron integration
- Support for multiple log formats
- Improved log file detection

### v1.0.0 (2025-02-09)

- Initial release
- Multi-language code cleanup
- Backup functionality
- Interactive CLI

---
Made with Python by Olumide Awodeji
