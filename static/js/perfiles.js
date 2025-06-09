// --- FUNCIÓN PARA OBTENER EL PERFIL DEL USUARIO ACTUAL ---
async function obtenerPerfilUsuarioActual() {
    try {
        const response = await fetch('/usuarios/perfil-actual'); 
        if (!response.ok) throw new Error('No se pudo verificar la sesión.');
        const data = await response.json();
        if (data && typeof data.perfil !== 'undefined') {
            return data.perfil;
        } else {
            throw new Error('Respuesta de sesión inválida.');
        }
    } catch (error) {
        console.error("Error de autenticación:", error);
        throw error; // Propaga el error para que el bloque principal lo maneje.
    }
}

// --- FUNCIÓN PARA APLICAR PERMISOS VISUALES ---
function aplicarPermisosVisuales(idPerfil) {
    if (idPerfil !== 1) { // 1 = Administrador
        // Oculta todo el contenido principal de la página.
        // Usa el ID que añadiste a la etiqueta <main>
        const divContenido = document.getElementById('main-content');
        if (divContenido) {
            divContenido.style.display = 'none';
        }
        // Muestra la notificación de error.
        mostrarNotificacion('No tienes permisos para acceder a esta sección.', 'error');
        return false; // No es admin
    }
    return true; // Es admin
}

// --- PUNTO DE ENTRADA PRINCIPAL ---
document.addEventListener('DOMContentLoaded', async () => {
    // Inicializa los íconos de Lucide primero.
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    try {
        // 1. SIEMPRE se verifica el permiso primero.
        const idPerfil = await obtenerPerfilUsuarioActual();
        const esAdmin = aplicarPermisosVisuales(idPerfil);

        // 2. Si la función de permisos devuelve 'false', detenemos todo aquí.
        if (!esAdmin) {
            return; 
        }

        // 3. Si esAdmin es 'true', entonces y solo entonces, inicializamos la página.
        inicializarPaginaDePerfiles();

    } catch (error) {
        // Este bloque se ejecuta si falla la comunicación con el servidor (ej. sesión expirada).
        mostrarNotificacion(error.message, 'error');
        const divContenido = document.getElementById('main-content');
        if (divContenido) {
            divContenido.style.display = 'none';
        }
    }
});


/**
 * Esta función contiene toda la lógica que SÓLO debe ejecutarse para un administrador.
 */
function inicializarPaginaDePerfiles() {
    // Referencias a elementos del DOM
    const nombreInput = document.getElementById('nombre');
    const descripcionInput = document.getElementById('descripcion');
    const formularioPerfil = document.getElementById('formularioPerfil');
    const buscadorInput = document.getElementById('buscador');
    const btnCancelarEdicion = document.getElementById('btn-cancelar-edicion');
    const themeToggleBtn = document.getElementById('theme-toggle');

    // Configuración del Tema
    const rootElement = document.documentElement;
    const setTheme = (theme) => {
        rootElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        if (themeToggleBtn) themeToggleBtn.checked = theme === 'dark';
    };
    const toggleTheme = () => {
        const current = rootElement.getAttribute('data-theme');
        setTheme(current === 'light' ? 'dark' : 'light');
    };
    if (themeToggleBtn) themeToggleBtn.addEventListener('change', toggleTheme);
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme);
    } else {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setTheme(prefersDark ? 'dark' : 'light');
    }
    
    // Carga inicial de datos
    cargarPerfiles();
    actualizarEstadoBotonGuardar();

    // Asignación de Eventos
    if (formularioPerfil) formularioPerfil.addEventListener('submit', guardarPerfil);
    if (buscadorInput) buscadorInput.addEventListener('input', () => filtrarPerfiles(buscadorInput.value));
    if (nombreInput) nombreInput.addEventListener('input', () => validarCampo(nombreInput, validarNombre));
    if (descripcionInput) descripcionInput.addEventListener('input', () => validarCampo(descripcionInput, validarDescripcion));
    if (btnCancelarEdicion) btnCancelarEdicion.addEventListener('click', cancelarEdicion);
}


