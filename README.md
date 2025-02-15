# Log & Console Cleanup Tool

A powerful Python utility for automatically removing logging statements and console outputs from your codebase. This tool supports Python logging statements and JavaScript/TypeScript console outputs, with intelligent handling of both single-line and multi-line statements.

## Features

- **Multi-Language Support**
  - Python (`.py`)
  - JavaScript (`.js`)
  - TypeScript (`.ts`)
  - React files (`.jsx`, `.tsx`)

- **Smart Detection**
  - Identifies and removes Python logging statements (`logger.*`, `logging.*`)
  - Catches all console methods in JavaScript/TypeScript
  - Handles multi-line logging statements
  - Preserves code formatting

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

After installation, you can run the tool from anywhere using:

  ```bash
  # Using the command-line tool
  log-cleaner

  # Or using Python's -m flag
  python -m log-cleaner
  ```

## Supported Patterns

### Python

- Import statements:
  
  ```python
  import logging
  from logging import getLogger
  ```

- Logger initialization:
  
  ```python
  logger = logging.getLogger(__name__)
  _logger = logging.getLogger()
  ```

- Logging statements (including multi-line):
  
  ```python
  logger.info("Message")
  logger.error(f"Error: {error}")
  _logger.warning(
      f"Warning message with "
      "multiple lines"
  )
  ```

### JavaScript/TypeScript

- Console statements:
  
  ```javascript
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

1. Always run the tool on version-controlled code
2. Review the summary before confirming changes
3. Enable backup option for important codebases
4. Test the cleaned code before committing changes

## Limitations

- Does not handle extremely complex string concatenations
- Cannot detect logging statements in string literals or comments
- May require manual review for edge cases

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
2. Include sample code that demonstrates the problem
3. Provide the error message if applicable
4. Describe the expected behavior

## Changelog

### v1.0.0 (2025-02-09)

- Initial release
- Multi-language support
- Backup functionality
- Interactive CLI

---
Made with python by Olumide Awodeji
