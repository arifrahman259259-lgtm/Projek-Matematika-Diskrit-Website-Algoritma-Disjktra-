import json, sqlite3, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from importlib.machinery import SourceFileLoader
from urllib.parse import urlparse, parse_qs

MODULES_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(MODULES_DIR)
algo = SourceFileLoader("algomod", os.path.join(MODULES_DIR, "algoritma dijsktra.py")).load_module()
grafmod = SourceFileLoader("grafmod", os.path.join(MODULES_DIR, "graf.py")).load_module()

DB_PATH = os.path.join(ROOT_DIR, "graf.db")

def db_init():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Aktifkan foreign key constraints
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("""
        CREATE TABLE IF NOT EXISTS graphs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            dibuat TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            graph_id INTEGER NOT NULL,
            id TEXT NOT NULL,
            nama TEXT,
            x REAL NOT NULL,
            y REAL NOT NULL,
            PRIMARY KEY (graph_id, id),
            FOREIGN KEY (graph_id) REFERENCES graphs(id) ON DELETE CASCADE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            graph_id INTEGER NOT NULL,
            a TEXT NOT NULL,
            b TEXT NOT NULL,
            w REAL NOT NULL DEFAULT 0,
            PRIMARY KEY (graph_id, a, b),
            FOREIGN KEY (graph_id) REFERENCES graphs(id) ON DELETE CASCADE
        )
    """)
    # Buat index untuk performa query yang lebih baik
    c.execute("CREATE INDEX IF NOT EXISTS idx_nodes_graph_id ON nodes(graph_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_edges_graph_id ON edges(graph_id)")
    conn.commit()
    conn.close()

def db_count_graphs():
    """Menghitung jumlah graf yang tersimpan"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        cnt = c.execute("SELECT COUNT(*) FROM graphs").fetchone()[0]
        return cnt
    finally:
        conn.close()

def db_insert_graph(nama, titik, garis):
    """Menyimpan graf baru ke database secara permanen"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("PRAGMA foreign_keys = ON")
        # Insert graf baru
        c.execute("INSERT INTO graphs(nama) VALUES (?)", (nama or "Graf Kustom",))
        gid = c.lastrowid
        # Insert semua node/titik
        for n in titik:
            node_id = str(n.get("id", ""))
            node_name = str(n.get("name", node_id))
            node_x = float(n.get("x", 0))
            node_y = float(n.get("y", 0))
            c.execute("INSERT OR REPLACE INTO nodes(graph_id,id,nama,x,y) VALUES (?,?,?,?,?)",
                      (gid, node_id, node_name, node_x, node_y))
        # Insert semua edge/garis
        for e in garis:
            edge_a = str(e.get("a", ""))
            edge_b = str(e.get("b", ""))
            edge_w = float(e.get("w", 0))
            # Simpan edge dalam kedua arah untuk memastikan konsistensi
            c.execute("INSERT OR REPLACE INTO edges(graph_id,a,b,w) VALUES (?,?,?,?)",
                      (gid, edge_a, edge_b, edge_w))
        conn.commit()
        return gid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def db_daftar_graf():
    """Mengambil daftar semua graf yang tersimpan"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        rows = c.execute("SELECT id, nama, dibuat FROM graphs ORDER BY id DESC").fetchall()
        return [{"id": r[0], "nama": r[1], "dibuat": r[2]} for r in rows]
    finally:
        conn.close()

def db_muat_graf(graph_id):
    """Memuat graf dari database berdasarkan ID"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        nodes = c.execute("SELECT id, nama, x, y FROM nodes WHERE graph_id=? ORDER BY id", (graph_id,)).fetchall()
        edges = c.execute("SELECT a, b, w FROM edges WHERE graph_id=?", (graph_id,)).fetchall()
        titik = [{"id": r[0], "name": r[1], "x": r[2], "y": r[3]} for r in nodes]
        garis = [{"a": r[0], "b": r[1], "w": r[2]} for r in edges]
        return {"titik": titik, "garis": garis}
    finally:
        conn.close()

