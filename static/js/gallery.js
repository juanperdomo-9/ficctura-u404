// ===========================================
// GALERÍA DE PRODUCTO — miniaturas (click cambia
// la imagen principal), flechas prev/next, y
// deslizar con el dedo en mobile (pedido del
// usuario, 30/8).
//
// Fotos "como en Mercado Libre" (16/10, pedido del
// cliente):
//   - Compu: al pasar el mouse la foto se agranda
//     siguiendo el cursor (lupa), para ver el detalle
//     del estampado sin hacer click.
//   - Click (o tocar en el celu) abre la foto a
//     pantalla completa. Ahí: flechas / deslizar para
//     pasar de foto, click o doble toque para hacer
//     zoom, y arrastrar para recorrerla con zoom.
//     Esc o la X cierran.
// Estilos del visor van inline (no clases de
// Tailwind) para no depender de que el CSS compilado
// incluya clases que solo aparecen en este JS.
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

    // Con una sola foto no hay miniaturas — igual tiene que andar la
    // lupa y la pantalla completa, así que la lista sale de la imagen
    // principal.
    const images = thumbs.length ? thumbs.map(t => t.getAttribute("data-src")) : [mainImg.src];

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

    // ---- Lupa al pasar el mouse (solo compu con mouse de verdad) ----
    const canHover = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

    mainWrap.style.cursor = "zoom-in";

    if (canHover) {

        mainImg.style.transition = "transform .2s ease-out";

        const resetZoom = () => {

            mainImg.style.transform = "";

        };

        mainWrap.addEventListener("mousemove", (e) => {

            if (e.target.closest("button")) {

                resetZoom();
                return;

            }

            const rect = mainWrap.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;

            mainImg.style.transformOrigin = `${x}% ${y}%`;
            mainImg.style.transform = "scale(2.2)";

        });

        mainWrap.addEventListener("mouseleave", resetZoom);

    }

    // ---- Click / toque → pantalla completa ----
    mainWrap.addEventListener("click", (e) => {

        if (e.target.closest("button")) return; // flechas de la galería

        openLightbox(images, current, (i) => goTo(i));

    });

    // Swipe mobile — solo horizontal (deja el scroll vertical normal
    // de la página en paz, ver touch-pan-y en el template). Un toque
    // sin mover el dedo cae al "click" de arriba y abre el visor.
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


// ===========================================
// VISOR A PANTALLA COMPLETA
// ===========================================

