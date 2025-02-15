#!/usr/bin/env python3
from datetime import datetime, timedelta
import sys
from .cleaner import LogCleaner
from .console import ConsoleUI 

def main():
    try:
        cleaner = LogCleaner()
        
        if len(sys.argv) > 1 and sys.argv[1] == '--clean-logs':
            # Running from cron job
            log_dir = sys.argv[2]
            log_files = cleaner.log_manager.get_log_files(log_dir)
            cutoff_date = datetime.now() - timedelta(days=30)
            cleaner.log_manager.clean_logs_before_date(log_files, cutoff_date)
        else:
            # Interactive mode
            if cleaner.initialize_session():
                cleaner.process_files()
                cleaner.print_summary()
                
                if cleaner.stats['files_processed'] > 0:
                    cleaner.ui.print_success("Cleanup completed successfully!")
                else:
                    cleaner.ui.print_warning("No modifications were made to the code files.")
                
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
    