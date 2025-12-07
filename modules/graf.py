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

def load_coordinates_from_kmz(kmz_path):
    """Memuat koordinat GPS dari file KMZ"""
    import zipfile
    import xml.etree.ElementTree as ET
    
    try:
        with zipfile.ZipFile(kmz_path, 'r') as kmz:
            for name in kmz.namelist():
                if name.endswith('.kml'):
                    kml_content = kmz.read(name).decode('utf-8')
                    root = ET.fromstring(kml_content)
                    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
                    
                    placemarks = root.findall('.//kml:Placemark', ns)
                    coordinates = {}
                    
                    for pm in placemarks:
                        name_elem = pm.find('kml:name', ns)
                        if name_elem is not None:
                            name = name_elem.text.strip()
                            point = pm.find('.//kml:Point/kml:coordinates', ns)
                            if point is not None:
                                coords = point.text.strip().split(',')
                                if len(coords) >= 2:
                                    lon, lat = float(coords[0]), float(coords[1])
                                    coordinates[name] = (lon, lat)
                    return coordinates
    except Exception:
        return {}
    return {}

def gps_to_canvas_coords(gps_coords, base_x=150, base_y=100, scale=600):
    """Konversi koordinat GPS ke koordinat canvas"""
    if not gps_coords:
        return {}
    
    # Hitung bounding box
    lons = [c[0] for c in gps_coords.values()]
    lats = [c[1] for c in gps_coords.values()]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    
    # Normalisasi dan konversi ke canvas
    canvas_coords = {}
    for name, (lon, lat) in gps_coords.items():
        # Normalisasi ke 0-1
        norm_x = (lon - min_lon) / (max_lon - min_lon) if max_lon != min_lon else 0.5
        norm_y = (lat - min_lat) / (max_lat - min_lat) if max_lat != min_lat else 0.5
        
        # Konversi ke koordinat canvas (flip Y karena canvas Y ke bawah)
        x = base_x + norm_x * scale
        y = base_y + (1 - norm_y) * scale  # Flip Y axis
        canvas_coords[name] = (x, y)
    
    return canvas_coords

def build_graph_with_perumahan_layout(json_path, nama_graf="Graf Perumahan"):
    """Membangun graf dari JSON dengan layout perumahan sesuai peta asli"""
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
    
    # Coba muat koordinat dari KMZ (Google Maps)
    kmz_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Peta Algoritma Dijsktra.kmz")
    gps_coords = {}
    if os.path.exists(kmz_path):
        gps_coords = load_coordinates_from_kmz(kmz_path)
    
    # Konversi GPS ke canvas coordinates
    canvas_coords = gps_to_canvas_coords(gps_coords, base_x=150, base_y=100, scale=600)
    
    # Mapping nama dari KMZ (Titik 1, Titik 2, ...) ke T1, T2, ...
    node_positions = {}
    import re
    for kmz_name, (x, y) in canvas_coords.items():
        # Ekstrak angka dari "Titik 1" -> "T1"
        match = re.search(r'(\d+)', kmz_name)
        if match:
            node_id = f"T{match.group(1)}"
            node_positions[node_id] = (x, y)
    
    # Fallback untuk node yang tidak ada di KMZ (gunakan layout manual)
    base_x, base_y = 150, 100
    grid = 60
    
    # Pastikan semua node T1-T25 ada
    for i in range(1, 26):
        node_id = f"T{i}"
        if node_id not in node_positions:
            # Gunakan posisi default berdasarkan struktur peta
            if i == 1:
                node_positions[node_id] = (base_x, base_y)
            elif i == 2:
                node_positions[node_id] = (base_x, base_y + grid * 1.8)
            elif i == 3:
                node_positions[node_id] = (base_x, base_y + grid * 3.6)
            elif i == 4:
                node_positions[node_id] = (base_x, base_y + grid * 5.4)
            elif i == 5:
                node_positions[node_id] = (base_x, base_y + grid * 7.2)
            elif i == 6:
                node_positions[node_id] = (base_x + grid * 2, base_y + grid * 7.0)
            elif i == 7:
                node_positions[node_id] = (base_x + grid * 9, base_y + grid * 6.5)
            elif i == 8:
                node_positions[node_id] = (base_x + grid * 6.5, base_y + grid * 7.0)
            elif i == 9:
                node_positions[node_id] = (base_x + grid * 7.2, base_y + grid * 7.2)
            elif i == 10:
                node_positions[node_id] = (base_x + grid * 6.5, base_y + grid * 8.0)
            elif i == 11:
                node_positions[node_id] = (base_x + grid * 6.5, base_y + grid * 9.0)
            elif i == 12:
                node_positions[node_id] = (base_x + grid * 6.5, base_y + grid * 10.0)
            elif i == 13:
                node_positions[node_id] = (base_x + grid * 6, base_y + grid * 10.5)
            elif i == 14:
                node_positions[node_id] = (base_x + grid * 9, base_y + grid * 8.5)
            elif i == 15:
                node_positions[node_id] = (base_x + grid * 9, base_y + grid * 9.5)
            elif i == 16:
                node_positions[node_id] = (base_x + grid * 3, base_y + grid * 10.0)
            elif i == 17:
                node_positions[node_id] = (base_x + grid * 3, base_y + grid * 9.0)
            elif i == 18:
                node_positions[node_id] = (base_x + grid * 3, base_y + grid * 8.0)
            elif i == 19:
                node_positions[node_id] = (base_x + grid * 9, base_y + grid * 10.5)
            elif i == 20:
                node_positions[node_id] = (base_x + grid * 7, base_y + grid * 6.0)
            elif i == 21:
                node_positions[node_id] = (base_x + grid * 9, base_y + grid * 11.5)
            elif i == 22:
                node_positions[node_id] = (base_x + grid * 2.5, base_y + grid * 2.5)
            elif i == 23:
                node_positions[node_id] = (base_x + grid * 8, base_y + grid * 12.5)
            elif i == 24:
                node_positions[node_id] = (base_x + grid * 5, base_y + grid * 12.5)
            elif i == 25:
                node_positions[node_id] = (base_x + grid * 2, base_y + grid * 12.5)
    
    # Buat titik dengan posisi yang sudah ditentukan
    titik = []
    for name in names:
        if name in node_positions:
            x, y = node_positions[name]
        else:
            # Fallback: posisi default untuk node yang belum didefinisikan
            idx = names.index(name)
            cols, dx, dy = 8, 60, 60
            x = base_x + (idx % cols) * dx
            y = base_y + (idx // cols) * dy
        titik.append({"id": name, "name": name, "x": float(x), "y": float(y)})
    
    # Buat garis dari data JSON
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
    
    return {"nama": nama_graf, "titik": titik, "garis": garis}

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

if __name__ == "__main__":
    try:
        _draw_networkx(graph_data, pos)
    except Exception:
        pass
