// Variables globales
let trafficChartInstance, protocolChartInstance, portChartInstance, ipChartInstance, sizeChartInstance;
let todosLosPaquetes = []; // Almacenará todos los paquetes cargados del servidor
let paquetesFiltradosYOrdenados = []; // Paquetes actualmente mostrados en la tabla después de filtrar y ordenar
let capturaActivaLocal = false; // Estado local de la captura, sincronizado con el servidor idealmente
let intervaloActualizacion;
const INTERVALO_POLLING_MS = 5000; // Pedir datos nuevos cada 5 segundos

// Mapeo de números de protocolo a nombres legibles
const MAPA_PROTOCOLOS = {
    "1": "ICMP", "2": "IGMP", "6": "TCP", "17": "UDP", "47": "GRE", 
    "50": "ESP", "51": "AH", "88": "EIGRP", "89": "OSPF", "58": "ICMPv6"
    // Puedes añadir más si tu IDS los detecta con otros números
};
// Lista de protocolos para los selectores de filtro
const OPCIONES_PROTOCOLO_FILTRO = ["TCP", "UDP", "ICMP", "HTTP", "HTTPS", "DNS", "ARP", "NTP", "SMTP", "IGMP", "OSPF", "GRE", "ESP", "AH"];

// --- INICIALIZACIÓN AL CARGAR EL DOM ---
document.addEventListener("DOMContentLoaded", () => {
    console.log("🛡️ IDS Monitoreo: DOM cargado, iniciando configuración (versión Polling)...");
    
    inicializarTema();
    inicializarIconosLucide(); // Asegúrate que Lucide se cargue antes de esto
    configurarEventListenersGenerales();
    inicializarGraficos();
    cargarDatosInicialesYConfigurarPolling(); // Carga inicial y configura el polling según el estado
    actualizarFechaHora();
    setInterval(actualizarFechaHora, 1000); // Actualiza reloj cada segundo
    popularSelectFiltroProtocolos();
});

function inicializarIconosLucide() {
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    } else {
        // Reintentar después de un breve retraso si Lucide aún no está listo
        setTimeout(() => {
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            } else {
                console.warn("Lucide icons no está disponible incluso después del retraso.");
            }
        }, 500);
    }
}

function popularSelectFiltroProtocolos() {
    const selectProtocoloAvanzado = document.getElementById('filtroProtocoloAvanzado');
    const selectProtocoloRapido = document.getElementById('filtroProtocolo');
    
    const agregarOpcion = (selectElement, valor, texto) => {
        if (selectElement) {
            const option = document.createElement('option');
            option.value = valor;
            option.textContent = texto;
            selectElement.appendChild(option);
        }
    };

    OPCIONES_PROTOCOLO_FILTRO.forEach(p => {
        agregarOpcion(selectProtocoloAvanzado, p, p);
    });
    // Llenar filtro rápido con los más comunes o todos si prefieres
    ["TCP", "UDP", "ICMP", "HTTP", "HTTPS", "DNS"].forEach(p => {
        agregarOpcion(selectProtocoloRapido, p, p);
    });
}

function actualizarFechaHora() {
  const ahora = new Date();
  const opciones = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'};
  const el = document.getElementById('currentDateTime');
  if(el) el.textContent = ahora.toLocaleDateString('es-ES', opciones);
}

function configurarEventListenersGenerales() {
    document.getElementById('menuToggle')?.addEventListener('click', () => document.getElementById('sideMenu')?.classList.toggle('hidden'));
    document.getElementById('temaSwitch')?.addEventListener('click', toggleTema);
    
    document.getElementById('btnIniciar')?.addEventListener('click', manejarInicioCaptura);
    document.getElementById('btnDetener')?.addEventListener('click', manejarDetencionCaptura);
    document.getElementById('btnFiltrar')?.addEventListener('click', () => document.getElementById('filtrosPanel')?.classList.remove('hidden'));
    document.getElementById('btnExportar')?.addEventListener('click', exportarDatosCSV);
    
    document.getElementById('cerrarDetalles')?.addEventListener('click', () => document.getElementById('detallesPanel')?.classList.add('hidden'));
    document.getElementById('cerrarFiltros')?.addEventListener('click', () => document.getElementById('filtrosPanel')?.classList.add('hidden'));
    
    document.getElementById('buscador')?.addEventListener('input', aplicarFiltrosRapidos);
    document.getElementById('filtroProtocolo')?.addEventListener('change', aplicarFiltrosRapidos);
    document.getElementById('filtroTamaño')?.addEventListener('change', aplicarFiltrosRapidos);

    document.getElementById('formFiltros')?.addEventListener('submit', (e) => { e.preventDefault(); aplicarFiltrosAvanzados(); });
    document.getElementById('limpiarFiltros')?.addEventListener('click', limpiarFormularioFiltros);

    document.querySelectorAll('#packetTable thead th[data-sort-key]').forEach(th => {
        th.addEventListener('click', () => manejarOrdenamientoTabla(th));
    });
    
    document.getElementById('packetTable')?.addEventListener('click', (event) => {
        const fila = event.target.closest('tr');
        const actionButton = event.target.closest('button'); 
        
        if (actionButton && fila && fila.dataset.paqueteId) {
             const paqueteId = parseInt(fila.dataset.paqueteId);
             const paquete = todosLosPaquetes.find(p => p.idescanear_red === paqueteId);
             if (paquete) mostrarDetallesPaquete(paquete);
        }
    });

    document.querySelectorAll('.bg-white [data-time]').forEach(button => { // Más específico para evitar conflictos
        button.addEventListener('click', (e) => cambiarRangoTiempoGraficoTrafico(e.target.dataset.time));
    });
    document.querySelectorAll('.bg-white [data-chart-type]').forEach(button => { // Más específico
        button.addEventListener('click', (e) => {
            const chartType = e.target.dataset.chartType;
            const chartTargetId = e.target.dataset.chartTarget;
            cambiarTipoGrafico(chartTargetId, chartType);
        });
    });
}

