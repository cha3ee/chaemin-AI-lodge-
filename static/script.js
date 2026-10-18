document.addEventListener("DOMContentLoaded", function () {
    // 1. Language Toggle Logic
    const langBtn = document.getElementById("lang-toggle");
    let currentLang = localStorage.getItem("preferred_lang") || "en";

    function applyLanguage(lang) {
        document.querySelectorAll("[data-kr][data-en]").forEach(el => {
            el.textContent = el.getAttribute(`data-${lang}`);
        });
        localStorage.setItem("preferred_lang", lang);
    }

    if (langBtn) {
        applyLanguage(currentLang);
        langBtn.addEventListener("click", function () {
            currentLang = currentLang === "en" ? "kr" : "en";
            applyLanguage(currentLang);
        });
    }

    // 2. Delete Pinned Notes Logic
    document.querySelectorAll(".delete-note-btn").forEach(btn => {
        btn.addEventListener("click", function (e) {
            e.stopPropagation();
            const noteCard = this.closest(".clipped-note-card");
            const itemId = noteCard.getAttribute("data-item-id");

            if (confirm("Delete this pinned note?")) {
                fetch(`/delete_board_item/${itemId}`, { method: "POST" })
                    .then(res => res.json())
                    .then(data => {
                        if (data.status === "success") {
                            noteCard.remove();
                        }
                    });
            }
        });
    });

    // 3. Interactive Drag, Rotate, Resize, & Delete for AI Stickers
    document.querySelectorAll(".transformable-item").forEach(item => {
        let isDragging = false;
        let isRotating = false;
        let isScaling = false;

        let currentX = parseFloat(item.dataset.x) || 0;
        let currentY = parseFloat(item.dataset.y) || 0;
        let currentRotation = parseFloat(item.dataset.rotation) || 0;
        let currentScale = parseFloat(item.dataset.scale) || 1;

        let startX = 0, startY = 0;

        // Apply initial positions from data attributes
        updateTransform();

        const dragHandle = item.querySelector(".drag-handle") || item;
        const rotateHandle = item.querySelector(".rotate-handle");
        const scaleHandle = item.querySelector(".scale-handle");
        const deleteHandle = item.querySelector(".delete-handle");

        // Delete Handler
        if (deleteHandle) {
            deleteHandle.addEventListener("click", e => {
                e.stopPropagation();
                const itemId = item.getAttribute("data-item-id");
                if (confirm("Delete this sticker?")) {
                    fetch(`/delete_board_item/${itemId}`, { method: "POST" })
                        .then(res => res.json())
                        .then(data => {
                            if (data.status === "success") {
                                item.remove();
                            }
                        });
                }
            });
        }

        // Drag Handler
        dragHandle.addEventListener("mousedown", e => {
            isDragging = true;
            startX = e.clientX - currentX;
            startY = e.clientY - currentY;
            item.style.cursor = "grabbing";
        });

        // Rotate Handler
        if (rotateHandle) {
            rotateHandle.addEventListener("mousedown", e => {
                e.stopPropagation();
                isRotating = true;
            });
        }

        // Scale Handler
        if (scaleHandle) {
            scaleHandle.addEventListener("mousedown", e => {
                e.stopPropagation();
                isScaling = true;
                startX = e.clientX;
            });
        }

        window.addEventListener("mousemove", e => {
            if (isDragging) {
                currentX = e.clientX - startX;
                currentY = e.clientY - startY;
                updateTransform();
            } else if (isRotating) {
                const rect = item.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                const radians = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                currentRotation = radians * (180 / Math.PI);
                updateTransform();
            } else if (isScaling) {
                const diff = e.clientX - startX;
                currentScale = Math.max(0.4, Math.min(2.5, currentScale + diff * 0.005));
                startX = e.clientX;
                updateTransform();
            }
        });

        window.addEventListener("mouseup", () => {
            if (isDragging || isRotating || isScaling) {
                isDragging = false;
                isRotating = false;
                isScaling = false;
                item.style.cursor = "grab";
                saveTransformToServer(item.getAttribute("data-item-id"), currentX, currentY, currentRotation, currentScale);
            }
        });

        function updateTransform() {
            item.style.transform = `translate(${currentX}px, ${currentY}px) rotate(${currentRotation}deg) scale(${currentScale})`;
        }

        function saveTransformToServer(itemId, x, y, rotation, scale) {
            fetch(`/update_board_item_transform/${itemId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ x: x, y: y, rotation: rotation, scale: scale })
            }).catch(err => console.error("Failed to save transform state:", err));
        }
    });
});