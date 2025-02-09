import pytest
from src.logcleaner import ConsoleUI

class TestConsoleUI:
    @pytest.fixture
    def ui(self):
        """Create a ConsoleUI instance."""
        return ConsoleUI()

    def test_print_logo(self, ui, capsys):
        """Test printing the application logo."""
        ui.print_logo()
        captured = capsys.readouterr()
        assert "Log Cleaner v1.0.0" in captured.out
        assert ui.CYAN in captured.out
        assert ui.BOLD in captured.out

    def test_print_step(self, ui, capsys):
        """Test printing the current step."""
        ui.print_step("Test Step", 3, 1)
        captured = capsys.readouterr()
        assert "Step 1/3" in captured.out
        assert "Test Step" in captured.out

    def test_print_success(self, ui, capsys):
        """Test printing a success message."""
        ui.print_success("Test Success")
        captured = capsys.readouterr()
        assert "✓ Test Success" in captured.out
        assert ui.GREEN in captured.out

    @pytest.mark.parametrize("input_values, expected", [
        (['1'], 1),
        (['invalid', '2'], 2),
        (['0', '3'], 3),
    ])
    def test_prompt_choice(self, ui, input_values, expected, monkeypatch):
        """Test prompting the user for a choice from a list of options."""
        inputs = iter(input_values)
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        result = ui.prompt_choice("Test choices", ["Option 1", "Option 2", "Option 3"])
        assert result == expected

    @pytest.mark.parametrize("input_values, expected", [
        (['y'], True),
        (['n'], False),
        (['invalid', 'yes'], True),
        (['invalid', 'no'], False),
    ])
    def test_prompt_yes_no(self, ui, input_values, expected, monkeypatch):
        """Test prompting the user for a yes/no response."""
        inputs = iter(input_values)
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        result = ui.prompt_yes_no("Test yes/no")
        assert result == expected
        
if __name__ == '__main__':
    pytest.main(['-v'])        
        
# import pytest

# from src.logcleaner import ConsoleUI

# class TestConsoleUI:
#     @pytest.fixture
#     def ui(self):
#         return ConsoleUI()

#     def test_print_logo(self, ui, capsys):
#         ui.print_logo()
#         captured = capsys.readouterr()
#         assert "Log & Console Cleanup Tool" in captured.out
#         assert ui.CYAN in captured.out
#         assert ui.BOLD in captured.out

#     def test_print_step(self, ui, capsys):
#         ui.print_step("Test Step", 3, 1)
#         captured = capsys.readouterr()
#         assert "Step 1/3" in captured.out
#         assert "Test Step" in captured.out

#     def test_print_success(self, ui, capsys):
#         ui.print_success("Test Success")
#         captured = capsys.readouterr()
#         assert "✓" in captured.out
#         assert "Test Success" in captured.out
#         assert ui.GREEN in captured.out

#     @pytest.mark.parametrize("input_values, expected", [
#         (['1'], 1),
#         (['invalid', '2'], 2),
#         (['0', '3'], 3),
#     ])
#     def test_prompt_choice(self, ui, input_values, expected, monkeypatch):
#         inputs = iter(input_values)
#         monkeypatch.setattr('builtins.input', lambda _: next(inputs))
#         result = ui.prompt_choice("Test choices", ["Option 1", "Option 2", "Option 3"])
#         assert result == expected

#     @pytest.mark.parametrize("input_values, expected", [
#         (['y'], True),
#         (['n'], False),
#         (['invalid', 'yes'], True),
#         (['invalid', 'no'], False),
#     ])
#     def test_prompt_yes_no(self, ui, input_values, expected, monkeypatch):
#         inputs = iter(input_values)
#         monkeypatch.setattr('builtins.input', lambda _: next(inputs))
#         result = ui.prompt_yes_no("Test yes/no")
#         assert result == expected
        
# if __name__ == '__main__':
#     pytest.main(['-v'])