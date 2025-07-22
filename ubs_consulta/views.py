import psycopg2
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings

@login_required
def consulta_cep_view(request):
    resultados = []
    mensagem_erro = None
    logradouros = []
    cep_input = request.GET.get('cep', '').strip()

    if cep_input:
        # Conexão com o banco
        conn = psycopg2.connect(
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD']
        )
        cursor = conn.cursor()

        # Validações
        if len(cep_input) != 8:
            mensagem_erro = f"CEP {cep_input} não tem 8 dígitos."
        elif not cep_input.startswith(("1320", "1321")):
            mensagem_erro = f"CEP {cep_input} não pertence a Jundiaí."
        else:
            # Buscar logradouros
            query_logradouro = """
                SELECT DISTINCT "LOGRADOURO", "BAIRRO"
                FROM logradouros
                WHERE "CEP" = %s
            """
            cursor.execute(query_logradouro, (cep_input,))
            logradouro_result = cursor.fetchall()

            if not logradouro_result:
                mensagem_erro = f"CEP {cep_input} não encontrado."
            else:
                for logradouro, bairro in logradouro_result:
                    # Buscar UBSs para cada logradouro
                    query_cod_ubs = """
                        SELECT DISTINCT "COD UBS"
                        FROM logradouros
                        WHERE "CEP" = %s AND "LOGRADOURO" = %s
                    """
                    cursor.execute(query_cod_ubs, (cep_input, logradouro))
                    cod_ubs_list = cursor.fetchall()

                    ubs_list = []
                    tem_ubs_real = False

                    for cod_ubs in cod_ubs_list:
                        cod = cod_ubs[0]
                        query_ubs = """
                            SELECT "UNIDADE DE SAÚDE", "logradouro", "numero", "bairro", "telefone"
                            FROM ubs
                            WHERE "PK" = %s
                        """
                        cursor.execute(query_ubs, (cod,))
                        ubs_info = cursor.fetchone()

                        if ubs_info:
                            nome, logradouro_ubs, numero, bairro_ubs, telefone = ubs_info

                            if nome == "SEM UNIDADE DESIGNADA":
                                continue  # pula, trata depois
                            else:
                                tem_ubs_real = True

                            if telefone:
                                telefone = str(int(float(telefone)))
                                tel_format = f"({telefone[:2]}){telefone[2:6]}-{telefone[6:]}"
                            else:
                                tel_format = "N/A"

                            ubs_list.append({
                                "nome": nome,
                                "endereco": f"{logradouro_ubs}, {numero} - {bairro_ubs}",
                                "telefone": tel_format
                            })
                        else:
                            ubs_list.append({
                                "nome": f"UBS código {cod} não encontrada",
                                "endereco": "",
                                "telefone": ""
                            })

                    # Se não tiver UBS real, adiciona 'Nenhuma UBS designada'
                    if not tem_ubs_real:
                        ubs_list.append({
                            "nome": "SEM UNIDADE DESIGNADA",
                            "endereco": "INFORME O RESPONSÁVEL PELO ENDEREÇAMENTO",
                            "telefone": ""
                        })

                    logradouros.append({
                        "nome": logradouro,
                        "bairro": bairro,
                        "ubs_list": ubs_list
                    })

        conn.close()

    context = {
        'resultados': logradouros,
        'mensagem_erro': mensagem_erro,
        'cep_input': cep_input
    }
    return render(request, 'ubs_consulta/consulta_cep.html', context)