document.addEventListener("DOMContentLoaded", function () {
    cargarUsuarios();
    cargarPerfiles();

    document.getElementById("formulario-usuario").addEventListener("submit", function (e) {
        e.preventDefault();

        const id = document.getElementById("id_usuario").value;
        const datos = {
            nombre: document.getElementById("nombre").value,
            apellido: document.getElementById("apellido").value,
            telefono: document.getElementById("telefono").value,
            email: document.getElementById("email").value,
            contrasena: document.getElementById("contrasena").value,
            id_perfil: document.getElementById("perfil").value
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
                alert(res.mensaje);
                if (res.exito) {
                    limpiarFormulario();
                    cargarUsuarios();
                }
            });
    });
});



function cargarUsuarios() {
    fetch("/usuarios/listar")
        .then(res => res.json())
        .then(data => {
            console.log(data); // <-- VERIFICACIÓN
            const tbody = document.getElementById("tabla-usuarios");
            tbody.innerHTML = "";
        
            data.forEach(u => {
                const fila = document.createElement("tr");

                // Normalizar el estado (por si viene en mayúsculas o minúsculas)
                const estado = (u.estado || "").toLowerCase();
                const estadoTexto = estado === "activo" ? "Activo" : "Inactivo";
                const estadoColor = estado === "activo"
                    ? "bg-green-100 text-green-700"
                    : "bg-red-100 text-red-700";

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

            lucide.createIcons(); // Renderiza íconos correctamente después del DOM update
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
            alert(res.mensaje);
            if (res.exito) cargarUsuarios();
        });
}

function limpiarFormulario() {
    document.getElementById("formulario-usuario").reset();
    document.getElementById("id_usuario").value = "";
}
