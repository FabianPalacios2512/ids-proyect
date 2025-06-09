// --- Variable global para guardar el ID del usuario que inició sesión ---
let idUsuarioLogueado = null;

// --- FUNCIÓN PARA OBTENER LOS DATOS DE SESIÓN DEL USUARIO ---
async function obtenerSesionUsuarioActual() {
    try {
        const response = await fetch('/usuarios/perfil-actual'); 
        if (!response.ok) throw new Error('No se pudo verificar la sesión del usuario.');
        const data = await response.json();
        // Verificamos que la respuesta contenga ambos datos
        if (data && typeof data.perfil !== 'undefined' && typeof data.id_usuario !== 'undefined') {
            return data; // Devuelve el objeto completo, ej: { perfil: 1, id_usuario: 5 }
        } else {
            throw new Error('Respuesta de sesión inválida desde el servidor.');
        }
    } catch (error) {
        console.error("Error crítico de autenticación:", error);
        throw error;
    }
}


// --- FUNCIÓN PARA OCULTAR ELEMENTOS SEGÚN EL PERFIL ---
function aplicarPermisosVisuales(idPerfil) {
    // El perfil de Administrador es 1
    if (idPerfil !== 1) {
        mostrarToast('No tienes permisos para acceder a esta sección.', 'error');

        const formUsuario = document.getElementById('formulario-usuario');
        const divTablaUsuarios = document.getElementById('tabla-usuarios-container'); 

        if (formUsuario) formUsuario.style.display = 'none';
        if (divTablaUsuarios) divTablaUsuarios.style.display = 'none';
        
        const navLinkUsuarios = document.querySelector('#nav-usuarios');
        if (navLinkUsuarios) navLinkUsuarios.style.display = 'none';

        return false;
    }
    return true; 
}


// --- EVENTO PRINCIPAL QUE SE EJECUTA AL CARGAR LA PÁGINA ---
document.addEventListener("DOMContentLoaded", async function () {
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    try {
        const sesion = await obtenerSesionUsuarioActual();
        idUsuarioLogueado = sesion.id_usuario; // Guardamos el ID en la variable global
        
        const esAdmin = aplicarPermisosVisuales(sesion.perfil);

        if (!esAdmin) {
            return; 
        }

        // --- El resto del código solo se ejecuta si el usuario ES Administrador ---
        cargarUsuarios();
        cargarPerfiles();
        cargarEventListenersValidacion();

        const formulario = document.getElementById("formulario-usuario");
        if(formulario) {
            formulario.addEventListener("submit", manejarEnvioFormulario);
        }

    } catch (error) {
        mostrarToast(error.message, 'error');
    }

    // Listener del botón de tema
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.documentElement.classList.toggle('dark');
            localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
            if (typeof lucide !== 'undefined') { lucide.createIcons(); }
        });
    }

    if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    }
    if (typeof lucide !== 'undefined') { lucide.createIcons(); }

    // Listener del buscador
    const inputBuscarUsuario = document.getElementById('buscar-usuario');
    if (inputBuscarUsuario) {
        inputBuscarUsuario.addEventListener('input', function(e) {
            const valorBusqueda = e.target.value.toLowerCase().trim();
            const tbody = document.getElementById('tabla-usuarios');
            if (!tbody) return;
            const filas = tbody.querySelectorAll('tr');
            let filasVisiblesCount = 0;
            const noResultadosClass = 'no-resultados';
            const existingNoResults = tbody.querySelector(`.${noResultadosClass}`);
            if (existingNoResults) { existingNoResults.remove(); }
            filas.forEach(fila => {
                if (fila.classList.contains('cargando-fila') || fila.classList.contains(noResultadosClass)) { return; }
                const textoFila = fila.textContent.toLowerCase();
                if (textoFila.includes(valorBusqueda)) {
                    fila.style.display = ''; filasVisiblesCount++;
                } else {
                    fila.style.display = 'none';
                }
            });
            if (filasVisiblesCount === 0 && valorBusqueda !== '') {
                const tr = document.createElement('tr');
                tr.className = `${noResultadosClass} text-center`;
                tr.innerHTML = `<td colspan="7" class="px-4 py-8 text-gray-500 dark:text-gray-400"><div class="flex flex-col items-center"><i data-lucide="search-x" class="w-10 h-10 mb-3"></i><span>No se encontraron resultados para "${valorBusqueda}"</span></div></td>`;
                tbody.appendChild(tr);
                if (typeof lucide !== 'undefined') { lucide.createIcons(); }
            }
        });
    }
    
    // Listener del botón Limpiar
    const btnLimpiarForm = document.getElementById('limpiar-formulario-btn');
    if (btnLimpiarForm) {
        btnLimpiarForm.addEventListener('click', (e) => { 
            e.preventDefault(); 
            limpiarFormulario(); 
        });
    }
});

