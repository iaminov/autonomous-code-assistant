"""Test suite for the autonomous code assistant."""

import pytest

from autonomous_code_assistant.core import CodeAssistant
from autonomous_code_assistant.exceptions import CodeAssistantError


def test_code_generation():
    """Test code generation capability of the assistant."""
    assistant = CodeAssistant(provider_name="openai", api_key="fake-key")
    
    # Assume we have a fake provider for testing purposes
    instruction = "Generate a function to calculate the factorial of a number in Python."
    result = assistant.process_instruction(instruction, target_file=None)
    
    assert result['success']
    assert "def factorial(n):" in result['generated_content']


@pytest.mark.parametrize("file, expected_lang", [
    ("tests/samples/sample.py", "python"),
    ("tests/samples/sample.js", "javascript"),
    ("tests/samples/sample.java", "java"),
])
def test_language_detection(file, expected_lang):
    """Test language detection on sample files."""
    assistant = CodeAssistant(provider_name="openai", api_key="fake-key")
    language = assistant.code_analyzer.detect_language(file)
    assert language == expected_lang


def test_file_backup_creation(tmp_path):
    """Test that backups are created when modifying files."""
    assistant = CodeAssistant(provider_name="openai", api_key="fake-key")
    filepath = tmp_path / "test.txt"
    filepath.write_text("Original content.")
    
    instruction = "Replace this text with 'Updated content.'"
    result = assistant.process_instruction(
        instruction=instruction,
        target_file=filepath,
        create_backup=True
    )
    
    # Verify backup was created
    backup_manager = assistant.backup_manager
    latest_backup = backup_manager.get_latest_backup(filepath)
    assert latest_backup.exists()
    assert latest_backup.read_text() == "Original content."


def test_code_review_suggestion():
    """Test that the assistant can provide a code review suggestion."""
    assistant = CodeAssistant(provider_name="openai", api_key="fake-key")
    review = assistant.review_code("samples/sample.py")
    
    assert "Code quality and maintainability" in review['review']


def test_unexpected_error_handling():
    """Test that unexpected errors are handled gracefully."""
    assistant = CodeAssistant(provider_name="openai", api_key="fake-key")
    
    with pytest.raises(CodeAssistantError) as excinfo:
        # Simulate an unexpected error by passing invalid args
        assistant.process_instruction(instruction=None)
    
    assert "UNEXPECTED_ERROR" in str(excinfo.value)
