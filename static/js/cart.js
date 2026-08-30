// ===========================================
// CARRITO — panel lateral con fetch, sin
// recargar página. Todo el estado vive en la
// sesión del server (catalog/cart.py); acá solo
// se pinta lo que la API devuelve.
// ===========================================

const CART_URLS = {
    state: "/catalogo/carrito/estado/",
    add: (id) => `/catalogo/carrito/sumar/${id}/`,
    subtract: (id) => `/catalogo/carrito/restar/${id}/`,
    remove: (id) => `/catalogo/carrito/sacar/${id}/`,
};

let cartPanelEl;
let cartScrimEl;

if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", initCart);

} else {

    initCart();

}

function initCart() {

    cartPanelEl = document.getElementById("cart-panel");
    cartScrimEl = document.getElementById("cart-scrim");

    document.querySelectorAll("[data-cart-open]").forEach(btn => {

        btn.addEventListener("click", (e) => {

            e.preventDefault();
            openCart();

        });

    });

    document.getElementById("cart-close")?.addEventListener("click", closeCart);

    // "Seguir comprando" (28/8): mismo cierre que la ✕ — este panel es
    // un overlay encima de la página en la que ya estabas, "seguir
    // comprando" es simplemente volver a verla.
    document.getElementById("cart-continue")?.addEventListener("click", closeCart);

    cartScrimEl?.addEventListener("click", closeCart);

    document.addEventListener("keydown", (e) => {

        if (e.key === "Escape") closeCart();

    });

    document.querySelectorAll("[data-add-to-cart-form]").forEach(form => {

        form.addEventListener("submit", handleAddToCart);

    });

    initVariantPickers();

    // Delegado: los botones +/-/quitar del panel se regeneran en cada
    // render, así que escuchamos en el contenedor fijo, no en cada botón.
    document.getElementById("cart-items")?.addEventListener("click", handleItemButtonClick);

    refreshCart();

}


// ===========================================
// PICKER DE TALLE + COLOR (por separado)
// Pedido del usuario (10/8): elegís talle y color
// como dos grupos independientes; si esa
// combinación puntual no existe o no tiene stock,
// se avisa "no disponible" — nunca se muestra el
// número de stock.
// ===========================================

function initVariantPickers() {

    document.querySelectorAll("[data-add-to-cart-form]").forEach(form => {

        let variants = [];

        try {

            variants = JSON.parse(form.dataset.variants || "[]");

        } catch (err) {

            variants = [];

        }

        const selection = { size: null, color: null };

        form.querySelectorAll("[data-variant-option]").forEach(btn => {

            btn.addEventListener("click", () => {

                const group = btn.dataset.group;

                // Deselecciona a los hermanos del mismo grupo (talle o color).
                form.querySelectorAll(`[data-variant-option][data-group="${group}"]`).forEach(sibling => {

                    const classes = (sibling.dataset.selectedClass || "").split(" ").filter(Boolean);
                    sibling.classList.remove(...classes);

                });

                const classes = (btn.dataset.selectedClass || "").split(" ").filter(Boolean);
                btn.classList.add(...classes);

                selection[group] = btn.dataset.value;

                updateVariantAvailability(form, variants, selection);

            });

        });

    });

}

function updateVariantAvailability(form, variants, selection) {

    const submitBtn = form.querySelector("[data-add-button]");
    const unavailableMsg = form.querySelector("[data-variant-unavailable]");
    const errorMsg = form.querySelector("[data-variant-error]");

    errorMsg?.classList.add("hidden");

    if (!selection.size || !selection.color) {

        if (submitBtn) submitBtn.disabled = true;
        unavailableMsg?.classList.add("hidden");
        delete form.dataset.selectedVariantId;
        return;

    }

    const match = variants.find(v => String(v.size_id) === String(selection.size) && v.color === selection.color);

    if (match && match.available) {

        if (submitBtn) submitBtn.disabled = false;
        unavailableMsg?.classList.add("hidden");
        form.dataset.selectedVariantId = match.id;

    } else {

        if (submitBtn) submitBtn.disabled = true;
        unavailableMsg?.classList.remove("hidden");
        delete form.dataset.selectedVariantId;

    }

}


