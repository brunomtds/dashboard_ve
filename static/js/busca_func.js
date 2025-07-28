document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('filtroForm');
    const searchInput = document.getElementById('q');
    const departamentoSelect = document.getElementById('departamento');
    const soChefias = document.getElementById('so_chefias');
    const responsabilidadeCheckboxes = document.querySelectorAll('.responsabilidade-checkbox');
    const resultadosContainer = document.getElementById('resultados');
    const paginacaoContainer = document.querySelector('.mt-6'); // Container da paginação
    
    let searchTimeout;
    let isLoading = false;
    
    // Função para mostrar indicador de carregamento
    function showLoading() {
        if (isLoading) return;
        isLoading = true;
        resultadosContainer.innerHTML = `
            <div class="col-span-full text-center py-12">
                <div class="text-6xl mb-4">⏳</div>
                <h3 class="text-xl font-semibold text-gray-800 mb-2">Carregando...</h3>
                <p class="text-gray-600">Buscando funcionários...</p>
            </div>
        `;
    }
    
    // Função para esconder indicador de carregamento
    function hideLoading() {
        isLoading = false;
    }
    
    // Função para fazer a requisição AJAX
    function performAjaxSearch() {
        if (isLoading) return;
        
        showLoading();
        
        // Coleta todos os dados do formulário
        const formData = new FormData(form);
        const params = new URLSearchParams(formData);
        
        // Faz a requisição AJAX
        fetch(form.action + '?' + params.toString(), {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro na requisição');
            }
            return response.json();
        })
        .then(data => {
            // Atualiza os resultados
            resultadosContainer.innerHTML = data.resultados_html;
            
            // Atualiza a paginação
            if (paginacaoContainer) {
                paginacaoContainer.innerHTML = data.paginacao_html;
                
                // Adiciona event listeners aos links de paginação
                addPaginationListeners();
            }
            
            hideLoading();
        })
        .catch(error => {
            console.error('Erro na busca AJAX:', error);
            resultadosContainer.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-6xl mb-4">❌</div>
                    <h3 class="text-xl font-semibold text-gray-800 mb-2">Erro na busca</h3>
                    <p class="text-gray-600">Ocorreu um erro ao buscar os funcionários. Tente novamente.</p>
                </div>
            `;
            hideLoading();
        });
    }
    
    // Função para fazer busca com delay (para o campo de texto)
    function performAjaxSearchWithDelay() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(performAjaxSearch, 500);
    }
    
    // Função para adicionar event listeners aos links de paginação
    function addPaginationListeners() {
        const paginationLinks = document.querySelectorAll('.pagination-link');
        paginationLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const page = this.getAttribute('data-page');
                
                // Adiciona o número da página ao formulário
                let pageInput = document.querySelector('input[name="page"]');
                if (!pageInput) {
                    pageInput = document.createElement('input');
                    pageInput.type = 'hidden';
                    pageInput.name = 'page';
                    form.appendChild(pageInput);
                }
                pageInput.value = page;
                
                performAjaxSearch();
            });
        });
    }
    
    // Event listeners para os filtros
    
    // Campo de busca por texto - com delay
    searchInput.addEventListener('input', function() {
        // Remove a página ao fazer nova busca
        const pageInput = document.querySelector('input[name="page"]');
        if (pageInput) {
            pageInput.remove();
        }
        performAjaxSearchWithDelay();
    });
    
    // Select de departamento - busca imediata
    departamentoSelect.addEventListener('change', function() {
        // Remove a página ao fazer nova busca
        const pageInput = document.querySelector('input[name="page"]');
        if (pageInput) {
            pageInput.remove();
        }
        performAjaxSearch();
    });
    
    // Checkbox de chefias - busca imediata
    soChefias.addEventListener('change', function() {
        // Remove a página ao fazer nova busca
        const pageInput = document.querySelector('input[name="page"]');
        if (pageInput) {
            pageInput.remove();
        }
        performAjaxSearch();
    });
    
    // Checkboxes de responsabilidades - busca imediata
    responsabilidadeCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            // Remove a página ao fazer nova busca
            const pageInput = document.querySelector('input[name="page"]');
            if (pageInput) {
                pageInput.remove();
            }
            performAjaxSearch();
        });
    });
    
    // Adiciona event listeners iniciais para paginação (se existir)
    addPaginationListeners();
});