// --- DEFINICIÓN DE TODAS LAS FUNCIONES ---

const MAX_NOMBRE_LENGTH = 50;
const MAX_APELLIDO_LENGTH = 50;
const MAX_EMAIL_LENGTH = 100;
const MAX_TELEFONO_LENGTH = 20;

let inputNombre, inputApellido, inputEmail, inputTelefono, selectPerfil, inputContrasena;

function inicializarReferenciasFormulario() {
    inputNombre = document.getElementById('nombre');
    inputApellido = document.getElementById('apellido');
    inputEmail = document.getElementById('email');
    inputTelefono = document.getElementById('telefono');
    selectPerfil = document.getElementById('perfil');
    inputContrasena = document.getElementById('contrasena');
}

function mostrarError(elementoInput, mensaje) {
    if (!elementoInput) return;
    let errorSpan = elementoInput.nextElementSibling;
    if (!errorSpan || !errorSpan.classList.contains('error-message')) {
        errorSpan = document.createElement('span');
        errorSpan.classList.add('error-message', 'text-red-500', 'text-xs', 'mt-1', 'block');
        if (elementoInput.parentNode) { elementoInput.parentNode.insertBefore(errorSpan, elementoInput.nextSibling); }
    }
    errorSpan.textContent = mensaje;
    elementoInput.classList.remove('border-gray-300', 'dark:border-gray-600');
    elementoInput.classList.add('border-red-500', 'dark:border-red-500');
}

function limpiarError(elementoInput) {
    if (!elementoInput) return;
    const errorSpan = elementoInput.nextElementSibling;
    if (errorSpan && errorSpan.classList.contains('error-message')) { errorSpan.remove(); }
    elementoInput.classList.remove('border-red-500', 'dark:border-red-500');
    elementoInput.classList.add('border-gray-300', 'dark:border-gray-600');
}

function validarNombre() {
    if (!inputNombre) return true;
    const nombreValor = inputNombre.value.trim();
    if (nombreValor.length === 0) { mostrarError(inputNombre, 'El nombre no puede estar vacío.'); return false; }
    if (nombreValor.length < 3) { mostrarError(inputNombre, 'El nombre debe tener al menos 3 caracteres.'); return false; }
    if (nombreValor.length > MAX_NOMBRE_LENGTH) { mostrarError(inputNombre, `El nombre no puede exceder los ${MAX_NOMBRE_LENGTH} caracteres.`); return false; }
    if (!/^[a-zA-Z_áéíóúÁÉÍÓÚñÑüÜ ]+$/.test(nombreValor)) { 
        mostrarError(inputNombre, 'El nombre solo puede contener letras, espacios y guion bajo (_).'); return false; 
    }
    limpiarError(inputNombre); return true;
}

