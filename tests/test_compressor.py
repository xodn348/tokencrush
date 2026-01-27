"""Tests for the TokenCompressor module."""

import pytest
from unittest.mock import patch, MagicMock


class TestTokenCompressor:
    """Tests for TokenCompressor class."""

    def test_compress_basic(self, sample_text):
        """Test basic compression returns CompressResult."""
        from tokencrush.compressor import TokenCompressor, CompressResult
        
        with patch('llmlingua.PromptCompressor') as mock_pc:
            mock_instance = MagicMock()
            mock_instance.compress_prompt.return_value = {
                'compressed_prompt': 'short text',
                'origin_tokens': 100,
                'compressed_tokens': 50,
            }
            mock_pc.return_value = mock_instance
            
            compressor = TokenCompressor(use_gpu=False)
            result = compressor.compress(sample_text, rate=0.5)
            
            assert isinstance(result, CompressResult)
            assert result.original_tokens == 100
            assert result.compressed_tokens == 50

    def test_compress_with_rate(self, sample_text):
        """Test compression respects rate parameter."""
        from tokencrush.compressor import TokenCompressor
        
        with patch('llmlingua.PromptCompressor') as mock_pc:
            mock_instance = MagicMock()
            mock_instance.compress_prompt.return_value = {
                'compressed_prompt': 'compressed',
                'origin_tokens': 100,
                'compressed_tokens': 30,
            }
            mock_pc.return_value = mock_instance
            
            compressor = TokenCompressor()
            compressor.compress(sample_text, rate=0.3)
            
            call_args = mock_instance.compress_prompt.call_args
            assert call_args[1].get('rate') == 0.3

    def test_gpu_flag(self):
        """Test GPU flag is passed correctly."""
        from tokencrush.compressor import TokenCompressor
        
        with patch('llmlingua.PromptCompressor') as mock_pc:
            TokenCompressor(use_gpu=True)
            assert mock_pc.call_args[1].get('device_map') in ['cuda', 'auto']
            
            mock_pc.reset_mock()
            TokenCompressor(use_gpu=False)
            assert mock_pc.call_args[1].get('device_map') == 'cpu'

    def test_empty_text(self):
        """Test compression handles empty text."""
        from tokencrush.compressor import TokenCompressor
        
        with patch('llmlingua.PromptCompressor'):
            compressor = TokenCompressor()
            result = compressor.compress("", rate=0.5)
            
            assert result.compressed_text == ""
            assert result.original_tokens == 0
