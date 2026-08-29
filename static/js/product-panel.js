// ===========================================
// PANEL — editor "Colores, talles y fotos".
// Agrupa en tarjetas por color, en el navegador,
// las filas de formset que Django YA renderizó
// con sus nombres/índices reales (nunca crea
// inputs nuevos — solo mueve/sincroniza los que
// existen). Evita el bug de TOTAL_FORMS que pagó
// el panel de referencia (Las Manolas). Las fotos
// viven adentro de cada tarjeta de color (con
// selector de archivo real), igual que en esa
// referencia.
// ===========================================

if (document.readyState === "loading") {

    document.addEventListener("DOMContentLoaded", initProductPanel);

} else {

    initProductPanel();

}

function initProductPanel() {

    const variantPool = document.getElementById("variant-pool");
    const colorContainer = document.getElementById("color-groups");
    const generalSlot = document.getElementById("general-photos-slot");
    const addColorBtn = document.getElementById("add-color-btn");
    const photoPool = document.getElementById("photo-pool");

    if (!variantPool || !colorContainer) return;

    const variantRows = Array.from(variantPool.querySelectorAll(".variant-row"));

    // Opciones de talle (id + nombre) — se leen UNA vez de cualquier
    // fila, todas comparten el mismo <select> de Size global.
    const sizeOptions = Array.from(variantRows[0].querySelector('[data-role="size-wrap"] select').options)
        .filter(opt => opt.value !== "")
        .map(opt => ({ value: opt.value, label: opt.textContent }));

    const variantGroups = new Map(); // nombre de color -> [rows]
    const unusedVariantRows = []; // filas en blanco, listas para usarse

    variantRows.forEach(row => {

        const colorInput = row.querySelector('[data-role="color-wrap"] input');
        const value = (colorInput.value || "").trim();

        if (!value) {

            unusedVariantRows.push(row);
            return;

        }

        if (!variantGroups.has(value)) variantGroups.set(value, []);
        variantGroups.get(value).push(row);

    });

    // Fotos: filas con imagen real ya guardada se agrupan por color
    // (o "general" si no tienen color); las filas libres (sin pk, sin
    // archivo todavía) quedan en una bolsa para usarse cuando el
    // usuario aprieta "+" en cualquier tarjeta.
    const photoData = { byColor: new Map(), general: [], unused: [] };

    if (photoPool) {

        Array.from(photoPool.querySelectorAll(".photo-row")).forEach(row => {

            const hasImage = !!row.querySelector('[data-role="preview"]');

            if (!hasImage) {

                row.querySelector('[data-role="color-wrap"] input').value = "";
                photoData.unused.push(row);
                return;

            }

            const value = (row.querySelector('[data-role="color-wrap"] input').value || "").trim();

            if (!value) {

                photoData.general.push(row);
                return;

            }

            if (!photoData.byColor.has(value)) photoData.byColor.set(value, []);
            photoData.byColor.get(value).push(row);

        });

    }

    variantGroups.forEach((rows, colorName) => renderVariantCard(colorContainer, colorName, rows, sizeOptions, unusedVariantRows, photoData));

    if (addColorBtn) {

        addColorBtn.addEventListener("click", () => {

            renderVariantCard(colorContainer, "", [], sizeOptions, unusedVariantRows, photoData, /* isNew */ true);

        });

    }

    if (generalSlot) renderGeneralPhotoCard(generalSlot, photoData);

}