// ===========================================
// ABRIR / CERRAR
// ===========================================

function openCart() {

    // El estado visual se fuerza también inline (no solo con la clase
    // "is-open") — en algunos navegadores la regla .cart-panel.is-open
    // no ganaba la cascada como debería contra .cart-panel sola. Inline
    // siempre gana, es la forma segura de garantizar que el panel se
    // vea (mismo criterio que el menú mobile, ver navbar.js).
    if (cartPanelEl) {

        cartPanelEl.classList.add("is-open");
        cartPanelEl.style.transform = "translateX(0)";

    }

    if (cartScrimEl) {

        cartScrimEl.classList.add("is-open");
        cartScrimEl.style.opacity = "1";
        cartScrimEl.style.pointerEvents = "auto";

    }

    document.body.classList.add("overflow-hidden");

}

function closeCart() {

    if (cartPanelEl) {

        cartPanelEl.classList.remove("is-open");
        cartPanelEl.style.transform = "translateX(100%)";

    }

    if (cartScrimEl) {

        cartScrimEl.classList.remove("is-open");
        cartScrimEl.style.opacity = "0";
        cartScrimEl.style.pointerEvents = "none";

    }

    document.body.classList.remove("overflow-hidden");

}


// ===========================================
// AGREGAR DESDE LA FICHA DE PRODUCTO
// ===========================================

function handleAddToCart(e) {

    e.preventDefault();

    const form = e.currentTarget;
    const variantId = form.dataset.selectedVariantId;

    if (!variantId) {

        form.querySelector("[data-variant-error]")?.classList.remove("hidden");
        return;

    }

    form.querySelector("[data-variant-error]")?.classList.add("hidden");

    cartAction(CART_URLS.add(variantId)).then((data) => {

        if (data && data.success) openCart();

    });

}


// ===========================================
// BOTONES DENTRO DEL PANEL
// ===========================================

function handleItemButtonClick(e) {

    const plus = e.target.closest("[data-cart-plus]");
    const minus = e.target.closest("[data-cart-minus]");
    const remove = e.target.closest("[data-cart-remove]");

    if (plus) return cartAction(CART_URLS.add(plus.dataset.variantId));
    if (minus) return cartAction(CART_URLS.subtract(minus.dataset.variantId));
    if (remove) return cartAction(CART_URLS.remove(remove.dataset.variantId));

}


// ===========================================
// LLAMADAS AL SERVER
// ===========================================

async function refreshCart() {

    const response = await fetch(CART_URLS.state);
    const data = await response.json();

    renderCart(data);

    return data;

}

async function cartAction(url) {

    const response = await fetch(url, {

        method: "POST",
        headers: { "X-CSRFToken": getCSRFToken() },

    });

    const data = await response.json();

    renderCart(data);

    return data;

}


// ===========================================
// RENDER
// ===========================================

function renderCart(data) {

    if (!data) return;

    document.querySelectorAll("[data-cart-count]").forEach(el => {

        el.textContent = data.count;

        el.classList.remove("cart-badge-pop");
        void el.offsetWidth; // fuerza reflow para poder re-disparar la animación
        el.classList.add("cart-badge-pop");

    });

    setText("cart-subtotal", formatPrice(data.subtotal));
    setText("cart-total", formatPrice(data.total));

    const discountRow = document.getElementById("cart-discount-row");

    if (discountRow) {

        if (Number(data.discount) > 0) {

            discountRow.classList.remove("hidden");
            setText("cart-discount", "− " + formatPrice(data.discount));

        } else {

            discountRow.classList.add("hidden");

        }

    }

    const packDiscountRow = document.getElementById("cart-pack-discount-row");

    if (packDiscountRow) {

        if (Number(data.pack_discount) > 0) {

            packDiscountRow.classList.remove("hidden");
            setText("cart-pack-discount", "− " + formatPrice(data.pack_discount));

        } else {

            packDiscountRow.classList.add("hidden");

        }

    }

    const freeShippingRow = document.getElementById("cart-free-shipping-row");
    if (freeShippingRow) freeShippingRow.classList.toggle("hidden", !data.free_shipping);

    const packBanner = document.getElementById("cart-pack-banner");

    if (packBanner) {

        if (data.active_pack_name) {

            packBanner.classList.remove("hidden");
            const pct = data.active_pack_percent ? ` — ${data.active_pack_percent}% off` : "";
            setText("cart-pack-name", `Pack ${data.active_pack_name} aplicado${pct}`);

        } else {

            packBanner.classList.add("hidden");

        }

    }

    renderPromotions(data.promotions || []);
    renderItems(data.items || []);

}

