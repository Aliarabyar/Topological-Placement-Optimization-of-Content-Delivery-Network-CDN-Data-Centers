import matplotlib
matplotlib.use('Agg')  # Ensure the 'Agg' backend is used
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

# Load the GML file
G = nx.read_gml("MainFolder/Datasets/interconnect_Corrected.gml")

# 2. Network Measures
degree_sequence = sorted([degree for node, degree in G.degree()], reverse=True)
average_clustering_coefficient = nx.average_clustering(G)



# Print the number of nodes and edges
print(f"Number of Nodes: {G.number_of_nodes()}")
print(f"Number of Edges: {G.number_of_edges()}")

# Print the new empty line
print()


print(f"Average Clustering Coefficient: {average_clustering_coefficient}")
if nx.is_connected(G):
    diameter = nx.diameter(G)
    average_shortest_path_length = nx.average_shortest_path_length(G)
    print(f"Diameter: {diameter}")
    print(f"Average Shortest Path Length: {average_shortest_path_length}")
else:
    print("The graph is not connected.")

# 1. Graph Visualization
plt.figure(figsize=(15, 10))
pos = {node: (data['Longitude'], data['Latitude']) for node, data in G.nodes(data=True)}
degree_centrality = nx.degree_centrality(G)
node_sizes = [degree_centrality[node] * 5000 for node in G.nodes()]
node_colors = [degree_centrality[node] for node in G.nodes()]
nx.draw_networkx(G, pos, node_size=node_sizes, node_color=node_colors, with_labels=False, edge_color='gray')
plt.title("Graph Visualization based on Longitude and Latitude")
plt.savefig('MainFolder/PlotsAndGraphs/graph_visualization.png')  # Save the figure

# 3. Plots
plt.figure(figsize=(10, 6))
plt.hist(degree_sequence, bins=30)
plt.title("Degree Distribution")
plt.xlabel("Degree")
plt.ylabel("Frequency")
plt.savefig('MainFolder/PlotsAndGraphs/degree_distribution.png')  # Save the figure

# 4. Tables
degree_df = pd.DataFrame(degree_sequence, columns=["Degree"]).head(10)
betweenness_centrality = nx.betweenness_centrality(G)
betweenness_df = pd.DataFrame(sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True), columns=["Node", "Betweenness Centrality"]).head(10)




# Print the new empty line
print()

print("Top 10 nodes by Degree:")
print(degree_df)

# Print the new empty line
print()

print("\nTop 10 nodes by Betweenness Centrality:")
print(betweenness_df)
