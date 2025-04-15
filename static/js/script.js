document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("loginForm");

    form.addEventListener("submit", async function (event) {
        event.preventDefault(); // Evita que la página se recargue

        // Capturamos los valores
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();

        // Elementos de error
        const emailError = document.getElementById("emailError");
        const passwordError = document.getElementById("passwordError");
        const loginError = document.getElementById("loginError");

        // Reiniciar errores
        emailError.classList.add("hidden");
        passwordError.classList.add("hidden");
        loginError.classList.add("hidden");

        let valid = true;

        // Validación de email
        if (!email.match(/^\S+@\S+\.\S+$/)) {
            emailError.classList.remove("hidden");
            valid = false;
        }

        // Validación de contraseña
        if (password.length < 5) {
            passwordError.classList.remove("hidden");
            valid = false;
        }

        if (!valid) return; // No enviar si hay errores

        // Enviar datos al backend
        const response = await fetch("http://127.0.0.1:5000/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, contrasena: password }),
        });

        const data = await response.json();

        if (response.ok) {
            alert(`Bienvenido ${data.usuario}`);
            window.location.href = "/dashboard"; // Redirigir a la página principal
        } else {
            loginError.classList.remove("hidden");
        }
    });
});
