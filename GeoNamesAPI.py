import requests
import pandas as pd
import urllib.parse

# Load your dataset
df = pd.read_csv('MainFolder/Datasets/Final_Corrected_Enriched_dataset_v4.csv')


# Define a function to get the population
def get_population(city, country):
    base_url = "http://api.geonames.org/searchJSON?"
    params = {
        "name": urllib.parse.quote(city),  # URL-encode special characters
        "country": country if len(country) == 2 else None,  # Use ISO code if available
        "maxRows": 1,
        "username": "aliarabyar"  # Replace with your GeoNames username
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        print(data)

        total_results = data.get('totalResultsCount', 0)

        if total_results == 0:
            print(f"No match found for City: {city}, Country: {country}")

        if total_results > 0:
            return data['geonames'][0].get('population')
        else:
            return None
    except requests.RequestException as e:
        print(f"An error occurred while fetching data: {e}")
        return None


# Apply the function to your dataframe
df['Population'] = df.apply(lambda row: get_population(row['City'], row['Country']), axis=1)

# Save the updated dataframe
df.to_csv('MainFolder/Datasets/path_to_save_updated_dataset_contains_Population.csv', index=False)
