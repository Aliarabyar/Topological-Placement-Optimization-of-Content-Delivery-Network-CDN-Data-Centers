from sklearn.neighbors import KDTree
import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
from math import log, exp
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import requests
import json
import time

# Function to fetch population data from an online source
def fetch_city_population(city_name):
    try:
        api_url = f'https://api.api-ninjas.com/v1/city?name={city_name}'
        headers = {'X-Api-Key': 'nt5IA2Cga/ueDlIBZbQNcg==WjZ5ll0jMLHxYKQE'}
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            city_data = json.loads(response.text)
            if city_data:
                population = city_data[0].get('population')
                print(f"City: {city_name}, Population: {population}")  # Print city and population
                return population
            else:
                print(f"No data found for city: {city_name}")
                return None
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# Define columns
columns = [
    'geonameid', 'name', 'asciiname', 'alternatenames', 'latitude', 'longitude',
    'feature_class', 'feature_code', 'country_code', 'cc2', 'admin1_code', 'admin2_code',
    'admin3_code', 'admin4_code', 'population', 'elevation', 'dem', 'timezone', 'modification_date'
]

# Load data
all_countries_df = pd.read_csv('MainFolder/Datasets/allCountries.txt', delimiter='\t', header=None,
                               names=columns, usecols=['latitude', 'longitude', 'population'])
all_countries_df.dropna(inplace=True)

# Concatenate dataframes
geonames_df = pd.concat([all_countries_df], ignore_index=True)
geonames_df.dropna(inplace=True)

# Build KDTree
tree = KDTree(geonames_df[['latitude', 'longitude']].values, leaf_size=100)

# Load your dataset
your_data_df = pd.read_csv('MainFolder/Datasets/Final_Corrected_Enriched_dataset_v4.csv')

# Placeholder list to store results for k-tuning
tuning_results = []

# K-Tuning Section
for k in range(1, 11):
    avg_population = 0
    sample_data = your_data_df.sample(frac=0.1)

    for i, row in sample_data.iterrows():
        lat, lon = row['Latitude'], row['Longitude']
        distances, indices = tree.query([[lat, lon]], k=k)

        weighted_population = 0
        total_weight = 0

        for dist_list, idx_list in zip(distances, indices):
            for dist, idx in zip(dist_list, idx_list):
                pop = geonames_df.iloc[idx]['population']
                log_pop = log(pop + 1)
                distance_threshold = log(pop + 1)

                if dist > distance_threshold:
                    continue

                population_weight = 0.7
                weight = (1 / (dist + 1e-5)) ** 2
                weighted_population += log_pop * weight * population_weight + weight * (1 - population_weight)
                total_weight += weight

        if total_weight > 0:
            avg_population += exp(weighted_population / total_weight)

    avg_population /= len(sample_data)
    tuning_results.append((k, avg_population))

# Convert to DataFrame for easier handling
tuning_df = pd.DataFrame(tuning_results, columns=['k', 'AvgPopulation'])

# Determine the best k
best_k = tuning_df.loc[tuning_df['AvgPopulation'].idxmax(), 'k']

# Initialize array for storing closest populations
closest_populations = np.empty(len(your_data_df))
closest_populations.fill(np.nan)

# Process results
for i, row in enumerate(your_data_df.itertuples()):
    lat, lon = row.Latitude, row.Longitude
    distances, indices = tree.query([[lat, lon]], k=best_k)

    weighted_population = 0
    total_weight = 0

    for dist_list, idx_list in zip(distances, indices):
        for dist, idx in zip(dist_list, idx_list):
            pop = geonames_df.iloc[idx]['population']
            log_pop = log(pop + 1)

            # Variable distance threshold based on log of population
            distance_threshold = log(pop + 1)

            if dist > distance_threshold:
                continue

            population_weight = 0.7  # Between 0 and 1
            weight = (1 / (dist + 1e-5)) ** 2
            weighted_population += log_pop * weight * population_weight + weight * (1 - population_weight)
            total_weight += weight

    if total_weight > 0:
        # Rounding the population to the nearest integer
        closest_populations[i] = np.round(exp(weighted_population / total_weight))

    if i % 1000 == 0:
        print(f"Processed {i + 1} rows.")

