from ortools.linear_solver import pywraplp
import networkx as nx
import folium
import random
import webbrowser
import os
import json
import datetime


def create_RCL(G, centers, alpha):
    # Calculate the distances from each node to its closest center
    closest_distances = {}
    for node in G.nodes():
        closest_distance = min(
            [precomputed_distances[str(node)][str(center)] for center in centers]) if centers else float('inf')
        closest_distances[node] = closest_distance

    # Sort the nodes by their closest distances in ascending order
    sorted_nodes = sorted(G.nodes(), key=lambda x: closest_distances[x])

    # Select the top-alpha percent nodes to form the RCL
    rcl_size = int(alpha * len(G.nodes()))
    RCL = sorted_nodes[:rcl_size]

    return RCL



def calculate_delta(G, old_center, new_center, centers):
    delta = 0
    for node in G.nodes():
        # Skip the centers; they are not affected
        if node in centers:
            continue

        old_distance = precomputed_distances[str(node)][str(old_center)]
        new_distance = precomputed_distances[str(node)][str(new_center)]

        # Calculate the closest distance to the existing centers for this node
        closest_distance = min([precomputed_distances[str(node)][str(center)] for center in centers if center != old_center])

        # Check how this swap would affect the maximum distance
        if old_distance == closest_distance:
            # The old center was contributing to the maximum distance.
            # So, consider the new center and the second closest distance.
            delta += max(0, max(new_distance, closest_distance) - old_distance)

        elif new_distance < closest_distance:
            # The new center offers a shorter distance than any existing center.
            delta += new_distance - closest_distance

    return delta




# One common approach to local search in the k-center problem is to explore
def local_search_optimized(G, centers):
    best_centers = centers.copy()
    best_objective_value = calculate_objective_value(G, best_centers)

    improved = True
    while improved:
        improved = False
        for i in range(len(best_centers)):
            for node in set(G.nodes()) - set(best_centers):
                # Swap and calculate only the affected distances
                old_center = best_centers[i]
                best_centers[i] = node
                delta = calculate_delta(G, old_center, node, best_centers)

                # Update if improvement found
                if delta < 0:
                    best_objective_value += delta
                    improved = True
                    break
                else:
                    best_centers[i] = old_center  # Revert the change

            if improved:
                break

    return best_centers




def calculate_objective_value(G, centers):
    # Calculate the maximum distance from any node to its closest center
    max_distance = 0
    for node in G.nodes():
        closest_distance = min([precomputed_distances[str(node)][str(center)] for center in centers])
        max_distance = max(max_distance, closest_distance)

    return max_distance






# Main Code
# Load precomputed shortest distances
json_file_path = "MainFolder/Datasets/ShortestDistances/all_shortest_distances_with_nodes_for_condensed_graph.json"
with open(json_file_path, 'r') as f:
    precomputed_data = json.load(f)
precomputed_distances = {i: precomputed_data[i]['distances'] for i in precomputed_data}





# Read the GML file
file_path = "MainFolder/Datasets/condensed_west_europe_Cleaned.gml"
G = nx.read_gml(file_path, label="id")

# GRASP parameters
alpha = 0.2
iterations = 100
N = 10

best_solution = []
best_objective_value = float('inf')
early_stopping_rounds = 10
rounds_without_improvement = 0



# Capture the start time and write to file
start_time = datetime.datetime.now()
print("Start Time: ", start_time)


for _ in range(iterations):
    # Greedy Randomized Phase
    centers = []
    while len(centers) < N:
        RCL = create_RCL(G, centers, alpha)
        new_center = random.choice(RCL)
        centers.append(new_center)

    # Local Search
    centers = local_search_optimized(G, centers)  # Note the corrected function name

    # Calculate objective value
    objective_value = calculate_objective_value(G, centers)

    if objective_value < best_objective_value:
        best_solution = centers
        best_objective_value = objective_value
        rounds_without_improvement = 0  # Reset the counter
    else:
        rounds_without_improvement += 1

    if rounds_without_improvement >= early_stopping_rounds:
        print("Stopped early.")
        break

