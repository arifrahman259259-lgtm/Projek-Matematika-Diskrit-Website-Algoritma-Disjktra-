import json, sqlite3, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from importlib.machinery import SourceFileLoader
from urllib.parse import urlparse, parse_qs

algo = SourceFileLoader("algomod", "algoritma dijsktra.py").load_module()
grafmod = SourceFileLoader("grafmod", "graf.py").load_module()

DB_PATH = "graf.db"

def db_init():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS graphs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            dibuat TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            graph_id INTEGER,
            id TEXT,
            nama TEXT,
            x REAL,
            y REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            graph_id INTEGER,
            a TEXT,
            b TEXT,
            w REAL
        )
    """)
    conn.commit(); conn.close()

def db_count_graphs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    cnt = c.execute("SELECT COUNT(*) FROM graphs").fetchone()[0]
    conn.close()
    return cnt

def db_insert_graph(nama, titik, garis):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO graphs(nama) VALUES (?)", (nama or "Tanpa Nama",))
    gid = c.lastrowid
    for n in titik:
        c.execute("INSERT INTO nodes(graph_id,id,nama,x,y) VALUES (?,?,?,?,?)",
                  (gid, str(n.get("id")), str(n.get("name")), float(n.get("x",0)), float(n.get("y",0))))
    for e in garis:
        c.execute("INSERT INTO edges(graph_id,a,b,w) VALUES (?,?,?,?)",
                  (gid, str(e.get("a")), str(e.get("b")), float(e.get("w",0))))
    conn.commit(); conn.close()
    return gid

def db_daftar_graf():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    rows = c.execute("SELECT id, nama, dibuat FROM graphs ORDER BY id DESC").fetchall()
    conn.close()
    return [{"id": r[0], "nama": r[1], "dibuat": r[2]} for r in rows]

def db_muat_graf(graph_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    nodes = c.execute("SELECT id, nama, x, y FROM nodes WHERE graph_id=?", (graph_id,)).fetchall()
    edges = c.execute("SELECT a, b, w FROM edges WHERE graph_id=?", (graph_id,)).fetchall()
    conn.close()
    titik = [{"id": r[0], "name": r[1], "x": r[2], "y": r[3]} for r in nodes]
    garis = [{"a": r[0], "b": r[1], "w": r[2]} for r in edges]
    return {"titik": titik, "garis": garis}

def db_find_graph_by_name(nama):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    row = c.execute("SELECT id FROM graphs WHERE nama=?", (nama,)).fetchone()
    conn.close()
    return row[0] if row else None

 

 

def _load_list_graf_json():
    try:
        base_dir = os.path.dirname(__file__)
        file_path = os.path.join(base_dir, "list graf.json")
        data = grafmod.build_graph_from_json(file_path)
        return data
    except Exception:
        return None

def preload_from_file():
    data = _load_list_graf_json()
    if data:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE graphs SET nama=? WHERE nama LIKE ?", (data.get("nama"), "Graf JSON Awal%"))
            conn.commit(); conn.close()
        except Exception:
            pass
        existing = db_find_graph_by_name(data.get("nama"))
        if not existing:
            db_insert_graph(data.get("nama"), data.get("titik", []), data.get("garis", []))
    if db_count_graphs() == 0:
        contoh_titik = [
            {"id": "1", "name": "A", "x": 120, "y": 120},
            {"id": "2", "name": "B", "x": 180, "y": 160},
            {"id": "3", "name": "C", "x": 240, "y": 180}
        ]
        contoh_garis = [
            {"a": "1", "b": "2", "w": 40},
            {"a": "2", "b": "3", "w": 60}
        ]
        db_insert_graph("Contoh Graf", contoh_titik, contoh_garis)

def jalankan_dijkstra(titik_ids, garis, awal_id, tujuan_id):
    ids = [str(n) for n in titik_ids]
    idx = {v: i for i, v in enumerate(ids)}
    n = len(ids)
    graf = [[0]*n for _ in range(n)]
    for e in garis:
        a, b = idx.get(str(e.get("a"))), idx.get(str(e.get("b")))
        if a is None or b is None: continue
        w = float(e.get("w", 0))
        graf[a][b] = w
        graf[b][a] = w
    s = idx.get(str(awal_id))
    t = idx.get(str(tujuan_id))
    if s is None or t is None:
        return {"path": [], "total": None, "edgePath": []}
    L = algo.dijkstra(graf, s)
    if not L or L[t][0] == float("inf"):
        return {"path": [], "total": None, "edgePath": []}
    path_idx = algo.lintasan(t, L)
    path_ids = [ids[i] for i in path_idx]
    total = L[t][0]
    edge_path = [{"a": path_ids[i], "b": path_ids[i+1]} for i in range(len(path_ids)-1)]
    return {"path": path_ids, "total": total, "edgePath": edge_path}

class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    def do_OPTIONS(self):
        self.send_response(200); self._cors(); self.end_headers()
    def do_GET(self):
        p = urlparse(self.path)
        if p.path == "/graf/daftar":
            data = json.dumps(db_daftar_graf()).encode("utf-8")
            self.send_response(200); self._cors(); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
        if p.path == "/graf/muat":
            qs = parse_qs(p.query)
            gid = int(qs.get("id", ["0"])[0])
            data = json.dumps(db_muat_graf(gid)).encode("utf-8")
            self.send_response(200); self._cors(); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
        self.send_response(404); self._cors(); self.end_headers()
    def do_POST(self):
        p = urlparse(self.path)
        n = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads((self.rfile.read(n) if n > 0 else b"{}").decode("utf-8"))
        except Exception:
            self.send_response(400); self._cors(); self.end_headers(); return
        if p.path == "/dijkstra":
            r = jalankan_dijkstra(body.get("titik", []), body.get("garis", []), body.get("awalId"), body.get("tujuanId"))
            d = json.dumps(r).encode("utf-8")
            self.send_response(200); self._cors(); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(d))); self.end_headers(); self.wfile.write(d); return
        
        self.send_response(404); self._cors(); self.end_headers()

if __name__ == "__main__":
    db_init(); preload_from_file()
    HTTPServer(("localhost", 5000), Handler).serve_forever()