function renderVariantCard(container, colorName, rows, sizeOptions, unused, photoData, isNew) {

    const card = document.createElement("div");
    card.className = "dash-card p-4";

    const header = document.createElement("div");
    header.className = "flex items-center gap-2 mb-3";

    const hexInput = document.createElement("input");
    hexInput.type = "color";
    const firstHex = rows[0]?.querySelector('[data-role="hex-wrap"] input');
    hexInput.value = (firstHex && firstHex.value) || "#000000";
    hexInput.className = "h-9 w-9 bg-transparent border border-white/15 rounded-full shrink-0";

    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.value = colorName;
    nameInput.placeholder = 'Nombre del color (ej: "Negro")';
    nameInput.className = "dash-input flex-1 font-semibold";

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "Quitar color";
    removeBtn.className = "text-xs text-red-400 hover:underline shrink-0 whitespace-nowrap";

    header.append(hexInput, nameInput, removeBtn);
    card.appendChild(header);

    const talleLabel = document.createElement("p");
    talleLabel.className = "text-xs uppercase tracking-wide text-white/40 mb-2";
    talleLabel.textContent = "Talles y stock";
    card.appendChild(talleLabel);

    const pillsWrap = document.createElement("div");
    pillsWrap.className = "flex flex-wrap items-center gap-2 mb-1";
    card.appendChild(pillsWrap);

    const addTalleSelect = document.createElement("select");
    addTalleSelect.className = "dash-input !w-24 !rounded-full !text-xs !py-1.5 !bg-white/5 mb-3";

    const cardRows = []; // filas de variante ya asignadas a esta tarjeta
    const removedRows = new Map(); // talle -> fila sacada de ESTA tarjeta, por si se vuelve a agregar (ver removePillBtn/addTalleSelect)
    const cardPhotoRows = []; // filas de foto ya asignadas a esta tarjeta

    const syncColorInto = (row) => {

        row.querySelector('[data-role="color-wrap"] input').value = nameInput.value;
        row.querySelector('[data-role="hex-wrap"] input').value = hexInput.value;

    };

    const refreshTalleOptions = () => {

        const usedSizeIds = cardRows.map(r => r.querySelector('[data-role="size-wrap"] select').value);
        addTalleSelect.innerHTML = '<option value="">+ Talle…</option>' +
            sizeOptions
                .filter(opt => !usedSizeIds.includes(opt.value))
                .map(opt => `<option value="${opt.value}">${escapeHtml(opt.label)}</option>`)
                .join("");

    };

    const addPill = (row) => {

        cardRows.push(row);
        syncColorInto(row);

        row.querySelector('[data-role="color-wrap"]').classList.add("hidden");
        row.querySelector('[data-role="hex-wrap"]').classList.add("hidden");
        row.querySelector('[data-role="sku-wrap"]').classList.add("hidden");

        const sizeSelect = row.querySelector('[data-role="size-wrap"] select');
        const stockInput = row.querySelector('[data-role="stock-wrap"] input');
        // Referencia directa guardada en la fila — stockInput se mueve
        // DENTRO del pill unas líneas más abajo, así que después de eso
        // ya no se lo puede encontrar buscando adentro de `row`. Se usa
        // para devolverlo a su lugar antes de sacar el pill (remover un
        // talle) o la tarjeta entera (quitar color) — ver esos handlers.
        row._stockInput = stockInput;

        const pill = document.createElement("span");
        pill.className = "inline-flex items-center gap-1 bg-white/8 rounded-full pl-1 pr-1.5 py-1 text-sm";

        const sizeLabel = document.createElement("span");
        sizeLabel.className = "inline-flex items-center justify-center w-6 h-6 rounded-full bg-white text-[#141417] text-xs font-bold shrink-0";
        sizeLabel.textContent = sizeSelect.options[sizeSelect.selectedIndex]?.textContent || "";

        stockInput.classList.add("!w-9", "!p-0", "!text-center", "!bg-white/10", "!border-0", "!rounded-full", "text-xs", "h-6");
        stockInput.placeholder = "0";

        const removePillBtn = document.createElement("button");
        removePillBtn.type = "button";
        removePillBtn.textContent = "×";
        removePillBtn.className = "w-5 h-5 rounded-full bg-white/10 hover:bg-red-500/70 text-white/70 hover:text-white leading-none text-xs shrink-0";

        pill.append(sizeLabel, stockInput, removePillBtn);
        pillsWrap.appendChild(pill);
        card.appendChild(row); // el <div class="variant-row"> real viaja acá (hidden fields)

        removePillBtn.addEventListener("click", () => {

            // OJO (bug real, reportado por el cliente 29/8): stockInput
            // vive DENTRO del pill (se movió ahí en el append de arriba)
            // — si acá se hace pill.remove() se lo lleva puesto, y esa
            // fila queda sin campo stock en el DOM. Django la sigue
            // validando igual (el DELETE no salta validación de campos)
            // y tira "este campo es obligatorio" aunque la fila se vaya
            // a borrar. Por eso primero se devuelve stockInput a su
            // wrapper original en `row` (que nunca se saca del DOM para
            // las filas con pk) antes de tirar el pill.
            row.querySelector('[data-role="stock-wrap"]').appendChild(row._stockInput);
            pill.remove();
            cardRows.splice(cardRows.indexOf(row), 1);

            if (row.dataset.hasPk === "1") {

                const del = row.querySelector('[data-role="delete-wrap"] input');
                if (del) del.checked = true;

                // Se guarda para poder "deshacer" (ver addTalleSelect
                // más abajo): si el mismo talle se vuelve a agregar en
                // esta misma tarjeta, hay que REUSAR esta fila en vez de
                // sacar una nueva del pool — dos filas con el mismo
                // Producto+Talle+Color (la vieja yéndose, la nueva
                // entrando) chocan contra la restricción de unicidad del
                // modelo (bug real, mismo reporte).
                const sizeId = row.querySelector('[data-role="size-wrap"] select').value;
                removedRows.set(sizeId, row);

            } else {

                row.querySelector('[data-role="color-wrap"] input').value = "";
                row.remove();
                unused.push(row);

            }

            refreshTalleOptions();

        });

    };

    rows.forEach(addPill);

    pillsWrap.after(addTalleSelect);
    refreshTalleOptions();

    addTalleSelect.addEventListener("change", () => {

        const sizeId = addTalleSelect.value;
        if (!sizeId) return;

        // Si este talle se acaba de sacar de ESTA tarjeta, reusar esa
        // misma fila (deshacer el DELETE) en vez de sacar una fila
        // nueva del pool — dos filas con el mismo Producto+Talle+Color
        // (la vieja con DELETE, la nueva sin guardar todavía) chocan
        // contra la restricción de unicidad del modelo (bug real,
        // reportado por el cliente 29/8).
        if (removedRows.has(sizeId)) {

            const row = removedRows.get(sizeId);
            removedRows.delete(sizeId);

            const del = row.querySelector('[data-role="delete-wrap"] input');
            if (del) del.checked = false;

            addPill(row);
            refreshTalleOptions();
            return;

        }

        const row = unused.shift();
        if (!row) {

            alert("No quedan filas libres — guardá el producto y volvé a entrar para tener más.");
            return;

        }

        row.querySelector('[data-role="size-wrap"] select').value = sizeId;
        row.querySelector('[data-role="stock-wrap"] input').value = 0;
        addPill(row);
        refreshTalleOptions();

    });

    nameInput.addEventListener("input", () => {

        cardRows.forEach(syncColorInto);
        cardPhotoRows.forEach(row => { row.querySelector('[data-role="color-wrap"] input').value = nameInput.value; });

    });
    hexInput.addEventListener("input", () => cardRows.forEach(syncColorInto));

    removeBtn.addEventListener("click", () => {

        // Mismo bug que el de un pill suelto (ver removePillBtn más
        // arriba), pero acá se lleva puesta la tarjeta ENTERA: card.
        // remove() de más abajo saca del DOM todo lo que esté adentro
        // de `card`, incluidas las filas con pk que addPill() metió ahí
        // — sin esto, esas filas (con su DELETE tildado) nunca llegan al
        // servidor, así que ni se borran ni se validan bien. Por eso acá
        // se las saca de la tarjeta ANTES de tirar la tarjeta, hacia el
        // pool (que sí sigue viviendo dentro del <form>).
        const pool = document.getElementById("variant-pool");

        cardRows.forEach(row => {

            if (row.dataset.hasPk === "1") {

                // El input de stock de esta fila vive DENTRO de su pill
                // (se movió ahí en addPill) — hay que devolverlo a su
                // wrapper en `row` antes de mover/tirar nada, mismo
                // motivo que en removePillBtn.
                if (row._stockInput) row.querySelector('[data-role="stock-wrap"]').appendChild(row._stockInput);

                const del = row.querySelector('[data-role="delete-wrap"] input');
                if (del) del.checked = true;
                row.classList.add("hidden");
                if (pool) pool.appendChild(row);

            } else {

                row.querySelector('[data-role="color-wrap"] input').value = "";

            }

        });

        cardPhotoRows.forEach(row => {

            if (row.dataset.hasPk === "1") {

                const del = row.querySelector('[data-role="delete-wrap"] input');
                if (del) del.checked = true;

            } else {

                row.querySelector('[data-role="color-wrap"] input').value = "";

            }

        });

        card.remove();

    });

    container.appendChild(card);

    const existingPhotoRows = (photoData && photoData.byColor.get(colorName)) || [];
    renderPhotoPicker(card, () => nameInput.value, existingPhotoRows, photoData, cardPhotoRows);

    if (isNew) nameInput.focus();

}

