// ===========================================
// CALCULADORA DE TALLE — pedido del usuario
// (13/8): "calculadora de talles con IA".
// Resuelto como cuestionario inteligente, no una
// IA conectada a una API externa (decisión
// explícita: así funciona hoy, gratis, sin
// depender de ninguna cuenta).
//
// Lógica: talle base según altura, ajustado por
// IMC (altura+peso) y por la contextura que
// eligió la persona. Es una heurística general de
// remeras unisex (S/M/L/XL) — un punto de partida
// razonable mientras no exista la tabla de
// medidas real del taller (ver talles.html).
// ===========================================

const SIZE_SCALE = ["S", "M", "L", "XL"];

const BUILD_ADJUST = {
    delgada: -0.5,
    mediana: 0,
    robusta: 0.5,
};

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

            const height = parseFloat(document.getElementById("size-calc-height").value);
            const weight = parseFloat(document.getElementById("size-calc-weight").value);
            const build = form.querySelector('input[name="size-calc-build"]:checked')?.value || "mediana";

            if (!height || !weight) return;

            const size = recommendSize(height, weight, build);
            showResult(size);

        });

    }

    initBackToPurchase();

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

function recommendSize(heightCm, weightKg, build) {

    // Punto de partida según altura (0=S, 1=M, 2=L, 3=XL).
    let index;

    if (heightCm < 165) index = 0;
    else if (heightCm < 175) index = 1;
    else if (heightCm < 183) index = 2;
    else index = 3;

    // Ajuste por IMC — complexión más allá de lo que dice la altura sola.
    const heightM = heightCm / 100;
    const bmi = weightKg / (heightM * heightM);

    let bmiAdjust = 0;

    if (bmi < 19) bmiAdjust = -0.7;
    else if (bmi < 24) bmiAdjust = 0;
    else if (bmi < 27) bmiAdjust = 0.4;
    else if (bmi < 30) bmiAdjust = 0.8;
    else bmiAdjust = 1.2;

    const buildAdjust = BUILD_ADJUST[build] ?? 0;

    let finalIndex = Math.round(index + bmiAdjust + buildAdjust);
    finalIndex = Math.max(0, Math.min(SIZE_SCALE.length - 1, finalIndex));

    return SIZE_SCALE[finalIndex];

}

function showResult(size) {

    const result = document.getElementById("size-calc-result");
    const value = document.getElementById("size-calc-result-value");

    if (!result || !value) return;

    value.textContent = size;
    result.classList.remove("hidden");
    result.scrollIntoView({ behavior: "smooth", block: "center" });

}
