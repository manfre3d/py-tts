import os
import pytest
from unittest.mock import patch, MagicMock


def test_is_available_with_key():
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
        from ai_cleanup import is_available
        assert is_available() is True


def test_is_available_without_key():
    env = {k: v for k, v in os.environ.items() if k != 'OPENAI_API_KEY'}
    with patch.dict(os.environ, env, clear=True):
        from ai_cleanup import is_available
        assert is_available() is False


def test_clean_text_returns_original_when_no_client():
    from ai_cleanup import clean_text
    with patch('ai_cleanup._get_client', return_value=None):
        result = clean_text("some raw text")
    assert result == "some raw text"


def test_clean_text_calls_gpt4o_mini_and_returns_cleaned():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="  cleaned text  "))]
    )
    from ai_cleanup import clean_text
    with patch('ai_cleanup._get_client', return_value=mock_client):
        result = clean_text("raw text")

    assert result == "cleaned text"
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs['model'] == 'gpt-4o-mini'
    assert call_kwargs['temperature'] == 0.0


def test_clean_text_caps_input_at_50k_chars():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="out"))]
    )
    long_input = "x" * 100_000
    from ai_cleanup import clean_text
    with patch('ai_cleanup._get_client', return_value=mock_client):
        clean_text(long_input)

    user_content = mock_client.chat.completions.create.call_args[1]['messages'][1]['content']
    assert len(user_content) == 50_000


def test_clean_text_returns_original_on_api_exception():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API error")
    from ai_cleanup import clean_text
    with patch('ai_cleanup._get_client', return_value=mock_client):
        result = clean_text("raw text")
    assert result == "raw text"
