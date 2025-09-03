document.addEventListener('DOMContentLoaded', () => {
    const containers = document.querySelectorAll('.shift-container');
    containers.forEach(container => {
        let lastChecked = null;
        container.addEventListener('click', event => {
            const label = event.target.closest('label');
            if (!label) return;
            const checkbox = label.querySelector('.shift-checkbox');
            if (!checkbox) return;

            if (event.shiftKey && lastChecked) {
                const checkboxes = Array.from(container.querySelectorAll('.shift-checkbox'));
                const start = checkboxes.indexOf(lastChecked);
                const end = checkboxes.indexOf(checkbox);

                checkboxes.slice(Math.min(start, end), Math.max(start, end) + 1).forEach(cb => {
                    if (cb.checked !== lastChecked.checked) {
                        cb.click(); // Dispara o evento @click do Alpine
                    }
                });
            }
            lastChecked = checkbox;
        });
    });
});