import unittest
import pandas as pd
from geocoder_script import GeoCoder, read_csv, clean_and_extract_coordinates

class TestGeoCoderScript(unittest.TestCase):
    def setUp(self):
        self.api_key = "AIzaSyCTNXDFj2A73fuTjTJS3-A_ytQEYKtlhBM"
        self.geo_coder = GeoCoder(self.api_key)
        self.test_data = pd.DataFrame({'Latitude': ["-16.38784, -47.115216", "-18.995999, -47.580682"]})
    
    def test_geocode(self):
        result = self.geo_coder.geocode(-16.38784, -47.115216)
        self.assertEqual(result, {"state": "Goiás", "city": "Goiânia"})
    
    def test_read_csv(self):
        df = read_csv('test_data.csv')
        self.assertIsInstance(df, pd.DataFrame)

    def test_clean_and_extract_coordinates(self):
        df = self.test_data.copy()
        clean_and_extract_coordinates(df)
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ['Latitude', 'Longitude'])

if __name__ == '__main__':
    unittest.main()