function validarApellido() {
    if (!inputApellido) return true;
    const apellidoValor = inputApellido.value.trim();
    if (apellidoValor.length === 0) { mostrarError(inputApellido, 'El apellido no puede estar vacío.'); return false; }
    if (apellidoValor.length < 3) { mostrarError(inputApellido, 'El apellido debe tener al menos 3 caracteres.'); return false; }
    if (apellidoValor.length > MAX_APELLIDO_LENGTH) { mostrarError(inputApellido, `El apellido no puede exceder los ${MAX_APELLIDO_LENGTH} caracteres.`); return false; }
    if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s-]+$/.test(apellidoValor)) { 
        mostrarError(inputApellido, 'El apellido solo puede contener letras, espacios y guiones (-).'); return false; 
    }
    limpiarError(inputApellido); return true;
}

function validarEmailFormato() {
    if (!inputEmail) return true;
    const dominiosValidos = ['gmail.com', 'hotmail.com'];
    const emailValor = inputEmail.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const idUsuario = document.getElementById("id_usuario")?.value;
    if (emailValor.length === 0) {
        if (!idUsuario) { mostrarError(inputEmail, 'El email no puede estar vacío.'); return false; }
        else { limpiarError(inputEmail); return true; }
    }
    if (emailValor.length > MAX_EMAIL_LENGTH) { mostrarError(inputEmail, `El email no puede exceder los ${MAX_EMAIL_LENGTH} caracteres.`); return false; }
    if (!emailRegex.test(emailValor)) { mostrarError(inputEmail, 'Ingrese un formato de correo válido (ej: usuario@dominio.com).'); return false; }
    const dominio = emailValor.split('@')[1];
    if (dominio && !dominiosValidos.includes(dominio.toLowerCase())) {
        mostrarError(inputEmail, `El dominio "@${dominio}" no es válido. Utilice un proveedor conocido.`);
        return false;
    }
    limpiarError(inputEmail); return true;
}

async function verificarExistenciaEmail() {
    if (!inputEmail) inicializarReferenciasFormulario();
    if (!validarEmailFormato()) return;
    const emailValor = inputEmail.value.trim();
    if (emailValor === "") return;

    try {
        const idUsuarioActual = document.getElementById("id_usuario").value;
        const response = await fetch(`/usuarios/verificar-email?email=${encodeURIComponent(emailValor)}`);
        if (!response.ok) return;
        
        const data = await response.json();
        if (data.existe && (!idUsuarioActual || parseInt(data.usuarioId) !== parseInt(idUsuarioActual))) {
            mostrarError(inputEmail, 'Este correo electrónico ya está registrado.');
        } else {
            limpiarError(inputEmail);
        }
    } catch (error) {
        console.error('Error al verificar email:', error);
    }
}

function validarTelefono() {
    if (!inputTelefono) return true;
    const telefonoValor = inputTelefono.value.trim();
    if (telefonoValor.length === 0) { limpiarError(inputTelefono); return true; }
    if (!telefonoValor.startsWith('3')) { mostrarError(inputTelefono, 'El número de teléfono debe comenzar con 3.'); return false; }
    if (telefonoValor.length !== 10 || !/^[0-9]+$/.test(telefonoValor)) { mostrarError(inputTelefono, 'El teléfono debe contener 10 dígitos numéricos.'); return false; }
    limpiarError(inputTelefono); return true;
}

function validarPerfil() {
    if (!selectPerfil) return true;
    if (selectPerfil.value === "") { mostrarError(selectPerfil, 'Debe seleccionar un perfil.'); return false; }
    limpiarError(selectPerfil); return true;
}

function validarContrasena() {
    if (!inputContrasena) return true;
    const contrasenaValor = inputContrasena.value;
    const idUsuario = document.getElementById("id_usuario")?.value;
    if (idUsuario && contrasenaValor === "") { limpiarError(inputContrasena); return true; } 
    if (contrasenaValor.length === 0) { mostrarError(inputContrasena, 'La contraseña no puede estar vacía.'); return false; }
    if (contrasenaValor.length < 8) { mostrarError(inputContrasena, 'La contraseña debe tener al menos 8 caracteres.'); return false; }
    if (!/[A-Z]/.test(contrasenaValor)) { mostrarError(inputContrasena, 'Debe contener al menos una mayúscula.'); return false; }
    if (!/[a-z]/.test(contrasenaValor)) { mostrarError(inputContrasena, 'Debe contener al menos una minúscula.'); return false; }
    if (!/[0-9]/.test(contrasenaValor)) { mostrarError(inputContrasena, 'Debe contener al menos un número.'); return false; }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(contrasenaValor)) { mostrarError(inputContrasena, 'Debe contener al menos un carácter especial.'); return false; }
    limpiarError(inputContrasena); return true;
}

