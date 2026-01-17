from flask import Flask, jsonify, render_template, request
from network_scanner import scan_network

app = Flask(__name__)

NETWORK_RANGE = "192.168.1.0/24"  # Cambia según tu red

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.json
    lat = float(data["latitude"])
    lon = float(data["longitude"])

    devices = scan_network(NETWORK_RANGE, lat, lon)

    return jsonify({
        "base": {"lat": lat, "lon": lon},
        "devices": devices
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
