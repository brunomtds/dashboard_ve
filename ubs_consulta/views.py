import psycopg2
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
import logging

# Configurar logging para debug
logger = logging.getLogger(__name__)

@login_required
def consulta_cep_view(request):
    resultados = []
    mensagem_erro = None
    logradouros = []
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

                # Buscar logradouros
                query_logradouro = """
                    SELECT DISTINCT "LOGRADOURO", "BAIRRO"
                    FROM logradouros
                    WHERE "CEP" = %s
                    ORDER BY "LOGRADOURO"
                """
                cursor.execute(query_logradouro, (cep_input,))
                logradouro_result = cursor.fetchall()

                if not logradouro_result:
                    mensagem_erro = f"CEP {cep_input} não foi encontrado na base de dados de Jundiaí."
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

                                # Formatação melhorada do telefone
                                if telefone:
                                    try:
                                        telefone_str = str(int(float(telefone)))
                                        if len(telefone_str) >= 10:
                                            tel_format = f"({telefone_str[:2]}) {telefone_str[2:6]}-{telefone_str[6:]}"
                                        else:
                                            tel_format = telefone_str
                                    except (ValueError, TypeError):
                                        tel_format = "Não informado"
                                else:
                                    tel_format = "Não informado"

                                # Formatação melhorada do endereço
                                endereco_parts = []
                                if logradouro_ubs:
                                    endereco_parts.append(logradouro_ubs)
                                if numero:
                                    endereco_parts.append(f"nº {numero}")
                                if bairro_ubs:
                                    endereco_parts.append(f"- {bairro_ubs}")
                                
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

                        # Se não há UBS real, adiciona mensagem padrão
                        if not tem_ubs_real:
                            ubs_list.append({
                                "nome": "SEM UNIDADE DESIGNADA",
                                "endereco": "Entre em contato com a Secretaria de Saúde para mais informações sobre o endereçamento desta região",
                                "telefone": "Não informado"
                            })

                        logradouros.append({
                            "nome": logradouro,
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
            return JsonResponse({
                'erro': mensagem_erro,
                'cep_consultado': cep_input
            })
        else:
            return JsonResponse({
                'resultados': logradouros,
                'total_logradouros': len(logradouros),
                'total_ubs': sum(len(log['ubs_list']) for log in logradouros),
                'cep_consultado': cep_input
            })

    # Requisição normal: renderiza template
    context = {
        'resultados': logradouros,
        'mensagem_erro': mensagem_erro,
        'cep_input': cep_input,
    }
    return render(request, 'ubs_consulta/consulta_cep.html', context)
