from scapy.all import ARP, Ether, srp
import socket
import math

# Convertir RSSI a distancia aproximada en metros
def rssi_to_distance(rssi, tx_power=-59, n=2):
    return round(10 ** ((tx_power - rssi) / (10 * n)), 2)

# Calcular coordenadas estimadas usando distancia y dirección (bearing)
def destination_point(lat, lon, distance_m, bearing_deg):
    R = 6371000  # Radio de la Tierra en metros
    bearing = math.radians(bearing_deg)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)

    lat2 = math.asin(
        math.sin(lat1) * math.cos(distance_m / R) +
        math.cos(lat1) * math.sin(distance_m / R) * math.cos(bearing)
    )

    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(distance_m / R) * math.cos(lat1),
        math.cos(distance_m / R) - math.sin(lat1) * math.sin(lat2)
    )

    return round(math.degrees(lat2), 6), round(math.degrees(lon2), 6)

# Escaneo de red con estimación de ubicación
def scan_network(ip_range, base_lat, base_lon):
    devices = []

    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    result = srp(ether / arp, timeout=2, verbose=False)[0]

    for _, received in result:
        try:
            name = socket.gethostbyaddr(received.psrc)[0]
        except:
            name = "Desconocido"

        # Simulación de RSSI entre -50 y -80 dBm
        rssi = -50 - (hash(received.psrc) % 30)
        distance = rssi_to_distance(rssi)

        bearing = (hash(received.psrc) % 360)  # dirección aleatoria
        est_lat, est_lon = destination_point(base_lat, base_lon, distance, bearing)

        devices.append({
            "ip": received.psrc,
            "mac": received.hwsrc,
            "name": name,
            "rssi": rssi,
            "distance_m": distance,
            "lat": est_lat,
            "lon": est_lon
        })

    return devices
