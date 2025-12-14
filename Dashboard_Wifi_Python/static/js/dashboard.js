let radar;

function loadDevices() {
    fetch("/api/devices")
        .then(res => res.json())
        .then(data => {
            updateTable(data.devices);
            updateRadar(data.devices);

            if (data.new_devices.length > 0) {
                document.getElementById("alert").innerHTML =
                    "🚨 Nuevo dispositivo conectado: " + data.new_devices.join(", ");
            }
        });
}

function updateTable(devices) {
    const tbody = document.querySelector("#deviceTable tbody");
    tbody.innerHTML = "";

    devices.forEach(d => {
        tbody.innerHTML += `
            <tr>
                <td>${d.ip}</td>
                <td>${d.mac}</td>
                <td>${d.name}</td>
                <td>${d.zone}</td>
                <td>${d.distance}</td>
            </tr>
        `;
    });
}

function updateRadar(devices) {
    const labels = devices.map(d => d.name || d.ip);
    const distances = devices.map(d => d.distance);

    if (radar) radar.destroy();

    radar = new Chart(document.getElementById("radarChart"), {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: "Distancia estimada (m)",
                data: distances,
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                r: {
                    beginAtZero: true
                }
            },
            plugins: {
                datalabels: {
                    color: 'black',
                    align: 'top',
                    formatter: function(value, context) {
                        const d = devices[context.dataIndex];
                        return [
                            `Nombre: ${d.name}`,
                            `IP: ${d.ip}`,
                            `MAC: ${d.mac}`,
                            `Distancia: ${d.distance} m`
                        ];
                    },
                    font: {
                        size: 10
                    }
                },
                tooltip: {
                    enabled: false  // opcional: desactiva tooltip si no lo quieres
                }
            }
        },
        plugins: [ChartDataLabels]
    });
}

setInterval(loadDevices, 10000);
loadDevices();
