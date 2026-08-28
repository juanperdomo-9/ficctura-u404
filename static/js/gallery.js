// ===========================================
// GALERÍA DE PRODUCTO — click en una miniatura
// cambia la imagen principal.
// ===========================================

if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", initGallery);

} else {

    initGallery();

}

function initGallery() {

    const mainImg = document.getElementById("gallery-main-img");

    if (!mainImg) return;

    document.querySelectorAll("[data-gallery-thumb]").forEach(thumb => {

        thumb.addEventListener("click", () => {

            mainImg.src = thumb.getAttribute("data-src");

        });

    });

}
