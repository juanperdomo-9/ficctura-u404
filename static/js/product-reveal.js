// ===========================================
// RESERVAS — reveal tipo videojuego para las tarjetas de productos
// agotados. Pedido del usuario (11/9): "que no muestre la foto de
// una, como que mientras vaya apretando se vayan desbloqueando
// niveles, tipo videojuego". Cada click sobre la imagen sube un
// nivel (menos blur/grayscale, más opacidad); en el último nivel, el
// siguiente click ya navega a la ficha de reserva. El progreso se
// guarda en localStorage por producto — es un juego, no un dato real,
// así que si falla (privado/bloqueado) simplemente no persiste entre
// visitas y listo, no hace falta avisar de nada.
// ===========================================

const REVEAL_LEVELS = [
    { blur: 8, gray: 90, opacity: 0.4 },
    { blur: 5, gray: 65, opacity: 0.6 },
    { blur: 2, gray: 35, opacity: 0.8 },
    { blur: 0, gray: 0, opacity: 1 },
];
const REVEAL_MAX = REVEAL_LEVELS.length - 1;

function revealStorageKey(slug) {

    return `reveal-${slug}`;

}

function getRevealLevel(slug) {

    try {

        const raw = window.localStorage.getItem(revealStorageKey(slug));
        const level = raw === null ? 0 : parseInt(raw, 10);
        return Number.isFinite(level) ? Math.min(Math.max(level, 0), REVEAL_MAX) : 0;

    } catch (err) {

        return 0;

    }

}

function setRevealLevel(slug, level) {

    try {

        window.localStorage.setItem(revealStorageKey(slug), String(level));

    } catch (err) {

        // Sin persistencia — el juego sigue andando en memoria para
        // esta carga de página nomás.

    }

}

function paintRevealCard(card, level) {

    const img = card.querySelector("[data-reveal-img]");
    const hint = card.querySelector("[data-reveal-hint]");
    const lock = card.querySelector("[data-reveal-lock]");
    const config = REVEAL_LEVELS[level];

    if (img) {

        img.style.filter = `blur(${config.blur}px) grayscale(${config.gray}%)`;
        img.style.opacity = String(config.opacity);

    }

    card.dataset.revealLevel = String(level);

    if (lock) lock.textContent = level >= REVEAL_MAX ? "🔓" : "🔒";

    if (hint) {

        hint.textContent = level >= REVEAL_MAX
            ? "Reservar próxima entrega →"
            : `Tocá para desbloquear (Nivel ${level + 1}/${REVEAL_MAX + 1})`;

    }

}

function initRevealCards() {

    document.querySelectorAll("[data-reveal-card]").forEach(card => {

        const slug = card.dataset.revealSlug;
        const level = getRevealLevel(slug);

        paintRevealCard(card, level);

        card.addEventListener("click", () => {

            const currentLevel = parseInt(card.dataset.revealLevel || "0", 10);

            if (currentLevel >= REVEAL_MAX) {

                window.location.href = card.dataset.revealHref;
                return;

            }

            const nextLevel = currentLevel + 1;
            setRevealLevel(slug, nextLevel);
            paintRevealCard(card, nextLevel);

            card.classList.remove("reveal-pop");
            void card.offsetWidth; // fuerza reflow para poder re-disparar la animación
            card.classList.add("reveal-pop");

        });

    });

}

if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", initRevealCards);

} else {

    initRevealCards();

}
