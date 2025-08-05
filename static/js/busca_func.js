document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('filtroForm');
    const searchInput = document.getElementById('q');
    const departamentoSelect = document.getElementById('departamento');
    const soChefiaCheckbox = document.getElementById('so_chefias');
    const responsabilidadeCheckboxes = document.querySelectorAll('.responsabilidade-checkbox-input');
    
    let searchTimeout;
    let autocompleteContainer;
    let isAutocompleteVisible = false;

    // Cria o container do autocomplete
    function createAutocompleteContainer() {
        if (autocompleteContainer) return;
        
        autocompleteContainer = document.createElement('div');
        autocompleteContainer.id = 'autocomplete-container';
        autocompleteContainer.className = 'absolute z-50 w-full bg-white border border-gray-300 rounded-md shadow-lg mt-1 max-h-60 overflow-y-auto hidden';
        
        // Insere o container após o input
        searchInput.parentNode.style.position = 'relative';
        searchInput.parentNode.appendChild(autocompleteContainer);
    }

    // Busca funcionários para autocomplete usando a mesma view
    function fetchFuncionarios(query = '') {
        const url = new URL(form.action, window.location.origin);
        url.searchParams.append('autocomplete', '1'); // Parâmetro que indica autocomplete
        
        if (query) {
            url.searchParams.append('q', query);
        }

        fetch(url)
            .then(response => response.json())
            .then(data => {
                displayAutocomplete(data.funcionarios);
            })
            .catch(error => {
                console.error('Erro ao buscar funcionários:', error);
            });
    }

    // Exibe os resultados do autocomplete
    function displayAutocomplete(funcionarios) {
        if (!autocompleteContainer) return;

        autocompleteContainer.innerHTML = '';

        if (funcionarios.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'px-4 py-2 text-gray-500 text-sm';
            noResults.textContent = 'Nenhum funcionário encontrado';
            autocompleteContainer.appendChild(noResults);
        } else {
            funcionarios.forEach(funcionario => {
                const item = document.createElement('div');
                item.className = 'px-4 py-2 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0';
                
                item.innerHTML = `
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="font-medium text-gray-900">${funcionario.nome}</div>
                            <div class="text-sm text-gray-500">
                                ${funcionario.departamento} • Ramal: ${funcionario.ramal}
                                ${funcionario.is_chefia ? ' • <span class="text-yellow-600">👑 Chefia</span>' : ''}
                            </div>
                        </div>
                        <div class="text-xs text-gray-400">
                            Clique para selecionar
                        </div>
                    </div>
                `;

                item.addEventListener('click', function() {
                    searchInput.value = funcionario.nome;
                    hideAutocomplete();
                    // Submete o formulário automaticamente após seleção
                    submitForm();
                });

                autocompleteContainer.appendChild(item);
            });
        }

        showAutocomplete();
    }

    // Mostra o autocomplete
    function showAutocomplete() {
        if (autocompleteContainer) {
            autocompleteContainer.classList.remove('hidden');
            isAutocompleteVisible = true;
        }
    }

    // Esconde o autocomplete
    function hideAutocomplete() {
        if (autocompleteContainer) {
            autocompleteContainer.classList.add('hidden');
            isAutocompleteVisible = false;
        }
    }

    // Submete o formulário via AJAX (sem parâmetro autocomplete)
    function submitForm() {
        const formData = new FormData(form);
        const params = new URLSearchParams(formData);
        
        // Adiciona indicador de carregamento
        const resultadosContainer = document.getElementById('resultados');
        resultadosContainer.innerHTML = `
            <div class="col-span-full flex justify-center items-center py-12">
                <div class="text-center">
                    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p class="text-gray-600">Buscando funcionários...</p>
                </div>
            </div>
        `;

        fetch(form.action + '?' + params.toString(), {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => response.json())
        .then(data => {
            // Atualiza os resultados
            resultadosContainer.innerHTML = data.resultados_html;
            
            // Atualiza a paginação
            const paginacaoContainer = document.querySelector('.mt-6');
            if (paginacaoContainer && data.paginacao_html) {
                paginacaoContainer.innerHTML = data.paginacao_html;
                
                // Re-adiciona event listeners para os links de paginação
                addPaginationListeners();
            }
        })
        .catch(error => {
            console.error('Erro na busca:', error);
            resultadosContainer.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-red-600 mb-4">❌</div>
                    <h3 class="text-lg font-semibold text-gray-800 mb-2">Erro na busca</h3>
                    <p class="text-gray-600">Ocorreu um erro ao buscar os funcionários. Tente novamente.</p>
                </div>
            `;
        });
    }

    // Adiciona listeners para links de paginação
    function addPaginationListeners() {
        const paginationLinks = document.querySelectorAll('.pagination-link');
        paginationLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const page = this.getAttribute('data-page');
                
                // Adiciona o parâmetro de página ao formulário
                const pageInput = document.createElement('input');
                pageInput.type = 'hidden';
                pageInput.name = 'page';
                pageInput.value = page;
                form.appendChild(pageInput);
                
                submitForm();
                
                // Remove o input temporário
                form.removeChild(pageInput);
            });
        });
    }

    // Event listeners
    
    // Foco no campo de busca - mostra todos os funcionários
    searchInput.addEventListener('focus', function() {
        createAutocompleteContainer();
        fetchFuncionarios();
    });

    // Input no campo de busca - filtra funcionários
    searchInput.addEventListener('input', function() {
        createAutocompleteContainer();
        
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const query = this.value.trim();
            fetchFuncionarios(query);
        }, 300); // Delay de 300ms para evitar muitas requisições
    });

    // Clique fora do campo - esconde autocomplete
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !autocompleteContainer?.contains(e.target)) {
            hideAutocomplete();
        }
    });

    // Teclas de navegação no autocomplete
    searchInput.addEventListener('keydown', function(e) {
        if (!isAutocompleteVisible) return;

        const items = autocompleteContainer.querySelectorAll('.cursor-pointer');
        let currentIndex = -1;
        
        // Encontra o item atualmente selecionado
        items.forEach((item, index) => {
            if (item.classList.contains('bg-blue-100')) {
                currentIndex = index;
            }
        });

        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                if (currentIndex < items.length - 1) {
                    if (currentIndex >= 0) {
                        items[currentIndex].classList.remove('bg-blue-100');
                    }
                    items[currentIndex + 1].classList.add('bg-blue-100');
                }
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                if (currentIndex > 0) {
                    items[currentIndex].classList.remove('bg-blue-100');
                    items[currentIndex - 1].classList.add('bg-blue-100');
                }
                break;
                
            case 'Enter':
                e.preventDefault();
                if (currentIndex >= 0) {
                    items[currentIndex].click();
                } else {
                    hideAutocomplete();
                    submitForm();
                }
                break;
                
            case 'Escape':
                hideAutocomplete();
                break;
        }
    });

    // Outros filtros - submete automaticamente
    departamentoSelect.addEventListener('change', submitForm);
    soChefiaCheckbox.addEventListener('change', submitForm);
    
    responsabilidadeCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', submitForm);
    });

    // Inicializa os listeners de paginação
    addPaginationListeners();
});