// --- LÓGICA DE CAPTURA Y POLLING ---
async function manejarInicioCaptura() {
    try {
        mostrarMensaje("⚙️ Iniciando captura...", "info", 0); // 0 para no auto-cerrar
        const response = await fetch('/iniciar_captura', { method: 'POST' });
        const data = await response.json();
        if (response.ok && data.status === 'success') {
            capturaActivaLocal = true;
            actualizarEstadoCapturaUI(true);
            mostrarMensaje(`✅ ${data.mensaje || 'Captura iniciada.'}`, "success");
            localStorage.setItem('capturaActiva', 'true');
            if (intervaloActualizacion) clearInterval(intervaloActualizacion);
            intervaloActualizacion = setInterval(solicitarNuevosDatos, INTERVALO_POLLING_MS);
            solicitarNuevosDatos(); // Primera carga inmediata
        } else {
            mostrarMensaje(`⚠️ ${data.mensaje || 'No se pudo iniciar la captura.'}`, "warning");
            actualizarEstadoCapturaUI(false); // Asegurar que la UI refleje el fallo
        }
    } catch (error) {
        console.error("❌ Error al iniciar captura:", error);
        mostrarMensaje("❌ Error de red al intentar iniciar la captura.", "error");
        actualizarEstadoCapturaUI(false);
    }
}

async function manejarDetencionCaptura() {
    try {
        mostrarMensaje("⚙️ Deteniendo captura...", "info", 0);
        const response = await fetch('/detener_captura', { method: 'POST' });
        const data = await response.json();
        if (response.ok && data.status === 'success') {
            capturaActivaLocal = false;
            actualizarEstadoCapturaUI(false);
            mostrarMensaje(`🛑 ${data.mensaje || 'Captura detenida.'}`, "info");
            localStorage.setItem('capturaActiva', 'false');
            if (intervaloActualizacion) clearInterval(intervaloActualizacion);
        } else {
            mostrarMensaje(`⚠️ ${data.mensaje || 'No se pudo detener la captura.'}`, "warning");
            // No cambiar UI si el backend falla al detener, podría seguir activa
        }
    } catch (error) {
        console.error("❌ Error al detener captura:", error);
        mostrarMensaje("❌ Error de red al intentar detener la captura.", "error");
    }
}

async function cargarDatosInicialesYConfigurarPolling() {
    console.log("🔄 Cargando datos iniciales y configurando polling...");
    try {
        // Idealmente, este endpoint devuelve el estado de captura del servidor.
        const response = await fetch('/datos_red'); 
        if (!response.ok) throw new Error(`HTTP Error al cargar datos iniciales: ${response.status}`);
        
        const data = await response.json();
        let paquetesRecibidos = [];
        // Asumimos que el backend puede devolver un objeto con 'paquetes' y 'captura_activa_servidor'
        // o solo un array de paquetes.
        let capturaActivaServidor = localStorage.getItem('capturaActiva') === 'true'; // Default a localStorage

        if (data && typeof data === 'object' && data !== null) {
            if (Array.isArray(data.paquetes)) {
                paquetesRecibidos = data.paquetes;
            } else if (Array.isArray(data)) { // Fallback si solo devuelve array
                paquetesRecibidos = data;
            }
            if (typeof data.captura_activa_servidor === 'boolean') {
                capturaActivaServidor = data.captura_activa_servidor;
            }
        } else if (Array.isArray(data)) {
             paquetesRecibidos = data;
        }

        todosLosPaquetes = paquetesRecibidos.sort((a, b) => b.idescanear_red - a.idescanear_red);
        aplicarFiltrosRapidos(); // Renderiza la tabla con los filtros actuales
        actualizarTodosLosGraficos(todosLosPaquetes); 
        actualizarContadoresGlobales(todosLosPaquetes);
        console.log(`📊 ${todosLosPaquetes.length} paquetes iniciales cargados.`);
        
        capturaActivaLocal = capturaActivaServidor;
        localStorage.setItem('capturaActiva', capturaActivaLocal.toString()); // Sincronizar localStorage
        actualizarEstadoCapturaUI(capturaActivaLocal);

        if (capturaActivaLocal) {
            if (intervaloActualizacion) clearInterval(intervaloActualizacion);
            intervaloActualizacion = setInterval(solicitarNuevosDatos, INTERVALO_POLLING_MS);
            mostrarMensaje("🔄 Captura activa, actualizando datos periódicamente...", "info", 3000);
        }

    } catch (error) {
        console.error("❌ Error en cargarDatosInicialesYConfigurarPolling:", error);
        mostrarMensaje("⚠️ Error al cargar datos iniciales. La captura puede estar detenida.", "warning");
        actualizarEstadoCapturaUI(false); // Asumir que no está activa si hay error
    }
}