// --- RESTO DE FUNCIONES DE LA APLICACIÓN ---

let todosLosPerfiles = []; // Guarda la lista original para el buscador

function mostrarNotificacion(mensaje, tipo = 'info', duracion = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) { alert(mensaje); return; }
    const toast = document.createElement('div');
    toast.className = `toast toast-${tipo}`;
    const iconos = {
        success: '<i data-lucide="check-circle" class="w-5 h-5"></i>',
        error: '<i data-lucide="x-circle" class="w-5 h-5"></i>',
        warning: '<i data-lucide="alert-triangle" class="w-5 h-5"></i>',
        info: '<i data-lucide="info" class="w-5 h-5"></i>'
    };
    toast.innerHTML = `<div>${iconos[tipo] || iconos['info']}<span>${mensaje}</span></div><button onclick="this.parentElement.remove()" class="p-1 rounded-full hover:bg-black/10 transition-colors"><i data-lucide="x" class="w-4 h-4"></i></button>`;
    container.appendChild(toast);
    lucide.createIcons();
    setTimeout(() => { if (toast.parentElement) toast.remove(); }, duracion);
}

function validarNombre(valor) { if (!valor.trim()) return "El nombre del perfil es obligatorio."; if (valor.trim().length < 3) return "Mínimo 3 caracteres."; if (valor.trim().length > 50) return "Máximo 50 caracteres."; if (/^\d+$/.test(valor.trim())) return "No puede contener solo números."; return ""; }
function validarDescripcion(valor) { if (!valor.trim()) return "La descripción es obligatoria."; if (valor.trim().length < 5) return "Mínimo 5 caracteres."; if (valor.trim().length > 200) return "Máximo 200 caracteres."; return ""; }

function validarCampo(input, validador) {
    const errorElement = document.getElementById(`${input.id}-error`);
    const errorMsg = validador(input.value);
    if (errorMsg) {
        input.classList.add('error');
        if (errorElement) { errorElement.textContent = errorMsg; errorElement.classList.remove('hidden'); }
    } else {
        input.classList.remove('error');
        if (errorElement) errorElement.classList.add('hidden');
    }
    actualizarEstadoBotonGuardar();
}

function actualizarEstadoBotonGuardar() {
    const btnGuardar = document.getElementById('btn-guardar');
    const nombreInput = document.getElementById('nombre');
    const descripcionInput = document.getElementById('descripcion');
    if (!btnGuardar || !nombreInput || !descripcionInput) return;
    const nombreValido = !validarNombre(nombreInput.value);
    const descripcionValida = !validarDescripcion(descripcionInput.value);
    btnGuardar.disabled = !(nombreValido && descripcionValida);
}

function modoCrear() {
    const formularioPerfil = document.getElementById('formularioPerfil');
    const idPerfilEditarInput = document.getElementById('id_perfil_editar');
    const formTitle = document.getElementById('form-title');
    const btnGuardarTexto = document.getElementById('btn-guardar-texto');
    const btnCancelarEdicion = document.getElementById('btn-cancelar-edicion');
    
    formularioPerfil.reset();
    idPerfilEditarInput.value = '';
    formTitle.innerHTML = '<i data-lucide="plus-circle" class="w-5 h-5 text-blue-500"></i> Crear Nuevo Perfil';
    btnGuardarTexto.textContent = 'Guardar Perfil';
    btnCancelarEdicion.classList.add('hidden');
    [document.getElementById('nombre'), document.getElementById('descripcion')].forEach(input => {
        input.classList.remove('error');
        const errorElement = document.getElementById(`${input.id}-error`);
        if(errorElement) errorElement.classList.add('hidden');
    });
    actualizarEstadoBotonGuardar();
    lucide.createIcons();
}

function cancelarEdicion() {
    modoCrear();
}

