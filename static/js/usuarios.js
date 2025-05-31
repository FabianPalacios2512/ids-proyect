document.addEventListener("DOMContentLoaded", function () {
    // Inicializar iconos de Lucide
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // --- Carga inicial de usuarios y perfiles ---
    cargarUsuarios();
    cargarPerfiles();
    // Carga los event listeners para todas las validaciones instantáneas
    cargarEventListenersValidacion();

    // --- Manejo del Envío del Formulario ---
    document.getElementById("formulario-usuario").addEventListener("submit", function (e) {
        e.preventDefault();

        const esNombreValido = validarNombre();
        const esApellidoValido = validarApellido();
        const esEmailFormatoValido = validarEmailFormato(); // Solo formato aquí
        const esTelefonoValido = validarTelefono();
        const esPerfilValido = validarPerfil();
        const esContrasenaValida = validarContrasena();

        if (!esNombreValido || !esApellidoValido || !esEmailFormatoValido ||
            !esTelefonoValido || !esPerfilValido || !esContrasenaValida) {
            mostrarToast('Por favor, corrija los errores de formato en el formulario antes de guardar.', 'error');
            return;
        }

        const id = document.getElementById("id_usuario").value;
        const datos = {
            nombre: document.getElementById("nombre").value,
            apellido: document.getElementById("apellido").value,
            telefono: document.getElementById("telefono").value,
            email: document.getElementById("email").value,
            contrasena: document.getElementById("contrasena")?.value || "", // Se envía texto plano
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
        .then(async res => { // <--- MARCADO COMO ASYNC
            if (!res.ok) {
                let errorData;
                let errorMessageFromServer;
                try {
                    // Intenta parsear como JSON primero, clonando la respuesta
                    errorData = await res.clone().json(); 
                    errorMessageFromServer = errorData.mensaje || JSON.stringify(errorData); // Usa el mensaje o el objeto stringifeado
                } catch (e) {
                    // Si falla el parseo JSON (ej. es HTML de error 500), lee el cuerpo original como texto
                    errorMessageFromServer = await res.text(); 
                }

                const lowerErrorMessage = (errorMessageFromServer || '').toLowerCase();
                const esErrorDeEmailDuplicadoDetectadoEnSubmit =
                    (lowerErrorMessage.includes('duplicate entry') && lowerErrorMessage.includes('email')) ||
                    lowerErrorMessage.includes('correo ya registrado') ||
                    lowerErrorMessage.includes('el correo electrónico ya existe');

                if (esErrorDeEmailDuplicadoDetectadoEnSubmit) {
                    mostrarError(inputEmail, 'EL CORREO YA SE ENCUENTRA REGISTRADO POR FAVOR INTENTE CON OTRO');
                    throw new Error('EL CORREO YA SE ENCUENTRA REGISTRADO POR FAVOR INTENTE CON OTRO');
                }
                // Para otros errores, lanzar el mensaje obtenido del servidor
                throw new Error(errorMessageFromServer || `Error ${res.status} del servidor.`);
            }
            return res.json(); // Si res.ok es true
        })
        .then(responseData => {
            mostrarToast(responseData.mensaje, responseData.exito ? "success" : "error");
            if (responseData.exito) {
                limpiarFormulario();
                cargarUsuarios();
            }
        })
        .catch(error => { 
            console.error('Error en la petición de submit:', error);
            mostrarToast(error.message || 'Error al procesar la solicitud.', 'error');
        });
    });

    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.documentElement.classList.toggle('dark');
            if (document.documentElement.classList.contains('dark')) {
                localStorage.setItem('theme', 'dark');
            } else {
                localStorage.setItem('theme', 'light');
            }
            if (typeof lucide !== 'undefined') { lucide.createIcons(); }
        });
    }

    if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
    if (typeof lucide !== 'undefined') { lucide.createIcons(); }

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
});

const MAX_NOMBRE_LENGTH = 50;
const MAX_APELLIDO_LENGTH = 50;
const MAX_EMAIL_LENGTH = 100;
const MAX_TELEFONO_LENGTH = 20;