async function solicitarNuevosDatos() {
    if (!capturaActivaLocal) {
        if (intervaloActualizacion) clearInterval(intervaloActualizacion);
        return;
    }
    // console.log("📡 Solicitando nuevos datos al servidor...");
    try {
        const response = await fetch('/datos_red');
        if (!response.ok) {
            // Si el servidor devuelve un error específico indicando que la captura ya no está activa
            if (response.status === 409) { // Ejemplo: 409 Conflict = captura no activa en servidor
                console.warn("Servidor indica que la captura no está activa. Deteniendo polling.");
                manejarDetencionCaptura(); // Llama a la función para actualizar UI y estado local
                return;
            }
            throw new Error(`HTTP Error en polling: ${response.status}`);
        }
        const data = await response.json();
        let paquetesRecibidos = [];

        if (data && Array.isArray(data.paquetes)) { // Si el backend devuelve {paquetes: [...]}
            paquetesRecibidos = data.paquetes;
        } else if (Array.isArray(data)) { // Si el backend solo devuelve [...]
            paquetesRecibidos = data;
        }

        if (paquetesRecibidos.length > 0) {
            // Estrategia simple: reemplazar todos los paquetes.
            // Para optimizar, podrías comparar con `todosLosPaquetes` y solo añadir los nuevos.
            todosLosPaquetes = paquetesRecibidos.sort((a,b) => b.idescanear_red - a.idescanear_red); 
            // console.log(`📦 ${todosLosPaquetes.length} paquetes totales actualizados vía polling.`);
            aplicarFiltrosRapidos(); // Re-renderiza la tabla con los nuevos datos y filtros actuales
            actualizarTodosLosGraficos(paquetesFiltradosYOrdenados.length > 0 ? paquetesFiltradosYOrdenados : todosLosPaquetes);
            actualizarContadoresGlobales(todosLosPaquetes);
        }
    } catch (error) {
        console.error("❌ Error durante el polling:", error);
        // Considerar detener el polling si hay errores repetidos de red
        // mostrarMensaje("⚠️ Problema de red al actualizar datos.", "warning", 2000);
    }
}

function actualizarEstadoCapturaUI(activa) {
    const btnIniciar = document.getElementById("btnIniciar");
    const btnDetener = document.getElementById("btnDetener");
    const mensajeEstado = document.getElementById("mensajeEstado");

    if (btnIniciar) { btnIniciar.disabled = activa; btnIniciar.classList.toggle("opacity-50", activa); btnIniciar.classList.toggle("cursor-not-allowed", activa); }
    if (btnDetener) { btnDetener.disabled = !activa; btnDetener.classList.toggle("opacity-50", !activa); btnDetener.classList.toggle("cursor-not-allowed", !activa); }
    if (mensajeEstado) {
        mensajeEstado.className = activa ? "state-active mb-6 py-3 px-4 text-sm" : "state-inactive mb-6 py-3 px-4 text-sm";
        mensajeEstado.innerHTML = activa 
            ? `<span class="inline-flex items-center gap-2"><i data-lucide="activity" class="w-5 h-5"></i>Captura en curso. Actualizando...</span>`
            : `<span class="inline-flex items-center gap-2"><i data-lucide="pause-circle" class="w-5 h-5"></i>Captura detenida.</span>`;
        if (typeof lucide !== 'undefined') { const i = mensajeEstado.querySelector('i'); if(i) lucide.createIcons({nodes: [i]});}
    }
}

// --- MANEJO DE LA TABLA ---
let sortConfig = { key: 'idescanear_red', direction: 'desc' }; // Default sort

function manejarOrdenamientoTabla(thElement) {
    const newKey = thElement.dataset.sortKey;
    let newDirection = 'asc';
    if (sortConfig.key === newKey && sortConfig.direction === 'asc') {
        newDirection = 'desc';
    }
    sortConfig = { key: newKey, direction: newDirection };
    
    document.querySelectorAll('#packetTable thead th[data-sort-key] i').forEach(icon => {
        icon.setAttribute('data-lucide', 'arrow-up-down'); // Reset other icons
    });
    const currentIcon = thElement.querySelector('i');
    if(currentIcon) currentIcon.setAttribute('data-lucide', newDirection === 'asc' ? 'arrow-up' : 'arrow-down');
    if (typeof lucide !== 'undefined') lucide.createIcons();

    renderizarTabla(); // Re-renderiza la tabla con el nuevo orden
}

function ordenarPaquetes(paquetesAOrdenar) {
    // Crea una copia para no modificar el array original de filtros rápidos
    return [...paquetesAOrdenar].sort((a, b) => {
        let valA = a[sortConfig.key];
        let valB = b[sortConfig.key];

        // Conversión para ordenamiento numérico o de fechas
        if (['idescanear_red', 'tamano', 'ttl', 'puerto_origen', 'puerto_destino'].includes(sortConfig.key)) {
            valA = Number(valA);
            valB = Number(valB);
        } else if (sortConfig.key === 'fecha_captura') {
            valA = new Date(valA).getTime();
            valB = new Date(valB).getTime();
        } else if (typeof valA === 'string') {
            valA = valA.toLowerCase();
            valB = valB.toLowerCase();
        }

        if (valA < valB) return sortConfig.direction === 'asc' ? -1 : 1;
        if (valA > valB) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
    });
}

