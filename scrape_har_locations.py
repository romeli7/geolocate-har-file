import json
import requests
import folium
from folium.plugins import MarkerCluster
from pathlib import Path
from typing import List, Tuple

# === CONFIGURATION ===
HAR_FILE = "ipinfo.io.har"  # Replace with your HAR filename
OUTPUT_MAP = "ip_map.html"
MAX_IPS = 25  # Limit to avoid API rate limiting

# === FUNCTIONS ===


def load_ips_from_har(path: str) -> List[str]:
    """Extract unique IP addresses from a HAR file."""
    with open(path, "r", encoding="utf-8") as f:
        har = json.load(f)

    entries = har.get("log", {}).get("entries", [])
    ips = set()
    for entry in entries:
        ip = entry.get("serverIPAddress")
        if ip:
            print(f"Found IP: {ip}")
            ip = ip.strip("[]")
            ips.add(ip)
    return list(ips)


def geolocate_ip(ip: str) -> Tuple[str, float, float]:
    """Geolocate IP using ipinfo.io API."""
    try:
        resp = requests.get(f"https://ipinfo.io/{ip}/json")
        data = resp.json()
        loc = data.get("loc")
        print(f"Geolocating {ip}: {data}")
        if loc:
            lat, lon = map(float, loc.split(","))
            return ip, lat, lon
    except Exception as e:
        print(f"Error locating {ip}: {e}")
    return ip, None, None


def build_map(ip_locations: List[Tuple[str, float, float]], output_path: str) -> None:
    """Generate Folium map from list of IP + lat/lon tuples."""
    m = folium.Map(location=[20, 0], zoom_start=2)
    cluster = MarkerCluster().add_to(m)

    for ip, lat, lon in ip_locations:
        if lat and lon:
            folium.Marker(
                location=[lat, lon],
                popup=f"IP: {ip}",
                icon=folium.Icon(color="blue", icon="info-sign"),
            ).add_to(cluster)

    m.save(output_path)
    print(f"Map saved to: {output_path}")


# === RUN ===

if __name__ == "__main__":
    ip_list = load_ips_from_har(HAR_FILE)
    print(f"Found {len(ip_list)} IPs")
    # deduplicate and limit to MAX_IPS
    ips = set(ip_list)
    print(f"Unique IPs: {len(ips)}")

    ip_locations = [geolocate_ip(ip) for ip in ip_list[:MAX_IPS]]
    build_map(ip_locations, OUTPUT_MAP)