# Add closest populations to your DataFrame
your_data_df['Closest_Population'] = closest_populations

# Debugging for KNN Imputation
imputer = KNNImputer(n_neighbors=3)
imputed_values = imputer.fit_transform(your_data_df[['Closest_Population']])
# Rounding the imputed population to the nearest integer
your_data_df['Closest_Population_Imputed'] = np.round(imputed_values)


# Avoid zero population: Set minimum population threshold for imputed values
min_population_threshold = 500  # Minimum population
your_data_df['Closest_Population_Imputed'] = np.maximum(your_data_df['Closest_Population_Imputed'], min_population_threshold)

# Optimize KNN Imputation
# Use only non-zero closest populations for KNN imputation
non_zero_populations = your_data_df[your_data_df['Closest_Population'] > 0][['Closest_Population']]
imputed_values = imputer.fit_transform(non_zero_populations)
your_data_df.loc[your_data_df['Closest_Population'] > 0, 'Closest_Population_Imputed'] = np.round(imputed_values)



zero_imputed_indices = np.where(imputed_values == 0)[0]
if len(zero_imputed_indices) > 0:
    print(f"Zero values imputed at indices {zero_imputed_indices}")

# Debugging before saving the DataFrame
zero_population_rows = your_data_df[
    (your_data_df['Closest_Population'] == 0) | (your_data_df['Closest_Population_Imputed'] == 0)
]
if not zero_population_rows.empty:
    print("Found rows with zero population:")
    print(zero_population_rows)



# Update DataFrame for known cities with online data
known_cities = {
    # Large cities
    'Paris': (2000000, 3000000),
    'London': (8000000, 10000000),

}

for city in known_cities.keys():
    new_population = fetch_city_population(city)
    if new_population:
        your_data_df.loc[your_data_df['City'] == city, 'Closest_Population'] = new_population
        your_data_df.loc[
            your_data_df['City'] == city, 'Closest_Population_Imputed'] = new_population  # Update imputed value as well


# Save the updated DataFrame
your_data_df.to_csv('MainFolder/Datasets/Final_Corrected_Enriched_dataset_with_population_imputed.csv', index=False)

# Histogram
plt.figure(figsize=(10, 6))
sns.histplot(your_data_df['Closest_Population'], bins=50, kde=True)
plt.title('Distribution of Closest Population')
plt.xlabel('Closest Population')
plt.ylabel('Frequency')
plt.savefig('histogram.png')

# Correlation Matrix
numeric_df = your_data_df.select_dtypes(include=['number'])
correlation_matrix = numeric_df.corr()

plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
plt.title('Correlation Matrix')
plt.tight_layout()  # Adjusts the layout
plt.savefig('correlation_matrix.png')




# Scatter plot of latitude and longitude
plt.figure(figsize=(10, 6))

# Create bins for 'Closest_Population'
bins = [0, 100000, 500000, 1000000, 5000000, 10000000, np.inf]
labels = ['<100K', '100K-500K', '500K-1M', '1M-5M', '5M-10M', '>10M']
your_data_df['Population_Bin'] = pd.cut(your_data_df['Closest_Population'], bins=bins, labels=labels, right=False)

# Create a custom color palette
palette = {
    '<100K': 'lightgreen',
    '100K-500K': 'darkgreen',
    '500K-1M': 'blue',
    '1M-5M': 'purple',
    '5M-10M': 'brown',
    '>10M': 'black'
}

sns.scatterplot(
    x='Longitude',
    y='Latitude',
    hue='Population_Bin',
    data=your_data_df,
    palette=palette
)

plt.title('Geographic Distribution of Data Points')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.savefig('Geographic_Distribution_of_Data_Points.png')