function renderizarTabla() {
    const tablaBody = document.getElementById('packetTable');
    const mensajeSinResultados = document.getElementById('noResultsMessage');
    if (!tablaBody || !mensajeSinResultados) return;

    tablaBody.innerHTML = ''; // Limpiar tabla antes de re-renderizar

    // 1. Filtrar `todosLosPaquetes` usando los filtros rápidos
    const paquetesParaMostrar = filtrarPaquetesConFiltrosRapidos(todosLosPaquetes);
    // 2. Ordenar los paquetes filtrados
    paquetesFiltradosYOrdenados = ordenarPaquetes(paquetesParaMostrar);
    
    if (paquetesFiltradosYOrdenados.length === 0) {
        mensajeSinResultados.classList.remove('hidden');
        tablaBody.innerHTML = `<tr><td colspan="12" class="text-center p-4 text-gray-500 dark:text-gray-400">No se encontraron paquetes que coincidan con los filtros actuales.</td></tr>`;
    } else {
        mensajeSinResultados.classList.add('hidden');
        paquetesFiltradosYOrdenados.forEach(paquete => {
            const fila = crearFilaDePaquete(paquete);
            tablaBody.appendChild(fila);
        });
    }
    if (typeof tippy !== 'undefined') inicializarTooltipsTabla();
}

function crearFilaDePaquete(paquete) {
    const fila = document.createElement('tr');
    fila.className = 'hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-150 text-xs'; // Tamaño de fuente base para celdas
    fila.dataset.paqueteId = paquete.idescanear_red;

    const fechaFormateada = paquete.fecha_captura ? new Date(paquete.fecha_captura).toLocaleString('es-ES', { dateStyle: 'short', timeStyle: 'medium'}) : 'N/A';
    const protocoloLegible = MAPA_PROTOCOLOS[String(paquete.protocolo)] || paquete.protocolo_nombre || String(paquete.protocolo) || "N/A";
    
    let protocoloBadgeClass = "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
    if (protocoloLegible === 'TCP') protocoloBadgeClass = "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
    else if (protocoloLegible === 'UDP') protocoloBadgeClass = "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
    else if (protocoloLegible === 'ICMP') protocoloBadgeClass = "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
    else if (protocoloLegible === 'HTTP') protocoloBadgeClass = "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200";
    else if (protocoloLegible === 'HTTPS') protocoloBadgeClass = "bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200";


    fila.innerHTML = `
        <td class="p-2 text-center">${paquete.idescanear_red || 'N/A'}</td>
        <td class="p-2 truncate-cell" title="${paquete.iporigen || 'N/A'}">${paquete.iporigen || 'N/A'}</td>
        <td class="p-2 truncate-cell" title="${paquete.ipdestino || 'N/A'}">${paquete.ipdestino || 'N/A'}</td>
        <td class="p-2 truncate-cell hidden md:table-cell" title="${paquete.mac_origen || 'N/A'}">${paquete.mac_origen || 'N/A'}</td>
        <td class="p-2 truncate-cell hidden md:table-cell" title="${paquete.mac_destino || 'N/A'}">${paquete.mac_destino || 'N/A'}</td>
        <td class="p-2 text-center">${paquete.puerto_origen || 'N/A'}</td>
        <td class="p-2 text-center">${paquete.puerto_destino || 'N/A'}</td>
        <td class="p-2"><span class="px-2 py-0.5 rounded-full font-medium text-xs ${protocoloBadgeClass}">${protocoloLegible}</span></td>
        <td class="p-2 text-right">${paquete.tamano !== null ? paquete.tamano + ' B' : 'N/A'}</td>
        <td class="p-2">${fechaFormateada}</td>
        <td class="p-2 text-center">${paquete.ttl || 'N/A'}</td>
        <td class="p-2 text-center">
            <button class="text-primary-600 hover:text-primary-800 dark:text-primary-400 dark:hover:text-primary-200 p-1" title="Ver Detalles">
                <i data-lucide="eye" class="w-4 h-4 pointer-events-none"></i>
            </button>
        </td>
    `;
    if (typeof lucide !== 'undefined') {
        const eyeIcon = fila.querySelector('i[data-lucide="eye"]');
        if(eyeIcon) lucide.createIcons({nodes: [eyeIcon]});
    }
    return fila;
}

