document.addEventListener("DOMContentLoaded", () => {
    // Ждём загрузки HTML, чтобы кнопка уже существовала в DOM.
    const backToTop = document.getElementById("back-to-top");

    if (!backToTop) {
        return;
    }

    const updateVisibility = () => {
        // Кнопка нужна только после прокрутки страницы вниз.
        backToTop.classList.toggle("is-visible", window.scrollY > 240);
    };

    backToTop.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
    });
    window.addEventListener("scroll", updateVisibility, { passive: true });
    updateVisibility();
});
