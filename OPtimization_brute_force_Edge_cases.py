import networkx as nx
import json
import itertools
import folium
import random
import webbrowser
import os
import datetime

# Modified version of calculate_objective_value to handle edge cases
def calculate_objective_value_with_fallback(cdn_centers, precomputed_distances, G):
    total_distance = 0
    for j in G.nodes():
        min_distance = float('inf')
        for i in cdn_centers:
            if nx.has_path(G, i, j):
                distance = precomputed_distances.get(str(i), {}).get(str(j), None)
                if distance is None:
                    # Fallback: Compute the distance using NetworkX for edge cases
                    distance = nx.shortest_path_length(G, source=i, target=j, weight='weight')
                min_distance = min(min_distance, distance)
            else:
                print(f"No path exists between {i} and {j}.")
        if min_distance == float('inf'):
            return float('inf')  # If no path exists, return infinity
        total_distance += min_distance
    return total_distance

# Modified version of run_brute_force_on_graph to handle edge cases
def run_brute_force_on_graph_with_fallback(G, num_cdn, precomputed_distances=None):
    best_objective_value = float('inf')
    best_cdn_centers = None
    all_possible_combinations = itertools.combinations(G.nodes(), num_cdn)
    for cdn_centers in all_possible_combinations:
        objective_value = calculate_objective_value_with_fallback(cdn_centers, precomputed_distances if precomputed_distances else {}, G)
        if objective_value < best_objective_value:
            best_objective_value = objective_value
            best_cdn_centers = cdn_centers
    return best_cdn_centers, best_objective_value




# Edge Case 1: Minimal Network
print("Edge Case 1: Minimal Network")
G1 = nx.Graph()
G1.add_edge(0, 1, weight=10)
result_1 = run_brute_force_on_graph_with_fallback(G1, 1)  # Use the updated function
print("Brute Force:", result_1)

# Edge Case 2: Fully Connected Network
print("\nEdge Case 2: Fully Connected Network")
G2 = nx.complete_graph(5)
for u, v in G2.edges():
    G2[u][v]['weight'] = 10
result_2 = run_brute_force_on_graph_with_fallback(G2, 2)  # Use the updated function
print("Brute Force:", result_2)

# Edge Case 3: Sparse Network
print("\nEdge Case 3: Sparse Network")
G3 = nx.Graph()
G3.add_edges_from([(0, 1, {'weight': 10}), (2, 3, {'weight': 10})])
result_3 = run_brute_force_on_graph_with_fallback(G3, 1)  # Use the updated function
print("Brute Force:", result_3)

# Read the GML file
file_path = "MainFolder/Datasets/italy_network.gml"
G = nx.read_gml(file_path, label="id")

# Load precomputed shortest distances and paths from JSON file
json_file_path = "MainFolder/Datasets/ShortestDistances/all_shortest_distances_with_nodes_for_condensed_graph.json"
with open(json_file_path, 'r') as f:
    precomputed_data = json.load(f)
precomputed_distances = {i: precomputed_data[i]['distances'] for i in precomputed_data if i in map(str, G.nodes())}

# Maximum number of CDN centers
N = 4

# Initialize variables to keep track of the best solution
best_objective_value = float('inf')
best_cdn_centers = None

# Enumerate all possible combinations of N CDN centers
all_possible_combinations = itertools.combinations(G.nodes(), N)

# Capture the start time
start_time = datetime.datetime.now()
print("Start Time: ", start_time)

# Brute-force approach for main graph
for cdn_centers in all_possible_combinations:
    objective_value = calculate_objective_value_with_fallback(cdn_centers, precomputed_distances,
                                                              G)  # use the modified function
    if objective_value < best_objective_value:
        best_objective_value = objective_value
        best_cdn_centers = cdn_centers

# Capture the end time
end_time = datetime.datetime.now()
print("End Time: ", end_time)

# Calculate and print the duration
duration = end_time - start_time
print("Total Time: ", duration)


