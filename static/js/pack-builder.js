// ===========================================
// ARMAR PACK — pedido del usuario (29/8): a medida
// que elige cada remera, sumar el precio de lista,
// tacharlo, y mostrar el precio con el % del pack ya
// aplicado. Las remeras "gratis" (bonus_basica del
// pack, ej. la básica de regalo del CEO) no suman al
// precio de lista — quedan afuera de la cuenta.
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

    if (!selects.length || !finalEl) return;

    const discountPercent = window.PACK_DISCOUNT_PERCENT || 0;

    const formatPesos = (value) => "$ " + Math.round(value).toLocaleString("es-AR");

    const recalc = () => {

        let total = 0;

        selects.forEach(select => {

            if (select.dataset.free === "true") return;

            const opt = select.options[select.selectedIndex];
            const price = opt ? parseFloat(opt.dataset.price || "0") : 0;
            total += price;

        });

        if (originalEl) originalEl.textContent = formatPesos(total);

        const final = total - (total * discountPercent / 100);
        finalEl.textContent = formatPesos(final);

    };

    selects.forEach(select => select.addEventListener("change", recalc));
    recalc();

}
