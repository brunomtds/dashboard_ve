function debounce(fn, delay) {
    let timeoutID;
    return function(...args) {
        clearTimeout(timeoutID);
        timeoutID = setTimeout(() => fn.apply(this, args), delay);
    };
}

let isLoading = false;

// Função para mostrar indicador de carregamento
function showLoading() {
    if (isLoading) return;
    isLoading = true;
    
    const resultadosDiv = document.getElementById('resultados');
    const mensagemErro = document.getElementById('mensagem_erro');
    
    // Limpa mensagens de erro
    mensagemErro.textContent = "";
    
    // Mostra indicador de carregamento
    resultadosDiv.innerHTML = `
        <div class="col-span-full text-center py-12">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <h3 class="text-xl font-semibold text-gray-800 mb-2">Consultando CEP...</h3>
            <p class="text-gray-600">Buscando UBSs próximas ao seu endereço...</p>
        </div>
    `;
}

// Função para esconder indicador de carregamento
function hideLoading() {
    isLoading = false;
}

// Função para mostrar estado vazio (quando CEP tem menos de 8 dígitos)
function showEmptyState() {
    const resultadosDiv = document.getElementById('resultados');
    const mensagemErro = document.getElementById('mensagem_erro');
    
    mensagemErro.textContent = "";
    resultadosDiv.innerHTML = `
        <div class="col-span-full text-center py-12">
            <div class="text-6xl mb-4">🏥</div>
            <h3 class="text-xl font-semibold text-gray-800 mb-2">Digite um CEP para consultar</h3>
            <p class="text-gray-600">Informe um CEP de 8 dígitos para encontrar as UBSs da região.</p>
        </div>
    `;
}

// Função para mostrar erro de forma mais amigável
function showError(mensagem) {
    const resultadosDiv = document.getElementById('resultados');
    const mensagemErro = document.getElementById('mensagem_erro');
    
    mensagemErro.textContent = mensagem;
    resultadosDiv.innerHTML = `
        <div class="col-span-full text-center py-12">
            <div class="text-6xl mb-4">❌</div>
            <h3 class="text-xl font-semibold text-gray-800 mb-2">CEP não encontrado</h3>
            <p class="text-gray-600">Verifique se o CEP está correto e tente novamente.</p>
        </div>
    `;
}

// Função para mostrar resultado vazio (CEP válido mas sem UBSs)
function showNoResults(cep) {
    const resultadosDiv = document.getElementById('resultados');
    const mensagemErro = document.getElementById('mensagem_erro');
    
    mensagemErro.textContent = "";
    resultadosDiv.innerHTML = `
        <div class="col-span-full text-center py-12">
            <div class="text-6xl mb-4">📭</div>
            <h3 class="text-xl font-semibold text-gray-800 mb-2">Nenhuma UBS encontrada</h3>
            <p class="text-gray-600">Não foram encontradas UBSs para o CEP ${cep}.</p>
        </div>
    `;
}

// Função para adicionar animação de entrada aos resultados
function addFadeInAnimation() {
    const cards = document.querySelectorAll('#resultados .bg-white');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.3s ease-out';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100); // Delay escalonado para cada card
    });
}

async function consultarCepAjax(cep) {
    const mensagemErro = document.getElementById('mensagem_erro');
    const resultadosDiv = document.getElementById('resultados');

    // Limpa mensagens e resultados ao digitar menos de 8 caracteres
    if (cep.length < 8) {
        hideLoading();
        showEmptyState();
        return;
    }

    // Validação básica do CEP
    if (cep.length !== 8 || !/^\d{8}$/.test(cep)) {
        hideLoading();
        showError("CEP deve conter exatamente 8 dígitos numéricos.");
        return;
    }

    // Mostra loading apenas se não estiver já carregando
    if (!isLoading) {
        showLoading();
    }

    try {
        const response = await fetch(`?cep=${cep}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error(`Erro na requisição: ${response.statusText}`);
        }

        const data = await response.json();

        hideLoading();

        if (data.erro) {
            showError(data.erro);
            return;
        }

        mensagemErro.textContent = "";

        // Verifica se há resultados
        if (!data.resultados || data.resultados.length === 0) {
            showNoResults(cep);
            return;
        }

        // Monta o HTML dos resultados dinamicamente
        let html = "";
        data.resultados.forEach(logradouro => {
            html += `<div class="bg-white p-6 rounded-lg shadow-md transform transition hover:-translate-y-1 hover:shadow-lg">`;
            html += `<h3 class="text-lg font-semibold mb-2 text-blue-800">${logradouro.nome}</h3>`;
            html += `<p class="text-gray-600 mb-4 font-medium">📍 Bairro: ${logradouro.bairro}</p>`;
            
            logradouro.ubs_list.forEach(ubs => {
                html += `<div class="mb-4 p-3 bg-gray-50 rounded-lg border-l-4 border-blue-500">`;
                html += `<p class="font-medium text-gray-800">🏥 ${ubs.nome}</p>`;
                if (ubs.endereco) {
                    html += `<p class="text-gray-600 text-sm mt-1">📍 ${ubs.endereco}</p>`;
                }
                if (ubs.telefone && ubs.telefone !== "N/A") {
                    html += `<p class="text-gray-600 text-sm mt-1">📞 ${ubs.telefone}</p>`;
                }
                html += `</div>`;
            });
            html += `</div>`;
        });

        resultadosDiv.innerHTML = html;
        
        // Adiciona animação de entrada
        setTimeout(() => {
            addFadeInAnimation();
        }, 50);

    } catch (error) {
        hideLoading();
        console.error('Erro na consulta CEP:', error);
        
        resultadosDiv.innerHTML = `
            <div class="col-span-full text-center py-12">
                <div class="text-6xl mb-4">⚠️</div>
                <h3 class="text-xl font-semibold text-gray-800 mb-2">Erro na consulta</h3>
                <p class="text-gray-600">Ocorreu um erro ao consultar o CEP. Verifique sua conexão e tente novamente.</p>
                <button onclick="consultarCepAjax('${cep}')" class="mt-4 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition">
                    🔄 Tentar novamente
                </button>
            </div>
        `;
        mensagemErro.textContent = "";
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const inputCep = document.getElementById('cep');
    
    // Inicializa com estado vazio se não há CEP
    if (!inputCep.value.trim()) {
        showEmptyState();
    }
    
    // Formatação automática do CEP (adiciona hífen)
    inputCep.addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, ''); // Remove não-dígitos
        
        // Limita a 8 dígitos
        if (value.length > 8) {
            value = value.substring(0, 8);
        }
        
        // Formata com hífen: 12345-678
        if (value.length > 5) {
            value = value.substring(0, 5) + '-' + value.substring(5);
        }
        
        e.target.value = value;
        
        // Remove hífen para a consulta
        const cepLimpo = value.replace(/\D/g, '');
        
        // Debounce da consulta
        debouncedConsulta(cepLimpo);
    });
    
    // Função com debounce
    const debouncedConsulta = debounce((cep) => {
        consultarCepAjax(cep);
    }, 300); // Reduzido para 300ms para melhor responsividade
    
    // Permite apenas números e hífen
    inputCep.addEventListener('keypress', (e) => {
        const char = String.fromCharCode(e.which);
        if (!/[\d-]/.test(char)) {
            e.preventDefault();
        }
    });
    
    // Foco no campo ao carregar a página
    inputCep.focus();
});