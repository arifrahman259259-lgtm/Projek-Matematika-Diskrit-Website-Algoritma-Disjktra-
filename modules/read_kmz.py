"""
Script untuk membaca koordinat dari file KMZ/KML
"""
import zipfile
import xml.etree.ElementTree as ET
import os

def extract_kmz(kmz_path):
    """Ekstrak KML dari KMZ"""
    try:
        with zipfile.ZipFile(kmz_path, 'r') as kmz:
            for name in kmz.namelist():
                if name.endswith('.kml'):
                    return kmz.read(name).decode('utf-8')
    except Exception as e:
        print(f"Error extracting KMZ: {e}")
    return None

def parse_kml(kml_content):
    """Parse KML dan ekstrak koordinat placemark"""
    try:
        root = ET.fromstring(kml_content)
        # Namespace untuk KML
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        placemarks = root.findall('.//kml:Placemark', ns)
        coordinates = {}
        
        for pm in placemarks:
            name_elem = pm.find('kml:name', ns)
            if name_elem is not None:
                name = name_elem.text.strip()
                # Cari koordinat di Point atau LineString
                point = pm.find('.//kml:Point/kml:coordinates', ns)
                if point is not None:
                    coords = point.text.strip().split(',')
                    if len(coords) >= 2:
                        lon, lat = float(coords[0]), float(coords[1])
                        coordinates[name] = (lon, lat)
        
        return coordinates
    except Exception as e:
        print(f"Error parsing KML: {e}")
        return {}

if __name__ == "__main__":
    kmz_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Peta Algoritma Dijsktra.kmz")
    if os.path.exists(kmz_path):
        print(f"Reading KMZ: {kmz_path}")
        kml_content = extract_kmz(kmz_path)
        if kml_content:
            coords = parse_kml(kml_content)
            print(f"\nFound {len(coords)} coordinates:")
            for name, (lon, lat) in sorted(coords.items()):
                print(f"  {name}: ({lon}, {lat})")
        else:
            print("Failed to extract KML")
    else:
        print(f"KMZ file not found: {kmz_path}")