# Summary of Analysis
print("\nSummary of Analysis:")
print(f"Total Number of Data Points: {len(your_data_df)}")
print(f"Average Closest Population: {your_data_df['Closest_Population'].mean():.2f}")
print(f"Minimum Closest Population: {your_data_df['Closest_Population'].min():.2f}")
print(f"Maximum Closest Population: {your_data_df['Closest_Population'].max():.2f}")

# If you want to print the correlation matrix
print("Correlation Matrix:")
print(correlation_matrix)



# Summary of Analysis with Enhanced Print Statements
print("\nSummary of Enhanced Analysis:")

# Descriptive statistics
print("\nDescriptive Statistics:")
print(your_data_df[['Closest_Population', 'Closest_Population_Imputed']].describe())

# Missing values
print("\nMissing Values:")
print(your_data_df[['Closest_Population', 'Closest_Population_Imputed']].isna().sum())

# Zero values
print("\nZero Values:")
print((your_data_df[['Closest_Population', 'Closest_Population_Imputed']] == 0).sum())

# Sample data
print("\nSample Data:")
print(your_data_df.sample(5))

# Unique values in key columns (adjust according to your specific columns)
print("\nUnique Values in Key Columns:")
print(f"Unique values in 'Closest_Population': {your_data_df['Closest_Population'].nunique()}")
print(f"Unique values in 'Closest_Population_Imputed': {your_data_df['Closest_Population_Imputed'].nunique()}")

# Any other checks you might find useful can go here

# If you want to print the correlation matrix
print("\nCorrelation Matrix:")
print(correlation_matrix)


# Skewness and Kurtosis
skewness = your_data_df[['Closest_Population', 'Closest_Population_Imputed']].skew()
kurtosis = your_data_df[['Closest_Population', 'Closest_Population_Imputed']].kurt()

# Identifying Outliers
Q1 = your_data_df[['Closest_Population', 'Closest_Population_Imputed']].quantile(0.25)
Q3 = your_data_df[['Closest_Population', 'Closest_Population_Imputed']].quantile(0.75)
IQR = Q3 - Q1

outliers = ((your_data_df[['Closest_Population', 'Closest_Population_Imputed']] < (Q1 - 1.5 * IQR)) |
            (your_data_df[['Closest_Population', 'Closest_Population_Imputed']] > (Q3 + 1.5 * IQR))).sum()

# Print Additional Summary
print("\nAdditional Summary of Enhanced Analysis:")
print(f"Skewness:\n{skewness}")
print(f"Kurtosis:\n{kurtosis}")
print(f"Number of Outliers:\n{outliers}")


# Define thresholds for small, medium, and large populations
small_threshold = 5000
medium_threshold = 50000

# Categorize cities into small, medium, and large
small_cities = your_data_df[your_data_df['Closest_Population_Imputed'] <= small_threshold]
medium_cities = your_data_df[(your_data_df['Closest_Population_Imputed'] > small_threshold) &
                             (your_data_df['Closest_Population_Imputed'] <= medium_threshold)]
large_cities = your_data_df[your_data_df['Closest_Population_Imputed'] > medium_threshold]

# Count the number of cities in each category
num_small_cities = len(small_cities)
num_medium_cities = len(medium_cities)
num_large_cities = len(large_cities)

# Identify 10 most crowded and least crowded cities
most_crowded_cities = your_data_df.nlargest(10, 'Closest_Population_Imputed')
least_crowded_cities = your_data_df.nsmallest(10, 'Closest_Population_Imputed')

# Print the summary
print("\nCity Population Categories:")
print(f"Number of small cities (population <= {small_threshold}): {num_small_cities}")
print(f"Number of medium cities ({small_threshold} < population <= {medium_threshold}): {num_medium_cities}")
print(f"Number of large cities (population > {medium_threshold}): {num_large_cities}")

print("\n10 Most Crowded Cities:")
print(most_crowded_cities[['City', 'Closest_Population_Imputed']])

print("\n10 Least Crowded Cities:")
print(least_crowded_cities[['City', 'Closest_Population_Imputed']])
