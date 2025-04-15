let trafficChart;
let protocolChart;
let paquetesTotales = [];
let protocoloConteo = {};
let intervaloAutoRefresh;
let capturaActiva = false;

const protocoloMap = {
    "1": "ICMP",
    "6": "TCP",
    "17": "UDP",
    "2": "IGMP",
    "89": "OSPF",
    "47": "GRE",
    "50": "ESP",
    "51": "AH",
    "58": "ICMPv6",
};

document.addEventListener("DOMContentLoaded", () => {
    console.log("🚀 Página cargada, esperando acción del usuario...");

    const socket = io();

    socket.on("nuevo_paquete", function (data) {
        if (capturaActiva) {
            console.log("📡 Paquete recibido vía WebSocket:", data);
            agregarPaqueteATabla(data);
            actualizarGrafico(data);
            actualizarGraficoProtocolos(data);
        }
    });

    document.getElementById("btnIniciar").addEventListener("click", iniciarCaptura);
    document.getElementById("btnDetener").addEventListener("click", detenerCaptura);
    document.getElementById("btnRegresar").addEventListener("click", () => window.location.href = "/dashboard");

    cargarDatosIniciales();
});

async function cargarDatosIniciales() {
    try {
        const response = await fetch('/datos_red');
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        const datos = await response.json();

        datos.sort((a, b) => b.idescanear_red - a.idescanear_red);
        actualizarTabla(datos);
        actualizarGrafico(datos);
        actualizarGraficoProtocolos(datos);
    } catch (error) {
        console.error("❌ Error al cargar datos:", error);
        mostrarMensaje("Error al cargar los datos.", "error");
    }
}

function actualizarTabla(datos) {
    const tableBody = document.getElementById('packetTable');
    if (!tableBody) return;
    tableBody.innerHTML = "";
    datos.forEach(dato => agregarPaqueteATabla(dato));
    mostrarMensaje("✅ Datos cargados correctamente.", "success");
}

function agregarPaqueteATabla(dato) {
    const tableBody = document.getElementById('packetTable');
    if (!tableBody) return;

    const fechaFormateada = dato.fecha_captura ? new Date(dato.fecha_captura).toLocaleTimeString() : 'N/A';
    const protocoloLegible = protocoloMap[dato.protocolo] || dato.protocolo || "Desconocido";

    const row = `
        <tr class="border-b">
            <td class="p-2">${dato.idescanear_red || 'N/A'}</td>
            <td class="p-2">${dato.iporigen || 'N/A'}</td>
            <td class="p-2">${dato.ipdestino || 'N/A'}</td>
            <td class="p-2">${dato.mac_origen || 'N/A'}</td>
            <td class="p-2">${dato.mac_destino || 'N/A'}</td>
            <td class="p-2">${dato.puerto_origen || 'N/A'}</td>
            <td class="p-2">${dato.puerto_destino || 'N/A'}</td>
            <td class="p-2">${protocoloLegible}</td>
            <td class="p-2">${dato.tamano || 'N/A'}</td>
            <td class="p-2">${fechaFormateada}</td>
            <td class="p-2">${dato.ttl || 'N/A'}</td>
        </tr>
    `;
    tableBody.insertAdjacentHTML("afterbegin", row);
}

function actualizarGrafico(datos) {
    if (!Array.isArray(datos)) datos = [datos];

    paquetesTotales = paquetesTotales.concat(datos).slice(-50);
    const ctx = document.getElementById('trafficChart').getContext('2d');

    const labels = paquetesTotales.map(d => d.fecha_captura ? new Date(d.fecha_captura).toLocaleTimeString() : 'N/A');
    const paquetes = paquetesTotales.map(d => d.tamano || 0);

    if (trafficChart) trafficChart.destroy();

    trafficChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Tráfico en Red',
                data: paquetes,
                borderColor: '#FF5733',
                backgroundColor: 'rgba(255, 87, 51, 0.2)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { ticks: { color: '#000' } },
                y: { ticks: { color: '#000' } }
            }
        }
    });
}

