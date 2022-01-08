import unittest
from pathlib import Path

from src.invoice_parser import pdf_reader

TEST_DIR = Path('./tests/inv_test_documents')

class TestPdfReader(unittest.TestCase):
    def test_extract_text(self):
        for f in TEST_DIR.glob('*.*'):
            text = pdf_reader.extract_text(f)


if __name__ == '__main__':
    unittest.main()