import matplotlib
matplotlib.use('TkAgg')

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

# Load the GML file into a NetworkX graph
file_path = "D:\\UPC\\Courses\\FMT\\Needed Datasets\\Data\\MainFolder\\Datasets\\condensed_west_europe_corrected.gml"
G = nx.read_gml(file_path)

# Basic information about the graph
print("Basic Information:")
print(f"Number of Nodes: {len(G.nodes())}")
print(f"Number of Edges: {len(G.edges())}")
print("\n" + "="*50 + "\n")

# Degree Distribution
print("Degree Distribution:")
degrees = [degree for node, degree in G.degree()]
plt.hist(degrees, bins=30, edgecolor='black', alpha=0.7)
plt.title('Degree Distribution')
plt.xlabel('Degree')
plt.ylabel('Number of Nodes')
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.axvline(np.mean(degrees), color='r', linestyle='dashed', linewidth=1)
plt.text(np.mean(degrees)+0.5, 20, 'Mean', rotation=0, color='r')
plt.tight_layout()
plt.show()
print("\n" + "="*50 + "\n")

# Clustering Coefficient
print("Clustering Coefficient:")
clustering_coeffs = nx.clustering(G)
clustering_values = list(clustering_coeffs.values())
plt.hist(clustering_values, bins=30, edgecolor='black', alpha=0.7)
plt.title('Clustering Coefficient Distribution')
plt.xlabel('Clustering Coefficient')
plt.ylabel('Number of Nodes')
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.axvline(np.mean(clustering_values), color='r', linestyle='dashed', linewidth=1)
plt.text(np.mean(clustering_values)+0.05, 20, 'Mean', rotation=0, color='r')
plt.tight_layout()
plt.show()
print("\n" + "="*50 + "\n")

# Centrality Measures
print("Centrality Measures:")

# Betweenness Centrality
print("\nBetweenness Centrality:")
betweenness_centrality = nx.betweenness_centrality(G)
betweenness_values = list(betweenness_centrality.values())
plt.hist(betweenness_values, bins=30, edgecolor='black', alpha=0.7)
plt.title('Betweenness Centrality Distribution')
plt.xlabel('Betweenness Centrality')
plt.ylabel('Number of Nodes')
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()

# Closeness Centrality
print("\nCloseness Centrality:")
closeness_centrality = nx.closeness_centrality(G)
closeness_values = list(closeness_centrality.values())
plt.hist(closeness_values, bins=30, edgecolor='black', alpha=0.7)
plt.title('Closeness Centrality Distribution')
plt.xlabel('Closeness Centrality')
plt.ylabel('Number of Nodes')
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()

print("\n" + "="*50 + "\n")

# Connected Components
print("Connected Components:")
connected_components = list(nx.connected_components(G))
print(f"Number of Connected Components: {len(connected_components)}")
for i, component in enumerate(connected_components):
    print(f"Component {i+1} Size: {len(component)}")
