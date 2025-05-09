let intervaloDispositivos = null;
let intervaloBotones = null;
let dispositivosGlobales = [];

// Aplicar tema desde localStorage
(function aplicarTemaGuardado() {
  const tema = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', tema);
})();

async function actualizarBotones() {
  try {
    const res = await fetch('/estado_escaneo');
    const data = await res.json();

    const btnIniciar = document.querySelector('button[onclick="iniciarEscaneo()"]');
    const btnDetener = document.querySelector('button[onclick="detenerEscaneo()"]');

    if (data.en_progreso) {
      btnIniciar.disabled = true;
      btnIniciar.classList.add("opacity-50", "cursor-not-allowed");
      btnDetener.disabled = false;
      btnDetener.classList.remove("opacity-50", "cursor-not-allowed");
    } else {
      btnIniciar.disabled = false;
      btnIniciar.classList.remove("opacity-50", "cursor-not-allowed");
      btnDetener.disabled = true;
      btnDetener.classList.add("opacity-50", "cursor-not-allowed");
    }
  } catch (error) {
    console.error("Error al actualizar botones:", error);
  }
}

async function obtenerDispositivos() {
  try {
    const res = await fetch('/datos_dispositivos');
    dispositivosGlobales = await res.json();
    mostrarDispositivos();
    actualizarContadores();
  } catch (error) {
    console.error("Error al obtener dispositivos:", error);
  }
}

function mostrarDispositivos() {
  const tabla = document.getElementById('tabla-dispositivos');
  const busqueda = document.getElementById('search-devices')?.value.trim().toLowerCase() || '';
  const filtroEstado = document.getElementById('filter-status')?.value || 'all';
  const filtroSO = document.getElementById('filter-os')?.value || 'all';

  const dispositivosFiltrados = dispositivosGlobales.filter(dispositivo => {
    const nombre = dispositivo.nombre_host?.toLowerCase() || '';
    const ip = dispositivo.direccion_ip || '';
    const sistema = (dispositivo.sistema_operativo || '').toLowerCase();
    const estado = dispositivo.estado_dispositivo || 'desconocido';

    const coincideBusqueda = nombre.includes(busqueda) || ip.includes(busqueda);
    const coincideEstado = filtroEstado === 'all' || 
      (filtroEstado === 'active' && estado === 'activo') ||
      (filtroEstado === 'offline' && estado === 'inactivo') ||
      (filtroEstado === 'warning' && estado === 'advertencia');

    const coincideSO = filtroSO === 'all' || 
      (filtroSO === 'windows' && sistema.includes('windows')) ||
      (filtroSO === 'linux' && sistema.includes('linux')) ||
      (filtroSO === 'macos' && sistema.includes('mac')) ||
      (filtroSO === 'other' && !sistema.includes('windows') && !sistema.includes('linux') && !sistema.includes('mac'));

    return coincideBusqueda && coincideEstado && coincideSO;
  });

  tabla.innerHTML = '';

  if (dispositivosFiltrados.length === 0) {
    tabla.innerHTML = `<tr><td colspan="8" class="text-center text-gray-500 py-4">No se encontraron dispositivos</td></tr>`;
    return;
  }

  dispositivosFiltrados.forEach(dispositivo => {
    const row = document.createElement('tr');
    row.className = 'bg-white hover:bg-gray-50 transition';
    row.innerHTML = `
      <td class="px-6 py-3 rounded-l-lg">${dispositivo.direccion_ip || '-'}</td>
      <td class="px-6 py-3">${dispositivo.direccion_mac || '-'}</td>
      <td class="px-6 py-3">${dispositivo.nombre_host || '-'}</td>
      <td class="px-6 py-3">${dispositivo.sistema_operativo || '-'}</td>
      <td class="px-6 py-3">${(dispositivo.puertos_abiertos || []).join(', ')}</td>
      <td class="px-6 py-3">${new Date(dispositivo.fecha_escaneo).toLocaleString()}</td>
      <td class="px-6 py-3">
        <span class="inline-block px-2 py-1 text-xs font-semibold rounded-full 
          ${dispositivo.estado_dispositivo === 'activo' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}">
          ${dispositivo.estado_dispositivo || 'desconocido'}
        </span>
      </td>
      <td class="px-6 py-3 rounded-r-lg text-center">
        <button onclick="desconectarDispositivo('${dispositivo.direccion_ip}')" 
                class="bg-yellow-500 hover:bg-yellow-600 text-white text-xs font-bold px-3 py-1 rounded transition">
          Desconectar
        </button>
      </td>`;
    tabla.appendChild(row);
  });
}

function actualizarContadores() {
  const total = dispositivosGlobales.length;
  const activos = dispositivosGlobales.filter(d => d.estado_dispositivo === 'activo').length;
  const inactivos = total - activos;

  document.getElementById('total-devices').textContent = total;
  document.getElementById('active-devices').textContent = activos;
  document.getElementById('inactive-devices').textContent = inactivos;
}

async function iniciarEscaneo() {
  try {
    const res = await fetch('/iniciar_escaneo_dispositivos', { method: 'POST' });
    const data = await res.json();
    alert(data.mensaje);
    await actualizarBotones();
    await obtenerDispositivos();
  } catch (error) {
    console.error("Error al iniciar escaneo:", error);
  }
}

async function detenerEscaneo() {
  try {
    const res = await fetch('/detener_escaneo_dispositivos', { method: 'POST' });
    const data = await res.json();
    alert(data.mensaje);
    await actualizarBotones();
  } catch (error) {
    console.error("Error al detener escaneo:", error);
  }
}

async function desconectarDispositivo(ip) {
  if (confirm(`¿Deseas desconectar el dispositivo con IP ${ip}?`)) {
    try {
      const res = await fetch(`/desconectar_dispositivo/${ip}`, { method: 'POST' });
      const data = await res.json();
      alert(data.mensaje);
      await obtenerDispositivos();
    } catch (error) {
      alert("❌ Error al intentar desconectar");
      console.error("Error:", error);
    }
  }
}

// Asignar eventos y configurar intervalos
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('search-devices')?.addEventListener('input', mostrarDispositivos);
  document.getElementById('filter-status')?.addEventListener('change', mostrarDispositivos);
  document.getElementById('filter-os')?.addEventListener('change', mostrarDispositivos);

  obtenerDispositivos();
  actualizarBotones();

  intervaloDispositivos = setInterval(obtenerDispositivos, 5000);
  intervaloBotones = setInterval(actualizarBotones, 1000);
});