function actualizarGraficoProtocolos(datos) {
    if (!Array.isArray(datos)) datos = [datos];

    datos.forEach(packet => {
        const protocolo = protocoloMap[packet.protocolo] || packet.protocolo || "Desconocido";
        protocoloConteo[protocolo] = (protocoloConteo[protocolo] || 0) + 1;
    });

    const ctx = document.getElementById("protocolChart").getContext("2d");
    const labels = Object.keys(protocoloConteo);
    const values = Object.values(protocoloConteo);

    if (protocolChart) protocolChart.destroy();

    protocolChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Cantidad de Paquetes",
                data: values,
                backgroundColor: "#6366f1",
                borderColor: "#4f46e5",
                borderWidth: 1,
                borderRadius: 5,
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { ticks: { color: '#000' } },
                y: { beginAtZero: true, ticks: { color: '#000' } }
            }
        }
    });
}

async function iniciarCaptura() {
    try {
        const response = await fetch('/iniciar_captura', {
            method: 'POST',
            headers: { "Content-Type": "application/json" }
        });

        const data = await response.json();
        if (response.ok) {
            mostrarMensaje("✅ " + data.mensaje, "success");
            capturaActiva = true;
            actualizarBotones(true);
            cargarDatosIniciales();
            iniciarAutoRefresh();
        } else {
            mostrarMensaje("⚠️ " + data.mensaje, "warning");
        }
    } catch (error) {
        console.error("❌ Error al iniciar captura:", error);
        mostrarMensaje("❌ No se pudo iniciar la captura.", "error");
    }
}

async function detenerCaptura() {
    try {
        const response = await fetch('/detener_captura', {
            method: 'POST',
            headers: { "Content-Type": "application/json" }
        });

        const data = await response.json();
        if (response.ok) {
            mostrarMensaje("🛑 " + data.mensaje, "success");
            capturaActiva = false;
            actualizarBotones(false);
            detenerAutoRefresh();
        } else {
            mostrarMensaje("⚠️ " + data.mensaje, "warning");
        }
    } catch (error) {
        console.error("❌ Error al detener captura:", error);
        mostrarMensaje("❌ No se pudo detener la captura.", "error");
    }
}

function iniciarAutoRefresh() {
    if (intervaloAutoRefresh) clearInterval(intervaloAutoRefresh);

    intervaloAutoRefresh = setInterval(() => {
        if (capturaActiva) {
            console.log("🔁 Refrescando datos...");
            cargarDatosIniciales();
        }
    }, 1000);
}

function detenerAutoRefresh() {
    if (intervaloAutoRefresh) {
        clearInterval(intervaloAutoRefresh);
        intervaloAutoRefresh = null;
        console.log("🧊 Auto-refresh detenido.");
    }
}

function actualizarBotones(capturaIniciada) {
    const btnIniciar = document.getElementById("btnIniciar");
    const btnDetener = document.getElementById("btnDetener");

    if (!btnIniciar || !btnDetener) return;

    btnIniciar.classList.toggle("opacity-50", capturaIniciada);
    btnIniciar.classList.toggle("cursor-not-allowed", capturaIniciada);
    btnIniciar.disabled = capturaIniciada;

    btnDetener.classList.toggle("opacity-50", !capturaIniciada);
    btnDetener.classList.toggle("cursor-not-allowed", !capturaIniciada);
    btnDetener.disabled = !capturaIniciada;
}



document.addEventListener("DOMContentLoaded", function () {
    const mensajeEstado = document.getElementById("mensajeEstado");
  
    // Ocultar el mensaje por defecto
    if (mensajeEstado) {
      mensajeEstado.style.display = "none";
    }
  });
  
  // Función para mostrar mensaje solo cuando haya contenido
  function mostrarMensaje(texto, tipo = "info") {
    const mensajeEstado = document.getElementById("mensajeEstado");
  
    if (mensajeEstado) {
      mensajeEstado.textContent = texto;
      
      // Cambia el color según el tipo de mensaje
      if (tipo === "error") {
        mensajeEstado.className = "mt-4 font-semibold text-lg text-red-500";
      } else if (tipo === "success") {
        mensajeEstado.className = "mt-4 font-semibold text-lg text-green-500";
      } else {
        mensajeEstado.className = "mt-4 font-semibold text-lg text-blue-500";
      }
  
      // Mostrar solo si hay texto
      mensajeEstado.style.display = texto ? "block" : "none";
    }
  }
  