function mostrarError(elementoInput, mensaje) {
    if (!elementoInput) return;
    let errorSpan = elementoInput.nextElementSibling;
    if (!errorSpan || !errorSpan.classList.contains('error-message')) {
        errorSpan = document.createElement('span');
        errorSpan.classList.add('error-message', 'text-red-500', 'text-xs', 'mt-1', 'block');
        if (elementoInput.parentNode) { elementoInput.parentNode.insertBefore(errorSpan, elementoInput.nextSibling); }
    }
    errorSpan.textContent = mensaje;
    elementoInput.classList.remove('border-gray-300', 'dark:border-gray-600', 'focus:border-blue-500', 'dark:focus:border-blue-500', 'focus:ring-blue-500');
    elementoInput.classList.add('border-red-500', 'dark:border-red-500', 'focus:border-red-500', 'dark:focus:border-red-500', 'focus:ring-red-500');
}

function limpiarError(elementoInput) {
    if (!elementoInput) return;
    const errorSpan = elementoInput.nextElementSibling;
    if (errorSpan && errorSpan.classList.contains('error-message')) { errorSpan.remove(); }
    elementoInput.classList.remove('border-red-500', 'dark:border-red-500', 'focus:border-red-500', 'dark:focus:border-red-500', 'focus:ring-red-500');
    elementoInput.classList.add('border-gray-300', 'dark:border-gray-600', 'focus:border-blue-500', 'dark:focus:border-blue-500', 'focus:ring-blue-500');
}

let inputNombre, inputApellido, inputEmail, inputTelefono, selectPerfil, inputContrasena;

function inicializarReferenciasFormulario() {
    inputNombre = document.getElementById('nombre');
    inputApellido = document.getElementById('apellido');
    inputEmail = document.getElementById('email');
    inputTelefono = document.getElementById('telefono');
    selectPerfil = document.getElementById('perfil');
    inputContrasena = document.getElementById('contrasena');
}
document.addEventListener('DOMContentLoaded', inicializarReferenciasFormulario);

function validarNombre() {
    if (!inputNombre) inicializarReferenciasFormulario(); if (!inputNombre) return true;
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
    if (!inputApellido) inicializarReferenciasFormulario(); if (!inputApellido) return true;
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
    if (!inputEmail) inicializarReferenciasFormulario(); if (!inputEmail) return true;
    const emailValor = inputEmail.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const idUsuario = document.getElementById("id_usuario")?.value;
    if (emailValor.length === 0) {
        if (!idUsuario) {
            mostrarError(inputEmail, 'El email no puede estar vacío.'); return false;
        } else {
            limpiarError(inputEmail); return true;
        }
    }
    if (emailValor.length > MAX_EMAIL_LENGTH) {
        mostrarError(inputEmail, `El email no puede exceder los ${MAX_EMAIL_LENGTH} caracteres.`); return false;
    }
    if (!emailRegex.test(emailValor)) {
        mostrarError(inputEmail, 'Ingrese un formato de correo electrónico válido (ej: usuario@dominio.com).'); return false;
    }
    const errorSpan = inputEmail.nextElementSibling;
    if (errorSpan && errorSpan.classList.contains('error-message') && 
        (errorSpan.textContent.toLowerCase().includes('formato') || errorSpan.textContent.toLowerCase().includes('vacío'))) {
        limpiarError(inputEmail);
    }
    return true;
}

