// ===========================================
// CUENTA REGRESIVA — widget de urgencia opcional
// por producto (ver Product.urgency_type). La
// fecha límite la carga el cliente en el admin;
// esto solo la muestra tickeando en vivo.
// ===========================================

if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", initCountdowns);

} else {

    initCountdowns();

}

function initCountdowns() {

    document.querySelectorAll("[data-countdown-to]").forEach(el => {

        const target = new Date(el.getAttribute("data-countdown-to")).getTime();

        const tick = () => {

            const diff = target - Date.now();

            if (diff <= 0) {

                el.textContent = "¡Termina ya!";

                clearInterval(timer);

                return;

            }

            const hours = Math.floor(diff / 3600000);
            const minutes = Math.floor((diff % 3600000) / 60000);
            const seconds = Math.floor((diff % 60000) / 1000);

            const pad = (n) => String(n).padStart(2, "0");

            el.textContent = `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;

        };

        tick();

        const timer = setInterval(tick, 1000);

    });

}