function mostrarDetallesPaquete(paquete) {
    const panel = document.getElementById('detallesPanel');
    const contenido = document.getElementById('contenidoDetallesPaquete');
    if (!panel || !contenido) return;

    const fechaFormateada = paquete.fecha_captura ? new Date(paquete.fecha_captura).toLocaleString('es-ES', { dateStyle: 'long', timeStyle: 'medium'}) : 'N/A';
    const protocoloLegible = MAPA_PROTOCOLOS[String(paquete.protocolo)] || paquete.protocolo_nombre || String(paquete.protocolo) || "N/A";

    // Construir el HTML para los detalles
    let detallesHtml = '<div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3 text-sm">';
    const campos = {
        "ID": paquete.idescanear_red, "Fecha": fechaFormateada,
        "IP Origen": paquete.iporigen, "IP Destino": paquete.ipdestino,
        "Puerto Origen": paquete.puerto_origen, "Puerto Destino": paquete.puerto_destino,
        "MAC Origen": paquete.mac_origen, "MAC Destino": paquete.mac_destino,
        "Protocolo": `${protocoloLegible} (Num: ${paquete.protocolo || 'N/A'})`,
        "Tamaño": paquete.tamano !== null ? `${paquete.tamano} bytes` : 'N/A',
        "TTL": paquete.ttl,
        "Flags TCP": paquete.flags_tcp
    };

    for (const [label, value] of Object.entries(campos)) {
        detallesHtml += `
            <div class="border-b dark:border-gray-700 py-1.5 flex">
                <strong class="text-gray-500 dark:text-gray-400 w-32 inline-block flex-shrink-0">${label}:</strong>
                <span class="text-gray-800 dark:text-gray-200 break-all">${value || 'N/A'}</span>
            </div>`;
    }
    detallesHtml += '</div>'; // Cierre del grid

    // Payload
    const payloadEscapado = paquete.payload ? paquete.payload.replace(/</g, '&lt;').replace(/>/g, '&gt;') : 'N/A';
    detallesHtml += `
        <div class="mt-4">
            <h4 class="text-md font-medium mb-1 text-gray-700 dark:text-gray-300">Payload (Preview):</h4>
            <pre class="text-xs font-mono whitespace-pre-wrap break-all overflow-x-auto p-3 bg-gray-100 dark:bg-gray-700 rounded-md max-h-40">${payloadEscapado.substring(0, 250)}${payloadEscapado.length > 250 ? '...' : ''}</pre>
        </div>`;
    
    contenido.innerHTML = detallesHtml;
    panel.classList.remove('hidden');
}

// --- FILTROS ---
function aplicarFiltrosRapidos() {
    renderizarTabla(); // RenderizarTabla ahora filtra y ordena
    actualizarTodosLosGraficos(paquetesFiltradosYOrdenados); // Actualizar gráficos con los datos filtrados y ordenados
    actualizarContadoresGlobales(todosLosPaquetes); // Contadores siempre sobre todos los paquetes
}

function filtrarPaquetesConFiltrosRapidos(paquetes) {
    const busqueda = document.getElementById('buscador')?.value.toLowerCase() || "";
    const protocoloSeleccionado = document.getElementById('filtroProtocolo')?.value || "";
    const tamañoSeleccionado = document.getElementById('filtroTamaño')?.value || "";

    return paquetes.filter(paquete => {
        const textoDelPaquete = `
            ${paquete.idescanear_red} ${paquete.iporigen} ${paquete.ipdestino} 
            ${paquete.mac_origen} ${paquete.mac_destino} 
            ${paquete.puerto_origen} ${paquete.puerto_destino} 
            ${MAPA_PROTOCOLOS[String(paquete.protocolo)] || paquete.protocolo_nombre || String(paquete.protocolo)} 
            ${paquete.tamano} ${paquete.ttl}`.toLowerCase();
        
        const cumpleBusqueda = !busqueda || textoDelPaquete.includes(busqueda);
        const cumpleProtocolo = !protocoloSeleccionado || (MAPA_PROTOCOLOS[String(paquete.protocolo)] || paquete.protocolo_nombre) === protocoloSeleccionado;
        
        let cumpleTamaño = true;
        if (tamañoSeleccionado) {
            if (tamañoSeleccionado === 'pequeño') cumpleTamaño = paquete.tamano < 100;
            else if (tamañoSeleccionado === 'mediano') cumpleTamaño = paquete.tamano >= 100 && paquete.tamano <= 1000;
            else if (tamañoSeleccionado === 'grande') cumpleTamaño = paquete.tamano > 1000;
        }
        return cumpleBusqueda && cumpleProtocolo && cumpleTamaño;
    });
}

function aplicarFiltrosAvanzados() {
    const filtros = {
        ipOrigen: document.getElementById('filtroIPOrigen').value.trim(),
        ipDestino: document.getElementById('filtroIPDestino').value.trim(),
        puertoOrigen: document.getElementById('filtroPuertoOrigen').value,
        puertoDestino: document.getElementById('filtroPuertoDestino').value,
        protocolo: document.getElementById('filtroProtocoloAvanzado').value,
        tamañoMin: document.getElementById('filtroTamañoMin').value,
        tamañoMax: document.getElementById('filtroTamañoMax').value,
        fechaInicio: document.getElementById('filtroFechaInicio').value,
        fechaFin: document.getElementById('filtroFechaFin').value
    };

    let datosFiltradosAvanzados = todosLosPaquetes.filter(paquete => {
        return (!filtros.ipOrigen || (paquete.iporigen && paquete.iporigen.includes(filtros.ipOrigen))) &&
               (!filtros.ipDestino || (paquete.ipdestino && paquete.ipdestino.includes(filtros.ipDestino))) &&
               (!filtros.puertoOrigen || paquete.puerto_origen == filtros.puertoOrigen) &&
               (!filtros.puertoDestino || paquete.puerto_destino == filtros.puertoDestino) &&
               (!filtros.protocolo || (MAPA_PROTOCOLOS[String(paquete.protocolo)] || paquete.protocolo_nombre) === filtros.protocolo) &&
               (!filtros.tamañoMin || paquete.tamano >= parseInt(filtros.tamañoMin)) &&
               (!filtros.tamañoMax || paquete.tamano <= parseInt(filtros.tamañoMax)) &&
               (!filtros.fechaInicio || new Date(paquete.fecha_captura) >= new Date(filtros.fechaInicio)) &&
               (!filtros.fechaFin || new Date(paquete.fecha_captura) <= new Date(filtros.fechaFin));
    });
    
    paquetesFiltradosYOrdenados = ordenarPaquetes(datosFiltradosAvanzados); // Ordenar después de filtrar
    renderizarTablaFiltrada(paquetesFiltradosYOrdenados); // Usar función que no re-filtra ni re-ordena
    actualizarTodosLosGraficos(paquetesFiltradosYOrdenados);
    document.getElementById('filtrosPanel')?.classList.add('hidden');
    mostrarMensaje(`🔎 Filtros avanzados aplicados. Mostrando ${paquetesFiltradosYOrdenados.length} paquetes.`, "info");
}

