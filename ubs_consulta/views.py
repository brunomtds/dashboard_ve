# ubs_consulta/views.py

import psycopg2
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
import logging
from collections import defaultdict

# Configurar logging para debug
logger = logging.getLogger(__name__ )

def consulta_cep_view(request):
    resultados = []
    mensagem_erro = None
    cep_input = request.GET.get('cep', '').strip()

    if cep_input:
        # Validações básicas do CEP
        if len(cep_input) != 8:
            mensagem_erro = f"CEP deve conter exatamente 8 dígitos. Você digitou {len(cep_input)} dígitos."
        elif not cep_input.isdigit():
            mensagem_erro = "CEP deve conter apenas números."
        elif not cep_input.startswith(("1320", "1321")):
            mensagem_erro = f"CEP {cep_input} não pertence à região de Jundiaí (deve começar com 1320 ou 1321)."
        else:
            try:
                # Conexão com o banco
                conn = psycopg2.connect(
                    host=settings.DATABASES['default']['HOST'],
                    port=settings.DATABASES['default']['PORT'],
                    dbname=settings.DATABASES['default']['NAME'],
                    user=settings.DATABASES['default']['USER'],
                    password=settings.DATABASES['default']['PASSWORD']
                )
                cursor = conn.cursor()

                # Query principal para buscar logradouros e códigos de UBS por bairro
                query_logradouros_por_bairro = """
                    SELECT "BAIRRO", "LOGRADOURO", "COD UBS"
                    FROM logradouros
                    WHERE "CEP" = %s
                    ORDER BY "BAIRRO", "LOGRADOURO";
                """
                cursor.execute(query_logradouros_por_bairro, (cep_input,))
                logradouro_results = cursor.fetchall()

                if not logradouro_results:
                    mensagem_erro = f"CEP {cep_input} não foi encontrado na base de dados de Jundiaí."
                else:
                    # Agrupa os resultados por bairro para processamento
                    bairros_data = defaultdict(lambda: {'logradouros': set(), 'cod_ubs_set': set()})
                    for bairro, logradouro, cod_ubs in logradouro_results:
                        bairros_data[bairro]['logradouros'].add(logradouro)
                        if cod_ubs:
                            bairros_data[bairro]['cod_ubs_set'].add(cod_ubs)

                    # Processa cada bairro para montar a lista de resultados
                    for bairro, data in bairros_data.items():
                        logradouro_nome = ", ".join(sorted(list(data['logradouros'])))
                        cod_ubs_list = sorted(list(data['cod_ubs_set']))
                        
                        ubs_list = []
                        tem_ubs_real = False

                        for cod in cod_ubs_list:
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
                                    continue
                                else:
                                    tem_ubs_real = True

                                # Formatação do telefone
                                if telefone:
                                    try:
                                        telefone_str = str(int(float(telefone)))
                                        tel_format = f"({telefone_str[:2]}) {telefone_str[2:6]}-{telefone_str[6:]}" if len(telefone_str) >= 10 else telefone_str
                                    except (ValueError, TypeError):
                                        tel_format = "Não informado"
                                else:
                                    tel_format = "Não informado"

                                # Formatação do endereço
                                endereco_parts = [part for part in [logradouro_ubs, f"nº {numero}" if numero else None, f"- {bairro_ubs}" if bairro_ubs else None] if part]
                                endereco_formatado = ", ".join(endereco_parts) if endereco_parts else "Endereço não informado"

                                ubs_list.append({
                                    "nome": nome,
                                    "endereco": endereco_formatado,
                                    "telefone": tel_format
                                })
                            else:
                                ubs_list.append({
                                    "nome": f"UBS código {cod} - Informações não encontradas",
                                    "endereco": "Dados não disponíveis",
                                    "telefone": "Não informado"
                                })
                        
                        # Se não houver UBS real, adiciona a mensagem padrão
                        if not tem_ubs_real and not any(u['nome'] == "SEM UNIDADE DESIGNADA" for u in ubs_list):
                            ubs_list.append({
                                "nome": "SEM UNIDADE DESIGNADA",
                                "endereco": "Entre em contato com a Secretaria de Saúde para mais informações sobre o endereçamento desta região",
                                "telefone": "Não informado"
                            })

                        # Adiciona o card do bairro à lista de resultados
                        resultados.append({
                            "nome": logradouro_nome, # Agora pode ser mais de um logradouro por bairro
                            "bairro": bairro,
                            "ubs_list": ubs_list
                        })

                conn.close()

            except psycopg2.Error as e:
                logger.error(f"Erro de banco de dados na consulta CEP {cep_input}: {e}")
                mensagem_erro = "Erro interno do sistema. Tente novamente em alguns instantes."
            except Exception as e:
                logger.error(f"Erro inesperado na consulta CEP {cep_input}: {e}")
                mensagem_erro = "Erro inesperado. Tente novamente ou entre em contato com o suporte."

    # Se for requisição AJAX, retorne JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if mensagem_erro:
            return JsonResponse({'erro': mensagem_erro, 'cep_consultado': cep_input})
        else:
            return JsonResponse({
                'resultados': resultados,
                'total_logradouros': len(resultados), # Agora representa o total de bairros
                'total_ubs': sum(len(log['ubs_list']) for log in resultados),
                'cep_consultado': cep_input
            })

    # Requisição normal: renderiza template
    context = {
        'resultados': resultados,
        'mensagem_erro': mensagem_erro,
        'cep_input': cep_input,
    }
    return render(request, 'ubs_consulta/consulta_cep.html', context)
