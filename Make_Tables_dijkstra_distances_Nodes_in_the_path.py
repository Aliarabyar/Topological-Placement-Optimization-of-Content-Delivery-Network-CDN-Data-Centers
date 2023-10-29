import os
import json
import heapq
import networkx as nx
from math import radians, sin, cos, sqrt, atan2


# Function to calculate haversine distance between two coordinates
def haversine_distance(coord1, coord2):
    R = 6371  # Earth radius in kilometers
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


# Function to add weights to the edges in the graph
def add_edge_weights_to_graph(G):
    for i, j, data in G.edges(data=True):
        coord_i = (G.nodes[i]['Latitude'], G.nodes[i]['Longitude'])
        coord_j = (G.nodes[j]['Latitude'], G.nodes[j]['Longitude'])
        distance = haversine_distance(coord_i, coord_j)
        G[i][j]['weight'] = distance  # Add as an attribute to the edge


# Function to calculate shortest distances and paths using Dijkstra's algorithm
def dijkstra_distances_and_paths(G, source):
    distances = {node: float('inf') for node in G.nodes()}
    distances[source] = 0
    predecessors = {node: None for node in G.nodes()}
    queue = [(0, source)]

    while queue:
        current_distance, current_node = heapq.heappop(queue)

        if current_distance > distances[current_node]:
            continue

        for neighbor, data in G[current_node].items():
            distance = current_distance + G[current_node][neighbor]['weight']

            if distance < distances[neighbor]:
                distances[neighbor] = distance
                predecessors[neighbor] = current_node
                heapq.heappush(queue, (distance, neighbor))

    # Reconstruct paths
    paths = {}
    for node in G.nodes():
        if predecessors[node] is None:
            paths[node] = []
        else:
            path = []
            current = node
            while current is not None:
                path.insert(0, current)
                current = predecessors[current]
            paths[node] = path

    return distances, paths


# Read the GML file
file_path = "MainFolder/Datasets/interconnect_Cleaned.gml"  # condensed_west_europe_Cleaned or interconnect_Cleaned
G = nx.read_gml(file_path, label="id")

# Add weights to the graph edges
add_edge_weights_to_graph(G)

# Create folder for JSON files if it doesn't exist
json_folder_path = "MainFolder/Datasets/ShortestDistances"
if not os.path.exists(json_folder_path):
    os.makedirs(json_folder_path)

# Initialize an empty dictionary to hold all shortest distances
all_shortest_distances = {}

# Precompute shortest distances and paths
for i in G.nodes():
    shortest_distances, paths = dijkstra_distances_and_paths(G, i)
    all_shortest_distances[str(i)] = {'distances': shortest_distances, 'paths': paths}


# Store all shortest distances in a single JSON file
json_file_path = os.path.join(json_folder_path, "all_shortest_distances_with_nodes.json")

with open(json_file_path, 'w') as f:
    json.dump(all_shortest_distances, f, indent=4)
