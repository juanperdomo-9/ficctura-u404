// ===========================================
// CALCULADORA DE TALLE — pedido del usuario
// (13/8): "calculadora de talles con IA".
// Resuelto como cuestionario inteligente, no una
// IA conectada a una API externa (decisión
// explícita: así funciona hoy, gratis, sin
// depender de ninguna cuenta).
//
// Dos métodos (30/8, pedido del cliente):
//   1. Pecho + cintura reales, contra la tabla de
//      medidas real de esta misma página — más
//      preciso, y el único que puede mostrar el
//      cartel de "carpa" (ver showResult()).
//   2. Altura + peso + contextura — el cuestionario
//      original (13/8), estimación indirecta para
//      quien no tiene cómo medirse ahora mismo.
// Si carga pecho Y cintura, gana el método 1 (más
// preciso). Si no, cae al método 2. Si no completó
// ninguno de los dos pares, se lo avisa.
// ===========================================

const SIZE_TABLE = [
    { name: "S", chest: 53, waist: 54 },
    { name: "M", chest: 55, waist: 56 },
    { name: "L", chest: 57, waist: 58 },
    { name: "XL", chest: 59, waist: 60 },
    { name: "XXL", chest: 61, waist: 62 },
];

const SIZE_SCALE = ["S", "M", "L", "XL", "XXL"];

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

            const chest = parseFloat(document.getElementById("size-calc-chest").value);
            const waist = parseFloat(document.getElementById("size-calc-waist").value);
            const height = parseFloat(document.getElementById("size-calc-height").value);
            const weight = parseFloat(document.getElementById("size-calc-weight").value);
            const build = form.querySelector('input[name="size-calc-build"]:checked')?.value || "mediana";

            const errorEl = document.getElementById("size-calc-error");

            if (chest && waist) {

                // Método 1 (más preciso): contra la tabla real.
                const size = recommendSizeByMeasurements(chest, waist);
                showResult(size, waist > chest);

            } else if (height && weight) {

                // Método 2 (de siempre): altura+peso+contextura.
                const size = recommendSizeByHeightWeight(height, weight, build);
                showResult(size, false);

            } else if (errorEl) {

                errorEl.textContent = "Completá altura y peso, o (mejor todavía) pecho y cintura.";
                errorEl.classList.remove("hidden");

            }

        });

    }

    initBackToPurchase();

}

function recommendSizeByMeasurements(chestCm, waistCm) {

    // El talle recomendado es el MÁS CHICO que entra cómodo en las dos
    // medidas a la vez (ni pecho ni cintura quedan ajustados) — si el
    // cuerpo tiene más cintura que pecho, la cintura suele ser la que
    // termina empujando a un talle más grande, tal cual explica el
    // texto de la calculadora más arriba en esta misma página.
    const fit = SIZE_TABLE.find(s => chestCm <= s.chest && waistCm <= s.waist);

    return fit ? fit.name : SIZE_TABLE[SIZE_TABLE.length - 1].name; // se pasó de la tabla entera -> se recomienda el XXL igual

}

function recommendSizeByHeightWeight(heightCm, weightKg, build) {

    // Punto de partida según altura (0=S, 1=M, 2=L, 3=XL, 4=XXL).
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

function showResult(size, showCarpaNote) {

    const result = document.getElementById("size-calc-result");
    const value = document.getElementById("size-calc-result-value");
    const carpaNote = document.getElementById("size-calc-carpa-note");
    const errorEl = document.getElementById("size-calc-error");

    if (!result || !value) return;

    if (errorEl) errorEl.classList.add("hidden");

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
