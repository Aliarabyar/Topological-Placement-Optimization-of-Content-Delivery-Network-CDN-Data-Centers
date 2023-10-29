import pandas as pd
import requests
import networkx as nx
import os
import time
# Load the GML dataset into a NetworkX graph
graph = nx.read_gml('MainFolder/Datasets/interconnect_Corrected.gml')

# Convert the graph nodes to a DataFrame
df = pd.DataFrame.from_dict(dict(graph.nodes(data=True)), orient='index')

# Retrieve only the relevant columns (Longitude and Latitude)
df = df[['Longitude', 'Latitude']]

# Retrieve API key from environment variable
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("API key not found in the environment variables.")

# Define a function to get the city and country from the latitude and longitude
def get_location_details(lat, lon, api_key):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lon}",
        "key": api_key
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        # print(data)

        # Extract country and city
        city, country = None, None
        if 'results' in data and len(data['results']) > 0:
            for component in data['results'][0]['address_components']:
                if 'locality' in component['types']:
                    city = component['long_name']
                if 'country' in component['types']:
                    country = component['long_name']
        return city, country
    except Exception as e:
        print(f"Error occurred: {e}")
        return None, None

# Apply the function to the dataframe
df['City'], df['Country'] = zip(*df.apply(lambda row: get_location_details(row['Latitude'], row['Longitude'], api_key), axis=1))
# time.sleep(0.5)  # 0.5 seconds delay

# Save the enriched dataframe to a new CSV file
df.to_csv('MainFolder/Datasets/Enriched_dataset_By_Population.csv', index=False, encoding='utf-8')
