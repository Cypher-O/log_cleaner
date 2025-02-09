import sys
import time
from typing import List

class ConsoleUI:
    """
    A class to handle console output and user interaction in a styled manner.

    This class provides various methods for displaying messages with ANSI color codes,
    prompting user input, and managing visual elements like progress bars and spinners.
    It enhances the user experience by providing informative and visually appealing output.
    """
    
    # ANSI color codes for styling console output
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    CLEAR_LINE = '\x1b[2K'
    CURSOR_UP = '\033[A'
    
    def __init__(self):
        """
        Initializes the ConsoleUI class, setting up the spinner frames for visual feedback.

        This constructor prepares the spinner frames that will be used in the spinner method
        for indicating ongoing processes in the console. The current frame index is initialized
        to zero.
        """
        self.spinner_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current_frame = 0

    def print_logo(self):
        """Print the application logo with a properly aligned box, enhanced styling and text"""
        box_width = 42  

        title_text = "Log Cleaner v1.0.0".center(box_width) 
        tagline_text = "Clean your logs with style".center(box_width)  

        # Apply styling **after** centering to avoid misalignment
        title = f"{self.BOLD}{self.WHITE}{title_text}{self.END}"
        tagline = f"{self.MAGENTA}{tagline_text}{self.END}"

        logo = (
            f"{self.CYAN}╔{'═' * box_width}╗\n"
            f"{self.CYAN}║{title}{self.CYAN}║\n"
            f"{self.CYAN}║{' ' * box_width}║\n"
            f"{self.CYAN}║{tagline}{self.CYAN}║\n"
            f"{self.CYAN}╚{'═' * box_width}╝{self.END}\n"
        )

        print(logo)
        
    def print_step(self, step_name: str, total_steps: int, current_step: int):
        """
        Prints the current step of a multi-step process with exact padding for alignment and enhanced visibility.

        This method formats and displays the current step out of the total steps, providing
        users with clear feedback on their progress in the application.

        Args:
            step_name (str): The name or description of the current step.
            total_steps (int): The total number of steps in the process.
            current_step (int): The current step number being executed.
        """
        box_width = 40 
        step_text = f"Step {current_step}/{total_steps}: {step_name}"  
        text_length = len(step_text)

        # Ensure the text is centered by calculating padding
        padding = box_width - text_length - 2  # -2 accounts for the side borders "│ │"
        left_padding = padding // 2
        right_padding = padding - left_padding

        print(f"\n{self.CYAN}┌{'─' * (box_width)}┐{self.END}")
        print(f"{self.CYAN}│{self.END} {' ' * left_padding}{self.BOLD}{step_text}{self.END}{' ' * right_padding} {self.CYAN}│{self.END}")
        print(f"{self.CYAN}└{'─' * (box_width)}┘{self.END}")

    def print_error(self, message: str):
        """Prints an error message in red for visibility."""
        print(f"{self.RED}✗ Error: {message}{self.END}")

    def print_warning(self, message: str):
        """Prints a warning message in yellow to alert the user."""
        print(f"{self.YELLOW}⚠ Warning: {message}{self.END}")

    def print_success(self, message: str):
        """Prints a success message in green to indicate a successful operation."""
        print(f"{self.GREEN}✓ {message}{self.END}")

    def print_info(self, message: str):
        """Prints an informational message in blue for general information."""
        print(f"{self.BLUE}ℹ {message}{self.END}")
    
    def prompt_input(self, message: str) -> str:
        """
        Prompts the user for input with enhanced styling.

        This method displays a formatted prompt message and waits for the user to enter
        their response.

        Args:
            message (str): The message to display in the input prompt.

        Returns:
            str: The user's input as a string.
        """
        return input(f"{self.CYAN}❯ {self.BOLD}{message}: {self.END}")

    def prompt_choice(self, question: str, options: List[str]) -> int:
        """
        Prompts the user to choose from a list of numbered options.

        This method displays a question along with a list of options for the user to select
        from. It ensures the user's choice is valid before returning the selected option.

        Args:
            question (str): The question to ask the user.
            options (List[str]): A list of options for the user to choose from.

        Returns:
            int: The selected option number (1-based).
        """
        print(f"\n{self.CYAN}{self.BOLD}{question}{self.END}")
        for i, option in enumerate(options, 1):
            print(f"{self.CYAN}{i}.{self.END} {option}")
            
        while True:
            try:
                choice = self.prompt_input(f"Enter your choice (1-{len(options)})")
                choice_num = int(choice)
                if 1 <= choice_num <= len(options):
                    return choice_num
                self.print_error(f"Please enter a number between 1 and {len(options)}")
            except ValueError:
                self.print_error("Please enter a valid number")

    def prompt_yes_no(self, question: str) -> bool:
        """
        Prompts the user for a yes/no answer.

        This method asks the user a question and expects a response of 'y' (yes) or 'n' (no).
        It will continue prompting until a valid response is received.

        Args:
            question (str): The question to ask the user.

        Returns:
            bool: True if the answer is yes, False if the answer is no.
        """
        while True:
            response = self.prompt_input(f"{question} (y/n)").lower()
            if response in ['y', 'yes']:
                return True
            if response in ['n', 'no']:
                return False
            self.print_error("Please answer 'y' or 'n'")

    def spinner(self, message: str):
        """
        Creates a spinner for showing progress in the console.

        This method returns a callable function that updates the spinner's frame while displaying
        the provided message. It provides visual feedback to the user during long-running processes.

        Args:
            message (str): The message to display alongside the spinner.

        Returns:
            callable: A function that updates the spinner with each call.
        """
        def spin():
            frame = self.spinner_frames[self.current_frame]
            sys.stdout.write(f'\r{frame} {message}')
            sys.stdout.flush()
            self.current_frame = (self.current_frame + 1) % len(self.spinner_frames)
            time.sleep(0.1)
        return spin

    def progress_bar(self, total: int):
        """
        Creates a progress bar to visually represent progress.

        This method returns a callable function that updates the progress bar based on the current
        progress relative to the total number of items.

        Args:
            total (int): The total number of items to process.

        Returns:
            callable: A function to update the progress bar.
        """
        def update(current: int):
            percent = (current / total) * 100
            bar_length = 40
            filled = int(bar_length * current / total)
            bar = '█' * filled + '░' * (bar_length - filled)
            sys.stdout.write(f'\r|{bar}| {percent:.1f}% ({current}/{total})')
            sys.stdout.flush()
            if current == total:
                print()
        return update

    def clear_line(self):
        """Clears the current line in the terminal for cleaner output."""
        sys.stdout.write('\r' + self.CLEAR_LINE)
        sys.stdout.flush()

    def print_header(self, text: str):
        """Prints a header with decorative formatting for sections."""
        print(f"\n{self.CYAN}══════ {self.BOLD}{text}{self.END}{self.CYAN} ══════{self.END}\n")

    def print_section(self, text: str):
        """Prints a section title in bold for emphasis."""
        print(f"\n{self.BOLD}{text}{self.END}")
 