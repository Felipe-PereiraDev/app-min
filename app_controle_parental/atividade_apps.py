import psutil
import win32gui
import win32process
from datetime import datetime
import time
from auth_uteis import load_token_from_file, fazer_login
import json
import requests

# Lista de processos e títulos de janelas que queremos ignorar
processos_ignorados = [
    "ApplicationFrameHost.exe", "CalculatorApp.exe", "TextInputHost.exe",
    "SystemSettings.exe", "explorer.exe", "RtkUWP.exe", "svchost.exe", "csrss.exe"
]


# Função para listar janelas abertas com base no estado atual
def listar_janelas_abertas():
    janelas_abertas = []

    def callback(hwnd, janelas):
        if win32gui.IsWindowVisible(hwnd):  # Verifica se a janela é visível
            _, pid = win32process.GetWindowThreadProcessId(hwnd)  # Obtém o PID do processo
            try:
                processo = psutil.Process(pid)  # Objeto do processo via psutil
                nome_processo = processo.name()  # Nome do executável
                hora_abertura = datetime.fromtimestamp(processo.create_time()).strftime(
                    "%Y-%m-%d %H:%M:%S")  # Hora de criação do processo

                if nome_processo not in processos_ignorados:
                    janelas.append((nome_processo, hora_abertura))

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    win32gui.EnumWindows(callback, janelas_abertas)  # Enumera todas as janelas visíveis

    return janelas_abertas


def salvar_no_bd(token, processo, hora_abertura):
    api_url = f"http://localhost:8080/user/f/apps-abertos"

    # Ajuste o formato da hora_inicio para o padrão ISO 8601
    hora_inicio_iso = datetime.strptime(hora_abertura, "%Y-%m-%d %H:%M:%S").isoformat()

    data_lista = {
        "nome": processo,
        "hora_inicio": hora_inicio_iso,  # Enviando no formato ISO 8601
        "ativo": True
    }

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Cria o corpo da requisição com os dados
    json_data = json.dumps(data_lista)

    try:
        response = requests.post(api_url, data=json_data, headers=headers)
        if response.status_code == 200:
            print("Atividade enviada com sucesso")
        else:
            print(f"Erro ao enviar o histórico: {response.status_code}")
    except requests.RequestException as e:
        print(f"Ocorreu um erro ao enviar os dados: {e}")


def remover_janelas_bd(token, processo):
    api_url = f"http://localhost:8080/user/f/apps-atualizar"

    # Ajuste o formato da hora_inicio para o padrão ISO 8601

    data_lista = {
        "nome": processo,
        "ativo": False
    }

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Cria o corpo da requisição com os dados
    json_data = json.dumps(data_lista)

    try:
        response = requests.put(api_url, data=json_data, headers=headers)
        if response.status_code == 204:
            print("Estado da janela modificada pra (False) com sucesso")
        else:
            print(f"Erro ao enviar o histórico: {response.status_code}")
    except requests.RequestException as e:
        print(f"Ocorreu um erro ao enviar os dados: {e}")


estado_anterior = set()


def monitorar_janelas(token: str, intervalo=5):
    # Função chamada periodicamente (sem loop infinito)
    global estado_anterior
    estado_atual = set(listar_janelas_abertas())  # Lista o estado atual das janelas

    # Verifica se alguma nova janela foi aberta comparando os estados
    novas_janelas = estado_atual - estado_anterior  # Janelas que estão no estado atual, mas não no anterior
    janelas_fechadas = estado_anterior - estado_atual

    if novas_janelas:
        for janela in novas_janelas:
            processo, hora_abertura = janela
            print(f"Nova janela aberta -> Processo: {processo}, Iniciado em: {hora_abertura}")
            salvar_no_bd(token, processo, hora_abertura)

    if janelas_fechadas:
        for janela in janelas_fechadas:
            processo, hora_abertura = janela
            remover_janelas_bd(token, processo)
            print(f"Janela fechada -> Processo: {processo}, Iniciado em: {hora_abertura}")

    # Atualiza o estado anterior para a próxima comparação
    estado_anterior = estado_atual

# Iniciar o monitoramento (com intervalo de 5 segundos)
# if __name__ == '__main__':
#     email = "fs804680@gmail.com"
#     senha = "123"
#     # Primeiro tenta carregar o token do arquivo
#     token = load_token_from_file()
#     if not token:
#         # Se o token não for encontrado ou estiver expirado, faz login novamente
#         token = fazer_login(senha=senha, email=email)
#     monitorar_janelas(intervalo=5, id=1, token=token)
