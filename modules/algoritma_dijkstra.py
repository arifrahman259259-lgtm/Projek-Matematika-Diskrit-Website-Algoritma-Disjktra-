TAK_TERHINGGA = float("inf")

def dijkstra(graf, titik_awal):
    jumlah = len(graf)
    hasil = [[TAK_TERHINGGA, None] for _ in range(jumlah)]
    hasil[titik_awal] = [0.0, None]
    terkunjungi = set()
    for _ in range(jumlah):
        jarak_min, indeks_min = TAK_TERHINGGA, None
        for j in range(jumlah):
            if j not in terkunjungi and hasil[j][0] < jarak_min:
                jarak_min, indeks_min = hasil[j][0], j
        if indeks_min is None:
            break
        terkunjungi.add(indeks_min)
        for i in range(jumlah):
            berat = graf[indeks_min][i]
            if i not in terkunjungi and berat != 0:
                jarak_baru = hasil[indeks_min][0] + berat
                if jarak_baru < hasil[i][0]:
                    hasil[i][0], hasil[i][1] = jarak_baru, indeks_min
    return hasil

def dijkstra_dengan_iterasi(graf, titik_awal, titik_tujuan, ids):
    """Dijkstra yang mengembalikan hasil dan data iterasi"""
    jumlah = len(graf)
    hasil = [[TAK_TERHINGGA, None] for _ in range(jumlah)]
    hasil[titik_awal] = [0.0, None]
    terkunjungi = set()
    iterasi_data = []
    iterasi_count = 0
    
    for _ in range(jumlah):
        jarak_min, indeks_min = TAK_TERHINGGA, None
        for j in range(jumlah):
            if j not in terkunjungi and hasil[j][0] < jarak_min:
                jarak_min, indeks_min = hasil[j][0], j
        if indeks_min is None:
            break
        
        iterasi_count += 1
        terkunjungi.add(indeks_min)
        
        # Relaksasi tetangga
        for i in range(jumlah):
            berat = graf[indeks_min][i]
            if i not in terkunjungi and berat != 0:
                jarak_baru = hasil[indeks_min][0] + berat
                if jarak_baru < hasil[i][0]:
                    hasil[i][0], hasil[i][1] = jarak_baru, indeks_min
        
        # Simpan status iterasi setelah relaksasi
        status_row = {'Iterasi': iterasi_count, 'Diproses': ids[indeks_min] if indeks_min < len(ids) else str(indeks_min)}
        for i in range(jumlah):
            node_name = ids[i] if i < len(ids) else str(i)
            dist = hasil[i][0]
            pred_idx = hasil[i][1]
            pred_name = ids[pred_idx] if pred_idx is not None and pred_idx < len(ids) else None
            
            if dist == TAK_TERHINGGA:
                status_row[node_name] = 'inf (-)'
            else:
                status_row[node_name] = f'{int(dist)} ({pred_name if pred_name else "-"})'
        
        iterasi_data.append(status_row)
        
        # Hentikan jika tujuan ditemukan
        if indeks_min == titik_tujuan:
            break
    
    return hasil, iterasi_data

def lintasan(titik_akhir, hasil_graf):
    rute = [titik_akhir]
    induk = hasil_graf[titik_akhir][1]
    while induk is not None:
        rute.append(induk)
        induk = hasil_graf[induk][1]
    return rute[::-1]

def bangun_matriks_dari_garis(titik_ids, garis):
    ids = [str(n) for n in titik_ids]
    idx = {v: i for i, v in enumerate(ids)}
    n = len(ids)
    graf = [[0]*n for _ in range(n)]
    for e in garis:
        a = idx.get(str(e.get("a")))
        b = idx.get(str(e.get("b")))
        if a is None or b is None:
            continue
        w = float(e.get("w", 0))
        graf[a][b] = w
        graf[b][a] = w
    return ids, idx, graf

def jalankan_dijkstra_dari_garis(titik_ids, garis, awal_id, tujuan_id):
    ids, idx, graf = bangun_matriks_dari_garis(titik_ids, garis)
    s = idx.get(str(awal_id))
    t = idx.get(str(tujuan_id))
    if s is None or t is None:
        return {"path": [], "total": None, "edgePath": []}
    L = dijkstra(graf, s)
    if not L or L[t][0] == float("inf"):
        return {"path": [], "total": None, "edgePath": []}
    path_idx = lintasan(t, L)
    path_ids = [ids[i] for i in path_idx]
    total = L[t][0]
    edge_path = [{"a": path_ids[i], "b": path_ids[i+1]} for i in range(len(path_ids)-1)]
    return {"path": path_ids, "total": total, "edgePath": edge_path}

