// Variables globales
let trafficChart, protocolChart, portChart, ipChart, sizeChart;
let paquetesTotales = [];
let protocoloConteo = {};
let intervaloAutoRefresh;
let capturaActiva = false;

const protocoloMap = {
    "1": "ICMP", "6": "TCP", "17": "UDP", "2": "IGMP", "89": "OSPF",
    "47": "GRE", "50": "ESP", "51": "AH", "58": "ICMPv6",
};

document.addEventListener("DOMContentLoaded", () => {
    console.log("🚀 Página cargada, iniciando configuración...");

    const socket = io();

    socket.on("nuevo_paquete", function (data) {
        if (capturaActiva) {
            console.log("📡 Paquete recibido vía WebSocket:", data);
            agregarPaqueteATabla(data);
            actualizarGraficos(data);
            actualizarContadores();
        }
    });

    // Event Listeners
    document.getElementById("btnIniciar").addEventListener("click", iniciarCaptura);
    document.getElementById("btnDetener").addEventListener("click", detenerCaptura);
    document.getElementById("btnFiltrar").addEventListener("click", mostrarPanelFiltros);
    document.getElementById("btnExportar").addEventListener("click", exportarDatos);
    document.getElementById("btnRegresar").addEventListener("click", () => window.location.href = "/dashboard");
    document.getElementById("buscador").addEventListener("input", filtrarTabla);
    document.getElementById("filtroProtocolo").addEventListener("change", filtrarTabla);
    document.getElementById("filtroTamaño").addEventListener("change", filtrarTabla);
    document.getElementById("limpiarFiltros").addEventListener("click", limpiarFiltros);
    document.getElementById("formFiltros").addEventListener("submit", aplicarFiltros);

    // Event listeners para cambiar entre gráficos de pie y barra
    document.querySelectorAll('[data-chart]').forEach(button => {
        button.addEventListener('click', cambiarTipoGrafico);
    });

    // Event listeners para cambiar el rango de tiempo del gráfico de tráfico
    document.querySelectorAll('[data-time]').forEach(button => {
        button.addEventListener('click', cambiarRangoTiempo);
    });

    // Inicializar gráficos
    inicializarGraficos();

    // Cargar datos iniciales
    cargarDatosIniciales();

    // Inicializar tooltips
    inicializarTooltips();

    // Inicializar tema
    inicializarTema();
});

function inicializarGraficos() {
    trafficChart = crearGrafico('trafficChart', 'line', 'Tráfico en Tiempo Real');
    protocolChart = crearGrafico('protocolChart', 'pie', 'Protocolos Detectados');
    portChart = crearGrafico('portChart', 'bar', 'Distribución por Puertos');
    ipChart = crearGrafico('ipChart', 'bar', 'Actividad por IP');
    sizeChart = crearGrafico('sizeChart', 'bar', 'Tamaño de Paquetes');
}

