// perfiles.js

// Función para verificar permisos del perfil
function verificarPermisoPerfil() {
  fetch('/usuarios/perfil-actual')
    .then(res => res.json())
    .then(data => {
      if (data.perfil !== 1) {
        alert("No tienes permisos para ver esta página.");
        document.getElementById("contenido").style.display = "none";
        document.getElementById("tabla-perfiles").style.display = "none";
      } else {
        cargarPerfiles();
      }
    });
}

let perfiles = [];

// Evento que se ejecuta al cargar el documento
document.addEventListener('DOMContentLoaded', function() {
verificarPermisoPerfil();

// Verificar y aplicar el tema guardado o predeterminado
if (localStorage.getItem('theme') === 'dark' || 
    (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
} else {
    document.documentElement.classList.remove('dark');
}

// Configuración de evento para el botón de cambiar tema
const themeToggleButton = document.getElementById("theme-toggle");
themeToggleButton.addEventListener("click", toggleTheme);
});

// Función para cargar los perfiles desde el servidor
function cargarPerfiles() {
  fetch('/perfiles')
    .then(res => res.json())
    .then(data => {
      if (data.status && data.status === 'error') {
        mostrarToast(data.mensaje, 'error');
        document.getElementById("tabla-perfiles").style.display = 'none';
      } else {
        perfiles = data;
        renderizarPerfiles(perfiles);
      }
    })
    .catch(() => {
      mostrarToast("Hubo un error al cargar los perfiles.", 'error');
    });
}

// Función para renderizar los perfiles en la tabla
function renderizarPerfiles(lista) {
  const tabla = document.getElementById("tabla-perfiles");
  tabla.innerHTML = '';

  lista.forEach(perfil => {
      tabla.insertAdjacentHTML("beforeend", `
        <tr class="bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100 border-b dark:border-gray-600">
          <td class="px-4 py-2">${perfil.id_perfil}</td>
          <td class="px-4 py-2">${perfil.nombre}</td>
          <td class="px-4 py-2 text-gray-600 dark:text-gray-300">${perfil.descripcion}</td>
          <td class="px-4 py-2">
            <span class="inline-block px-2 py-1 text-xs font-semibold rounded-full
              ${perfil.estado === 'activo' ? 'bg-green-100 text-green-700 dark:bg-green-200 dark:text-green-900' : 'bg-red-100 text-red-700 dark:bg-red-200 dark:text-red-900'}">
              ${perfil.estado}
            </span>
          </td>
          <td class="px-4 py-2 text-center">
            <div class="flex justify-center gap-2">
              <button onclick="editarPerfil(${perfil.id_perfil}, '${perfil.nombre}', '${perfil.estado}', '${perfil.descripcion}')" 
                      class="bg-yellow-400 text-white px-3 py-1 rounded text-xs hover:bg-yellow-500">
                Editar
              </button>
              <button onclick="inhabilitarPerfil(${perfil.id_perfil})" 
                      class="bg-red-500 text-white px-3 py-1 rounded text-xs hover:bg-red-600">
                Inhabilitar
              </button>
            </div>
          </td>
        </tr>
      `);
  });
}

// Función para buscar perfiles en la tabla
function filtrarPerfiles() {
  const texto = document.getElementById("buscador").value.toLowerCase();
  const filtrados = perfiles.filter(p =>
    p.nombre.toLowerCase().includes(texto) || p.estado.toLowerCase().includes(texto)
  );
  renderizarPerfiles(filtrados);
}

// Función para guardar o editar un perfil
function guardarPerfil(event) {
  event.preventDefault();

  const id = document.getElementById("id_perfil_editar").value;
  const nombre = document.getElementById("nombre").value.trim();
  const estado = document.getElementById("estado").value.trim();
  const descripcion = document.getElementById("descripcion").value.trim();

  const datos = { nombre, estado, descripcion };

  const url = id ? `/editar_perfil/${id}` : '/crear_perfil';
  const metodo = id ? 'PUT' : 'POST';

  fetch(url, {
    method: metodo,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(datos)
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === 'success') {
      alert(data.mensaje);
      document.getElementById("formularioPerfil").reset();
      document.getElementById("id_perfil_editar").value = '';
      cargarPerfiles();
    } else {
      alert(data.mensaje);
    }
  })
  .catch(err => {
    console.error("Error al guardar perfil:", err);
    alert("Ocurrió un error al guardar el perfil.");
  });
}

// Función para editar un perfil
function editarPerfil(id, nombre, estado, descripcion) {
  document.getElementById("id_perfil_editar").value = id;
  document.getElementById("nombre").value = nombre;
  document.getElementById("estado").value = estado;
  document.getElementById("descripcion").value = descripcion;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Función para inhabilitar un perfil
function inhabilitarPerfil(id) {
  if (!confirm("¿Estás seguro de que deseas inhabilitar este perfil?")) return;

  fetch(`/inhabilitar_perfil/${id}`, { method: 'PUT' })
    .then(res => res.json())
    .then(data => {
      alert(data.mensaje);
      cargarPerfiles();
    })
    .catch(() => alert("Error al inhabilitar el perfil"));
}

// Función para mostrar mensajes (toasts)
function mostrarToast(mensaje, tipo = "error") {
  const toast = document.getElementById("toast");
  toast.textContent = mensaje;

  toast.className = `fixed top-5 right-5 px-4 py-2 rounded-lg shadow-lg z-50 transition-all duration-500 ${
      tipo === "error" ? "bg-red-100 text-red-800 dark:bg-red-200 dark:text-red-900" : "bg-green-100 text-green-800 dark:bg-green-200 dark:text-green-900"
  }`;

  toast.classList.remove("hidden");

  setTimeout(() => {
      toast.classList.add("hidden");
  }, 8000);
}

// Función para cambiar entre tema claro y oscuro
function toggleTheme() {
  if (document.documentElement.classList.contains("dark")) {
    document.documentElement.classList.remove("dark");
    localStorage.setItem("theme", "light");
  } else {
    document.documentElement.classList.add("dark");
    localStorage.setItem("theme", "dark");
  }
}
