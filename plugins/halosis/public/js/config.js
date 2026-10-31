/**
 * Halaman konfigurasi HaloSIS: tampilkan nilai kedua ambang keyakinan secara langsung saat slider digeser.
 */
(() => {
    const form = document.querySelector('[data-halosis-config]');
    if (!form) {
        return;
    }

    form.querySelectorAll('[data-halosis-threshold]').forEach((slider) => {
        const output = form.querySelector(`output[for="${slider.id}"]`);
        if (output) {
            slider.addEventListener('input', () => {
                output.textContent = `${slider.value}%`;
            });
        }
    });
})();