def db_find_graph_by_name(nama):
    """Mencari graf berdasarkan nama"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        row = c.execute("SELECT id FROM graphs WHERE nama=?", (nama,)).fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def db_update_graph(graph_id, nama, titik, garis):
    """Update graf yang sudah ada di database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("PRAGMA foreign_keys = ON")
        # Update nama graf
        c.execute("UPDATE graphs SET nama=? WHERE id=?", (nama or "Graf Kustom", graph_id))
        # Hapus node dan edge lama
        c.execute("DELETE FROM nodes WHERE graph_id=?", (graph_id,))
        c.execute("DELETE FROM edges WHERE graph_id=?", (graph_id,))
        # Insert node dan edge baru
        for n in titik:
            node_id = str(n.get("id", ""))
            node_name = str(n.get("name", node_id))
            node_x = float(n.get("x", 0))
            node_y = float(n.get("y", 0))
            c.execute("INSERT INTO nodes(graph_id,id,nama,x,y) VALUES (?,?,?,?,?)",
                      (graph_id, node_id, node_name, node_x, node_y))
        for e in garis:
            edge_a = str(e.get("a", ""))
            edge_b = str(e.get("b", ""))
            edge_w = float(e.get("w", 0))
            c.execute("INSERT INTO edges(graph_id,a,b,w) VALUES (?,?,?,?)",
                      (graph_id, edge_a, edge_b, edge_w))
        conn.commit()
        return graph_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def db_delete_graph(graph_id):
    """Menghapus graf dari database (akan otomatis menghapus node dan edge karena CASCADE)"""
    # Graf ID 2 (Graf Perumahan - Layout Peta) tidak boleh dihapus
    if graph_id == 2:
        raise ValueError("Graf Perumahan - Layout Peta tidak dapat dihapus")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("PRAGMA foreign_keys = ON")
        c.execute("DELETE FROM graphs WHERE id=?", (graph_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def _load_list_graf_json():
    try:
        file_path = os.path.join(ROOT_DIR, "data", "list graf.json")
        data = grafmod.build_graph_from_json(file_path)
        return data
    except Exception:
        return None

def preload_from_file():
    # Coba load dengan layout perumahan terlebih dahulu
    file_path = os.path.join(ROOT_DIR, "data", "list graf.json")
    if os.path.exists(file_path):
        data = grafmod.build_graph_with_perumahan_layout(file_path, "Graf Perumahan - Layout Peta")
        if not data:
            data = _load_list_graf_json()
    else:
        data = None
    
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
        if p.path in ("/", "/index.html", "/Home.html"):
            try:
                file_path = os.path.join(ROOT_DIR, "template", "Home.html")
                with open(file_path, "rb") as f:
                    data = f.read()
                self.send_response(200); self._cors(); self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
            except Exception:
                self.send_response(500); self._cors(); self.end_headers(); return
        if p.path == "/desain.css":
            try:
                file_path = os.path.join(ROOT_DIR, "desain.css")
                with open(file_path, "rb") as f:
                    data = f.read()
                self.send_response(200); self._cors(); self.send_header("Content-Type", "text/css; charset=utf-8")
                self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
            except Exception:
                self.send_response(404); self._cors(); self.end_headers(); return
        if p.path == "/Script.js":
            try:
                file_path = os.path.join(ROOT_DIR, "Script.js")
                with open(file_path, "rb") as f:
                    data = f.read()
                self.send_response(200); self._cors(); self.send_header("Content-Type", "application/javascript; charset=utf-8")
                self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
            except Exception:
                self.send_response(404); self._cors(); self.end_headers(); return
        if p.path.startswith("/Static/"):
            from urllib.parse import unquote
            rel = unquote(p.path[len("/Static/"):])
            try:
                file_path = os.path.join(ROOT_DIR, "Static", rel)
                ctype = "text/css; charset=utf-8" if rel.endswith(".css") else (
                    "application/javascript; charset=utf-8" if rel.endswith(".js") else "application/octet-stream"
                )
                with open(file_path, "rb") as f:
                    data = f.read()
                self.send_response(200); self._cors(); self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
            except Exception:
                self.send_response(404); self._cors(); self.end_headers(); return
        if p.path.startswith("/gambar/"):
            from urllib.parse import unquote
            rel = unquote(p.path[len("/gambar/"):])
            try:
                primary = os.path.join(ROOT_DIR, "Static", "Gambar", rel)
                fallback = os.path.join(ROOT_DIR, "Gambar", rel)
                file_path = primary if os.path.exists(primary) else fallback
                with open(file_path, "rb") as f:
                    data = f.read()
                self.send_response(200); self._cors(); self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
            except Exception:
                self.send_response(404); self._cors(); self.end_headers(); return
        if p.path in ("/graf/daftar", "/api/graf/daftar"):
            data = json.dumps(db_daftar_graf()).encode("utf-8")
            self.send_response(200); self._cors(); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
        if p.path in ("/graf/muat", "/api/graf/muat"):
            qs = parse_qs(p.query)
            gid = int(qs.get("id", ["0"])[0])
            data = json.dumps(db_muat_graf(gid)).encode("utf-8")
            self.send_response(200); self._cors(); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
        if p.path in ("/graf/json", "/api/graf/json"):
            file_path = os.path.join(ROOT_DIR, "data", "list graf.json")
            # Gunakan layout perumahan yang lebih baik
            data = grafmod.build_graph_with_perumahan_layout(file_path, "Graf Perumahan - Layout Peta") or {}
            if not data:
                # Fallback ke fungsi lama jika fungsi baru gagal
                data = grafmod.build_graph_from_json(file_path) or {}
            try:
                nama = data.get("nama")
                if nama and not db_find_graph_by_name(nama):
                    db_insert_graph(nama, data.get("titik", []), data.get("garis", []))
            except Exception:
                pass
            d = json.dumps(data).encode("utf-8")
            self.send_response(200); self._cors(); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(d))); self.end_headers(); self.wfile.write(d); return
        self.send_response(404); self._cors(); self.end_headers()
    def do_POST(self):
        p = urlparse(self.path)
        n = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads((self.rfile.read(n) if n > 0 else b"{}").decode("utf-8"))
        except Exception:
            self.send_response(400); self._cors(); self.end_headers(); return
        if p.path in ("/graf/simpan", "/api/graf/simpan"):
            nama = body.get("nama") or "Graf Kustom"
            titik = body.get("titik", [])
            garis = body.get("garis", [])
            graph_id = body.get("id")  # Jika ada ID, berarti update
            try:
                if graph_id:
                    # Update graf yang sudah ada
                    gid = db_update_graph(int(graph_id), nama, titik, garis)
                    d = json.dumps({"id": gid, "nama": nama, "message": "Graf berhasil diperbarui"}).encode("utf-8")
                else:
                    # Simpan graf baru
                    gid = db_insert_graph(nama, titik, garis)
                    d = json.dumps({"id": gid, "nama": nama, "message": "Graf berhasil disimpan"}).encode("utf-8")
                self.send_response(200); self._cors(); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(d))); self.end_headers(); self.wfile.write(d); return
            except Exception as e:
                error_msg = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500); self._cors(); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(error_msg))); self.end_headers(); self.wfile.write(error_msg); return
        if p.path in ("/graf/hapus", "/api/graf/hapus"):
            graph_id = body.get("id")
            if not graph_id:
                self.send_response(400); self._cors(); self.end_headers(); return
            try:
                graph_id_int = int(graph_id)
                # Cek apakah graf ID 2 (protected)
                if graph_id_int == 2:
                    error_msg = json.dumps({"error": "Graf Perumahan - Layout Peta tidak dapat dihapus"}).encode("utf-8")
                    self.send_response(403); self._cors(); self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(error_msg))); self.end_headers(); self.wfile.write(error_msg); return
                db_delete_graph(graph_id_int)
                d = json.dumps({"message": "Graf berhasil dihapus"}).encode("utf-8")
                self.send_response(200); self._cors(); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(d))); self.end_headers(); self.wfile.write(d); return
            except ValueError as e:
                error_msg = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(403); self._cors(); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(error_msg))); self.end_headers(); self.wfile.write(error_msg); return
            except Exception as e:
                error_msg = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500); self._cors(); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(error_msg))); self.end_headers(); self.wfile.write(error_msg); return
        if p.path in ("/dijkstra", "/api/dijkstra"):
            r = jalankan_dijkstra(body.get("titik", []), body.get("garis", []), body.get("awalId"), body.get("tujuanId"))
            d = json.dumps(r).encode("utf-8")
            self.send_response(200); self._cors(); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(d))); self.end_headers(); self.wfile.write(d); return
        
        self.send_response(404); self._cors(); self.end_headers()

if __name__ == "__main__":
    db_init(); preload_from_file()
    port = int(os.environ.get("PORT", "5000"))
    HTTPServer(("", port), Handler).serve_forever()
