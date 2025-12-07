"""
Script untuk membuat gambar visualisasi graf dari database
"""
import os
import sys
import sqlite3

MODULES_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(MODULES_DIR)
DB_PATH = os.path.join(ROOT_DIR, "graf.db")
OUTPUT_DIR = os.path.join(ROOT_DIR, "Static", "Gambar")

def muat_graf_dari_database(graph_id):
    """Memuat graf dari database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        # Ambil nama graf
        row = c.execute("SELECT nama FROM graphs WHERE id=?", (graph_id,)).fetchone()
        if not row:
            return None
        nama = row[0]
        
        # Ambil nodes
        nodes = c.execute("SELECT id, nama, x, y FROM nodes WHERE graph_id=? ORDER BY id", (graph_id,)).fetchall()
        # Ambil edges
        edges = c.execute("SELECT a, b, w FROM edges WHERE graph_id=?", (graph_id,)).fetchall()
        
        titik = [{"id": r[0], "name": r[1], "x": r[2], "y": r[3]} for r in nodes]
        garis = [{"a": r[0], "b": r[1], "w": r[2]} for r in edges]
        
        return {"nama": nama, "titik": titik, "garis": garis}
    finally:
        conn.close()

def buat_gambar_graf(graf_data, output_path):
    """Membuat gambar visualisasi graf menggunakan matplotlib"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.set_aspect('equal')
        ax.axis('off')
        
        titik = graf_data['titik']
        garis = graf_data['garis']
        
        # Buat dictionary untuk akses cepat node
        node_dict = {n['id']: n for n in titik}
        
        # Gambar garis/edges
        for e in garis:
            a = node_dict.get(e['a'])
            b = node_dict.get(e['b'])
            if a and b:
                x1, y1 = a['x'], a['y']
                x2, y2 = b['x'], b['y']
                ax.plot([x1, x2], [y1, y2], 'gray', linewidth=2, alpha=0.6, zorder=1)
                # Tulis bobot di tengah garis
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                ax.text(mx, my, f"{e['w']:.0f}m", fontsize=8, ha='center', va='center',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8), zorder=3)
        
        # Gambar node/titik
        for n in titik:
            x, y = n['x'], n['y']
            # Lingkaran node
            circle = plt.Circle((x, y), 12, color='#6a00f4', zorder=2)
            ax.add_patch(circle)
            # Border
            border = plt.Circle((x, y), 12, fill=False, edgecolor='#1e293b', linewidth=1.5, zorder=2)
            ax.add_patch(border)
            # Label
            ax.text(x, y - 20, n['name'], fontsize=10, ha='center', va='top', 
                   fontweight='bold', color='#0f172a', zorder=3)
        
        # Set batas gambar
        if titik:
            xs = [n['x'] for n in titik]
            ys = [n['y'] for n in titik]
            margin = 50
            ax.set_xlim(min(xs) - margin, max(xs) + margin)
            ax.set_ylim(min(ys) - margin, max(ys) + margin)
            ax.invert_yaxis()  # Invert karena canvas web menggunakan koordinat terbalik
        
        plt.title(f"Graf: {graf_data['nama']}", fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()
        
        # Simpan gambar
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        return True
    except ImportError:
        print("Matplotlib tidak tersedia. Menggunakan metode alternatif...")
        return False
    except Exception as e:
        print(f"Error membuat gambar: {e}")
        return False

def main():
    """Fungsi utama"""
    print("=" * 60)
    print("Script Pembuatan Gambar Graf")
    print("=" * 60)
    
    # Cari graf perumahan
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    rows = c.execute("SELECT id, nama FROM graphs WHERE nama LIKE '%Perumahan%' ORDER BY id DESC").fetchall()
    conn.close()
    
    if not rows:
        print("Tidak ada graf perumahan ditemukan di database")
        return
    
    print(f"\nDitemukan {len(rows)} graf perumahan:")
    for row in rows:
        print(f"  - ID: {row[0]}, Nama: {row[1]}")
    
    # Ambil graf pertama (terbaru)
    graph_id = rows[0][0]
    print(f"\nMenggunakan graf ID: {graph_id}")
    
    # Muat graf
    print("Memuat graf dari database...")
    graf_data = muat_graf_dari_database(graph_id)
    
    if not graf_data:
        print("✗ Gagal memuat graf")
        return
    
    print(f"✓ Graf dimuat: {len(graf_data['titik'])} titik, {len(graf_data['garis'])} garis")
    
    # Buat gambar
    output_path = os.path.join(OUTPUT_DIR, "graf_perumahan.png")
    print(f"\nMembuat gambar graf...")
    print(f"Output: {output_path}")
    
    if buat_gambar_graf(graf_data, output_path):
        print("✓ Gambar berhasil dibuat!")
        print(f"  File: {output_path}")
    else:
        print("✗ Gagal membuat gambar")

if __name__ == "__main__":
    main()

