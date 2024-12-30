import unittest
from unittest.mock import patch
from scripts.data_cleaning.clean_up_loc_farms import * 

class TestScript(unittest.TestCase):
    
    def test_dms_to_decimal(self):
        result = dms_to_decimal(10, 30, 30)
        self.assertAlmostEqual(result, -10.508333333333333)
    
    def test_string_to_float(self):
        self.assertAlmostEqual(string_to_float("123.45"), 123.45)
        self.assertAlmostEqual(string_to_float("7.89"), 7.89)
        self.assertIsNone(string_to_float("abc"))
    
    def test_convert_to_negative_float(self):
        self.assertAlmostEqual(convert_to_negative_float("10.5"), -10.5)
        self.assertIsNone(convert_to_negative_float("abc"))
    
    def test_extract_gc(self):
        # Teste com um exemplo conhecido
        result = extract_gc("10o30'30.0\"")
        self.assertEqual(result, (10, 30, 30.0))
        # Teste com um valor que não é um GC
        self.assertIsNone(extract_gc("abc"))

    @patch('builtins.open')
    @patch('chardet.detect')
    def test_discover_csv_encoding(self, mock_detect, mock_open):
        mock_detect.return_value = {'encoding': 'utf-8', 'confidence': 0.99}
        encoding, confidence = discover_csv_encoding('dummy_path')
        self.assertEqual(encoding, 'utf-8')
        self.assertAlmostEqual(confidence, 0.99)

if __name__ == '__main__':
    unittest.main()
