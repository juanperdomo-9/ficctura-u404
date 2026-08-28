// ===========================================
// ENFOQUE — animación de entrada al scrollear,
// para todo el sitio EXCEPTO el gateway (tiene
// la suya propia, no tocar: gateway.js). Pedido
// del usuario (13/8): "no reveal, algo nuevo".
//
// Efecto tipo "pull focus" de cámara: cada
// [data-fx-focus] arranca desenfocado/achicado
// (ver .js [data-fx-focus] en input.css) y se
// enfoca solo al entrar en pantalla. El estado
// final se fuerza por inline style (no por clase
// combinada) — más robusto contra la cascada,
// mismo criterio que cart.js/navbar.js.
// ===========================================

if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", initScrollFx);

} else {

    initScrollFx();

}

function initScrollFx() {

    const items = document.querySelectorAll("[data-fx-focus]");

    if (!items.length) return;

    // Sin soporte de IntersectionObserver (muy viejo/roto): mostrar
    // todo directo, mejor que dejarlo desenfocado para siempre.
    if (!("IntersectionObserver" in window)) {

        items.forEach(focusIn);
        return;

    }

    // Stagger: si varios items caen juntos en el mismo scroll (ej. una
    // grilla de productos), entran en cadena en vez de todos de golpe.
    // El delay se calcula por ORDEN DE APARICIÓN EN PANTALLA, no por
    // posición en el DOM, así que se acumula por lote de intersección.
    const observer = new IntersectionObserver((entries, obs) => {

        const visibleNow = entries.filter(e => e.isIntersecting);

        visibleNow.forEach((entry, i) => {

            const el = entry.target;
            const delay = Math.min(i * 90, 450);

            window.setTimeout(() => focusIn(el), delay);

            obs.unobserve(el);

        });

    }, {

        threshold: 0.15,
        rootMargin: "0px 0px -60px 0px",

    });

    items.forEach(item => observer.observe(item));

}

function focusIn(el) {

    el.style.opacity = "1";
    el.style.filter = "blur(0px)";
    el.style.transform = "scale(1)";

}
