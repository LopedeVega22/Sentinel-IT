// main.js — JS general del sitio

// Navbar: añadir sombra al hacer scroll
window.addEventListener('scroll', () => {
    const nav = document.getElementById('mainNav');
    if (nav) {
        nav.style.boxShadow = window.scrollY > 20
            ? '0 4px 24px rgba(0,0,0,0.4)'
            : 'none';
    }
});

// Animación de counters (página home)
function animarCounter(el) {
    const target = parseInt(el.getAttribute('data-target'), 10);
    const duration = 1800;
    const step = target / (duration / 16);
    let current = 0;

    const timer = setInterval(() => {
        current += step;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        el.textContent = Math.floor(current).toLocaleString('es-ES');
    }, 16);
}

// Activar counters cuando entran en pantalla
const counters = document.querySelectorAll('[data-target]');
if (counters.length > 0) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animarCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(c => observer.observe(c));
}