// ---------- FOTOS ----------
// Selector de archivo real por color (o "general"): muestra las fotos
// ya guardadas como miniaturas con una × para sacarlas, y un botón "+"
// que abre el explorador de archivos del sistema y arma la vista
// previa al toque (FileReader), sin subir nada todavía — el archivo
// viaja en el <input type="file"> real cuando se manda el form.

function renderGeneralPhotoCard(slot, photoData) {

    const card = document.createElement("div");
    card.className = "dash-card p-4 mb-2";

    const label = document.createElement("p");
    label.className = "text-xs uppercase tracking-wide text-white/40 mb-1";
    label.textContent = "Fotos generales";
    const sub = document.createElement("p");
    sub.className = "text-xs text-white/30 mb-2";
    sub.textContent = 'No dependen de un color puntual.';
    card.append(label, sub);

    slot.appendChild(card);

    renderPhotoPicker(card, () => "", photoData.general, photoData, []);

}

function renderPhotoPicker(container, getColorValue, existingRows, photoData, trackInto) {

    const wrap = document.createElement("div");
    wrap.className = "mt-3";

    const label = document.createElement("p");
    label.className = "text-xs uppercase tracking-wide text-white/40 mb-2";
    label.textContent = "Fotos";
    wrap.appendChild(label);

    const grid = document.createElement("div");
    grid.className = "flex flex-wrap gap-2";
    wrap.appendChild(grid);

    let addBtn;

    const addThumbForRow = (row, dataUrl) => {

        trackInto.push(row);

        const thumb = document.createElement("div");
        thumb.className = "relative w-14 h-14 rounded-xl overflow-hidden border border-white/15 bg-white/5 shrink-0";

        const img = document.createElement("img");
        img.className = "w-full h-full object-cover";
        const existingPreview = row.querySelector('[data-role="preview"]');
        img.src = dataUrl || (existingPreview ? existingPreview.src : "");
        thumb.appendChild(img);

        const rmBtn = document.createElement("button");
        rmBtn.type = "button";
        rmBtn.textContent = "×";
        rmBtn.className = "absolute top-0 right-0 w-5 h-5 bg-black/70 text-white text-xs leading-none rounded-bl-lg hover:bg-red-500";
        rmBtn.addEventListener("click", () => {

            if (row.dataset.hasPk === "1") {

                const del = row.querySelector('[data-role="delete-wrap"] input');
                if (del) del.checked = true;

            } else {

                const fileInput = row.querySelector('[data-role="image-wrap"] input');
                if (fileInput) fileInput.value = "";
                row.querySelector('[data-role="color-wrap"] input').value = "";

            }

            const idx = trackInto.indexOf(row);
            if (idx > -1) trackInto.splice(idx, 1);
            thumb.remove();

        });
        thumb.appendChild(rmBtn);

        if (addBtn) grid.insertBefore(thumb, addBtn); else grid.appendChild(thumb);

    };

    existingRows.forEach(row => addThumbForRow(row));

    addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.className = "w-14 h-14 rounded-xl border border-dashed border-white/25 flex items-center justify-center text-white/40 text-xl hover:border-white/50 hover:text-white/70 shrink-0";
    addBtn.textContent = "+";
    addBtn.addEventListener("click", () => {

        const row = photoData.unused.shift();
        if (!row) {

            alert("No quedan casilleros libres para fotos nuevas — guardá el producto y volvé a entrar para tener más.");
            return;

        }

        const fileInput = row.querySelector('[data-role="image-wrap"] input');
        const colorInput = row.querySelector('[data-role="color-wrap"] input');
        colorInput.value = getColorValue();

        fileInput.addEventListener("change", () => {

            if (!fileInput.files || !fileInput.files[0]) {

                photoData.unused.unshift(row);
                return;

            }

            const reader = new FileReader();
            reader.onload = () => addThumbForRow(row, reader.result);
            reader.readAsDataURL(fileInput.files[0]);

        }, { once: true });

        container.appendChild(row); // el <div class="photo-row"> real (con su <input type="file">) viaja acá
        fileInput.click();

    });
    grid.appendChild(addBtn);

    container.appendChild(wrap);

}

function escapeHtml(str) {

    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;

}
