// ===========================================
// GATEWAY (FICCTURA × UNIVERSO 404)
// Split-screen de entrada — spotlight, reveal +
// decodificación de texto, botón magnético y
// glitch ambiental en ÉPICAS.
// ===========================================

// El script va al final de <body>, así que el DOM ya está listo cuando
// esto corre — "DOMContentLoaded" puede haber disparado antes de que el
// listener llegue a registrarse. Chequeamos readyState en vez de asumir.
if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", init);

} else {

    init();

}

function init() {

    revealPanels();

    trackSpotlight();

    magneticCta();

    ambientGlitch();

}


// ===========================================
// REVEAL ESCALONADO + DECODIFICACIÓN DE TEXTO
// ===========================================

function revealPanels() {

    document.querySelectorAll(".panel").forEach((panel, panelIndex) => {

        const items = panel.querySelectorAll(".reveal-up");

        items.forEach((item, itemIndex) => {

            const delay = panelIndex * 120 + itemIndex * 110;

            item.style.transitionDelay = `${delay}ms`;

            // Los títulos, además del fade, "decodifican" su texto letra
            // por letra — ver scrambleText().
            if (item.hasAttribute("data-scramble")) {

                const finalText = item.textContent.trim();

                item.textContent = finalText;

                setTimeout(() => scrambleText(item, finalText), delay + 80);

            }

        });

    });

    // Doble rAF para asegurar que el navegador ya pintó el estado
    // inicial (opacity:0) antes de agregar la clase que dispara la
    // transición — si no, a veces "salta" directo al final sin animar.
    requestAnimationFrame(() => {

        requestAnimationFrame(() => {

            document.querySelectorAll(".reveal-up").forEach(item => {

                item.classList.add("is-in");

            });

        });

    });

}


function scrambleText(el, finalText, duration = 750) {

    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#%&/_";
    const steps = 16;
    const stepTime = duration / steps;

    let frame = 0;

    const timer = setInterval(() => {

        frame++;

        const progress = frame / steps;

        el.textContent = finalText
            .split("")
            .map((char, i) => {

                if (char === " ") return " ";

                if (i / finalText.length < progress) return char;

                return chars[Math.floor(Math.random() * chars.length)];

            })
            .join("");

        if (frame >= steps) {

            clearInterval(timer);

            el.textContent = finalText;

        }

    }, stepTime);

}


// ===========================================
// SPOTLIGHT QUE SIGUE EL CURSOR
// ===========================================

function trackSpotlight() {

    document.querySelectorAll(".panel").forEach(panel => {

        const spot = panel.querySelector(".spotlight");

        if (!spot) return;

        panel.addEventListener("mousemove", (e) => {

            const rect = panel.getBoundingClientRect();

            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;

            panel.style.setProperty("--spot-x", `${x}%`);
            panel.style.setProperty("--spot-y", `${y}%`);

        });

    });

}


// ===========================================
// CTA MAGNÉTICO
// ===========================================

function magneticCta() {

    document.querySelectorAll(".magnetic").forEach(cta => {

        cta.addEventListener("mousemove", (e) => {

            const rect = cta.getBoundingClientRect();

            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;

            cta.style.transform = `translate(${x * 0.35}px, ${y * 0.35}px)`;

        });

        cta.addEventListener("mouseleave", () => {

            cta.style.transform = "";

        });

    });

}


// ===========================================
// GLITCH AMBIENTAL EN "ÉPICAS"
// Movimiento aunque nadie toque el mouse — tira
// al concepto de "señal rota" de Universo 404.
// ===========================================

function ambientGlitch() {

    const target = document.querySelector("[data-glitch]");

    if (!target) return;

    const trigger = () => {

        target.classList.add("glitching");

        setTimeout(() => target.classList.remove("glitching"), 300);

        const nextIn = 3500 + Math.random() * 4500;

        setTimeout(trigger, nextIn);

    };

    setTimeout(trigger, 2200);

}