function modoEditar(perfil) {
    const nombreInput = document.getElementById('nombre');
    const descripcionInput = document.getElementById('descripcion');
    const estadoInput = document.getElementById('estado');
    const idPerfilEditarInput = document.getElementById('id_perfil_editar');
    const formTitle = document.getElementById('form-title');
    const btnGuardarTexto = document.getElementById('btn-guardar-texto');
    const btnCancelarEdicion = document.getElementById('btn-cancelar-edicion');
    
    nombreInput.value = perfil.nombre;
    descripcionInput.value = perfil.descripcion;
    estadoInput.value = perfil.estado.toLowerCase();
    idPerfilEditarInput.value = perfil.id_perfil;
    formTitle.innerHTML = '<i data-lucide="edit-3" class="w-5 h-5 text-amber-500"></i> Editar Perfil';
    btnGuardarTexto.textContent = 'Actualizar Perfil';
    btnCancelarEdicion.classList.remove('hidden');
    validarCampo(nombreInput, validarNombre);
    validarCampo(descripcionInput, validarDescripcion);
    lucide.createIcons();
    nombreInput.focus();
}

async function cargarPerfiles() {
    const tablaPerfilesBody = document.getElementById('tabla-perfiles');
    const filaVacia = document.getElementById('fila-vacia');
    try {
        const respuesta = await fetch('/perfiles', { cache: 'no-store' });
        if (!respuesta.ok) throw new Error(`Error del servidor: ${respuesta.status}`);
        const perfiles = await respuesta.json();
        todosLosPerfiles = perfiles; // Actualizamos la lista global
        renderizarTablaPerfiles(todosLosPerfiles);
    } catch (error) {
        console.error("Error al cargar perfiles:", error);
        mostrarNotificacion("No se pudieron cargar los perfiles.", "error");
        if(tablaPerfilesBody) tablaPerfilesBody.innerHTML = '';
        if(filaVacia) {
            filaVacia.classList.remove('hidden');
            filaVacia.querySelector('span').textContent = 'Error al cargar datos. Intente de nuevo.';
        }
    }
}

function renderizarTablaPerfiles(perfiles) {
    const tablaPerfilesBody = document.getElementById('tabla-perfiles');
    const filaVacia = document.getElementById('fila-vacia');
    if(!tablaPerfilesBody || !filaVacia) return;

    tablaPerfilesBody.innerHTML = '';
    if (perfiles.length === 0) {
        filaVacia.classList.remove('hidden');
    } else {
        filaVacia.classList.add('hidden');
        perfiles.forEach(perfil => {
            const tr = document.createElement('tr');
            tr.setAttribute('data-perfil-id', perfil.id_perfil);
            tr.innerHTML = `
                <td class="px-4 py-3 font-medium">${perfil.id_perfil}</td>
                <td class="px-4 py-2">${perfil.nombre}</td>
                <td class="px-4 py-2 max-w-xs truncate" title="${perfil.descripcion}">${perfil.descripcion}</td>
                <td class="px-4 py-2 text-center">
                    <span class="badge ${perfil.estado.toLowerCase() === 'activo' ? 'active' : 'inactive'}">
                        <span class="badge-dot"></span>
                        ${perfil.estado}
                    </span>
                </td>
                <td class="px-4 py-2 text-center">
                    <div class="flex justify-center items-center gap-1">
                        <button onclick='modoEditar(${JSON.stringify(perfil)})' class="btn-action btn-edit" title="Editar">
                            <i data-lucide="edit-3"></i>
                        </button>
                        <button onclick="confirmarCambioEstado(${perfil.id_perfil}, '${perfil.nombre}', '${perfil.estado.toLowerCase()}')" class="btn-action btn-delete" title="${perfil.estado.toLowerCase() === 'activo' ? 'Inhabilitar' : 'Habilitar'}">
                            <i data-lucide="${perfil.estado.toLowerCase() === 'activo' ? 'power-off' : 'power'}"></i>
                        </button>
                    </div>
                </td>`;
            tablaPerfilesBody.appendChild(tr);
        });
    }
    lucide.createIcons();
}