function cargarEventListenersValidacion() {
    inicializarReferenciasFormulario();
    if (inputNombre) inputNombre.addEventListener('input', validarNombre);
    if (inputApellido) inputApellido.addEventListener('input', validarApellido);
    if (inputEmail) {
        inputEmail.addEventListener('input', validarEmailFormato);
        inputEmail.addEventListener('blur', verificarExistenciaEmail);
    }
    if (inputTelefono) inputTelefono.addEventListener('input', validarTelefono);
    if (selectPerfil) selectPerfil.addEventListener('change', validarPerfil);
    if (inputContrasena) inputContrasena.addEventListener('input', validarContrasena);
}

function manejarEnvioFormulario(e) {
    e.preventDefault();
    const esValido = [validarNombre(), validarApellido(), validarEmailFormato(), validarTelefono(), validarPerfil(), validarContrasena()].every(v => v);
    if (!esValido) {
        mostrarToast('Por favor, corrija los errores del formulario.', 'error');
        return;
    }
    const id = document.getElementById("id_usuario").value;
    const datos = {
        nombre: document.getElementById("nombre").value,
        apellido: document.getElementById("apellido").value,
        telefono: document.getElementById("telefono").value,
        email: document.getElementById("email").value,
        contrasena: document.getElementById("contrasena")?.value || "",
        id_perfil: document.getElementById("perfil").value,
        estado: document.getElementById("estado")?.value || "Activo"
    };
    const url = id ? `/usuarios/actualizar/${id}` : "/usuarios/crear";
    const metodo = id ? "PUT" : "POST";

    fetch(url, {
        method: metodo,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos)
    })
    .then(res => res.json())
    .then(data => {
        mostrarToast(data.mensaje, data.exito ? 'success' : 'error');
        if (data.exito) {
            limpiarFormulario();
            cargarUsuarios();
        } else if (data.mensaje && data.mensaje.toLowerCase().includes('correo')) {
            mostrarError(inputEmail, data.mensaje);
        }
    })
    .catch(err => {
        console.error("Error al guardar usuario:", err);
        mostrarToast("Ocurrió un error inesperado al guardar.", "error");
    });
}

function cargarUsuarios() {
    fetch("/usuarios/listar")
        .then(res => {
            if (!res.ok) throw new Error(`Error del servidor: ${res.status}`);
            return res.json();
        })
        .then(data => {
            const tbody = document.getElementById("tabla-usuarios");
            if (!tbody) return;
            tbody.innerHTML = "";
            if (!data || data.length === 0) {
                tbody.innerHTML = `<tr class="text-center"><td colspan="7" class="px-4 py-8 text-gray-500">No hay usuarios registrados.</td></tr>`;
                return;
            }
            data.forEach(u => {
                const estadoColor = u.estado === "Activo" ? "bg-green-100 text-green-700 dark:bg-green-700 dark:text-green-100" : "bg-red-100 text-red-700 dark:bg-red-700 dark:text-red-100";
                const fila = document.createElement('tr');
                fila.className = "border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50";
                fila.innerHTML = `
                    <td class="px-4 py-3 whitespace-nowrap">${u.nombre || 'N/A'}</td>
                    <td class="px-4 py-3 whitespace-nowrap">${u.apellido || 'N/A'}</td>
                    <td class="px-4 py-3 whitespace-nowrap">${u.email || 'N/A'}</td>
                    <td class="px-4 py-3 hidden sm:table-cell whitespace-nowrap">${u.telefono || 'N/A'}</td>
                    <td class="px-4 py-3 hidden md:table-cell whitespace-nowrap">${u.perfil || 'N/A'}</td>
                    <td class="px-4 py-3 hidden lg:table-cell"><span class="px-3 py-1 rounded-full text-xs font-semibold ${estadoColor}">${u.estado}</span></td>
                    <td class="px-4 py-3 text-center whitespace-nowrap">
                        <button onclick="editarUsuario(${u.id_usuario})" class="bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1 rounded-md text-sm">Editar</button>
                        <button onclick="eliminarUsuario(${u.id_usuario})" class="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded-md text-sm">Eliminar</button>
                    </td>
                `;
                tbody.appendChild(fila);
            });
        }).catch(err => {
            console.error("Error al cargar usuarios:", err);
            mostrarToast("Error al cargar la lista de usuarios.", "error");
        });
}