print("Best CDN centers:", best_solution)
print("Best objective value:", best_objective_value)






# Generate a unique name for the map and text files based on parameters
file_suffix = f"{len(G.nodes())}_Nodes_{N}_CDNs_'k_center'_{os.path.basename(file_path).replace('.gml', '')}"
map_file_name = f"MainFolder/Map/map_{file_suffix}.html"
text_file_name = f"MainFolder/Map/results_{file_suffix}.txt"



# Open text file for writing results
with open(text_file_name, 'w') as text_file:


    text_file.write(f"Start Time: {start_time}\n")


    # Capture the end time and write to file
    end_time = datetime.datetime.now()
    print("End Time: ", end_time)
    text_file.write(f"End Time: {end_time}\n")

    # Calculate and print the duration
    duration = end_time - start_time
    print("Total Time: ", duration)
    text_file.write(f"Total Time: {duration}\n")
    # write the number of CDNs in the text file
    text_file.write(f"Number of CDNs: {N}\n")

    print('Optimal solution found')
    text_file.write("Optimal solution found\n")


    # Create Folium map for visualization
    m = folium.Map(location=[47.36667, 8.55], zoom_start=5)

    # Add edges for the real topology links in light gray dashed lines
    for i, j, data in G.edges(data=True):
        coord_i = (G.nodes[i]['Latitude'], G.nodes[i]['Longitude'])
        coord_j = (G.nodes[j]['Latitude'], G.nodes[j]['Longitude'])
        folium.PolyLine([coord_i, coord_j], color='gray', weight=2, dash_array='5').add_to(m)

    color_map = {}  # Map from CDN centers to their unique colors

    # Create a dictionary to store the shortest distance from each node to its corresponding CDN
    shortest_distances = {}

     # First, determine the shortest distance for each node to its CDN center
    for i, data in G.nodes(data=True):
        for j, data_j in G.nodes(data=True):
            if y[i, j].solution_value() == 1:
                distance = precomputed_distances[str(i)].get(str(j), float('inf'))
                shortest_distances[j] = distance

    # Then, add all served nodes with blue markers with tooltips
    for i, data in G.nodes(data=True):
        if x[i].solution_value() == 0:  # Only add if it's not a CDN center
            distance = shortest_distances.get(i, 'Unknown')
            folium.CircleMarker(
                location=[data['Latitude'], data['Longitude']],
                radius=4,
                color='blue',
                fill=True,
                fill_color='blue',
                fill_opacity=0.7,
                tooltip=f"Node: {data['label']}, Shortest Distance to CDN: {distance} km"
            ).add_to(m)

    # Then, add CDN centers and nodes they serve with red markers
    for i, data in G.nodes(data=True):
        if x[i].solution_value() == 1:
            random_color = "#{:02x}{:02x}{:02x}".format(random.randint(0, 128),
                                                        random.randint(0, 128),
                                                        random.randint(0, 128))
            color_map[i] = random_color

            print(f"CDN center at node {i}, Location: {data['label']}")
            folium.Marker([data['Latitude'], data['Longitude']], icon=folium.Icon(color='red'),
                          tooltip=f"CDN Center: {data['label']}").add_to(m)

        for j, data_j in G.nodes(data=True):
            if y[i, j].solution_value() == 1:
                path = nx.shortest_path(G, source=i, target=j, weight='weight')
                coordinates = [(G.nodes[node]['Latitude'], G.nodes[node]['Longitude']) for node in path]
                distance = precomputed_distances[str(i)].get(str(j), float('inf'))  # Update here
                text_line = f"Node {j} is served by {i}, Distance: {round(distance, 1)} km"
                print(text_line)
                text_file.write(text_line + "\n")
                folium.PolyLine(coordinates, color=color_map.get(i, 'black'), weight=2.5).add_to(m)




# Save the Folium map
full_map_file_path = os.path.abspath(map_file_name)
m.save(full_map_file_path)

# Open the map in Google Chrome
chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'  # Windows
webbrowser.get(chrome_path).open(f'file://{full_map_file_path}', new=2)