# print the selected CDN centers
print("Best CDN centers: ", best_cdn_centers)
# print the objective value
print("Best objective value: ", best_objective_value)

# Generate a unique name for the map and text files based on parameters
file_suffix = f"{len(G.nodes())}_Nodes_{N}_CDNs_'BruteForce'_{os.path.basename(file_path).replace('.gml', '')}"
map_file_name = f"MainFolder/Map/map_{file_suffix}.html"
text_file_name = f"MainFolder/Map/results_{file_suffix}.txt"

# Open text file for writing results
with open(text_file_name, 'w') as text_file:
    text_file.write(f"Start Time: {start_time}\n")
    text_file.write(f"End Time: {end_time}\n")
    text_file.write(f"Total Time: {duration}\n")
    text_file.write(f"Number of CDNs: {N}\n")
    text_file.write(f"Best CDN centers: {best_cdn_centers}\n")
    text_file.write(f"Best objective value: {best_objective_value}\n")

    # Create Folium map for visualization
    m = folium.Map(location=[47.36667, 8.55], zoom_start=5)

    # Add edges for the real topology links in light gray dashed lines
    for i, j, data in G.edges(data=True):
        coord_i = (G.nodes[i]['Latitude'], G.nodes[i]['Longitude'])
        coord_j = (G.nodes[j]['Latitude'], G.nodes[j]['Longitude'])
        folium.PolyLine([coord_i, coord_j], color='gray', weight=2, dash_array='5').add_to(m)

    # Add all served nodes with blue markers with tooltips
    for i, data in G.nodes(data=True):
        if i not in best_cdn_centers:  # Only add if it's not a CDN center
            folium.CircleMarker(
                location=[data['Latitude'], data['Longitude']],
                radius=4,
                color='blue',
                fill=True,
                fill_color='blue',
                fill_opacity=0.7,
                tooltip=f"Node: {data['label']}"
            ).add_to(m)

    # Then, add CDN centers with red markers
    for i in best_cdn_centers:
        data = G.nodes[i]
        folium.Marker([data['Latitude'], data['Longitude']], icon=folium.Icon(color='red'),
                      tooltip=f"CDN Center: {data['label']}").add_to(m)

        # Create a dictionary to store the shortest distance from each node to its corresponding CDN
        shortest_distances = {}

        # First, determine the shortest distance for each node to its CDN center
        for j in G.nodes():
            min_distance = float('inf')
            serving_cdn = None
            for i in best_cdn_centers:
                distance = precomputed_distances[str(i)].get(str(j), float('inf'))
                if distance < min_distance:
                    min_distance = distance
                    serving_cdn = i
            shortest_distances[j] = (min_distance, serving_cdn)

        color_map = {}  # Map from CDN centers to their unique colors

        # Then, add colorful edges connecting CDN centers to the nodes they serve
        for j, (min_distance, serving_cdn) in shortest_distances.items():
            data_j = G.nodes[j]
            data_i = G.nodes[serving_cdn]
            random_color = "#{:02x}{:02x}{:02x}".format(random.randint(0, 128), random.randint(0, 128),
                                                        random.randint(0, 128))
            color_map[serving_cdn] = random_color
            coordinates = [(data_i['Latitude'], data_i['Longitude']), (data_j['Latitude'], data_j['Longitude'])]
            folium.PolyLine(coordinates, color=color_map.get(serving_cdn, 'black'), weight=2.5).add_to(m)

            # Print to console and write to text file
            text_line = f"Node {j} is served by CDN {serving_cdn}, Distance: {round(min_distance, 1)} km"
            print(text_line)
            text_file.write(text_line + "\n")

    # Save the Folium map
    full_map_file_path = os.path.abspath(map_file_name)
    m.save(full_map_file_path)

    # Open the map in Google Chrome
    chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'  # Windows
    webbrowser.get(chrome_path).open(f'file://{full_map_file_path}', new=2)
