document.addEventListener("DOMContentLoaded", function () {
    verificarPermiso();

    document.getElementById("formulario-usuario").addEventListener("submit", function (e) {
        e.preventDefault();

        const id = document.getElementById("id_usuario").value;
        const datos = {
            nombre: document.getElementById("nombre").value,
            apellido: document.getElementById("apellido").value,
            telefono: document.getElementById("telefono").value,
            email: document.getElementById("email").value,
            contrasena: document.getElementById("contrasena")?.value || "",
            id_perfil: document.getElementById("perfil").value,
            estado: document.getElementById("estado")?.value || "activo"
        };

        const url = id ? `/usuarios/actualizar/${id}` : "/usuarios/crear";
        const metodo = id ? "PUT" : "POST";

        fetch(url, {
            method: metodo,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos)
        })
        .then(res => res.json())
        .then(res => {
            mostrarToast(res.mensaje, res.exito ? "success" : "error");
            if (res.exito) {
                limpiarFormulario();
                cargarUsuarios();
            }
        });
    });
});

// ========================== FUNCIONES ==========================

function verificarPermiso() {
    fetch('/usuarios/perfil-actual')
        .then(res => res.json())
        .then(data => {
            console.log(data);  // Verificar lo que devuelve el servidor
            if (data.perfil !== 1) {  // Cambia aquí a '1' si el id_perfil del admin es 1
                mostrarToast('Usted no tiene permiso para acceder aquí, comunicate con el administrador', 'error');
                document.querySelector('form').style.display = 'none';
                document.getElementById('tabla-usuarios').innerHTML = '';
            } else {
                cargarUsuarios();
                cargarPerfiles();
            }
        });
}


function cargarUsuarios() {
    fetch("/usuarios/listar")
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById("tabla-usuarios");
            tbody.innerHTML = "";

            data.forEach(u => {
                const estado = (u.estado || "").toLowerCase();
                const estadoTexto = estado === "activo" ? "Activo" : "Inactivo";
                const estadoColor = estado === "activo"
                    ? "bg-green-100 text-green-700"
                    : "bg-red-100 text-red-700";

                const fila = document.createElement("tr");
                fila.innerHTML = `
                    <td class="px-4 py-3">${u.nombre}</td>
                    <td class="px-4 py-3">${u.apellido}</td>
                    <td class="px-4 py-3">${u.email}</td>
                    <td class="px-4 py-3">${u.telefono}</td>
                    <td class="px-4 py-3">${u.perfil}</td>
                    <td class="px-4 py-3">
                        <span class="px-3 py-1 rounded-full text-xs font-semibold ${estadoColor}">
                            ${estadoTexto}
                        </span>
                    </td>
                    <td class="px-4 py-3 text-center">
                        <button onclick="editarUsuario(${u.id_usuario})"
                            class="bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1 rounded-full text-sm mr-2 flex items-center gap-1 inline-flex">
                            <i data-lucide="edit" class="w-4 h-4"></i> Editar
                        </button>
                        <button onclick="eliminarUsuario(${u.id_usuario})"
                            class="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded-full text-sm flex items-center gap-1 inline-flex">
                            <i data-lucide="trash-2" class="w-4 h-4"></i> Eliminar
                        </button>
                    </td>
                `;
                tbody.appendChild(fila);
            });

            lucide.createIcons();
        });
}

function cargarPerfiles() {
    fetch("/usuarios/perfiles")
        .then(res => res.json())
        .then(perfiles => {
            const select = document.getElementById("perfil");
            select.innerHTML = "<option value=''>Seleccione un perfil</option>";
            perfiles.forEach(p => {
                const option = document.createElement("option");
                option.value = p.id_perfil;
                option.textContent = p.nombre;
                select.appendChild(option);
            });
        });
}

function editarUsuario(id) {
    fetch(`/usuarios/obtener/${id}`)
        .then(res => res.json())
        .then(u => {
            document.getElementById("id_usuario").value = u.id_usuario;
            document.getElementById("nombre").value = u.nombre;
            document.getElementById("apellido").value = u.apellido;
            document.getElementById("telefono").value = u.telefono;
            document.getElementById("email").value = u.email;
            document.getElementById("contrasena").value = u.contrasena;
            document.getElementById("perfil").value = u.id_perfil;
        });
}

function eliminarUsuario(id) {
    if (!confirm("¿Eliminar este usuario?")) return;
    fetch(`/usuarios/eliminar/${id}`, { method: "DELETE" })
        .then(res => res.json())
        .then(res => {
            mostrarToast(res.mensaje, res.exito ? "success" : "error");
            if (res.exito) cargarUsuarios();
        });
}

function limpiarFormulario() {
    document.getElementById("formulario-usuario").reset();
    document.getElementById("id_usuario").value = "";
}

// ========================== TOAST ==========================

function mostrarToast(mensaje, tipo = "error") {
    const toast = document.getElementById("toast");
    toast.textContent = mensaje;

    toast.className = `fixed top-5 right-5 px-4 py-2 rounded-lg shadow-lg z-50 transition-all duration-500 ${
        tipo === "error" ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"
    }`;

    toast.classList.remove("hidden");

    setTimeout(() => {
        toast.classList.add("hidden");
    }, 8000);
}

