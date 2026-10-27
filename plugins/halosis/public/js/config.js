/**
 * Halaman konfigurasi HaloSIS: tampilkan nilai ambang keyakinan secara langsung saat slider digeser.
 */
(() => {
    const form = document.querySelector('[data-halosis-config]');
    if (!form) {
        return;
    }

    const slider = form.querySelector('[data-halosis-threshold]');
    const output = form.querySelector('[data-halosis-threshold-output]');
    if (slider && output) {
        slider.addEventListener('input', () => {
            output.textContent = `${slider.value}%`;
        });
    }
})();
