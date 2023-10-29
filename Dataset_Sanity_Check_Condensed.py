import matplotlib
matplotlib.use('Agg')  # Ensure the 'Agg' backend is used
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

# Load the corrected GML file
G_condensed = nx.read_gml("MainFolder/Datasets/condensed_west_europe_corrected.gml")

# Network Measures
average_clustering_coefficient_condensed = nx.average_clustering(G_condensed)

# Print the number of nodes and edges
print("Number of Nodes (Condensed Dataset):", G_condensed.number_of_nodes())
print("Number of Edges (Condensed Dataset):", G_condensed.number_of_edges())
# Print the new empty line
print()


metrics = {
    "Average Clustering Coefficient": average_clustering_coefficient_condensed
}

if nx.is_connected(G_condensed):
    diameter_condensed = nx.diameter(G_condensed)
    average_shortest_path_length_condensed = nx.average_shortest_path_length(G_condensed)
    metrics["Diameter"] = diameter_condensed
    metrics["Average Shortest Path Length"] = average_shortest_path_length_condensed
else:
    metrics["Diameter"] = "The graph is not connected."
    metrics["Average Shortest Path Length"] = "The graph is not connected."

# Graph Visualization
plt.figure(figsize=(15, 10))
pos_condensed = {node: (data['Longitude'], data['Latitude']) for node, data in G_condensed.nodes(data=True)}
degree_centrality_condensed = nx.degree_centrality(G_condensed)
node_sizes_condensed = [degree_centrality_condensed[node] * 5000 for node in G_condensed.nodes()]
node_colors_condensed = [degree_centrality_condensed[node] for node in G_condensed.nodes()]
nx.draw_networkx(G_condensed, pos_condensed, node_size=node_sizes_condensed, node_color=node_colors_condensed, with_labels=False, edge_color='gray')
plt.title("Graph Visualization based on Longitude and Latitude (Condensed Dataset)")
graph_visualization_path_condensed = "MainFolder/PlotsAndGraphs/graph_visualization_condensed.png"
plt.savefig(graph_visualization_path_condensed)  # Save the figure

# Degree Distribution
plt.figure(figsize=(10, 6))
degree_sequence_condensed = sorted([degree for node, degree in G_condensed.degree()], reverse=True)
plt.hist(degree_sequence_condensed, bins=30)
plt.title("Degree Distribution (Condensed Dataset)")
plt.xlabel("Degree")
plt.ylabel("Frequency")
degree_distribution_path_condensed = "MainFolder/PlotsAndGraphs/degree_distribution_condensed.png"
plt.savefig(degree_distribution_path_condensed)  # Save the figure

# Tables
degree_df_condensed = pd.DataFrame(degree_sequence_condensed, columns=["Degree"]).head(10)
betweenness_centrality_condensed = nx.betweenness_centrality(G_condensed)
betweenness_df_condensed = pd.DataFrame(sorted(betweenness_centrality_condensed.items(), key=lambda x: x[1], reverse=True), columns=["Node", "Betweenness Centrality"]).head(10)



# Print the new empty line
print()

# Print the metrics
print("Metrics (Condensed Dataset):")
for metric, value in metrics.items():
    print(f"{metric}: {value}")


# Print the new empty line
print()

# Print the degree distribution and betweenness centrality
print("Degree Distribution (Condensed Dataset):")
print(degree_df_condensed)

# Print the new empty line
print()

print("Betweenness Centrality (Condensed Dataset):")
print(betweenness_df_condensed)


metrics, graph_visualization_path_condensed, degree_distribution_path_condensed, degree_df_condensed, betweenness_df_condensed
