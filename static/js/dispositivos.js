let intervaloDispositivos = null;
let intervaloBotones = null;
let dispositivosGlobales = [];

// Funciones globales (showToast, showModal) se asume que están en el HTML.

async function actualizarBotones() {
    try {
        const res = await fetch('/estado_escaneo');
        const data = await res.json();
        const btnIniciar = document.getElementById('scan-btn');
        const btnDetener = document.getElementById('stop-btn');

        if (btnIniciar && btnDetener) {
            btnIniciar.disabled = data.en_progreso;
            btnDetener.disabled = !data.en_progreso;
        }
    } catch (error) {
        console.error("Error al actualizar botones:", error);
    }
}

async function obtenerDispositivos() {
    try {
        const res = await fetch('/datos_dispositivos');
        if (!res.ok) {
            console.error("Error al obtener datos:", res.statusText);
            return;
        }
        dispositivosGlobales = await res.json();
        if(dispositivosGlobales.error) {
            console.error("Error del servidor:", dispositivosGlobales.detalle);
            showToast('Error de Datos', dispositivosGlobales.detalle, 'error');
            return;
        }
        mostrarDispositivos();
        actualizarContadores();
    } catch (error) {
        console.error("Error al obtener dispositivos:", error);
        showToast('Error de Red', 'No se pudo cargar la lista de dispositivos.', 'error');
    }
}

function mostrarDispositivos() {
    const tabla = document.getElementById('tabla-dispositivos');
    const busqueda = document.getElementById('search-devices')?.value.trim().toLowerCase() || '';
    const filtroEstado = document.getElementById('filter-status')?.value || 'all';
    const filtroSO = document.getElementById('filter-os')?.value || 'all';

    if (!tabla) return;

    const dispositivosFiltrados = dispositivosGlobales.filter(d => {
        const nombre = (d.nombre_host || '').toLowerCase();
        const ip = (d.direccion_ip || '');
        const mac = (d.direccion_mac || '').toLowerCase();
        const sistema = (d.sistema_operativo || '').toLowerCase();
        const estado = (d.estado_dispositivo || 'desconocido').toLowerCase();
        const bloqueado = d.bloqueado === 1;

        const coincideBusqueda = nombre.includes(busqueda) || ip.includes(busqueda) || mac.includes(busqueda);

        let coincideEstado = false;
        switch (filtroEstado) {
            case 'all': coincideEstado = true; break;
            case 'active': coincideEstado = estado === 'activo' && !bloqueado; break;
            case 'offline': coincideEstado = estado !== 'activo' && !bloqueado; break;
            case 'blocked': coincideEstado = bloqueado; break;
        }

        const coincideSO = filtroSO === 'all' ||
            (filtroSO === 'windows' && sistema.includes('windows')) ||
            (filtroSO === 'linux' && sistema.includes('linux')) ||
            (filtroSO === 'macos' && sistema.includes('mac')) ||
            (filtroSO === 'other' && !['windows', 'linux', 'mac'].some(os => sistema.includes(os)));

        return coincideBusqueda && coincideEstado && coincideSO;
    });

    tabla.innerHTML = '';

    if (dispositivosFiltrados.length === 0) {
        tabla.innerHTML = `<tr><td colspan="8" class="text-center py-10 text-gray-500">No se encontraron dispositivos.</td></tr>`;
        return;
    }

    dispositivosFiltrados.forEach(d => {
        const row = document.createElement('tr');
        const isBlocked = d.bloqueado === 1;
        const isActive = d.estado_dispositivo === 'activo';

        row.className = `bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition ${isBlocked ? 'opacity-60 bg-red-50 dark:bg-red-900/20' : ''}`;
        const puertos = d.puerto ? d.puerto.split(',').join(', ') : 'N/A';

        let estadoBadge = '';
        if (isBlocked) {
            estadoBadge = `<span class="status-badge status-blocked">Bloqueado</span>`;
        } else if (isActive) {
            estadoBadge = `<span class="status-badge status-active">Activo</span>`;
        } else {
            estadoBadge = `<span class="status-badge status-offline">Inactivo</span>`;
        }

        row.innerHTML = `
            <td>${d.direccion_ip || '-'}</td>
            <td>${d.direccion_mac || '-'}</td>
            <td>${d.nombre_host || '-'}</td>
            <td>${d.sistema_operativo || '-'}</td>
            <td class="text-xs">${puertos}</td>
            <td>${new Date(d.fecha_escaneo).toLocaleString()}</td>
            <td>${estadoBadge}</td>
            <td class="text-center">
                <button
                    onclick="confirmToggleBlockDevice('${d.direccion_ip}', ${isBlocked})"
                    class="px-3 py-1.5 rounded-md text-white text-xs font-semibold transition shadow-sm
                           ${isBlocked ? 'bg-green-500 hover:bg-green-600' : 'bg-red-500 hover:bg-red-600'}
                           disabled:opacity-50"
                    title="${isBlocked ? 'Permitir conexión' : 'Bloquear conexión'}">
                    ${isBlocked ? 'Reconectar' : 'Desconectar'}
                </button>
            </td>`;
        tabla.appendChild(row);
    });
}