function filtrarPerfiles(termino) {
    const busqueda = termino.toLowerCase();
    const perfilesFiltrados = todosLosPerfiles.filter(perfil =>
        perfil.nombre.toLowerCase().includes(busqueda) ||
        perfil.descripcion.toLowerCase().includes(busqueda)
    );
    renderizarTablaPerfiles(perfilesFiltrados);
}

async function guardarPerfil(event) {
    event.preventDefault();
    const idPerfilEditarInput = document.getElementById('id_perfil_editar');
    const btnGuardar = document.getElementById('btn-guardar');
    if (btnGuardar.disabled) return;
    const esEdicion = !!idPerfilEditarInput.value;
    const url = esEdicion ? `/editar_perfil/${idPerfilEditarInput.value}` : '/crear_perfil';
    const method = esEdicion ? 'PUT' : 'POST';
    const datosPerfil = {
        nombre: document.getElementById('nombre').value.trim(),
        descripcion: document.getElementById('descripcion').value.trim(),
        estado: document.getElementById('estado').value
    };
    try {
        const respuesta = await fetch(url, { method: method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(datosPerfil) });
        const resultado = await respuesta.json();
        if (respuesta.ok) {
            mostrarNotificacion(resultado.mensaje || (esEdicion ? 'Perfil actualizado' : 'Perfil creado'), 'success');
            modoCrear();
            cargarPerfiles();
        } else {
            mostrarNotificacion(resultado.mensaje || 'Error al guardar el perfil', 'error');
        }
    } catch (error) {
        console.error('Error en la petición:', error);
        mostrarNotificacion('Error de conexión con el servidor.', 'error');
    }
}

function confirmarCambioEstado(id, nombre, estadoActual) {
    const accionTexto = estadoActual === 'activo' ? 'inhabilitar' : 'habilitar';
    const esAdmin = nombre.toLowerCase() === 'administrador';
    
    if (esAdmin && accionTexto === 'inhabilitar') {
        mostrarNotificacion("El perfil 'Administrador' no puede ser inhabilitado.", 'warning', 6000);
        return;
    }
    
    const modal = document.getElementById('confirmationModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    let modalConfirmBtn = document.getElementById('modalConfirmButton');

    modalTitle.textContent = `${accionTexto.charAt(0).toUpperCase() + accionTexto.slice(1)} Perfil`;
    modalMessage.innerHTML = `¿Está seguro de que desea ${accionTexto} el perfil "<strong>${nombre}</strong>"?`;
    
    modalConfirmBtn.className = 'px-4 py-2 rounded-md text-white transition-colors'; // Reset classes
    modalConfirmBtn.classList.add(accionTexto === 'inhabilitar' ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600');
    modalConfirmBtn.textContent = accionTexto.charAt(0).toUpperCase() + accionTexto.slice(1);
    
    const newModalConfirmButton = modalConfirmBtn.cloneNode(true);
    modalConfirmBtn.parentNode.replaceChild(newModalConfirmButton, modalConfirmBtn);
    
    newModalConfirmButton.onclick = () => {
        cambiarEstadoPerfil(id, estadoActual);
        hideModal();
    };
    
    showModal();
}

async function cambiarEstadoPerfil(id, estadoActual) {
    const nuevoEstado = estadoActual === 'activo' ? 'inactivo' : 'activo';
    const url = `/toggle_perfil_estado/${id}`;
    
    try {
        const respuesta = await fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ estado: nuevoEstado })
        });
        const resultado = await respuesta.json();
        if (respuesta.ok) {
            mostrarNotificacion(resultado.mensaje, 'success');
            cargarPerfiles();
        } else {
            mostrarNotificacion(resultado.mensaje, 'error');
        }
    } catch (error) {
        console.error(`Error al cambiar estado del perfil ${id}:`, error);
        mostrarNotificacion('Error de conexión al cambiar estado.', 'error');
    }
}

function hideModal() {
    const modal = document.getElementById('confirmationModal');
    if(!modal) return;
    modal.classList.remove('flex');
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
}