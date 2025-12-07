"""
Script untuk menyimpan graf perumahan dari list graf.json ke database secara permanen
"""
import os
import sys

# Tambahkan path modules ke sys.path
MODULES_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(MODULES_DIR)
sys.path.insert(0, MODULES_DIR)

from importlib.machinery import SourceFileLoader
import sqlite3

# Load modules
grafmod = SourceFileLoader("grafmod", os.path.join(MODULES_DIR, "graf.py")).load_module()

DB_PATH = os.path.join(ROOT_DIR, "graf.db")
JSON_PATH = os.path.join(ROOT_DIR, "data", "list graf.json")

def init_database():
    """Inisialisasi database jika belum ada"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
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
    c.execute("CREATE INDEX IF NOT EXISTS idx_nodes_graph_id ON nodes(graph_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_edges_graph_id ON edges(graph_id)")
    conn.commit()
    conn.close()

def simpan_graf_ke_database(nama, titik, garis):
    """Menyimpan graf ke database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("PRAGMA foreign_keys = ON")
        # Cek apakah graf dengan nama yang sama sudah ada
        existing = c.execute("SELECT id FROM graphs WHERE nama=?", (nama,)).fetchone()
        if existing:
            graph_id = existing[0]
            # Update graf yang sudah ada
            c.execute("UPDATE graphs SET nama=? WHERE id=?", (nama, graph_id))
            # Hapus node dan edge lama
            c.execute("DELETE FROM nodes WHERE graph_id=?", (graph_id,))
            c.execute("DELETE FROM edges WHERE graph_id=?", (graph_id,))
            print(f"Memperbarui graf '{nama}' (ID: {graph_id})")
        else:
            # Insert graf baru
            c.execute("INSERT INTO graphs(nama) VALUES (?)", (nama,))
            graph_id = c.lastrowid
            print(f"Menyimpan graf baru '{nama}' (ID: {graph_id})")
        
        # Insert semua node/titik
        for n in titik:
            node_id = str(n.get("id", ""))
            node_name = str(n.get("name", node_id))
            node_x = float(n.get("x", 0))
            node_y = float(n.get("y", 0))
            c.execute("INSERT OR REPLACE INTO nodes(graph_id,id,nama,x,y) VALUES (?,?,?,?,?)",
                      (graph_id, node_id, node_name, node_x, node_y))
        
        # Insert semua edge/garis
        for e in garis:
            edge_a = str(e.get("a", ""))
            edge_b = str(e.get("b", ""))
            edge_w = float(e.get("w", 0))
            c.execute("INSERT OR REPLACE INTO edges(graph_id,a,b,w) VALUES (?,?,?,?)",
                      (graph_id, edge_a, edge_b, edge_w))
        
        conn.commit()
        print(f"✓ Berhasil menyimpan {len(titik)} titik dan {len(garis)} garis")
        return graph_id
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        raise e
    finally:
        conn.close()

def main():
    """Fungsi utama"""
    print("=" * 60)
    print("Script Penyimpanan Graf Perumahan ke Database")
    print("=" * 60)
    
    # Inisialisasi database
    print("\n1. Menginisialisasi database...")
    init_database()
    print("✓ Database siap")
    
    # Baca data dari JSON
    print(f"\n2. Membaca data dari {JSON_PATH}...")
    if not os.path.exists(JSON_PATH):
        print(f"✗ File tidak ditemukan: {JSON_PATH}")
        return
    
    # Build graf dengan layout perumahan
    print("3. Membangun graf dengan layout perumahan...")
    graf_data = grafmod.build_graph_with_perumahan_layout(JSON_PATH, "Graf Perumahan - Layout Peta")
    
    if not graf_data:
        print("✗ Gagal membangun graf dari JSON")
        return
    
    print(f"✓ Graf berhasil dibangun: {len(graf_data['titik'])} titik, {len(graf_data['garis'])} garis")
    
    # Simpan ke database
    print("\n4. Menyimpan graf ke database...")
    try:
        graph_id = simpan_graf_ke_database(
            graf_data['nama'],
            graf_data['titik'],
            graf_data['garis']
        )
        print(f"\n{'=' * 60}")
        print(f"✓ SUKSES! Graf tersimpan dengan ID: {graph_id}")
        print(f"  Nama: {graf_data['nama']}")
        print(f"  Titik: {len(graf_data['titik'])}")
        print(f"  Garis: {len(graf_data['garis'])}")
        print(f"{'=' * 60}")
        print("\nGraf sekarang dapat dimuat dari aplikasi web!")
    except Exception as e:
        print(f"\n✗ Gagal menyimpan graf: {e}")
        return

if __name__ == "__main__":
    main()

