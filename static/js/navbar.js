// ===========================================
// NAVBAR — menú mobile + sombra al scrollear
// Compartido entre las dos marcas (U404/Ficctura),
// se engancha por atributos data-* así que no le
// importa de qué tienda viene.
// ===========================================

if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", initNavbar);

} else {

    initNavbar();

}

function initNavbar() {

    toggleMobileMenus();

    shadowOnScroll();

}


// ===========================================
// MENÚ MOBILE
// ===========================================

function toggleMobileMenus() {

    document.querySelectorAll("[data-menu-toggle]").forEach(btn => {

        const menu = document.getElementById(btn.getAttribute("data-menu-toggle"));

        if (!menu) return;

        // El estado visual (abierto/cerrado) se fuerza también inline,
        // no solo con la clase "is-open" — en algunos navegadores esa
        // regla (.mobile-menu.is-open, más específica que .mobile-menu)
        // no ganaba la cascada como debería. Inline siempre gana, así
        // que es la forma segura de garantizar que el menú se vea.
        const setOpen = (open) => {

            menu.classList.toggle("is-open", open);
            menu.style.maxHeight = open ? menu.scrollHeight + "px" : "0px";
            menu.style.opacity = open ? "1" : "0";

            btn.setAttribute("aria-expanded", open ? "true" : "false");

            document.body.classList.toggle("overflow-hidden", open);

        };

        const close = () => setOpen(false);

        btn.addEventListener("click", () => {

            setOpen(!menu.classList.contains("is-open"));

        });

        // Cerrar al tocar un link del menú.
        menu.querySelectorAll("a").forEach(link => {

            link.addEventListener("click", close);

        });

    });

}


// ===========================================
// SOMBRA/FONDO MÁS OPACO AL SCROLLEAR
// ===========================================

function shadowOnScroll() {

    const navbars = document.querySelectorAll("[data-navbar]");

    if (!navbars.length) return;

    const onScroll = () => {

        navbars.forEach(nav => {

            nav.classList.toggle("is-scrolled", window.scrollY > 8);

        });

    };

    onScroll();

    window.addEventListener("scroll", onScroll, { passive: true });

}
