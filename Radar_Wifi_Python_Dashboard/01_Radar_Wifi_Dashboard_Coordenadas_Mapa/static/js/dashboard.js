let map;
let markers = [];
let radar;

window.scan = function() {
    const lat = parseFloat(document.getElementById("lat").value);
    const lon = parseFloat(document.getElementById("lon").value);

    fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ latitude: lat, longitude: lon })
    })
    .then(res => res.json())
    .then(data => {
        initMap(lat, lon);
        updateMap(data.base, data.devices);
        updateTable(data.devices);
        updateRadar(data.devices);
    });
};

function initMap(lat, lon) {
    if (!map) {
        map = L.map("map").setView([lat, lon], 17);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap"
        }).addTo(map);
    }
}

function clearMarkers() {
    markers.forEach(m => map.removeLayer(m));
    markers = [];
}

function updateMap(base, devices) {
    clearMarkers();

    // Punto base azul
    markers.push(
        L.circleMarker([base.lat, base.lon], {
            radius: 10,
            color: "blue",
            fillColor: "blue",
            fillOpacity: 0.7
        })
        .addTo(map)
        .bindPopup("📍 Punto base")
    );

    // Dispositivos rojos
    devices.forEach(d => {
        markers.push(
            L.circleMarker([d.lat, d.lon], {
                radius: 8,
                color: "red",
                fillColor: "red",
                fillOpacity: 0.7
            })
            .addTo(map)
            .bindPopup(`
                IP: ${d.ip}<br>
                MAC: ${d.mac}<br>
                RSSI: ${d.rssi} dBm<br>
                Distancia: ${d.distance_m} m
            `)
        );
    });

    // Ajustar zoom y centro para mostrar todos los marcadores
    if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.5));
    }
}

function updateTable(devices) {
    const tbody = document.querySelector("#deviceTable tbody");
    tbody.innerHTML = "";

    devices.forEach(d => {
        tbody.innerHTML += `
        <tr>
            <td>${d.ip}</td>
            <td>${d.mac}</td>
            <td>${d.rssi}</td>
            <td>${d.distance_m}</td>
            <td>${d.lat}</td>
            <td>${d.lon}</td>
        </tr>`;
    });
}

function updateRadar(devices) {
    const labels = devices.map(d => d.ip);
    const data = devices.map(d => d.distance_m);

    if (radar) radar.destroy();

    radar = new Chart(document.getElementById("radarChart"), {
        type: "radar",
        data: {
            labels,
            datasets: [{
                label: "Distancia estimada (m)",
                data,
                backgroundColor: "rgba(255,0,0,0.2)",
                borderColor: "red"
            }]
        },
        options: {
            scales: {
                r: { beginAtZero: true }
            }
        }
    });
}
