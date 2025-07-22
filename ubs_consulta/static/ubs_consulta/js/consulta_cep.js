function consultarCep(cep) {
    if (cep.length === 8) {
        window.location.href = "?cep=" + cep;
    }
}