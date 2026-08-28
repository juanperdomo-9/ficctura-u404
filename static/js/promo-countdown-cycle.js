// ===========================================
// CONTADOR CÍCLICO DEL BANNER "OFERTA FLASH"
// Pedido del usuario (13/8): cuenta atrás de 10
// minutos, corta, y se reinicia solo a los 5.
// No apunta a una fecha real cargada en el admin
// (eso es BrandPromotion/PaymentDiscount, con su
// propio [data-countdown-to]) — este es un ciclo
// puramente visual que se repite solo.
//
// Sincronizado por reloj (Date.now() % ciclo), no
// por cuándo cada visitante entró — así todos ven
// el mismo número en simultáneo, en vez de que a
// cada uno le arranque su propia cuenta al cargar.
// ===========================================

(function () {

    const COUNTDOWN_MS = 10 * 60 * 1000;
    const PAUSE_MS = 5 * 60 * 1000;
    const CYCLE_MS = COUNTDOWN_MS + PAUSE_MS;

    function init() {

        const badges = document.querySelectorAll("[data-promo-cycle]");

        if (!badges.length) return;

        tick();
        setInterval(tick, 1000);

        function tick() {

            const phase = Date.now() % CYCLE_MS;
            const inCountdown = phase < COUNTDOWN_MS;

            badges.forEach(el => {

                el.classList.toggle("hidden", !inCountdown);
                el.classList.toggle("flex", inCountdown);

                if (!inCountdown) return;

                const remaining = COUNTDOWN_MS - phase;
                const totalSeconds = Math.ceil(remaining / 1000);
                const m = Math.floor(totalSeconds / 60);
                const s = totalSeconds % 60;

                el.textContent = `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;

            });

        }

    }

    if (document.readyState === "loading") {

        document.addEventListener("DOMContentLoaded", init);

    } else {

        init();

    }

})();