function actualizarContadores() {
    const total = dispositivosGlobales.length;
    const activos = dispositivosGlobales.filter(d => d.estado_dispositivo === 'activo' && d.bloqueado !== 1).length;
    const inactivos = total - activos;

    document.getElementById('total-devices').textContent = total;
    document.getElementById('active-devices').textContent = activos;
    document.getElementById('inactive-devices').textContent = inactivos;
    document.getElementById('total-entries').textContent = total;
}

// Lógica de Escaneo (con Modales)
function solicitarInicioEscaneo() {
    showModal({
        title: '⚠️ Consejo Antes de Escanear',
        message: 'Antes de realizar un escaneo, asegúrese de que no hay otro en curso. <br>Si está seguro, puede continuar.',
        confirmText: 'Entendido, continuar',
        onConfirm: () => ejecutarEscaneo(),
        showCancel: true
    });
}

async function ejecutarEscaneo() {
    showToast('Iniciando', 'El escaneo de red ha comenzado...', 'info');
    try {
        const res = await fetch('/iniciar_escaneo_dispositivos', { method: 'POST' });
        const data = await res.json();
        showToast('Escaneo', data.mensaje, res.ok ? 'success' : 'error');
        await actualizarBotones();
        await obtenerDispositivos();
    } catch (error) {
        showToast('Error', '❌ Fallo al iniciar el escaneo.', 'error');
        console.error("Error al iniciar escaneo:", error);
    }
}

async function detenerEscaneo() {
    showModal({
        title: '¿Detener Escaneo?',
        message: '¿Está seguro de que desea detener el proceso de escaneo actual?',
        confirmText: 'Sí, detener',
        danger: true,
        onConfirm: async () => {
            showToast('Deteniendo', 'Intentando detener el escaneo...', 'warning');
            try {
                const res = await fetch('/detener_escaneo_dispositivos', { method: 'POST' });
                const data = await res.json();
                showToast('Escaneo Detenido', data.mensaje, res.ok ? 'warning' : 'error');
                await actualizarBotones();
            } catch (error) {
                showToast('Error', '❌ Fallo al detener el escaneo.', 'error');
                console.error("Error al detener escaneo:", error);
            }
        }
    });
}

