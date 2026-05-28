import pytest
import os
from unittest.mock import Mock, patch
from extractor.llm import LLMClient
from extractor.strategies.base import BaseStrategy
from extractor.strategies.pure_text import PureTextStrategy

@pytest.fixture
def mock_llm_client():
    client = Mock(spec=LLMClient)
    client.call.return_value = Mock(text='{"success": true}')
    return client

def test_base_strategy_not_implemented(mock_llm_client):
    strategy = BaseStrategy(client=mock_llm_client)
    with pytest.raises(NotImplementedError):
        strategy.extract(["dummy.pdf"])

@patch('extractor.strategies.pure_text.fitz')
def test_pure_text_extraction(mock_fitz, mock_llm_client, tmp_path):
    # Setup mock PDF
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_text("dummy pdf content")
    
    mock_doc = Mock()
    mock_page = Mock()
    mock_page.get_text.return_value = "Mocked PDF text"
    mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
    mock_doc.__len__ = Mock(return_value=1)
    mock_fitz.open.return_value = mock_doc
    
    strategy = PureTextStrategy(client=mock_llm_client)
    result = strategy.extract([str(pdf_path)])
    
    assert mock_llm_client.call.called
    assert result.text == '{"success": true}'
    
    # Check that client was called with correct parameters
    call_args = mock_llm_client.call.call_args[0][0]
    assert "Mocked PDF text" in call_args[0]

from extractor.strategies.native_multimodal import NativeMultimodalStrategy

@patch('extractor.strategies.native_multimodal.genai')
def test_native_multimodal_extraction(mock_genai, mock_llm_client, tmp_path):
    pdf_path = tmp_path / "test_visual.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 mock data")

    mock_file = Mock()
    mock_file.name = "files/mock-123"
    mock_genai.upload_file.return_value = mock_file
    
    # We mock client.wait_for_files to do nothing
    mock_llm_client.wait_for_files = Mock()

    strategy = NativeMultimodalStrategy(client=mock_llm_client)
    result = strategy.extract([str(pdf_path)])

    assert mock_genai.upload_file.called
    assert mock_llm_client.wait_for_files.called
    assert mock_llm_client.call.called
    assert mock_genai.delete_file.called
    assert result.text == '{"success": true}'
