import datetime
import json

import browser_history
import pytz
import requests

from auth_uteis import getIdToken

# Função para salvar o token em um arquivo
last_sent_data = None


# Função para obter o histórico do navegador e enviá-lo para a API
def get_history(token: str, id):
    global last_sent_data  # Usamos a variável global para armazenar os últimos dados enviados

    # Obtém a data e hora atual no fuso horário 'America/Sao_Paulo'
    try:
        local_tz = pytz.timezone('America/Sao_Paulo')  # Substitua pelo fuso horário desejado
        now_local = datetime.datetime.now(local_tz)
        today = now_local.date()  # Obtém apenas a data
        date_time_obj = datetime.datetime.combine(today, datetime.time.min)  # Combina com a hora mínima (00:00:00)
        date_time_obj = date_time_obj.replace(tzinfo=None)
    except ValueError:
        print("Formato de data inválido! Por favor, tente novamente.")
        return

    # Obtém o histórico do navegador
    outputs = browser_history.get_history()
    # Converte o histórico para CSV, remove quebras de linha e inverte a ordem
    H = outputs.to_csv().replace('\r', '').split('\n')[::-1][1:]

    # Lista para armazenar os dados que serão enviados para a API
    data_list = []

    # Conjunto para armazenar URLs únicas
    seen_urls = set()

    # Limite para o tamanho da URL e conteúdo
    url_limit = 80
    conteudo_limit = 50

    # Itera sobre cada item no histórico
    for i in H:
        try:
            h = i.split(',', maxsplit=2)
            if len(h) < 3:
                continue  # Pula linhas que não têm o formato esperado

            date = h[0]  # Obtém a data e hora
            url = h[1]  # Obtém a URL
            content = h[2]  # Obtém o conteúdo

            # Converte a data e hora para datetime
            date_dt = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S%z')
            date_dt = date_dt.replace(tzinfo=None)

            url = url[:url_limit]
            content = content[:conteudo_limit]

            if url not in seen_urls and date_dt > date_time_obj:
                data_list.append({
                    "url": url,
                    "dataVisitada": date_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "conteudo": content.strip()
                })
                seen_urls.add(url)

        except (IndexError, ValueError):
            continue  # Pula linhas com erro

    # Verifica se há novos dados para enviar e se são diferentes dos últimos enviados
    if data_list and data_list != last_sent_data:
        api_url = f"http://localhost:8080/user/f/historico-sites"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # Cria o corpo da requisição com os dados
        json_data = json.dumps(data_list)
        try:
            response = requests.post(api_url, data=json_data, headers=headers)
            if response.status_code == 200:
                print("Histórico enviado com sucesso!")
                last_sent_data = data_list  # Atualiza o último histórico enviado
            else:
                print(f"Erro ao enviar o histórico: {response.status_code}")
        except requests.RequestException as e:
            print(f"Ocorreu um erro ao enviar os dados: {e}")
    else:
        print("Nenhum dado novo para enviar.")


def rodar_url(token):
    if token:
        id_user = getIdToken(token)
        if id_user:
            get_history(token, id_user)
        else:
            print("Erro ao pegar ID do usuário")
