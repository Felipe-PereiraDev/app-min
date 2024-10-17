import json
import os

import requests

from auth_uteis import getIdToken, getIdRespToken


# Função para carregar as URLs bloqueadas de um arquivo
def load_blocked_urls():
    try:
        with open("blocked_urls.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# Função para adicionar uma URL ao arquivo hosts
def block_url_in_hosts(url):
    hosts_path = "C:\\Windows\\System32\\drivers\\etc\\hosts"  # Caminho do arquivo hosts no Windows
    entries = [
        f"127.0.0.1 {url}\n",
        f"127.0.0.1 www.{url}\n"
    ]

    try:
        with open(hosts_path, "a") as hosts_file:
            hosts_file.writelines(entries)
            print(f"URLs bloqueadas no hosts: {url}, www.{url}")
    except PermissionError:
        print("Erro: Você precisa de permissões administrativas para modificar o arquivo hosts.")


# Função para bloquear uma URL (adiciona à lista de bloqueio)
def block_url(url, url_id):
    blocked_urls = load_blocked_urls()
    if url not in blocked_urls:
        blocked_urls.append(url)
        with open("blocked_urls.json", "w") as f:
            json.dump(blocked_urls, f)
        print(f"URL bloqueada: {url}")
        block_url_in_hosts(url)  # Adiciona a URL ao arquivo hosts
        return {'id': url_id, 'bloqueado': True}  # Retorna o ID e o estado de bloqueio
    else:
        print(f"A URL já está bloqueada: {url}")
        return None  # Retorna None se já estiver bloqueada


# Função para obter URLs a partir da API
def fetch_blocked_urls(id_resp, token):
    api_url = f"http://localhost:8080/user/f/{id_resp}/bloquear-url"
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url=api_url, headers=headers)

        if response.status_code == 200:
            blocked_urls = [(item['url'], item['id']) for item in response.json()]  # Retorna uma lista de tuplas (url, id)
            return blocked_urls
        else:
            print(f"Erro ao buscar URLs bloqueadas: {response.status_code}")
            return []

    except requests.ConnectionError:
        print("Erro de conexão: Verifique se a API está rodando e acessível.")
        return []

    except requests.Timeout:
        print("O tempo de conexão foi excedido. Tente novamente mais tarde.")
        return []

    except requests.RequestException as e:
        print(f"Ocorreu um erro ao acessar a API: {e}")
        return []


# Função para verificar se uma URL está bloqueada
def is_url_blocked(url):
    blocked_urls = load_blocked_urls()
    return url in blocked_urls


def flush_dns():
    os.system("ipconfig /flushdns")


# Função para enviar URLs a serem bloqueadas para a API
def update_blocked_urls(id_resp, payload, token):
    api_url = f"http://localhost:8080/user/f/{id_resp}/bloquear-url"
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        response = requests.put(url=api_url, headers=headers, json=payload)

        if response.status_code == 204:
            print("URLs bloqueadas com sucesso.")
        else:
            print(f"Erro ao atualizar URLs bloqueadas: {response.status_code}")

    except requests.ConnectionError:
        print("Erro de conexão: Verifique se a API está rodando e acessível.")
    except requests.Timeout:
        print("O tempo de conexão foi excedido. Tente novamente mais tarde.")
    except requests.RequestException as e:
        print(f"Ocorreu um erro ao acessar a API: {e}")


def rodar_block_url(token):
    if token:
        id_filho = getIdToken(token)
        id_resp = getIdRespToken(token)
        blocked_urls_from_api = fetch_blocked_urls(id_resp, token)

        if id_filho and id_resp:
            payload = []
            for url, url_id in blocked_urls_from_api:
                result = block_url(url, url_id)  # Supondo que blocked_urls_from_api retorna uma lista de tuplas (url, url_id)
                if result:
                    payload.append(result)

            flush_dns()
            update_blocked_urls(id_resp, payload, token)  # Atualiza a API
        else:
            print("Erro ao pegar ID do usuário")