async function verificarExistenciaEmail() {
    if (!inputEmail) inicializarReferenciasFormulario(); if (!inputEmail) return;
    const formatoValido = validarEmailFormato();
    const emailValor = inputEmail.value.trim();
    if (!formatoValido || emailValor === "") { return; }

    try {
        const idUsuarioActual = document.getElementById("id_usuario").value;
        let urlVerificacion = `/usuarios/verificar-email?email=${encodeURIComponent(emailValor)}`;
        const response = await fetch(urlVerificacion);
        if (!response.ok) {
            console.error('Error del servidor al verificar email (endpoint no encontrado o error):', response.status);
            const errorText = await response.text();
            console.error('Cuerpo de la respuesta de error (verificación):', errorText);
            mostrarError(inputEmail, 'No se pudo verificar el correo en este momento. Intente guardar.');
            return;
        }
        const data = await response.json();
        if (data.existe) {
            if (idUsuarioActual && data.usuarioId && parseInt(data.usuarioId) === parseInt(idUsuarioActual)) {
                limpiarError(inputEmail); 
            } else {
                mostrarError(inputEmail, 'EL CORREO YA SE ENCUENTRA REGISTRADO.');
            }
        } else {
            limpiarError(inputEmail); 
        }
    } catch (error) {
        console.error('Error en la petición fetch para verificar email (red o parseo JSON):', error);
        mostrarError(inputEmail, 'Fallo de red al verificar el correo. Intente guardar.');
    }
}

function validarTelefono() {
    if (!inputTelefono) inicializarReferenciasFormulario(); if (!inputTelefono) return true;
    const telefonoValor = inputTelefono.value.trim();
    const telefonoRegex = /^\+?[0-9\s\-()]*$/;
    const minDigitos = 7; 

    if (telefonoValor.length === 0) { 
        limpiarError(inputTelefono); return true; 
    }
    if (!telefonoRegex.test(telefonoValor)) { 
        mostrarError(inputTelefono, 'El teléfono solo puede contener números, espacios, y los símbolos +, -, (, ).');
        return false;
    }
    const soloNumeros = telefonoValor.replace(/[^\d]/g, "");
    if (soloNumeros.length > 0 && soloNumeros.length < minDigitos) {
         mostrarError(inputTelefono, `El teléfono debe tener al menos ${minDigitos} dígitos.`);
         return false;
    }
    if (telefonoValor.length > MAX_TELEFONO_LENGTH) {
        mostrarError(inputTelefono, `El teléfono no debe exceder los ${MAX_TELEFONO_LENGTH} caracteres.`);
        return false;
    }
    limpiarError(inputTelefono); return true;
}

function validarPerfil() {
    if (!selectPerfil) inicializarReferenciasFormulario(); if (!selectPerfil) return true;
    if (selectPerfil.value === "" || selectPerfil.value === "Seleccione un perfil") { mostrarError(selectPerfil, 'Debe seleccionar un perfil.'); return false; }
    limpiarError(selectPerfil); return true;
}

