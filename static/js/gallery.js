// ===========================================
// GALERÍA DE PRODUCTO — miniaturas (click cambia
// la imagen principal), flechas prev/next, y
// deslizar con el dedo en mobile (pedido del
// usuario, 30/8).
// ===========================================

if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", initGallery);

} else {

    initGallery();

}

function initGallery() {

    const mainImg = document.getElementById("gallery-main-img");
    const mainWrap = document.getElementById("gallery-main");

    if (!mainImg || !mainWrap) return;

    const thumbs = Array.from(document.querySelectorAll("[data-gallery-thumb]"));
    const dots = Array.from(document.querySelectorAll("[data-gallery-dot]"));
    const images = thumbs.map(t => t.getAttribute("data-src"));

    if (!images.length) return; // solo 1 foto (o ninguna) — sin flechas/thumbs, nada que inicializar

    let current = 0;

    const setActiveDot = () => {

        dots.forEach((dot, i) => {

            dot.classList.toggle("bg-white/50", i !== current);
            dot.classList.toggle("bg-white", i === current);

        });

    };

    const goTo = (index) => {

        current = (index + images.length) % images.length; // wrap-around en los dos sentidos
        mainImg.src = images[current];
        setActiveDot();

    };

    thumbs.forEach((thumb, i) => {

        thumb.addEventListener("click", () => goTo(i));

    });

    document.getElementById("gallery-prev")?.addEventListener("click", () => goTo(current - 1));
    document.getElementById("gallery-next")?.addEventListener("click", () => goTo(current + 1));

    setActiveDot();

    // Swipe mobile — solo horizontal (deja el scroll vertical normal
    // de la página en paz, ver touch-pan-y en el template).
    let touchStartX = null;
    let touchStartY = null;

    mainWrap.addEventListener("touchstart", (e) => {

        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;

    }, { passive: true });

    mainWrap.addEventListener("touchend", (e) => {

        if (touchStartX === null) return;

        const dx = e.changedTouches[0].clientX - touchStartX;
        const dy = e.changedTouches[0].clientY - touchStartY;

        // Umbral chico para que no dispare con un toque simple, y que
        // el gesto sea claramente más horizontal que vertical (si no,
        // se pisa con el scroll de la página).
        if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) {

            goTo(dx < 0 ? current + 1 : current - 1);

        }

        touchStartX = null;
        touchStartY = null;

    }, { passive: true });

}
