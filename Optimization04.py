from ortools.linear_solver import pywraplp
import networkx as nx
import folium
import random
import webbrowser
import os
import json
import datetime




# CDN Limit Constraint
N = 2 # Max number of CDN centers





# Load precomputed shortest distances from JSON file

# all_shortest_distances_for_interconnect_graph
# json_file_path = "MainFolder/Datasets/ShortestDistances/all_shortest_distances_with_nodes_for_interconnect_graph.json"

# all_shortest_distances_for_condensed_graph
json_file_path = "MainFolder/Datasets/ShortestDistances/all_shortest_distances_with_nodes_for_condensed_graph.json"



# Load precomputed shortest distances and paths from JSON file
with open(json_file_path, 'r') as f:
    precomputed_data = json.load(f)

# Extract just the distances
precomputed_distances = {i: precomputed_data[i]['distances'] for i in precomputed_data}




# Read the GML file

# condensed_west_europe_Cleaned
file_path = "MainFolder/Datasets/italy_network.gml"

# interconnect_Cleaned
# file_path = "MainFolder/Datasets/interconnect_Cleaned.gml"
G = nx.read_gml(file_path, label="id")





# Initialize the solver
solver = pywraplp.Solver.CreateSolver('SCIP')

# Variables
x = {}  # x[i] = 1 if node i is a CDN center, 0 otherwise
y = {}  # y[i][j] = 1 if node j is served by center i, 0 otherwise



# Create variables and constraints
for i in G.nodes():
    x[i] = solver.IntVar(0, 1, f'x_{i}')
    for j in G.nodes():
        y[i, j] = solver.IntVar(0, 1, f'y_{i}_{j}')
        solver.Add(y[i, j] <= x[i])

# # New Constraint: Prevent two CDN centers from serving each other
# for i in G.nodes():
#     for j in G.nodes():
#         if i != j:
#             solver.Add(y[i, j] + y[j, i] <= 2 - (x[i] + x[j]))




# Single Serving Constraint
for j in G.nodes():
    solver.Add(solver.Sum([y[i, j] for i in G.nodes()]) == 1)


# CDN Limit Constraint
solver.Add(solver.Sum([x[i] for i in G.nodes()]) <= N)


# Objective Function
num_nodes = len(G.nodes())

# Minimize the average distance objective function
objective_terms = []
for i in G.nodes():
    for j in G.nodes():
        distance = precomputed_distances[str(i)][str(j)]  # Assuming your JSON is indexed by strings
        objective_terms.append(distance * y[i, j])
solver.Minimize(solver.Sum(objective_terms))


# Capture the start time and write to file
start_time = datetime.datetime.now()
print("Start Time: ", start_time)

# Solve the problem
status = solver.Solve()

# Generate a unique name for the map and text files based on parameters
file_suffix = f"{len(G.nodes())}_Nodes_{N}_CDNs_'k_means'_{os.path.basename(file_path).replace('.gml', '')}"
map_file_name = f"MainFolder/Map/map_{file_suffix}.html"
text_file_name = f"MainFolder/Map/results_{file_suffix}.txt"

# Open text file for writing results
with open(text_file_name, 'w') as text_file:


    print("MILP Approach")
    text_file.write(f"Start Time: {start_time}\n")

    # Output results
    if status == pywraplp.Solver.OPTIMAL:
        # Capture the end time and write to file
        end_time = datetime.datetime.now()
        print("End Time: ", end_time)
        text_file.write(f"End Time: {end_time}\n")

        # print the list of CDN centers
        print("CDN Centers: ", [i for i in G.nodes() if x[i].solution_value() == 1])



        # Calculate and print the duration
        duration = end_time - start_time
        print("Total Time: ", duration)
        text_file.write(f"Total Time: {duration}\n")
        # write the number of CDNs in the text file
        text_file.write(f"Number of CDNs: {N}\n")

        print('Optimal solution found')
        text_file.write("Optimal solution found\n")

        average_objective_value = solver.Objective().Value() / num_nodes
        print(f"Average Distance = {average_objective_value}")
        text_file.write(f"Average Distance = {average_objective_value}\n")

        print(f"Objective value = {solver.Objective().Value()}")
        text_file.write(f"Objective value = {solver.Objective().Value()}\n")

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


    else:
        print('Solver ran to completion but did not find an optimal solution')



# Save the Folium map
full_map_file_path = os.path.abspath(map_file_name)
m.save(full_map_file_path)

# Open the map in Google Chrome
chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'  # Windows
webbrowser.get(chrome_path).open(f'file://{full_map_file_path}', new=2)

