// static/js/multiselect_preview.js

document.addEventListener('DOMContentLoaded', function () {
    const select = document.getElementById('fichas_disponiveis');
    // Se o elemento não existir na página, não faz nada.
    if (!select) {
        return;
    }

    const preview = document.getElementById('fichas_selecionadas_preview');
    const countSpan = document.getElementById('selected-count');

    select.addEventListener('change', function() {
        if (!preview || !countSpan) return;

        preview.innerHTML = '';
        const selectedOptions = Array.from(select.selectedOptions);
        countSpan.textContent = selectedOptions.length;
        
        selectedOptions.forEach(option => {
            const pill = document.createElement('span');
            pill.className = 'inline-block bg-gray-200 text-gray-800 text-xs font-medium mr-2 mb-2 px-2.5 py-1 rounded-full';
            pill.textContent = option.value;
            preview.appendChild(pill);
        });
    });

    // Dispara o evento 'change' uma vez no carregamento da página para refletir qualquer valor pré-selecionado.
    select.dispatchEvent(new Event('change'));
});