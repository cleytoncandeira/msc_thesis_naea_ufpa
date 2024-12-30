import unittest
from unittest.mock import patch
from scripts.data_cleaning.get_city_state_loc import *

class TestGeoCoder(unittest.TestCase):

    @patch('seu_modulo.requests.get')
    def test_geocode_success(self, mock_get):
        # Simula uma resposta bem-sucedida da API do Google Maps Geocoding
        mock_response = {
            "status": "OK",
            "results": [{
                "address_components": [
                    {
                        "long_name": "Belém",
                        "types": ["administrative_area_level_2"]
                    },
                    {
                        "long_name": "Pará",
                        "types": ["administrative_area_level_1"]
                    }
                ]
            }]
        }

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        # Instancia o GeoCoder com uma chave de API fictícia -- melhorar, pois isso não é mais possível
        geocoder = GeoCoder("fake_api_key")

        result = geocoder.geocode(-1.455755, -48.490180)
        self.assertEqual(result, {"state": "Pará", "city": "Belém"})

    @patch('seu_modulo.requests.get')
    def test_geocode_failure(self, mock_get):
        # Simula uma resposta falha da API do Google Maps Geocoding
        mock_response = {"status": "ZERO_RESULTS"}

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        geocoder = GeoCoder("fake_api_key")

        result = geocoder.geocode(-1.455755, -48.490180)

        self.assertEqual(result, {"state": None, "city": None})

if __name__ == '__main__':
    unittest.main()