function renderPromotions(promotions) {

    const container = document.getElementById("cart-promotions");

    if (!container) return;

    if (promotions.length === 0) {

        container.innerHTML = "";
        return;

    }

    container.innerHTML = promotions.map(promo => `
        <div class="mb-4 px-4 py-3 rounded-sm border border-current/30 text-sm">
            🎁 <strong>${escapeHtml(promo.badge_text || promo.name)}</strong>
            aplicado — ${promo.free_units} unidad(es) con descuento
        </div>
    `).join("");

}

function renderItems(items) {

    const container = document.getElementById("cart-items");

    if (!container) return;

    if (items.length === 0) {

        container.innerHTML = `
            <p class="text-center opacity-60 font-sans text-sm uppercase tracking-[0.1em] mt-10">
                Todavía no agregaste nada.
            </p>
        `;

        return;

    }

    container.innerHTML = items.map(item => `
        <div class="flex gap-4">
            <div class="w-16 h-20 rounded-sm overflow-hidden bg-current/5 flex-shrink-0 flex items-center justify-center">
                ${item.image_url
            ? `<img src="${escapeHtml(item.image_url)}" class="w-full h-full object-cover" alt="">`
            : `<span class="text-[9px] uppercase opacity-50 text-center px-1">Sin imagen</span>`}
            </div>
            <div class="flex-1 min-w-0">
                <p class="font-sans text-sm font-semibold uppercase truncate">${escapeHtml(item.product_name)}</p>
                <p class="font-sans text-xs opacity-60 uppercase">${escapeHtml(item.size)} · ${escapeHtml(item.color)}</p>
                <div class="flex items-center gap-3 mt-2">
                    <button type="button" data-cart-minus data-variant-id="${item.variant_id}"
                            class="w-6 h-6 flex items-center justify-center border border-current/30 rounded-sm text-sm">−</button>
                    <span class="font-sans text-sm w-4 text-center">${item.quantity}</span>
                    <button type="button" data-cart-plus data-variant-id="${item.variant_id}"
                            class="w-6 h-6 flex items-center justify-center border border-current/30 rounded-sm text-sm">+</button>
                    <button type="button" data-cart-remove data-variant-id="${item.variant_id}"
                        class="ml-auto font-sans text-[11px] uppercase tracking-[0.1em] opacity-60 hover:opacity-100">
                        Quitar
                    </button>
                </div>
            </div>
            <div class="font-sans text-sm font-semibold whitespace-nowrap">${formatPrice(item.subtotal)}</div>
        </div>
    `).join("");

}


// ===========================================
// HELPERS
// ===========================================

function setText(id, text) {

    const el = document.getElementById(id);
    if (el) el.textContent = text;

}

function formatPrice(value) {

    const amount = Math.round(Number(value) || 0);
    return "$ " + amount.toLocaleString("es-AR");

}

function escapeHtml(value) {

    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;

}

function getCSRFToken() {

    return document.querySelector("[name=csrfmiddlewaretoken]")?.value;

}

window.openCart = openCart;
window.closeCart = closeCart;
window.refreshCart = refreshCart;
