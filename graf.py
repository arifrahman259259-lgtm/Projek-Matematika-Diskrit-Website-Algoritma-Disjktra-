def build_graph_from_json(json_path):
    import json, os
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None

    name_set = set()
    for a, lst in data.items():
        name_set.add(str(a))
        for item in lst:
            if isinstance(item, (list, tuple)) and len(item) >= 1:
                name_set.add(str(item[0]))

    names = sorted(list(name_set))

    # Optional manual positions map (scaled)
    pos = {
        "T1": (0, 10), "T2": (1, 9), "T3": (2, 8), "T4": (3, 7),
        "T5": (3, 6), "T6": (4, 9), "T7": (4, 5), "T8": (5, 5),
        "T9": (6, 5), "T10": (5, 4), "T11": (5, 3), "T12": (5, 2),
        "T13": (4, 2), "T14": (7, 5), "T15": (6, 3), "T16": (5, 1),
        "T17": (4, 0), "T18": (3, 1), "T19": (7, 3), "T20": (6, 6),
        "T21": (8, 2), "T22": (2, 9), "T23": (9, 1), "T24": (8, 0),
        "T25": (1, -1),
    }
    scale, base_x, base_y = 60, 100, 100
    titik = []
    for i, name in enumerate(names):
        if name in pos:
            px, py = pos[name]
            x = base_x + px * scale
            y = base_y + py * scale
        else:
            cols, dx, dy = 8, 60, 60
            x = 100 + (i % cols) * dx
            y = 100 + (i // cols) * dy
        titik.append({"id": name, "name": name, "x": x, "y": y})

    garis = []
    seen = set()
    for a, lst in data.items():
        for item in lst:
            b = str(item[0])
            w = float(item[1]) if len(item) > 1 else 0.0
            key = tuple(sorted([str(a), b]))
            if key in seen:
                continue
            seen.add(key)
            garis.append({"a": str(a), "b": b, "w": w})

    return {"nama": "Graf 1", "titik": titik, "garis": garis}

def _draw_networkx(graph_data, pos):
    import networkx as nx
    import matplotlib.pyplot as plt
    G = nx.Graph()
    for node, edges in graph_data.items():
        for neighbor, weight in edges:
            G.add_edge(node, neighbor, weight=weight)
    plt.figure(figsize=(10, 10))
    nx.draw_networkx_nodes(G, pos, node_size=300, node_color="purple")
    nx.draw_networkx_labels(G, pos, font_color="white", font_size=8)
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.6)
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=7)
    plt.axis('off'); plt.tight_layout(); plt.show()

# ============================
# 1. DATA GRAPH
# ============================
graph_data = {
    "T1":  [("T2", 27), ("T25", 43)],
    "T2":  [("T1", 27), ("T3", 14)],
    "T3":  [("T4", 19), ("T2", 14)],
    "T4":  [("T3", 19), ("T5", 29), ("T20", 89)],
    "T5":  [("T4", 29), ("T6", 28), ("T7", 30), ("T18", 22)],
    "T6":  [("T5", 28)],
    "T7":  [("T5", 30), ("T14", 110), ("T8", 28)],
    "T8":  [("T7", 28), ("T9", 10), ("T10", 13)],
    "T9":  [("T8", 13)],
    "T10": [("T8", 13), ("T11", 43)],
    "T11": [("T10", 43), ("T12", 55)],
    "T12": [("T11", 55), ("T13", 19), ("T14", 29)],
    "T13": [("T12", 19)],
    "T14": [("T12", 29), ("T15", 32), ("T7", 110)],
    "T15": [("T14", 32), ("T16", 53), ("T19", 29)],
    "T16": [("T15", 53), ("T17", 18)],
    "T17": [("T16", 18), ("T18", 15)],
    "T18": [("T17", 15), ("T5", 22)],
    "T19": [("T15", 29), ("T20", 23), ("T21", 30)],
    "T20": [("T19", 23), ("T4", 89)],
    "T21": [("T19", 30), ("T22", 12), ("T23", 31)],
    "T22": [("T21", 12), ("T2", 98)],
    "T23": [("T21", 31), ("T24", 49)],
    "T24": [("T23", 49), ("T25", 18)],
    "T25": [("T24", 18), ("T1", 43)]
}

# ============================
# 2. MANUAL NODE POSITION (AGAR MIRIP PETA)
# ============================
pos = {
    "T1": (0, 10),
    "T2": (1, 9),
    "T3": (2, 8),
    "T4": (3, 7),
    "T5": (3, 6),
    "T6": (4, 9),
    "T7": (4, 5),
    "T8": (5, 5),
    "T9": (6, 5),
    "T10": (5, 4),
    "T11": (5, 3),
    "T12": (5, 2),
    "T13": (4, 2),
    "T14": (7, 5),
    "T15": (6, 3),
    "T16": (5, 1),
    "T17": (4, 0),
    "T18": (3, 1),
    "T19": (7, 3),
    "T20": (6, 6),
    "T21": (8, 2),
    "T22": (2, 9),
    "T23": (9, 1),
    "T24": (8, 0),
    "T25": (1, -1),
}

# ============================
# 3. BUILD GRAPH
# ============================
if __name__ == "__main__":
    try:
        _draw_networkx(graph_data, pos)
    except Exception:
        pass
