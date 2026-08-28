// ===========================================
// CHECKOUT — muestra/oculta los campos de
// tarjeta según el método de pago elegido, y si
// es tarjeta, tokeniza con el SDK de Payway
// (Decidir) ANTES de mandar el formulario. El
// número de tarjeta nunca llega a nuestro
// servidor, solo el token.
// ===========================================

if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", initCheckout);

} else {

    initCheckout();

}

function initCheckout() {

    const form = document.getElementById("checkout-form");

    if (!form) return;

    const cardFields = document.getElementById("card-fields");
    const paymentOptions = document.querySelectorAll("[data-payment-option]");

    paymentOptions.forEach(input => {

        input.addEventListener("change", () => {

            if (cardFields) {

                cardFields.classList.toggle("hidden", input.value !== "tarjeta" || !input.checked);

            }

            if (input.checked) updateCheckoutTotal(input.dataset.discountPercent);

        });

    });

    form.addEventListener("submit", handleCheckoutSubmit);

}

// Recalcula y muestra el total al elegir transferencia/efectivo (con
// descuento) o tarjeta/nada (sin descuento) — sin recargar la página.
// El % sale del admin (PaymentDiscount, ver catalog/cart.py), no está
// hardcodeado acá.
function updateCheckoutTotal(discountPercent) {

    const totalEl = document.getElementById("checkout-total");
    const noteEl = document.getElementById("checkout-payment-discount-note");

    if (!totalEl) return;

    const baseTotal = parseFloat(totalEl.dataset.baseTotal || "0");
    const percent = parseFloat(discountPercent || "0");

    const discountAmount = baseTotal * percent / 100;
    const finalTotal = Math.round(baseTotal - discountAmount);

    totalEl.textContent = formatPesos(finalTotal);

    if (noteEl) {

        if (percent > 0) {

            noteEl.textContent = `Incluye ${percent}% off por forma de pago (− ${formatPesos(Math.round(discountAmount))})`;
            noteEl.classList.remove("hidden");

        } else {

            noteEl.classList.add("hidden");

        }

    }

}

function formatPesos(amount) {

    return "$ " + Math.round(amount).toLocaleString("es-AR");

}

function handleCheckoutSubmit(e) {

    const form = e.currentTarget;

    const paywayConfigured = form.dataset.paywayConfigured === "true";
    const selectedPayment = form.querySelector('input[name="payment_preference"]:checked');

    if (!paywayConfigured || !selectedPayment || selectedPayment.value !== "tarjeta") {

        // Transferencia / efectivo (o Payway ni siquiera está
        // configurado): envío normal, sin tokenizar nada.
        return;

    }

    // A partir de acá, tarjeta con Payway configurado: hay que
    // tokenizar antes de que el formulario viaje al server.
    e.preventDefault();

    const errorEl = form.querySelector("[data-payway-error]");
    errorEl?.classList.add("hidden");

    if (typeof Decidir === "undefined") {

        showPaywayError(errorEl, "No se pudo cargar el sistema de pago. Probá de nuevo en un momento.");
        return;

    }

    const submitBtn = document.getElementById("checkout-submit");
    if (submitBtn) submitBtn.disabled = true;

    const decidir = new Decidir(form.dataset.paywayApiBaseUrl);
    decidir.setPublishableKey(form.dataset.paywayPublicKey);

    decidir.createToken(form, (status, response) => {

        if (submitBtn) submitBtn.disabled = false;

        if (status !== 200 && status !== 201) {

            showPaywayError(errorEl, "No pudimos validar la tarjeta. Revisá los datos e intentá de nuevo.");
            return;

        }

        const tokenInput = form.querySelector('input[name="payway_token"]');
        if (tokenInput) tokenInput.value = response.token;

        // form.submit() nativo no vuelve a disparar el evento "submit"
        // (a diferencia de un click en el botón), así que esto no
        // reentra en este mismo handler.
        HTMLFormElement.prototype.submit.call(form);

    });

}

function showPaywayError(errorEl, message) {

    if (!errorEl) return;

    errorEl.textContent = message;
    errorEl.classList.remove("hidden");

}
