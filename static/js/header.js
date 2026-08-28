// ===========================================
// ALTURA DINÁMICA DEL HEADER — el header fijo
// (banner de promo + banner cruzado de marca +
// navbar) puede tener 1, 2 o 3 franjas apiladas
// según qué esté activo. En vez de hardcodear un
// padding-top por página, medimos la altura real
// y la exponemos como --header-h para que el CSS
// la use (evita que el contenido quede tapado).
// ===========================================

if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", initHeaderHeight);

} else {

    initHeaderHeight();

}

function initHeaderHeight() {

    const header = document.getElementById("site-header");

    if (!header) return;

    const update = () => {

        document.documentElement.style.setProperty("--header-h", `${header.offsetHeight}px`);

    };

    update();

    window.addEventListener("resize", update);

    // Por si el banner de promo hace wrap a dos líneas en pantallas
    // chicas, o el navbar cambia de alto al abrir el menú mobile.
    if (window.ResizeObserver) {

        new ResizeObserver(update).observe(header);

    }

}