function crearGrafico(id, tipo, titulo) {
    const ctx = document.getElementById(id).getContext('2d');
    return new Chart(ctx, {
        type: tipo,
        data: {
            labels: [],
            datasets: [{
                label: titulo,
                data: [],
                backgroundColor: 'rgba(99, 102, 241, 0.5)',
                borderColor: 'rgb(99, 102, 241)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

async function cargarDatosIniciales() {
    try {
        const response = await fetch('/datos_red');
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        const datos = await response.json();

        datos.sort((a, b) => b.idescanear_red - a.idescanear_red);
        paquetesTotales = datos;
        actualizarTabla(datos);
        actualizarGraficos(datos);
        actualizarContadores();
        mostrarMensaje("✅ Datos cargados correctamente.", "success");
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
}

function agregarPaqueteATabla(dato) {
    const tableBody = document.getElementById('packetTable');
    if (!tableBody) return;

    const fechaFormateada = dato.fecha_captura ? new Date(dato.fecha_captura).toLocaleString() : 'N/A';
    const protocoloLegible = protocoloMap[dato.protocolo] || dato.protocolo || "Desconocido";

    const row = `
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors duration-150">
            <td class="p-2 text-center">${dato.idescanear_red || 'N/A'}</td>
            <td class="p-2">${dato.iporigen || 'N/A'}</td>
            <td class="p-2">${dato.ipdestino || 'N/A'}</td>
            <td class="p-2 truncate-cell" title="${dato.mac_origen || 'N/A'}">${dato.mac_origen || 'N/A'}</td>
            <td class="p-2 truncate-cell" title="${dato.mac_destino || 'N/A'}">${dato.mac_destino || 'N/A'}</td>
            <td class="p-2 text-center">${dato.puerto_origen || 'N/A'}</td>
            <td class="p-2 text-center">${dato.puerto_destino || 'N/A'}</td>
            <td class="p-2">
                <span class="px-2 py-1 bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200 rounded-full text-xs font-medium">
                    ${protocoloLegible}
                </span>
            </td>
            <td class="p-2 text-right">${dato.tamano || 'N/A'}</td>
            <td class="p-2">${fechaFormateada}</td>
            <td class="p-2 text-center">${dato.ttl || 'N/A'}</td>
        </tr>
    `;
    tableBody.insertAdjacentHTML("afterbegin", row);
}

function actualizarGraficos(datos) {
    if (!Array.isArray(datos)) datos = [datos];
    actualizarGraficoTrafico(datos);
    actualizarGraficoProtocolos(datos);
    actualizarGraficoPuertos(datos);
    actualizarGraficoIPs(datos);
    actualizarGraficoTamaños(datos);
}

function actualizarGraficoTrafico(datos) {
    const labels = datos.map(d => d.fecha_captura ? new Date(d.fecha_captura).toLocaleTimeString() : 'N/A');
    const paquetes = datos.map(d => d.tamano || 0);

    trafficChart.data.labels = labels.slice(-50);
    trafficChart.data.datasets[0].data = paquetes.slice(-50);
    trafficChart.update();
}

function actualizarGraficoProtocolos(datos) {
    const protocolos = datos.reduce((acc, d) => {
        const protocolo = protocoloMap[d.protocolo] || d.protocolo || "Desconocido";
        acc[protocolo] = (acc[protocolo] || 0) + 1;
        return acc;
    }, {});

    protocolChart.data.labels = Object.keys(protocolos);
    protocolChart.data.datasets[0].data = Object.values(protocolos);
    protocolChart.update();
}

function actualizarGraficoPuertos(datos) {
    const puertos = datos.reduce((acc, d) => {
        acc[d.puerto_destino] = (acc[d.puerto_destino] || 0) + 1;
        return acc;
    }, {});

    const topPuertos = Object.entries(puertos)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

    portChart.data.labels = topPuertos.map(p => p[0]);
    portChart.data.datasets[0].data = topPuertos.map(p => p[1]);
    portChart.update();
}

function actualizarGraficoIPs(datos) {
    const ips = datos.reduce((acc, d) => {
        acc[d.iporigen] = (acc[d.iporigen] || 0) + 1;
        return acc;
    }, {});

    const topIPs = Object.entries(ips)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

    ipChart.data.labels = topIPs.map(ip => ip[0]);
    ipChart.data.datasets[0].data = topIPs.map(ip => ip[1]);
    ipChart.update();
}

function actualizarGraficoTamaños(datos) {
    const tamaños = datos.reduce((acc, d) => {
        const size = d.tamano || 0;
        if (size < 100) acc.pequeño++;
        else if (size < 1000) acc.mediano++;
        else acc.grande++;
        return acc;
    }, { pequeño: 0, mediano: 0, grande: 0 });

    sizeChart.data.labels = ['Pequeño (<100)', 'Mediano (100-1000)', 'Grande (>1000)'];
    sizeChart.data.datasets[0].data = [tamaños.pequeño, tamaños.mediano, tamaños.grande];
    sizeChart.update();
}

function actualizarContadores() {
    document.getElementById('paquetesTotal').textContent = paquetesTotales.length;
    document.getElementById('traficoNormal').textContent = paquetesTotales.filter(p => p.tamano < 1000).length;
    document.getElementById('alertasTotal').textContent = paquetesTotales.filter(p => p.tamano >= 1000 && p.tamano < 5000).length;
    document.getElementById('amenazasTotal').textContent = paquetesTotales.filter(p => p.tamano >= 5000).length;
}

async function iniciarCaptura() {
    try {
        const response = await fetch('/iniciar_captura', { method: 'POST' });
        const data = await response.json();
        if (response.ok) {
            mostrarMensaje("✅ " + data.mensaje, "success");
            capturaActiva = true;
            actualizarBotones(true);
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
        const response = await fetch('/detener_captura', { method: 'POST' });
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
    }, 5000);
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
    const mensajeEstado = document.getElementById("mensajeEstado");

    btnIniciar.disabled = capturaIniciada;
    btnIniciar.classList.toggle("opacity-50", capturaIniciada);
    btnIniciar.classList.toggle("cursor-not-allowed", capturaIniciada);

    btnDetener.disabled = !capturaIniciada;
    btnDetener.classList.toggle("opacity-50", !capturaIniciada);
    btnDetener.classList.toggle("cursor-not-allowed", !capturaIniciada);

    mensajeEstado.className = capturaIniciada ? "state-active mb-6" : "state-inactive mb-6";
    mensajeEstado.innerHTML = capturaIniciada 
        ? '<span class="inline-flex items-center gap-2"><i data-lucide="activity" class="w-5 h-5"></i>Captura en curso</span>'
        : '<span class="inline-flex items-center gap-2"><i data-lucide="pause-circle" class="w-5 h-5"></i>Captura detenida</span>';
    lucide.createIcons();
}

function mostrarPanelFiltros() {
    document.getElementById('filtrosPanel').classList.remove('hidden');
}

function limpiarFiltros(e) {
    e.preventDefault();
    document.getElementById('formFiltros').reset();
}

function aplicarFiltros(e) {
    e.preventDefault();
    const filtros = {
        ipOrigen: document.getElementById('filtroIPOrigen').value,
        ipDestino: document.getElementById('filtroIPDestino').value,
        puertoOrigen: document.getElementById('filtroPuertoOrigen').value,
        puertoDestino: document.getElementById('filtroPuertoDestino').value,
        protocolo: document.getElementById('filtroProtocoloAvanzado').value,
        tamañoMin: document.getElementById('filtroTamañoMin').value,
        tamañoMax: document.getElementById('filtroTamañoMax').value,
        fechaInicio: document.getElementById('filtroFechaInicio').value,
        fechaFin: document.getElementById('filtroFechaFin').value
    };

    const datosFiltrados = filtrarDatos(paquetesTotales, filtros);
    actualizarTabla(datosFiltrados);
    actualizarGraficos(datosFiltrados);
    document.getElementById('filtrosPanel').classList.add('hidden');
}

function filtrarDatos(datos, filtros) {
    return datos.filter(paquete => {
        return (!filtros.ipOrigen || paquete.iporigen.includes(filtros.ipOrigen)) &&
               (!filtros.ipDestino || paquete.ipdestino.includes(filtros.ipDestino)) &&
               (!filtros.puertoOrigen || paquete.puerto_origen == filtros.puertoOrigen) &&
               (!filtros.puertoDestino || paquete.puerto_destino == filtros.puertoDestino) &&
               (!filtros.protocolo || protocoloMap[paquete.protocolo] == filtros.protocolo) &&
               (!filtros.tamañoMin || paquete.tamano >= parseInt(filtros.tamañoMin)) &&
               (!filtros.tamañoMax || paquete.tamano <= parseInt(filtros.tamañoMax)) &&
               (!filtros.fechaInicio || new Date(paquete.fecha_captura) >= new Date(filtros.fechaInicio)) &&
               (!filtros.fechaFin || new Date(paquete.fecha_captura) <= new Date(filtros.fechaFin));
    });
}

function exportarDatos() {
    const datos = paquetesTotales.map(p => ({
        ID: p.idescanear_red,
        IP_Origen: p.iporigen,
        IP_Destino: p.ipdestino,
        MAC_Origen: p.mac_origen,
        MAC_Destino: p.mac_destino,
        Puerto_Origen: p.puerto_origen,
        Puerto_Destino: p.puerto_destino,
        Protocolo: protocoloMap[p.protocolo] || p.protocolo,
        Tamaño: p.tamano,
        Fecha: p.fecha_captura,
        TTL: p.ttl
    }));

    const csv = Papa.unparse(datos);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute("download", "datos_red.csv");
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

function cambiarTipoGrafico(e) {
    const tipo = e.target.getAttribute('data-chart');
    const chartId = e.target.closest('.bg-white').querySelector('canvas').id;
    const chart = Chart.getChart(chartId);
    
    if (chart) {
        chart.config.type = tipo;
        chart.update();
    }
}

function cambiarRangoTiempo(e) {
    const tiempo = e.target.getAttribute('data-time');
    const ahora = new Date();
    let inicio;

    switch (tiempo) {
        case '1m':
            inicio = new Date(ahora - 60000);
            break;
        case '5m':
            inicio = new Date(ahora - 300000);
            break;
        case '15m':
            inicio = new Date(ahora - 900000);
            break;
        default:
            inicio = new Date(ahora - 900000); // Por defecto 15 minutos
    }

    const datosFiltrados = paquetesTotales.filter(p => new Date(p.fecha_captura) >= inicio);
    actualizarGraficoTrafico(datosFiltrados);
}

function filtrarTabla() {
    const busqueda = document.getElementById('buscador').value.toLowerCase();
    const protocolo = document.getElementById('filtroProtocolo').value;
    const tamaño = document.getElementById('filtroTamaño').value;

    const datosFiltrados = paquetesTotales.filter(paquete => {
        const cumpleBusqueda = Object.values(paquete).some(valor => 
            String(valor).toLowerCase().includes(busqueda)
        );
        const cumpleProtocolo = !protocolo || protocoloMap[paquete.protocolo] == protocolo;
        const cumpleTamaño = !tamaño || (
            (tamaño === 'pequeño' && paquete.tamano < 100) ||
            (tamaño === 'mediano' && paquete.tamano >= 100 && paquete.tamano <= 1000) ||
            (tamaño === 'grande' && paquete.tamano > 1000)
        );

        return cumpleBusqueda && cumpleProtocolo && cumpleTamaño;
    });

    actualizarTabla(datosFiltrados);
}

function inicializarTooltips() {
    tippy('.truncate-cell', {
        content: (reference) => reference.getAttribute('title'),
        placement: 'top',
    });
}

function inicializarTema() {
    const temaSwitch = document.getElementById('temaSwitch');
    temaSwitch.addEventListener('click', () => {
        document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
    });

    if (localStorage.getItem('theme') === 'dark' || 
        (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
}

function mostrarMensaje(texto, tipo = "info") {
    const mensajeEstado = document.getElementById("mensajeEstado");
    if (mensajeEstado) {
        mensajeEstado.textContent = texto;
        mensajeEstado.className = tipo === "error" ? "state-inactive mb-6" : "state-active mb-6";
        mensajeEstado.style.display = "block";
        setTimeout(() => {
            mensajeEstado.style.display = "none";
        }, 5000);
    }
}

// Asegúrate de que los iconos de Lucide se actualicen cuando sea necesario
function actualizarIconos() {
    lucide.createIcons();
}