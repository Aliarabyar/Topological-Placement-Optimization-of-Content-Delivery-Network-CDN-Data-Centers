from ortools.linear_solver import pywraplp
import networkx as nx
import folium
import random
import webbrowser
import os
import json
import datetime




# CDN Limit Constraint
N = 10  # Max number of CDN centers



# Load precomputed shortest distances from JSON file

# all_shortest_distances_for_interconnect_graph
# json_file_path = "MainFolder/Datasets/ShortestDistances/all_shortest_distances_for_interconnect_graph.json"

# all_shortest_distances_for_condensed_graph
json_file_path = "MainFolder/Datasets/ShortestDistances/all_shortest_distances_for_condensed_graph.json"



with open(json_file_path, 'r') as f:
    precomputed_distances = json.load(f)



# Read the GML file

# condensed_west_europe_Cleaned
file_path = "MainFolder/Datasets/condensed_west_europe_Cleaned.gml"

# interconnect_Cleaned
# file_path = "MainFolder/Datasets/interconnect_Cleaned.gml"
G = nx.read_gml(file_path, label="id")


# Initialize the solver
solver = pywraplp.Solver.CreateSolver('CBC')

# Variables
x = {}  # x[i] = 1 if node i is a CDN center, 0 otherwise
y = {}  # y[i][j] = 1 if node j is served by center i, 0 otherwise

# Create variables and constraints
for i in G.nodes():
    x[i] = solver.IntVar(0, 1, f'x_{i}')
    for j in G.nodes():
        y[i, j] = solver.IntVar(0, 1, f'y_{i}_{j}')
        solver.Add(y[i, j] <= x[i])

# New Constraint: Prevent two CDN centers from serving each other
for i in G.nodes():
    for j in G.nodes():
        if i != j:
            solver.Add(y[i, j] + y[j, i] <= 2 - (x[i] + x[j]))




# Single Serving Constraint
for j in G.nodes():
    solver.Add(solver.Sum([y[i, j] for i in G.nodes()]) == 1)


# CDN Limit Constraint
solver.Add(solver.Sum([x[i] for i in G.nodes()]) <= N)



# Objective function

# Objective: Minimize average sum of distances
total_nodes = len(G.nodes())
solver.Minimize(
    (1 / total_nodes) * solver.Sum(
        precomputed_distances[str(i)].get(str(j), float('inf')) * y[i, j]
        for i in G.nodes()
        for j in G.nodes()
    )
)

# print start time
start_time = datetime.datetime.now()
print("Start Time: ", start_time)


# Solve the problem
status = solver.Solve()


# Output results
# If Step 1 is successful, proceed to Step 2
if status == pywraplp.Solver.OPTIMAL:
    print('Step 1: Optimal solution for average distance found.')
    end_time = datetime.datetime.now()
    print("End Time: ", end_time)
    print("Total Time: ", end_time - start_time)
    # Collect CDN centers from Step 1
    selected_cdns = [i for i in G.nodes() if x[i].solution_value() == 1]

    # Initialize the solver for Step 2
    solver_step2 = pywraplp.Solver.CreateSolver('CBC')

    # Variables for Step 2
    y_step2 = {}
    z_step2 = solver_step2.NumVar(0, float('inf'), 'z')  # New Variable: maximum distance

    # Create variables and constraints for Step 2
    for i in selected_cdns:
        for j in G.nodes():
            y_step2[i, j] = solver_step2.IntVar(0, 1, f'y_{i}_{j}')

    # Single Serving Constraint for Step 2
    for j in G.nodes():
        solver_step2.Add(solver_step2.Sum([y_step2[i, j] for i in selected_cdns]) == 1)

    # Constraints to ensure z is greater than or equal to every possible distance
    for i in selected_cdns:
        for j in G.nodes():
            solver_step2.Add(z_step2 >= precomputed_distances[str(i)].get(str(j), float('inf')) * y_step2[i, j])

    # Objective Function for Step 2: Minimize z
    solver_step2.Minimize(z_step2)

    # Solve the problem for Step 2
    status_step2 = solver_step2.Solve()

    # Check and output results for Step 2
    if status_step2 == pywraplp.Solver.OPTIMAL:
        print(f"Step 2: Objective value (maximum distance) = {z_step2.solution_value()}")
    else:
        print('Step 2: Solver ran to completion but did not find an optimal solution.')


    print(f"Objective value = {solver.Objective().Value()}")

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
                radius=3,
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
                print(f"N {j} is served by {i}, : {round(distance, 0)} km")
                folium.PolyLine(coordinates, color=color_map.get(i, 'black'), weight=2.5).add_to(m)


else:
    print('Step 1: Solver ran to completion but did not find an optimal solution.')


file_path = "MainFolder/Map/map.html"
full_file_path = os.path.abspath(file_path)
m.save(full_file_path)

# Open the map in Google Chrome
chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'  # Windows

webbrowser.get(chrome_path).open(f'file://{full_file_path}', new=2)