function validarContrasena() {
    if (!inputContrasena) inicializarReferenciasFormulario(); if (!inputContrasena) return true;
    const contrasenaValor = inputContrasena.value;
    const idUsuario = document.getElementById("id_usuario")?.value;
    if (idUsuario && contrasenaValor === "") { limpiarError(inputContrasena); return true; } 
    if (!idUsuario || (idUsuario && contrasenaValor.length > 0)) { 
        if (contrasenaValor.length === 0 && !idUsuario) { mostrarError(inputContrasena, 'La contraseña no puede estar vacía.'); return false; }
        if (contrasenaValor.length < 8) { mostrarError(inputContrasena, 'La contraseña debe tener al menos 8 caracteres.'); return false; }
        if (!/[A-Z]/.test(contrasenaValor)) { mostrarError(inputContrasena, 'Debe contener al menos una letra mayúscula.'); return false; }
        if (!/[a-z]/.test(contrasenaValor)) { mostrarError(inputContrasena, 'Debe contener al menos una letra minúscula.'); return false; }
        if (!/[0-9]/.test(contrasenaValor)) { mostrarError(inputContrasena, 'Debe contener al menos un número.'); return false; }
        if (!/[!@#$%^&*(),.?":{}|<>]/.test(contrasenaValor)) { mostrarError(inputContrasena, 'Debe contener al menos un carácter especial (!@#$%^&*(),.?":{}|<>).'); return false; }
    }
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

function cargarUsuarios() {
    fetch("/usuarios/listar")
        .then(async res => { // Marcar como async para usar await adentro
            if (!res.ok) {
                let errorMsg = `Error del servidor (Código: ${res.status}) al intentar listar usuarios.`;
                try {
                    const errorBody = await res.clone().json(); // Intentar leer como JSON
                    errorMsg = errorBody.mensaje || JSON.stringify(errorBody);
                } catch (e) {
                    errorMsg = await res.text(); // Si falla JSON, leer como texto
                }
                throw new Error(errorMsg);
            }
            return res.json();
        })
        .then(data => {
            const tbody = document.getElementById("tabla-usuarios"); if (!tbody) return; tbody.innerHTML = "";
            if (!data || data.length === 0) {
                const noDataRow = document.createElement("tr"); noDataRow.className = "text-center no-resultados";
                noDataRow.innerHTML = `<td colspan="7" class="px-4 py-8 text-gray-500 dark:text-gray-400"><div class="flex flex-col items-center"><i data-lucide="info" class="w-10 h-10 mb-3"></i><span>No hay usuarios registrados.</span></div></td>`;
                tbody.appendChild(noDataRow);
            } else {
                data.forEach(u => {
                    const estado = (u.estado || "").toLowerCase(); const estadoTexto = estado === "activo" ? "Activo" : "Inactivo";
                    const estadoColor = estado === "activo" ? "bg-green-100 text-green-700 dark:bg-green-700 dark:text-green-100" : "bg-red-100 text-red-700 dark:bg-red-700 dark:text-red-100";
                    const fila = document.createElement("tr"); fila.className = "border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors duration-150";
                    fila.innerHTML = `
                        <td class="px-4 py-3 whitespace-nowrap">${u.nombre || 'N/A'}</td><td class="px-4 py-3 whitespace-nowrap">${u.apellido || 'N/A'}</td>
                        <td class="px-4 py-3 whitespace-nowrap">${u.email || 'N/A'}</td><td class="px-4 py-3 hidden sm:table-cell whitespace-nowrap">${u.telefono || 'N/A'}</td>
                        <td class="px-4 py-3 hidden md:table-cell whitespace-nowrap">${u.perfil || 'N/A'}</td>
                        <td class="px-4 py-3 hidden lg:table-cell"><span class="px-3 py-1 rounded-full text-xs font-semibold ${estadoColor}">${estadoTexto}</span></td>
                        <td class="px-4 py-3 text-center whitespace-nowrap">
                            <button onclick="editarUsuario(${u.id_usuario})" class="bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1 rounded-md text-sm mr-2 flex items-center gap-1 inline-flex shadow-sm hover:shadow-md transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-yellow-400"><i data-lucide="edit" class="w-4 h-4"></i> <span class="hidden xs:inline">Editar</span></button>
                            <button onclick="eliminarUsuario(${u.id_usuario})" class="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded-md text-sm flex items-center gap-1 inline-flex shadow-sm hover:shadow-md transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-red-400"><i data-lucide="trash-2" class="w-4 h-4"></i> <span class="hidden xs:inline">Eliminar</span></button>
                        </td>`;
                    tbody.appendChild(fila);
                });
            }
            if (typeof lucide !== 'undefined') { lucide.createIcons(); }
        })
        .catch(error => {
            console.error("Error al cargar usuarios:", error); const tbody = document.getElementById("tabla-usuarios"); if (!tbody) return;
            tbody.innerHTML = `<tr class="text-center no-resultados"><td colspan="7" class="px-4 py-8 text-red-500 dark:text-red-400"><div class="flex flex-col items-center"><i data-lucide="alert-triangle" class="w-10 h-10 mb-3"></i><span>Error al cargar los usuarios: ${error.message || 'Desconocido.'} Por favor, intente de nuevo más tarde.</span></div></td></tr>`;
            if (typeof lucide !== 'undefined') { lucide.createIcons(); }
        });
}

function cargarPerfiles() {
    fetch("/usuarios/perfiles")
        .then(async res => { // async para usar await
            if (!res.ok) {
                let errorMsg = `Error al obtener perfiles (Código: ${res.status})`;
                try { const err = await res.clone().json(); errorMsg = err.mensaje || JSON.stringify(err); } 
                catch (e) { errorMsg = await res.text(); }
                throw new Error(errorMsg);
            }
            return res.json();
        })
        .then(perfiles => {
            const select = document.getElementById("perfil"); if (!select) return;
            select.innerHTML = "<option value=''>Seleccione un perfil</option>";
            perfiles.forEach(p => { const option = document.createElement("option"); option.value = p.id_perfil; option.textContent = p.nombre; select.appendChild(option); });
        })
        .catch(error => { console.error("Error al cargar perfiles:", error); mostrarToast(error.message || 'Error al cargar los perfiles disponibles.', 'error'); });
}

function editarUsuario(id) {
    fetch(`/usuarios/obtener/${id}`)
        .then(async res => { // async para usar await
            if (!res.ok) {
                let errorMsg = `Error al obtener usuario (Código: ${res.status})`;
                try { const err = await res.clone().json(); errorMsg = err.mensaje || JSON.stringify(err); }
                catch (e) { errorMsg = await res.text(); }
                throw new Error(errorMsg);
            }
            return res.json();
        })
        .then(u => {
            if(!u) { mostrarToast('No se recibieron datos del usuario.', 'error'); return; }
            document.getElementById("id_usuario").value = u.id_usuario;
            if (inputNombre) inputNombre.value = u.nombre || ''; if (inputApellido) inputApellido.value = u.apellido || '';
            if (inputTelefono) inputTelefono.value = u.telefono || ""; if (inputEmail) inputEmail.value = u.email || '';
            if (inputContrasena) inputContrasena.value = ""; if (selectPerfil) selectPerfil.value = u.id_perfil || '';
            const estadoSelect = document.getElementById("estado"); if(estadoSelect) estadoSelect.value = u.estado || 'Activo';

            limpiarError(inputNombre); limpiarError(inputApellido); limpiarError(inputEmail); limpiarError(inputTelefono); limpiarError(selectPerfil); limpiarError(inputContrasena);
            const formElement = document.getElementById('formulario-usuario');
            if (formElement) {
                 formElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                 const submitButton = formElement.querySelector('button[type="submit"]'); if(submitButton) submitButton.textContent = 'Actualizar Usuario';
            }
            const tituloForm = document.getElementById('titulo-formulario'); if(tituloForm) tituloForm.textContent = 'Editar Usuario';
        })
        .catch(error => { console.error("Error al obtener usuario para editar:", error); mostrarToast(error.message || 'Error al cargar los datos del usuario para edición.', 'error'); });
}

function eliminarUsuario(id) {
    const modalConfirmacion = document.getElementById('confirmacion-modal');
    const mensajeModal = document.getElementById('mensaje-confirmacion');
    const btnConfirmarEliminar = document.getElementById('confirmar-eliminar');
    const btnCancelarEliminar = document.getElementById('cancelar-eliminar');
    const btnsCerrarModal = document.querySelectorAll('[data-modal-hide="confirmacion-modal"], .cerrar-modal-btn');

    if (!modalConfirmacion || !mensajeModal || !btnConfirmarEliminar || !btnCancelarEliminar) {
        if (!confirm(`¿Está seguro que desea eliminar este usuario (ID: ${id}) de forma permanente?`)) { return; }
        procederEliminacion(id); return;
    }
    mensajeModal.textContent = `¿Está seguro que desea eliminar este usuario (ID: ${id}) de forma permanente? Esta acción no se puede deshacer.`;
    modalConfirmacion.classList.remove('hidden', 'opacity-0'); 
    modalConfirmacion.classList.add('flex', 'opacity-100');
    const modalContent = document.getElementById('confirmacion-modal-content');
    if(modalContent) {
        modalContent.classList.remove('scale-95', 'opacity-0');
        modalContent.classList.add('scale-100', 'opacity-100');
    }

    const nuevoBtnConfirmar = btnConfirmarEliminar.cloneNode(true);
    btnConfirmarEliminar.parentNode.replaceChild(nuevoBtnConfirmar, btnConfirmarEliminar);
    nuevoBtnConfirmar.textContent = "Sí, eliminar";
    
    const cerrarModalFn = () => { 
        if(modalContent) {
            modalContent.classList.remove('scale-100', 'opacity-100');
            modalContent.classList.add('scale-95', 'opacity-0');
        }
        modalConfirmacion.classList.remove('opacity-100');
        modalConfirmacion.classList.add('opacity-0');
        setTimeout(() => {
            modalConfirmacion.classList.add('hidden'); 
            modalConfirmacion.classList.remove('flex');
        }, 300); 
    };
    nuevoBtnConfirmar.onclick = () => { procederEliminacion(id); cerrarModalFn(); };
    if(btnCancelarEliminar) btnCancelarEliminar.onclick = cerrarModalFn;
    btnsCerrarModal.forEach(btn => { 
        const nuevoBtnCerrar = btn.cloneNode(true); 
        btn.parentNode.replaceChild(nuevoBtnCerrar, btn); 
        nuevoBtnCerrar.onclick = cerrarModalFn; 
    });
}

function procederEliminacion(id) {
    fetch(`/usuarios/eliminar/${id}`, { method: "DELETE" })
        .then(async res => { // async para usar await
            if (!res.ok) {
                let errorMsg = `Error al eliminar (Código: ${res.status})`;
                try { const err = await res.clone().json(); errorMsg = err.mensaje || JSON.stringify(err); }
                catch (e) { errorMsg = await res.text(); }
                throw new Error(errorMsg);
            }
            return res.json();
        })
        .then(res => {
            mostrarToast(res.mensaje, res.exito ? "success" : "error");
            if (res.exito) { cargarUsuarios(); limpiarFormularioSiEditaba(id); }
        })
        .catch(error => { console.error("Error al eliminar usuario:", error); mostrarToast(error.message || 'Error al eliminar el usuario. Intente de nuevo.', 'error'); });
}

function limpiarFormularioSiEditaba(idEliminado) {
    const idActualEnForm = document.getElementById("id_usuario")?.value;
    if (idActualEnForm && parseInt(idActualEnForm) === parseInt(idEliminado)) { limpiarFormulario(); }
}

function limpiarFormulario() {
    const formulario = document.getElementById("formulario-usuario");
    if (formulario) {
        formulario.reset(); const idUsuarioInput = document.getElementById("id_usuario"); if (idUsuarioInput) idUsuarioInput.value = "";
        inicializarReferenciasFormulario();
        if(inputNombre) limpiarError(inputNombre); if(inputApellido) limpiarError(inputApellido); if(inputEmail) limpiarError(inputEmail);
        if(inputTelefono) limpiarError(inputTelefono); if(selectPerfil) limpiarError(selectPerfil); if(inputContrasena) limpiarError(inputContrasena);
        if (selectPerfil) selectPerfil.value = ""; const estadoSelect = document.getElementById("estado"); if (estadoSelect) estadoSelect.value = "Activo";
        const submitButton = formulario.querySelector('button[type="submit"]'); if(submitButton) submitButton.textContent = 'Guardar Usuario';
        const tituloForm = document.getElementById('titulo-formulario'); if(tituloForm) tituloForm.textContent = 'Crear Nuevo Usuario';
    }
}

function mostrarToast(mensaje, tipo = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    const toastIconElement = document.getElementById('toast-icon');
    const iconContainer = document.getElementById('toast-icon-container');

    if (!toast || !toastMessage || !toastIconElement || !iconContainer) {
        console.warn('Elementos del Toast no encontrados. Usando alert como fallback.');
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
        default: // info
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

const btnLimpiarForm = document.getElementById('limpiar-formulario-btn');
if (btnLimpiarForm) {
    btnLimpiarForm.addEventListener('click', (e) => { 
        e.preventDefault(); 
        limpiarFormulario(); 
        mostrarToast('Formulario limpiado.', 'info'); 
    });
}