// Renderiza la tabla con datos ya filtrados y ordenados (usado por filtros avanzados)
function renderizarTablaFiltrada(datosYaProcesados) {
    const tablaBody = document.getElementById('packetTable');
    const mensajeSinResultados = document.getElementById('noResultsMessage');
    if (!tablaBody || !mensajeSinResultados) return;

    tablaBody.innerHTML = '';
    if (datosYaProcesados.length === 0) {
        mensajeSinResultados.classList.remove('hidden');
        tablaBody.innerHTML = `<tr><td colspan="12" class="text-center p-4 text-gray-500 dark:text-gray-400">No se encontraron paquetes con los filtros aplicados.</td></tr>`;
    } else {
        mensajeSinResultados.classList.add('hidden');
        datosYaProcesados.forEach(paquete => tablaBody.appendChild(crearFilaDePaquete(paquete)));
    }
    if (typeof tippy !== 'undefined') inicializarTooltipsTabla();
}

function limpiarFormularioFiltros() {
    document.getElementById('formFiltros')?.reset();
    // Después de limpiar filtros avanzados, volvemos a aplicar los filtros rápidos (que pueden estar vacíos)
    aplicarFiltrosRapidos(); 
    mostrarMensaje("🧹 Filtros avanzados limpiados.", "info");
}

