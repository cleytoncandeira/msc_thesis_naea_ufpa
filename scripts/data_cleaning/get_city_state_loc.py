import pandas as pd
import requests
import re

class GeoCoder:
    def __init__(self, api_key):
        self.api_key = api_key

    def geocode(self, latitude, longitude):
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&key={self.api_key}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if data["status"] == "OK":
                address_components = data["results"][0]["address_components"]
                state = self.get_address_component(address_components, "administrative_area_level_1")
                city = self.get_address_component(address_components, "administrative_area_level_2")
                return {"state": state, "city": city}
            else:
                print("No address found.")
        else:
            print("Request error.")
        return {"state": None, "city": None}

    @staticmethod
    def get_address_component(components, component_type):
        for component in components:
            if component_type in component["types"]:
                return component["long_name"]
        return None


def read_csv(file_path):
    return pd.read_csv(file_path)

def clean_and_extract_coordinates(df):
    df['Latitude'], df['Longitude'] = zip(*df['Latitude'].str.extract(r'(-?\d+\.\d+), (-?\d+\.\d+)').dropna().values)
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)

def main():
    # Import DataFrame
    farm_branches_uf = read_csv('farm_branches_uf.csv')

    # Clean and extract coordinates
    clean_and_extract_coordinates(farm_branches_uf)

    # Addresses with Federative Unit and Municipality
    addresses = dict()

    # API KEY
    api_key = "AIzaSyCTNXDFj2A73fuTjTJS3-A_ytQEYKtlhBM"

    geocoder = GeoCoder(api_key)

    for index, row in farm_branches_uf.iterrows():
        latitude, longitude = row['Latitude'], row['Longitude']
        address_info = geocoder.geocode(latitude, longitude)
        addresses[index] = address_info
        print("State and city found:", address_info["state"], address_info["city"], index)
        print()

    new_df = pd.DataFrame(list(addresses.values()), columns=['state', 'city'])

    farm_branches_uf = pd.concat([farm_branches_uf, new_df], axis=1)

    farm_branches_uf.to_csv('farm_branches_uf_processed.csv', index=False)
    
if __name__ == "__main__":
    main()

