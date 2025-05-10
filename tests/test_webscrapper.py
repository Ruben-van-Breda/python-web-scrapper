import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

# Import the WebScrap function from the parent directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from WebScrapper import WebScrap


class TestWebScrapper(unittest.TestCase):
    """Test cases for the WebScrap function."""

    @patch('WebScrapper.requests.get')
    def test_successful_scrape(self, mock_get):
        """Test the expected use case of successfully scraping a URL."""
        # Set up mock
        mock_response = MagicMock()
        mock_response.text = "<html><body><h1>Test Title</h1><p>Test content</p></body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Call the function
            result = WebScrap("https://example.com", temp_path)
            
            # Check the returned dictionary
            self.assertEqual(result["url"], "https://example.com")
            self.assertIn("Test Title", result["content"])
            self.assertIn("Test content", result["content"])
            
            # Check the JSON file
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
                self.assertEqual(saved_data["url"], "https://example.com")
                self.assertIn("Test Title", saved_data["content"])
                self.assertIn("Test content", saved_data["content"])
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @patch('WebScrapper.requests.get')
    def test_empty_page(self, mock_get):
        """Test edge case with an empty page."""
        # Set up mock
        mock_response = MagicMock()
        mock_response.text = ""
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Call the function
            result = WebScrap("https://example.com", temp_path)
            
            # Check the returned dictionary
            self.assertEqual(result["url"], "https://example.com")
            self.assertEqual(result["content"], "")
            
            # Check the JSON file
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
                self.assertEqual(saved_data["url"], "https://example.com")
                self.assertEqual(saved_data["content"], "")
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @patch('WebScrapper.requests.get')
    def test_request_error(self, mock_get):
        """Test failure case - unable to access URL."""
        # Set up mock to raise an exception
        mock_get.side_effect = Exception("Connection error")

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            # Call the function and check for exception
            with self.assertRaises(ValueError):
                WebScrap("https://example.com", temp_path)
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main() 