function cargarPerfiles() {
    fetch("/usuarios/perfiles")
        .then(res => {
            if (!res.ok) throw new Error('Error al obtener perfiles');
            return res.json();
        })
        .then(perfiles => {
            const select = document.getElementById("perfil");
            if (!select) return;
            select.innerHTML = "<option value=''>Seleccione un perfil</option>";
            perfiles.forEach(p => {
                const option = document.createElement("option");
                option.value = p.id_perfil;
                option.textContent = p.nombre;
                select.appendChild(option);
            });
        }).catch(err => {
            console.error("Error al cargar perfiles:", err);
            mostrarToast("Error al cargar los perfiles para el formulario.", "error");
        });
}

function editarUsuario(id) {
    fetch(`/usuarios/obtener/${id}`)
        .then(res => {
            if (!res.ok) throw new Error('Error al obtener datos del usuario');
            return res.json();
        })
        .then(u => {
            if(!u) throw new Error('No se recibieron datos del usuario.');
            document.getElementById("id_usuario").value = u.id_usuario;
            if (inputNombre) inputNombre.value = u.nombre || ''; 
            if (inputApellido) inputApellido.value = u.apellido || '';
            if (inputTelefono) inputTelefono.value = u.telefono || ""; 
            if (inputEmail) inputEmail.value = u.email || '';
            if (inputContrasena) inputContrasena.value = ""; 
            if (selectPerfil) selectPerfil.value = u.id_perfil || '';
            const estadoSelect = document.getElementById("estado"); 
            if(estadoSelect) estadoSelect.value = u.estado || 'Activo';
            
            [inputNombre, inputApellido, inputEmail, inputTelefono, selectPerfil, inputContrasena].forEach(limpiarError);
            
            document.getElementById('titulo-formulario').textContent = 'Editar Usuario';
            document.querySelector('#formulario-usuario button[type="submit"]').textContent = 'Actualizar Usuario';
            
            window.scrollTo({ top: 0, behavior: 'smooth' });
        })
        .catch(error => { 
            console.error("Error al obtener usuario para editar:", error);
            mostrarToast(error.message, 'error');
        });
}

function eliminarUsuario(id) {
    if (id === idUsuarioLogueado) {
        mostrarToast('No puedes eliminar tu propia cuenta mientras tienes la sesión activa.', 'error');
        return;
    }
    if (confirm(`¿Estás seguro de que deseas eliminar este usuario (ID: ${id})? Esta acción es permanente.`)) {
        procederEliminacion(id);
    }
}

function procederEliminacion(id) {
    fetch(`/usuarios/eliminar/${id}`, { method: "DELETE" })
    .then(res => res.json())
    .then(data => {
        mostrarToast(data.mensaje, data.exito ? 'success' : 'error');
        if (data.exito) {
            cargarUsuarios();
            limpiarFormularioSiEditaba(id);
        }
    })
    .catch(err => {
        console.error("Error al eliminar usuario:", err);
        mostrarToast("Ocurrió un error al intentar eliminar el usuario.", "error");
    });
}

