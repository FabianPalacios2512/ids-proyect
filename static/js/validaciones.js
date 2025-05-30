function toggleTheme() {
    const body = document.body;
    body.classList.toggle('dark-mode');
    const themeButton = document.querySelector('.theme-toggle');
    themeButton.textContent = body.classList.contains('dark-mode') ? '☀️' : '🌙';
}

function togglePassword() {
    const password = document.getElementById('password');
    password.type = password.type === 'password' ? 'text' : 'password';
}

async function validateForm() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();
    const messageBox = document.getElementById('messageBox');

    // Reset mensajes
    messageBox.className = "hidden";
    messageBox.innerHTML = "";

    // Validaciones
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!email || !password) {
        mostrarError("⚠️ Todos los campos son obligatorios.");
        return;
    }

    if (!emailRegex.test(email)) {
        mostrarError("⚠️ El correo no es válido.");
        return;
    }

    if (password.length < 6) {
        mostrarError("⚠️ La contraseña debe tener al menos 6 caracteres.");
        return;
    }

    document.getElementById("spinner").style.display = "block";

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, contrasena: password })
        });

        const result = await response.json();

        if (response.ok) {
            mostrarExito(result.mensaje);
            setTimeout(() => {
                window.location.href = "/dashboard";
            }, 1000);
        } else {
            mostrarError(result.mensaje || "⚠️ Error al iniciar sesión.");
        }
    } catch (error) {
        mostrarError("⚠️ Hubo un problema con la conexión.");
    } finally {
        document.getElementById("spinner").style.display = "none";
    }
}

function mostrarError(mensaje) {
    const box = document.getElementById('messageBox');
    box.className = "error-msg";
    box.innerHTML = mensaje;
}

function mostrarExito(mensaje) {
    const box = document.getElementById('messageBox');
    box.className = "success-msg";
    box.innerHTML = mensaje;
}