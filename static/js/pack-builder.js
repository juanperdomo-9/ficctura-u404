// ===========================================
// ARMAR PACK — pedido del usuario (29/8): a medida
// que elige cada remera, sumar el precio de lista,
// tacharlo, y mostrar el precio con el % del pack ya
// aplicado. Las remeras "gratis" (bonus_basica del
// pack, ej. la básica de regalo del CEO) no suman al
// precio de lista — quedan afuera de la cuenta.
//
// Rediseño (14/9, pedido del cliente): "tiene que ser
// bien bien bien obvio, intuitivo" — se suma acá el
// contador de progreso, la marca visual de "lista" en
// cada remera elegida, y el botón deshabilitado con el
// texto de cuántas faltan hasta completar el pack.
// ===========================================

if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", initPackBuilder);

} else {

    initPackBuilder();

}

function initPackBuilder() {

    const selects = Array.from(document.querySelectorAll(".pack-slot"));
    const originalEl = document.getElementById("pack-price-original");
    const finalEl = document.getElementById("pack-price-final");
    const progressEl = document.getElementById("pack-progress");
    const submitBtn = document.getElementById("pack-submit");
    const form = document.getElementById("pack-form");

    if (!selects.length || !finalEl) return;

    const discountPercent = window.PACK_DISCOUNT_PERCENT || 0;

    // Colores por marca vía inline style (no clases Tailwind en
    // competencia) — mismo criterio que cart.js::openCart(): con dos
    // clases de Tailwind pisando la misma propiedad, gana la que
    // aparezca último en el CSS compilado, no la que se agrega último
    // acá — inline siempre gana, es la forma segura.
    const brand = (form && form.dataset.brand) || "u404";
    const accentColor = brand === "u404" ? "var(--color-u404-accent)" : "var(--color-ficctura-accent)";
    const onAccentColor = brand === "u404" ? "var(--color-u404-bg)" : "#fff";

    const formatPesos = (value) => "$ " + Math.round(value).toLocaleString("es-AR");

    const recalc = () => {

        let total = 0;
        let chosen = 0;

        selects.forEach(select => {

            const isChosen = select.value !== "";
            if (isChosen) chosen += 1;

            // Marca visual de "lista" en la tarjeta de esa remera — el
            // número pasa de círculo vacío a check, y el borde toma el
            // color de acento (ver pack_detail.html::pack-slot-card).
            const card = select.closest("[data-slot-card]");
            const numEl = card ? card.querySelector("[data-slot-num]") : null;

            if (card) card.style.borderColor = isChosen ? accentColor : "";

            if (numEl) {

                if (isChosen) {

                    numEl.textContent = "✓";
                    numEl.style.borderColor = accentColor;
                    numEl.style.backgroundColor = accentColor;
                    numEl.style.color = onAccentColor;

                } else {

                    numEl.textContent = String(selects.indexOf(select) + 1);
                    numEl.style.borderColor = "";
                    numEl.style.backgroundColor = "";
                    numEl.style.color = "";

                }

            }

            if (select.dataset.free === "true") return;

            const opt = select.options[select.selectedIndex];
            const price = opt ? parseFloat(opt.dataset.price || "0") : 0;
            total += price;

        });

        if (originalEl) originalEl.textContent = formatPesos(total);

        const final = total - (total * discountPercent / 100);
        finalEl.textContent = formatPesos(final);

        const remaining = selects.length - chosen;

        if (progressEl) progressEl.textContent = `${chosen} / ${selects.length}`;

        if (submitBtn) {

            submitBtn.disabled = remaining > 0;
            submitBtn.textContent = remaining > 0
                ? `Elegí ${remaining} más para continuar`
                : "Agregar pack al carrito";

        }

    };

    selects.forEach(select => select.addEventListener("change", recalc));
    recalc();

}