// --- GRÁFICOS ---
function inicializarGraficos() {
    const commonOptions = (titleText) => ({
        responsive: true, maintainAspectRatio: false,
        plugins: {
            legend: { display: titleText.includes('Protocolos'), position: 'top', labels: { color: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#374151' } },
            title: { display: false, text: titleText } // Título del gráfico, si se desea
        },
        scales: {
            y: { beginAtZero: true, ticks: { color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#4b5563' }, grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'} },
            x: { ticks: { color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#4b5563' }, grid: { display:false } }
        }
    });
    const getColor = (opacity = 1) => document.documentElement.classList.contains('dark') ? `rgba(165, 180, 252, ${opacity})` : `rgba(99, 102, 241, ${opacity})`;

    trafficChartInstance = new Chart(document.getElementById('trafficChart').getContext('2d'), { type: 'line', data: { labels: [], datasets: [{ label: 'Paquetes / Tiempo', data: [], borderColor: getColor(), backgroundColor: getColor(0.2), tension: 0.1, fill: true }] }, options: commonOptions('Tráfico en Tiempo Real') });
    const protocolColors = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#3b82f6', '#10b981', '#d946ef', '#06b6d4', '#f43f5e']; // Más colores
    protocolChartInstance = new Chart(document.getElementById('protocolChart').getContext('2d'), { type: 'pie', data: { labels: [], datasets: [{ data: [], backgroundColor: protocolColors }] }, options: commonOptions('Protocolos Detectados') });
    portChartInstance = new Chart(document.getElementById('portChart').getContext('2d'), { type: 'bar', data: { labels: [], datasets: [{ label: 'Uso de Puertos (Destino)', data: [], backgroundColor: getColor(0.6), borderColor: getColor() }] }, options: commonOptions('Distribución por Puertos') });
    ipChartInstance = new Chart(document.getElementById('ipChart').getContext('2d'), { type: 'bar', data: { labels: [], datasets: [{ label: 'Paquetes por IP (Origen)', data: [], backgroundColor: document.documentElement.classList.contains('dark') ? 'rgba(250, 204, 21, 0.6)' : 'rgba(234, 179, 8, 0.6)', borderColor: document.documentElement.classList.contains('dark') ? 'rgb(250, 204, 21)' : 'rgb(234, 179, 8)' }] }, options: commonOptions('Actividad por IP') });
    sizeChartInstance = new Chart(document.getElementById('sizeChart').getContext('2d'), { type: 'bar', data: { labels: [], datasets: [{ label: 'Cantidad de Paquetes', data: [], backgroundColor: [getColor(0.4), getColor(0.6), getColor(0.8)], borderColor: [getColor(),getColor(),getColor()] }] }, options: commonOptions('Tamaño de Paquetes') });
}

function actualizarTodosLosGraficos(datosParaGraficos) {
    if (!datosParaGraficos || !datosParaGraficos.length === 0) {
        // Limpiar gráficos si no hay datos
        [trafficChartInstance, protocolChartInstance, portChartInstance, ipChartInstance, sizeChartInstance].forEach(chart => {
            if (chart) { chart.data.labels = []; chart.data.datasets.forEach(dataset => dataset.data = []); chart.update('none'); }
        });
        return;
    }
    // Gráfico de Tráfico
    const datosTrafico = datosParaGraficos.slice(0, 50).reverse(); 
    trafficChartInstance.data.labels = datosTrafico.map(d => d.fecha_captura ? new Date(d.fecha_captura).toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit', second: '2-digit'}) : 'N/A');
    trafficChartInstance.data.datasets[0].data = datosTrafico.map(d => d.tamano || 0);
    trafficChartInstance.update('none');

    // Gráfico de Protocolos
    const conteoProtocolos = datosParaGraficos.reduce((acc, d) => { const proto = MAPA_PROTOCOLOS[String(d.protocolo)] || d.protocolo_nombre || String(d.protocolo) || "N/A"; acc[proto] = (acc[proto] || 0) + 1; return acc; }, {});
    protocolChartInstance.data.labels = Object.keys(conteoProtocolos);
    protocolChartInstance.data.datasets[0].data = Object.values(conteoProtocolos);
    protocolChartInstance.update('none');

    // Gráfico de Puertos (Destino)
    const conteoPuertos = datosParaGraficos.reduce((acc, d) => { if(d.puerto_destino) {acc[d.puerto_destino] = (acc[d.puerto_destino] || 0) + 1;} return acc; }, {});
    const topPuertos = Object.entries(conteoPuertos).sort((a,b) => b[1]-a[1]).slice(0,10);
    portChartInstance.data.labels = topPuertos.map(p => `P:${p[0]}`);
    portChartInstance.data.datasets[0].data = topPuertos.map(p => p[1]);
    portChartInstance.update('none');
    
    // Gráfico de IPs (Origen)
    const conteoIPs = datosParaGraficos.reduce((acc, d) => { if(d.iporigen) {acc[d.iporigen] = (acc[d.iporigen] || 0) + 1;} return acc; }, {});
    const topIPs = Object.entries(conteoIPs).sort((a,b) => b[1]-a[1]).slice(0,10);
    ipChartInstance.data.labels = topIPs.map(ip => ip[0]);
    ipChartInstance.data.datasets[0].data = topIPs.map(ip => ip[1]);
    ipChartInstance.update('none');

    // Gráfico de Tamaños
    const conteoTamaños = datosParaGraficos.reduce((acc, d) => { const size = d.tamano || 0; if (size < 100) acc.pequeño++; else if (size <= 1000) acc.mediano++; else acc.grande++; return acc; }, { pequeño: 0, mediano: 0, grande: 0 });
    sizeChartInstance.data.labels = ['Pequeño (<100B)', 'Mediano (100-1000B)', 'Grande (>1000B)'];
    sizeChartInstance.data.datasets[0].data = [conteoTamaños.pequeño, conteoTamaños.mediano, conteoTamaños.grande];
    sizeChartInstance.update('none');
}

function cambiarRangoTiempoGraficoTrafico(rango) {
    const ahora = new Date(); let tiempoLimite;
    switch(rango) { case '1m': tiempoLimite = new Date(ahora.getTime() - 1 * 60 * 1000); break; case '5m': tiempoLimite = new Date(ahora.getTime() - 5 * 60 * 1000); break; case '15m': tiempoLimite = new Date(ahora.getTime() - 15 * 60 * 1000); break; default: tiempoLimite = new Date(ahora.getTime() - 15 * 60 * 1000); }
    const datosFiltrados = todosLosPaquetes.filter(p => new Date(p.fecha_captura) >= tiempoLimite);
    const datosTrafico = datosFiltrados.slice(-50).reverse(); 
    trafficChartInstance.data.labels = datosTrafico.map(d => d.fecha_captura ? new Date(d.fecha_captura).toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit', second: '2-digit'}) : 'N/A');
    trafficChartInstance.data.datasets[0].data = datosTrafico.map(d => d.tamano || 0);
    trafficChartInstance.update();
}

function cambiarTipoGrafico(chartId, nuevoTipo) {
    const chartInstance = Chart.getChart(chartId);
    if (chartInstance && chartInstance.config.type !== nuevoTipo) {
        chartInstance.config.type = nuevoTipo;
        const isPieOrDoughnut = nuevoTipo === 'pie' || nuevoTipo === 'doughnut';
        chartInstance.options.scales = isPieOrDoughnut ? {} : { y: { beginAtZero: true, ticks: { color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#4b5563' }, grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'} }, x: { ticks: { color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#4b5563' }, grid: {display:false} } };
        chartInstance.options.plugins.legend.display = isPieOrDoughnut;
        chartInstance.update();
    }
}

// --- UTILIDADES ---
function actualizarContadoresGlobales(paquetes) {
    document.getElementById('paquetesTotal').textContent = paquetes.length;
    document.getElementById('paquetesTCP').textContent = paquetes.filter(p => (MAPA_PROTOCOLOS[String(p.protocolo)] || p.protocolo_nombre) === 'TCP').length;
    document.getElementById('paquetesUDP').textContent = paquetes.filter(p => (MAPA_PROTOCOLOS[String(p.protocolo)] || p.protocolo_nombre) === 'UDP').length;
    // Este contador de alertas es un placeholder. Necesitarías una fuente real de datos de alertas.
    const alertasHoyEjemplo = todosLosPaquetes.filter(p => p.tamano > 1500 && p.protocolo === "6").length; // Ejemplo: TCP > 1500B
    document.getElementById('alertasHoy').textContent = alertasHoyEjemplo;
}

function exportarDatosCSV() {
    if (todosLosPaquetes.length === 0) { mostrarMensaje("ℹ️ No hay datos para exportar.", "info"); return; }
    const datosAExportar = (paquetesFiltradosYOrdenados.length > 0 ? paquetesFiltradosYOrdenados : todosLosPaquetes).map(p => ({
        ID: p.idescanear_red, IP_Origen: p.iporigen, IP_Destino: p.ipdestino, MAC_Origen: p.mac_origen, MAC_Destino: p.mac_destino,
        Puerto_Origen: p.puerto_origen, Puerto_Destino: p.puerto_destino, Protocolo_Num: p.protocolo, Protocolo_Nombre: MAPA_PROTOCOLOS[String(p.protocolo)] || p.protocolo_nombre || String(p.protocolo),
        Tamaño_Bytes: p.tamano, Fecha_Captura: p.fecha_captura ? new Date(p.fecha_captura).toISOString() : 'N/A', TTL: p.ttl,
        Flags_TCP: p.flags_tcp, Payload_Preview: p.payload ? p.payload.substring(0,100).replace(/(\r\n|\n|\r)/gm," ") : 'N/A'
    }));
    try {
        const csv = Papa.unparse(datosAExportar); const blob = new Blob(["\uFEFF" + csv], { type: 'text/csv;charset=utf-8;' }); // Añadir BOM para Excel
        const link = document.createElement("a"); const url = URL.createObjectURL(blob);
        link.setAttribute("href", url); link.setAttribute("download", `monitoreo_red_${new Date().toISOString().slice(0,10)}.csv`);
        link.style.visibility = 'hidden'; document.body.appendChild(link); link.click(); document.body.removeChild(link); URL.revokeObjectURL(url);
        mostrarMensaje("✅ Datos exportados a CSV.", "success");
    } catch (error) { console.error("❌ Error al exportar CSV:", error); mostrarMensaje("❌ Error al exportar datos.", "error"); }
}

function inicializarTooltipsTabla() {
    if (typeof tippy !== 'undefined') {
        document.querySelectorAll('#packetTable .truncate-cell').forEach(cell => {
            if (cell._tippy) cell._tippy.destroy();
            tippy(cell, { content: cell.getAttribute('title') || cell.textContent, placement: 'top', arrow: true, animation: 'fade', theme: document.documentElement.classList.contains('dark') ? 'light-border' : 'material' });
        });
    }
}

function inicializarTema() {
    const temaGuardado = localStorage.getItem('theme'); const prefiereOscuro = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (temaGuardado === 'dark' || (!temaGuardado && prefiereOscuro)) { document.documentElement.classList.add('dark'); }
    else { document.documentElement.classList.remove('dark'); }
    Chart.defaults.color = document.documentElement.classList.contains('dark') ? '#9ca3af' : '#4b5563';
    Chart.defaults.borderColor = document.documentElement.classList.contains('dark') ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
}

function toggleTema() {
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
    Chart.defaults.color = document.documentElement.classList.contains('dark') ? '#9ca3af' : '#4b5563';
    Chart.defaults.borderColor = document.documentElement.classList.contains('dark') ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
    [trafficChartInstance, protocolChartInstance, portChartInstance, ipChartInstance, sizeChartInstance].forEach(chart => { if (chart) chart.update('none'); });
    if (typeof tippy !== 'undefined') inicializarTooltipsTabla();
}

function mostrarMensaje(texto, tipo = "info", duracion = 3500) {
    const el = document.getElementById("mensajeEstado");
    if (el) {
        let icono = 'info'; let colorClasses = 'bg-blue-100 border-blue-500 text-blue-700 dark:bg-blue-900 dark:border-blue-700 dark:text-blue-200';
        if (tipo === 'success') { icono = 'check-circle'; colorClasses = 'bg-green-100 border-green-500 text-green-700 dark:bg-green-900 dark:border-green-700 dark:text-green-200';}
        else if (tipo === 'error') { icono = 'x-circle'; colorClasses = 'bg-red-100 border-red-500 text-red-700 dark:bg-red-900 dark:border-red-700 dark:text-red-200';}
        else if (tipo === 'warning') { icono = 'alert-triangle'; colorClasses = 'bg-amber-100 border-amber-500 text-amber-700 dark:bg-amber-900 dark:border-amber-700 dark:text-amber-200';}
        
        el.innerHTML = `<span class="inline-flex items-center gap-2"><i data-lucide="${icono}" class="w-5 h-5"></i>${texto}</span>`;
        el.className = `mb-6 py-3 px-4 text-sm rounded-md border-l-4 ${colorClasses}`; // Usar clases de Tailwind para color
        
        if (typeof lucide !== 'undefined') { const i = el.querySelector('i'); if(i) lucide.createIcons({nodes: [i]});}
        
        if(el.mensajeTimeout) clearTimeout(el.mensajeTimeout);
        if(duracion > 0) {
            el.mensajeTimeout = setTimeout(() => {
                // Volver al estado 'Captura detenida' o simplemente ocultar
                const mensajeDetenido = '<span class="inline-flex items-center gap-2"><i data-lucide="pause-circle" class="w-5 h-5"></i>Captura detenida.</span>';
                el.innerHTML = capturaActivaLocal ? el.innerHTML : mensajeDetenido; // Mantiene mensaje si la captura sigue
                if (!capturaActivaLocal) el.className = "state-inactive mb-6 py-3 px-4 text-sm";
                if (typeof lucide !== 'undefined' && !capturaActivaLocal) { const i = el.querySelector('i'); if(i) lucide.createIcons({nodes: [i]});}
            }, duracion);
        }
    }
}