function openLightbox(images, startIndex, onChange) {

    let index = startIndex;
    let zoomed = false;

    const overlay = document.createElement("div");
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "Foto ampliada");
    overlay.style.cssText = "position:fixed;inset:0;z-index:300;background:rgba(0,0,0,.94);display:flex;align-items:center;justify-content:center;touch-action:none;";

    const stage = document.createElement("div");
    stage.style.cssText = "position:relative;width:100%;height:100%;overflow:hidden;display:flex;align-items:center;justify-content:center;";

    const img = document.createElement("img");
    img.alt = "";
    img.draggable = false;
    img.style.cssText = "max-width:100%;max-height:100%;object-fit:contain;user-select:none;cursor:zoom-in;transition:transform .25s ease-out;";

    stage.appendChild(img);
    overlay.appendChild(stage);

    const buttonCss = "position:absolute;display:flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:9999px;border:0;background:rgba(255,255,255,.12);color:#fff;cursor:pointer;";

    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.setAttribute("aria-label", "Cerrar");
    closeBtn.style.cssText = buttonCss + "top:16px;right:16px;font-size:20px;";
    closeBtn.textContent = "✕";
    overlay.appendChild(closeBtn);

    const counter = document.createElement("div");
    counter.style.cssText = "position:absolute;top:26px;left:20px;color:rgba(255,255,255,.75);font:600 13px/1 sans-serif;letter-spacing:.1em;";
    overlay.appendChild(counter);

    let prevBtn = null;
    let nextBtn = null;

    if (images.length > 1) {

        prevBtn = document.createElement("button");
        prevBtn.type = "button";
        prevBtn.setAttribute("aria-label", "Foto anterior");
        prevBtn.style.cssText = buttonCss + "left:16px;top:50%;transform:translateY(-50%);font-size:22px;";
        prevBtn.textContent = "‹";

        nextBtn = document.createElement("button");
        nextBtn.type = "button";
        nextBtn.setAttribute("aria-label", "Foto siguiente");
        nextBtn.style.cssText = buttonCss + "right:16px;top:50%;transform:translateY(-50%);font-size:22px;";
        nextBtn.textContent = "›";

        overlay.appendChild(prevBtn);
        overlay.appendChild(nextBtn);

    }

    const setZoom = (on, originX, originY) => {

        zoomed = on;

        if (on) {

            img.style.transformOrigin = `${originX}% ${originY}%`;
            img.style.transform = "scale(2.5)";
            img.style.cursor = "zoom-out";

        } else {

            img.style.transform = "";
            img.style.cursor = "zoom-in";

        }

    };

    const show = (i) => {

        index = (i + images.length) % images.length;
        img.src = images[index];
        counter.textContent = images.length > 1 ? `${index + 1} / ${images.length}` : "";
        setZoom(false);
        onChange(index);

    };

    const originFromEvent = (clientX, clientY) => {

        const rect = img.getBoundingClientRect();
        const x = Math.min(100, Math.max(0, ((clientX - rect.left) / rect.width) * 100));
        const y = Math.min(100, Math.max(0, ((clientY - rect.top) / rect.height) * 100));
        return [x, y];

    };

    // Click en la foto: zoom donde se hizo click / sacar zoom.
    img.addEventListener("click", (e) => {

        e.stopPropagation();

        if (zoomed) {

            setZoom(false);

        } else {

            const [x, y] = originFromEvent(e.clientX, e.clientY);
            setZoom(true, x, y);

        }

    });

    // Con zoom: mover el mouse / arrastrar el dedo recorre la foto.
    // Sin zoom: deslizar el dedo pasa de foto.
    let pointerStartX = null;
    let pointerStartY = null;
    let pointerMoved = false;

    stage.addEventListener("pointerdown", (e) => {

        pointerStartX = e.clientX;
        pointerStartY = e.clientY;
        pointerMoved = false;

    });

    stage.addEventListener("pointermove", (e) => {

        if (zoomed && (e.pointerType === "mouse" || pointerStartX !== null)) {

            const [x, y] = originFromEvent(e.clientX, e.clientY);
            img.style.transition = "none";
            img.style.transformOrigin = `${x}% ${y}%`;

        }

        if (pointerStartX !== null && Math.abs(e.clientX - pointerStartX) > 8) pointerMoved = true;

    });

    stage.addEventListener("pointerup", (e) => {

        img.style.transition = "transform .25s ease-out";

        if (pointerStartX !== null && !zoomed && e.pointerType !== "mouse") {

            const dx = e.clientX - pointerStartX;
            const dy = e.clientY - pointerStartY;

            if (images.length > 1 && Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) {

                show(dx < 0 ? index + 1 : index - 1);

            }

        }

        pointerStartX = null;
        pointerStartY = null;

    });

    // Click en el fondo negro (fuera de la foto) cierra — salvo que
    // venga de un arrastre.
    stage.addEventListener("click", (e) => {

        if (e.target === stage && !pointerMoved) close();

    });

    const onKey = (e) => {

        if (e.key === "Escape") close();
        if (e.key === "ArrowLeft" && images.length > 1) show(index - 1);
        if (e.key === "ArrowRight" && images.length > 1) show(index + 1);

    };

    const previousOverflow = document.body.style.overflow;

    function close() {

        document.removeEventListener("keydown", onKey);
        document.body.style.overflow = previousOverflow;
        overlay.remove();

    }

    closeBtn.addEventListener("click", close);
    prevBtn?.addEventListener("click", (e) => { e.stopPropagation(); show(index - 1); });
    nextBtn?.addEventListener("click", (e) => { e.stopPropagation(); show(index + 1); });
    document.addEventListener("keydown", onKey);

    document.body.style.overflow = "hidden";
    document.body.appendChild(overlay);
    show(index);
    closeBtn.focus();

}
