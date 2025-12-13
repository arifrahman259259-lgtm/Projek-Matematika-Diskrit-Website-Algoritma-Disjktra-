"""
Implementasi Dijkstra dengan logging iterasi yang detail
Menggunakan pendekatan dari dijkstra_db.py tapi tanpa database
"""
import heapq

def dijkstra_with_iterations(titik_ids, garis, awal_id, tujuan_id):
    """
    Menjalankan algoritma Dijkstra dan mengembalikan path, total jarak, dan data iterasi detail
    
    Args:
        titik_ids: List ID titik (contoh: ['T1', 'T2', 'T3'])
        garis: List edge dengan format [{'a': 'T1', 'b': 'T2', 'w': 10}, ...]
        awal_id: ID titik awal
        tujuan_id: ID titik tujuan
    
    Returns:
        dict dengan keys: path, total, edgePath, iterations
    """
    # Validasi input
    if not titik_ids or not garis:
        return {
            "path": [],
            "total": None,
            "edgePath": [],
            "iterations": []
        }
    
    # Konversi ke string dan validasi
    awal_id = str(awal_id)
    tujuan_id = str(tujuan_id)
    ids = [str(n) for n in titik_ids]
    
    # Validasi awal_id dan tujuan_id ada di ids
    if awal_id not in ids or tujuan_id not in ids:
        return {
            "path": [],
            "total": None,
            "edgePath": [],
            "iterations": []
        }
    
    idx = {v: i for i, v in enumerate(ids)}
    
    # Build adjacency list
    graph = {}
    all_nodes = set(ids)
    
    for node in all_nodes:
        graph[node] = []
    
    for e in garis:
        a = str(e.get("a", ""))
        b = str(e.get("b", ""))
        w = float(e.get("w", 0))
        
        if a in idx and b in idx and w > 0:
            if a not in graph:
                graph[a] = []
            graph[a].append((b, w))
            # Undirected graph
            if b not in graph:
                graph[b] = []
            graph[b].append((a, w))
    
    # Inisialisasi
    distances = {node: float('inf') for node in all_nodes}
    previous_nodes = {node: None for node in all_nodes}
    distances[awal_id] = 0
    
    # Priority Queue
    priority_queue = [(0, awal_id)]
    
    # Data iterasi
    iterations = []
    iteration_step = 0
    visited = set()
    
    # Fungsi helper untuk sorting node (numerik jika memungkinkan)
    def sort_nodes(nodes):
        def node_key(node):
            # Coba ekstrak angka dari nama node
            import re
            match = re.search(r'\d+', str(node))
            if match:
                return (0, int(match.group()))
            return (1, str(node))
        return sorted(nodes, key=node_key)
    
    # Log inisialisasi
    initial_row = {'Iterasi': iteration_step, 'Diproses': 'Inisialisasi'}
    for node in sort_nodes(all_nodes):
        dist = distances[node]
        prev = previous_nodes[node]
        if dist == float('inf'):
            initial_row[node] = 'inf (-)'
        else:
            initial_row[node] = f'{int(dist)} ({prev if prev else "-"})'
    iterations.append(initial_row)
    
    # Algoritma utama
    while priority_queue:
        iteration_step += 1
        current_distance, current_node = heapq.heappop(priority_queue)
        
        # Skip jika sudah dikunjungi dengan jarak lebih kecil
        if current_node in visited:
            continue
        
        visited.add(current_node)
        
        # Relaksasi tetangga
        for neighbor, weight in graph.get(current_node, []):
            if neighbor in visited:
                continue
            
            distance = current_distance + weight
            
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(priority_queue, (distance, neighbor))
        
        # Log status setelah relaksasi
        status_row = {'Iterasi': iteration_step, 'Diproses': current_node}
        for node in sort_nodes(all_nodes):
            dist = distances[node]
            prev = previous_nodes[node]
            if dist == float('inf'):
                status_row[node] = 'inf (-)'
            else:
                status_row[node] = f'{int(dist)} ({prev if prev else "-"})'
        iterations.append(status_row)
        
        # Hentikan jika tujuan ditemukan
        if current_node == tujuan_id:
            break
    
    # Build path
    if distances[tujuan_id] == float('inf'):
        return {
            "path": [],
            "total": None,
            "edgePath": [],
            "iterations": iterations
        }
    
    # Reconstruct path
    path = []
    current = tujuan_id
    while current is not None:
        path.insert(0, current)
        current = previous_nodes[current]
    
    # Validasi path dimulai dari awal_id
    if not path or path[0] != awal_id:
        return {
            "path": [],
            "total": None,
            "edgePath": [],
            "iterations": iterations
        }
    
    total = distances[tujuan_id]
    edge_path = [{"a": path[i], "b": path[i+1]} for i in range(len(path)-1)]
    
    return {
        "path": path,
        "total": total,
        "edgePath": edge_path,
        "iterations": iterations
    }