// Lógica de Bloqueo/Desbloqueo (con Modales y Contraseña)
function confirmToggleBlockDevice(ip, isCurrentlyBlocked) {
    const action = isCurrentlyBlocked ? 'RECONECTAR' : 'DESCONECTAR';
    const message = isCurrentlyBlocked
        ? `¿Seguro que deseas <strong>${action}</strong> el dispositivo con IP <strong>${ip}</strong>?`
        : `¿Seguro que deseas <strong>${action}</strong> el dispositivo <strong>${ip}</strong>? <br><br><strong>¡ADVERTENCIA!</strong><br> - Esto requiere permisos elevados (sudo). <br> - Podría causar inestabilidad temporal.`;

    showModal({
        title: `Confirmar ${action}`,
        message: message,
        confirmText: `Sí, ${action}`,
        danger: !isCurrentlyBlocked, // Peligroso si es desconectar
        requirePassword: !isCurrentlyBlocked, // Pedir contraseña SÓLO para desconectar
        onConfirm: () => executeToggleBlock(ip, isCurrentlyBlocked)
    });
}

async function executeToggleBlock(ip, isCurrentlyBlocked) {
    const action = isCurrentlyBlocked ? 'reconectar' : 'desconectar';
    const url = `/${action}_dispositivo/${ip}`;
    showToast('Procesando', `Intentando ${action} ${ip}...`, 'info');

    try {
        const res = await fetch(url, { method: 'POST' });
        const data = await res.json();
        showToast(
            action.charAt(0).toUpperCase() + action.slice(1),
            data.mensaje,
            res.ok ? 'success' : 'error'
        );
        await obtenerDispositivos(); // Actualizar la lista
    } catch (error) {
        showToast('Error Grave', `❌ Error de red al intentar ${action}.`, 'error');
        console.error("Error:", error);
    }
}

// Lógica para Cerrar Sesión (con Modal y Contraseña)
function solicitarCierreSesion() {
    showModal({
        title: 'Cerrar Sesión',
        message: 'Para cerrar la sesión de forma segura, por favor ingrese la contraseña de administrador.',
        confirmText: 'Cerrar Sesión',
        danger: true,
        requirePassword: true,
        onConfirm: () => {
             showToast('Cerrando Sesión', 'Serás redirigido en breve.', 'info');
             // Aquí iría la redirección real, por ejemplo:
             // window.location.href = '/logout'; // Cambia '/logout' a tu ruta real de cierre de sesión
             console.log("Cerrando sesión..."); // Placeholder
        }
    });
}


// Event Listeners y Arranque
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('search-devices')?.addEventListener('input', mostrarDispositivos);
    document.getElementById('filter-status')?.addEventListener('change', mostrarDispositivos);
    document.getElementById('filter-os')?.addEventListener('change', mostrarDispositivos);

    // Botones de escaneo usan las funciones con modal
    document.getElementById('scan-btn').onclick = solicitarInicioEscaneo;
    document.getElementById('stop-btn').onclick = detenerEscaneo;

    // Botón de cerrar sesión
    document.getElementById('logout-link').onclick = (e) => {
        e.preventDefault(); // Evita que el enlace # navegue
        solicitarCierreSesion();
    };


    obtenerDispositivos();
    actualizarBotones();

    intervaloDispositivos = setInterval(obtenerDispositivos, 5000);
    intervaloBotones = setInterval(actualizarBotones, 2000);
});

// Limpiar intervalos si la ventana se cierra o navega a otra parte
window.addEventListener('beforeunload', () => {
    clearInterval(intervaloDispositivos);
    clearInterval(intervaloBotones);
});

let interactuadoConBusqueda = false;

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-devices');

    searchInput?.addEventListener('input', () => {
        // Evitar la primera ejecución automática
        if (!interactuadoConBusqueda) {
            if (searchInput.value.trim() === '') return;
            interactuadoConBusqueda = true;
        }

        mostrarDispositivos();
    });

    document.getElementById('filter-status')?.addEventListener('change', mostrarDispositivos);
    document.getElementById('filter-os')?.addEventListener('change', mostrarDispositivos);

    obtenerDispositivos();
    actualizarBotones();

    intervaloDispositivos = setInterval(obtenerDispositivos, 5000);
    intervaloBotones = setInterval(actualizarBotones, 2000);
});