function limpiarFormularioSiEditaba(idEliminado) {
    const idActual = document.getElementById("id_usuario").value;
    if (idActual && parseInt(idActual) === parseInt(idEliminado)) {
        limpiarFormulario();
    }
}

function limpiarFormulario() {
    const formulario = document.getElementById("formulario-usuario");
    if (formulario) {
        formulario.reset();
        document.getElementById("id_usuario").value = "";
        
        if (!inputNombre) inicializarReferenciasFormulario();
        [inputNombre, inputApellido, inputEmail, inputTelefono, selectPerfil, inputContrasena].forEach(input => {
            if(input) limpiarError(input);
        });

        document.getElementById('titulo-formulario').textContent = 'Crear Nuevo Usuario';
        const submitButton = formulario.querySelector('button[type="submit"]');
        if(submitButton) submitButton.textContent = 'Guardar Usuario';
        
        mostrarToast('Formulario limpiado.', 'info');
    }
}

function mostrarToast(mensaje, tipo = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    const toastIconElement = document.getElementById('toast-icon');
    const iconContainer = document.getElementById('toast-icon-container');

    if (!toast || !toastMessage || !toastIconElement || !iconContainer) {
        alert(`${tipo.toUpperCase()}: ${mensaje}`);
        return;
    }

    toast.className = 'fixed top-5 right-5 max-w-xs sm:max-w-sm w-full sm:w-auto px-4 py-3 rounded-lg shadow-xl z-[100] transition-all duration-300 ease-out transform opacity-0 translate-x-full';
    iconContainer.className = 'inline-flex items-center justify-center flex-shrink-0 w-8 h-8 rounded-lg mr-3';
    toastIconElement.removeAttribute('data-lucide');
    toastIconElement.className = 'w-5 h-5';

    let arrToastClasses = [];
    let arrIconContainerClasses = [];
    let lucideIconName = 'info';

    switch (tipo) {
        case 'success':
            arrToastClasses = ['bg-green-100', 'dark:bg-green-800', 'text-green-700', 'dark:text-green-200'];
            arrIconContainerClasses = ['bg-green-200', 'dark:bg-green-700', 'text-green-600', 'dark:text-green-100'];
            lucideIconName = 'check-circle-2';
            break;
        case 'error':
            arrToastClasses = ['bg-red-100', 'dark:bg-red-800', 'text-red-700', 'dark:text-red-200'];
            arrIconContainerClasses = ['bg-red-200', 'dark:bg-red-700', 'text-red-600', 'dark:text-red-100'];
            lucideIconName = 'alert-circle';
            break;
        case 'warning':
            arrToastClasses = ['bg-yellow-100', 'dark:bg-yellow-800', 'text-yellow-700', 'dark:text-yellow-200'];
            arrIconContainerClasses = ['bg-yellow-200', 'dark:bg-yellow-700', 'text-yellow-600', 'dark:text-yellow-100'];
            lucideIconName = 'alert-triangle';
            break;
        default: 
            arrToastClasses = ['bg-blue-100', 'dark:bg-blue-800', 'text-blue-700', 'dark:text-blue-200'];
            arrIconContainerClasses = ['bg-blue-200', 'dark:bg-blue-700', 'text-blue-600', 'dark:text-blue-100'];
            lucideIconName = 'info';
            break;
    }

    arrToastClasses.forEach(cls => { if(cls) toast.classList.add(cls); });
    arrIconContainerClasses.forEach(cls => { if(cls) iconContainer.classList.add(cls); });
    
    toastIconElement.setAttribute('data-lucide', lucideIconName);
    toastMessage.textContent = mensaje;

    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    requestAnimationFrame(() => {
        toast.classList.remove('opacity-0', 'translate-x-full');
        toast.classList.add('opacity-100', 'translate-x-0');
    });

    setTimeout(() => {
        toast.classList.remove('opacity-100', 'translate-x-0');
        toast.classList.add('opacity-0', 'translate-x-full');
    }, 5000);
} 