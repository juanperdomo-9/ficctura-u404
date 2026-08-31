// ===========================================
// CALCULADORA DE TALLE — pedido del usuario
// (13/8): "calculadora de talles con IA".
// Resuelto como cuestionario inteligente, no una
// IA conectada a una API externa (decisión
// explícita: así funciona hoy, gratis, sin
// depender de ninguna cuenta).
//
// Rehecha (30/8, pedido del cliente): en vez de
// estimar por altura/peso/contextura, pide pecho
// (por abajo de las axilas) y cintura (altura del
// ombligo) directo, y los compara contra la TABLA
// REAL de medidas — los mismos números que se ven
// en la tabla de talles.html (una sola fuente de
// verdad, si el taller manda una tabla nueva, se
// actualiza acá Y ahí).
// ===========================================

const SIZE_TABLE = [
    { name: "S", chest: 53, waist: 54 },
    { name: "M", chest: 55, waist: 56 },
    { name: "L", chest: 57, waist: 58 },
    { name: "XL", chest: 59, waist: 60 },
    { name: "XXL", chest: 61, waist: 62 },
];

if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", initSizeCalculator);

} else {

    initSizeCalculator();

}

function initSizeCalculator() {

    const form = document.getElementById("size-calc-form");

    if (form) {

        form.addEventListener("submit", (e) => {

            e.preventDefault();

            const chest = parseFloat(document.getElementById("size-calc-chest").value);
            const waist = parseFloat(document.getElementById("size-calc-waist").value);

            if (!chest || !waist) return;

            const size = recommendSize(chest, waist);
            // "Carpa": pedido del cliente — si la cintura da más que el
            // pecho (más panza que pecho), este talle recomendado por
            // pecho le va a quedar justo de cintura, pero es DE TODAS
            // FORMAS mejor que subir de talle entero en una remera
            // común (que quedaría como una carpa arriba).
            const showCarpaNote = waist > chest;

            showResult(size, showCarpaNote);

        });

    }

    initBackToPurchase();

}

function recommendSize(chestCm, waistCm) {

    // El talle recomendado es el MÁS CHICO que entra cómodo en las dos
    // medidas a la vez (ni pecho ni cintura quedan ajustados) — si el
    // cuerpo tiene más cintura que pecho, la cintura suele ser la que
    // termina empujando a un talle más grande, tal cual explica el
    // texto de la calculadora más arriba en esta misma página.
    const fit = SIZE_TABLE.find(s => chestCm <= s.chest && waistCm <= s.waist);

    return fit ? fit.name : SIZE_TABLE[SIZE_TABLE.length - 1].name; // pasa el talle más grande de la tabla -> se recomienda el XXL igual

}

function showResult(size, showCarpaNote) {

    const result = document.getElementById("size-calc-result");
    const value = document.getElementById("size-calc-result-value");
    const carpaNote = document.getElementById("size-calc-carpa-note");

    if (!result || !value) return;

    value.textContent = size;
    result.classList.remove("hidden");

    if (carpaNote) carpaNote.classList.toggle("hidden", !showCarpaNote);

    result.scrollIntoView({ behavior: "smooth", block: "center" });

}

// "Volver a mi compra" — pedido del usuario (28/8). Sin tracking de
// sesión del lado del servidor: si document.referrer es del mismo
// sitio y no es esta misma página de talles (evita el caso de haber
// entrado, recargado, o venir de otro link a talles), se muestra el
// botón apuntando ahí. Si no hay referrer útil (entraste directo, por
// WhatsApp, favoritos, etc.), el botón se queda oculto.
function initBackToPurchase() {

    const btn = document.getElementById("back-to-purchase");

    if (!btn) return;

    const ref = document.referrer;

    if (!ref) return;

    try {

        const refUrl = new URL(ref);

        if (refUrl.origin !== window.location.origin) return;
        if (refUrl.pathname === window.location.pathname) return;

        btn.href = ref;
        btn.classList.remove("hidden");

    } catch {

        // referrer raro/no parseable — se deja oculto, no rompe nada.

    }

}
