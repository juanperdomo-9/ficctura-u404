// ===========================================
// SCROLL TO TOP — botón flotante que aparece
// después de bajar un poco, sitewide.
// ===========================================

if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", initScrollTop);

} else {

    initScrollTop();

}

function initScrollTop() {

    const btn = document.getElementById("scroll-top-btn");

    if (!btn) return;

    const SHOW_AFTER_PX = 480;

    // Inline, no clase CSS combinada — mismo criterio que cart.js/
    // navbar.js: más robusto que depender de una regla ".btn.is-visible"
    // ganando la cascada.
    const toggle = () => {

        const visible = window.scrollY > SHOW_AFTER_PX;
        btn.style.opacity = visible ? "1" : "0";
        btn.style.pointerEvents = visible ? "auto" : "none";
        btn.style.transform = visible ? "translateY(0)" : "translateY(8px)";

    };

    window.addEventListener("scroll", toggle, { passive: true });
    toggle();

    btn.addEventListener("click", () => {

        window.scrollTo({ top: 0, behavior: "smooth" });

    });

}
