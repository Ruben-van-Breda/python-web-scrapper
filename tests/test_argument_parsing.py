import unittest
import sys
import os
import subprocess
from io import StringIO

# Add parent directory to sys.path to import the main module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestArgumentParsing(unittest.TestCase):
    """
    Test the argument parsing functionality of the WebScrapper.py script.
    """
    
    def test_url_and_output_flags(self):
        """Test that the script accepts -url and -o flags."""
        # Run the script with --help to ensure it shows the right options
        result = subprocess.run(
            ["python", "../WebScrapper.py", "--help"], 
            capture_output=True, 
            text=True
        )
        
        self.assertIn("-url", result.stdout)
        self.assertIn("-o", result.stdout)
        self.assertIn("--output", result.stdout)
    
    def test_missing_required_args(self):
        """Test that the script requires both URL and output arguments."""
        # Test missing URL
        result_no_url = subprocess.run(
            ["python", "../WebScrapper.py", "-o", "output.json"], 
            capture_output=True, 
            text=True
        )
        self.assertIn("error", result_no_url.stderr.lower())
        
        # Test missing output
        result_no_output = subprocess.run(
            ["python", "../WebScrapper.py", "-url", "http://example.com"], 
            capture_output=True, 
            text=True
        )
        self.assertIn("error", result_no_output.stderr.lower())
    
    def test_symbolic_link_works(self):
        """Test that the WebScrap.py symbolic link works correctly."""
        if os.path.exists("../WebScrap.py"):
            result = subprocess.run(
                ["python", "../WebScrap.py", "--help"], 
                capture_output=True, 
                text=True
            )
            self.assertIn("-url", result.stdout)
            self.assertIn("-o", result.stdout)


if __name__ == "__main__":
    unittest.main() 