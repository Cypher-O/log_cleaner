#!/usr/bin/env python3
import sys
from .cleaner import LogCleaner
from .console import ConsoleUI 

def main():
    try:
        cleaner = LogCleaner()
        
        if cleaner.initialize_session():
            cleaner.process_files()
            cleaner.print_summary()
            
            if cleaner.stats['files_processed'] > 0:
                cleaner.ui.print_success("Cleanup completed successfully!")
            else:
                cleaner.ui.print_warning("No files were modified.")
                
        return 0
        
    except KeyboardInterrupt:
        return 1
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        return 1
    finally:
        print(ConsoleUI.END, end='')

if __name__ == "__main__":
    main()
    
    
# def main():
#     cleaner = LogCleaner()
    
#     if cleaner.initialize_session():
#         cleaner.process_files()
#         cleaner.print_summary()
        
#         if cleaner.stats['files_processed'] > 0:
#             cleaner.ui.print_success("Cleanup completed successfully!")
#         else:
#             cleaner.ui.print_warning("No files were modified.")

# if __name__ == "__main__":
#     main()