import schedule
from historico_urls import rodar_url
from block_url import rodar_block_url
from auth_uteis import load_token_from_file, fazer_login
from atividade_apps import monitorar_janelas
import schedule
import time


def executar_funcoes(token):
    rodar_url(token)
    rodar_block_url(token)
    monitorar_janelas(token=token)


def main():
    email = "felpera41@gmail.com"
    senha = "123"

    # Primeiro tenta carregar o token do arquivo
    token = load_token_from_file()
    if not token:
        # Se o token não for encontrado ou estiver expirado, faz login novamente
        token = fazer_login(senha=senha, email=email)

    # Agendar a execução das funções a cada 5 minutos (por exemplo)
    schedule.every(20).seconds.do(executar_funcoes, token)

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)  # Aguarda um segundo antes de verificar novamente
        except Exception as e:
            print(f"Ocorreu um erro: {e}")


if __name__ == "__main__":
    main()
