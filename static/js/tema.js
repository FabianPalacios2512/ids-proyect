document.addEventListener('DOMContentLoaded', () => {
    const switchBtn = document.getElementById('temaSwitch');
    const body = document.body;
  
    // Verificamos si ya hay un tema guardado en localStorage
    const temaGuardado = localStorage.getItem('tema');
    if (temaGuardado === 'oscuro') {
      activarTemaOscuro();
    }
  
    switchBtn.addEventListener('click', () => {
      if (body.classList.contains('dark')) {
        desactivarTemaOscuro();
      } else {
        activarTemaOscuro();
      }
    });
  
    function activarTemaOscuro() {
      body.classList.add('dark');
      body.classList.remove('bg-gray-50', 'text-gray-900');
      body.classList.add('bg-gray-900', 'text-gray-100');
      switchBtn.innerHTML = '☀️ Tema Claro';
      switchBtn.classList.remove('bg-gray-800');
      switchBtn.classList.add('bg-yellow-400', 'text-black');
      localStorage.setItem('tema', 'oscuro');
    }
  
    function desactivarTemaOscuro() {
      body.classList.remove('dark');
      body.classList.remove('bg-gray-900', 'text-gray-100');
      body.classList.add('bg-gray-50', 'text-gray-900');
      switchBtn.innerHTML = '🌙 Tema Oscuro';
      switchBtn.classList.remove('bg-yellow-400', 'text-black');
      switchBtn.classList.add('bg-gray-800', 'text-white');
      localStorage.setItem('tema', 'claro');
    }
  });
  