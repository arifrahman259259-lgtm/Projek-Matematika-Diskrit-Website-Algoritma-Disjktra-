"""
Script untuk menghapus graf yang tidak diperlukan
"""
import sqlite3
import os

MODULES_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(MODULES_DIR)
DB_PATH = os.path.join(ROOT_DIR, "graf.db")

def hapus_graf(graph_id):
    """Menghapus graf dari database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("PRAGMA foreign_keys = ON")
        # Cek apakah graf ada
        row = c.execute("SELECT nama FROM graphs WHERE id=?", (graph_id,)).fetchone()
        if row:
            c.execute("DELETE FROM graphs WHERE id=?", (graph_id,))
            conn.commit()
            print(f"✓ Graf ID {graph_id} ({row[0]}) berhasil dihapus")
            return True
        else:
            print(f"✗ Graf ID {graph_id} tidak ditemukan")
            return False
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Script Penghapusan Graf")
    print("=" * 60)
    
    # Hapus graf ID 1 dan ID 3
    graf_to_delete = [1, 3]
    
    for graph_id in graf_to_delete:
        hapus_graf(graph_id)
    
    print("\n" + "=" * 60)
    print("Selesai!")
    print("=" * 60)

