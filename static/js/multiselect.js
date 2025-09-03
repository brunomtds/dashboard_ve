document.addEventListener('DOMContentLoaded', function () {
    const selectElement = document.getElementById('fichas_disponiveis');
    const previewArea = document.getElementById('fichas_selecionadas_preview');
    const countElement = document.getElementById('selected-count');

    // Se o elemento principal '<select>' não existir na página, o script não faz nada.
    if (!selectElement) {
        return;
    }

    // Função para atualizar a área de preview
    // Ela será chamada toda vez que a seleção no Tom Select mudar.
    const updatePreview = (selectedItems) => {
        // Garante que os elementos de preview existam antes de tentar atualizá-los
        if (!previewArea || !countElement) return;

        // 1. Limpa o preview antigo
        previewArea.innerHTML = '';
        
        // 2. Atualiza o contador
        countElement.textContent = selectedItems.length;

        // 3. Cria as "pílulas" (tags) para cada item selecionado
        selectedItems.forEach(value => {
            const pill = document.createElement('span');
            pill.className = 'inline-block bg-gray-200 text-gray-800 text-xs font-medium mr-2 mb-2 px-2.5 py-1 rounded-full';
            pill.textContent = value;
            previewArea.appendChild(pill);
        });
    };

    // Inicialização do Tom Select
    const tomSelectInstance = new TomSelect(selectElement, {
        plugins: ['remove_button'], // Adiciona um 'x' para remover itens facilmente
        placeholder: 'Digite ou selecione as fichas...',
        create: false, // Impede que o usuário crie novas fichas que não existem na lista
        maxItems: 300,  // Um limite generoso de seleções

        // Evento principal: é disparado toda vez que a seleção muda (itens são adicionados ou removidos)
        onChange: function(values) {
            // 'values' é um array com todos os números das fichas selecionadas.
            // Chamamos nossa função para atualizar a área de preview com esses valores.
            updatePreview(values);
        }
    });

    // Chamada inicial para garantir que o preview reflita qualquer valor
    // que possa já estar selecionado quando a página carregar.
    updatePreview(tomSelectInstance.getValue());
});