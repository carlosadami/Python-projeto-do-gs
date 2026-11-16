"""AlertaCheia - transforma leituras de nível da água em decisões.

Uso interativo:   python main.py
Uso direto:       python main.py --boletim
                  python main.py --historico
                  python main.py --exportar
"""

import argparse
import os
import sys

from alertacheia import analise, dados, relatorio

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQ_SENSORES = os.path.join(PASTA, "dados", "sensores.csv")
ARQ_LEITURAS = os.path.join(PASTA, "dados", "leituras.csv")
ARQ_EVENTO = os.path.join(PASTA, "dados", "evento_completo.csv")
PASTA_SAIDA = os.path.join(PASTA, "saida")
ARQ_DB_SITE = os.path.join(PASTA, "..", "web", "db.json")


def carregar_tudo():
    """Lê os arquivos e devolve tudo o que o programa precisa."""
    try:
        sensores = dados.carregar_sensores(ARQ_SENSORES)
        leituras, descartadas = dados.carregar_leituras(ARQ_LEITURAS)
    except FileNotFoundError as erro:
        print(f"Arquivo de dados não encontrado: {erro.filename}")
        print("Rode primeiro:  python gerar_dados.py")
        sys.exit(1)
    boletim = analise.gerar_boletim(sensores, leituras)
    return sensores, leituras, descartadas, boletim


def exportar(boletim):
    """Salva o boletim em JSON e CSV e, se o site existir, atualiza o db.json."""
    relatorio.salvar_json(boletim, os.path.join(PASTA_SAIDA, "boletim.json"))
    relatorio.salvar_csv(boletim, os.path.join(PASTA_SAIDA, "boletim.csv"))
    print("Boletim salvo em saida/boletim.json e saida/boletim.csv")
    if os.path.exists(ARQ_DB_SITE):
        relatorio.exportar_para_site(boletim, ARQ_DB_SITE)
        print("Site atualizado: lista 'bairros' de web/db.json")
    else:
        print("web/db.json não encontrado: o site não foi atualizado.")


def mostrar_linha(sensor, leituras_do_sensor):
    """Calcula e mostra a linha do tempo de um sensor."""
    eventos = analise.linha_do_tempo(sensor, leituras_do_sensor)
    antecedencia = analise.antecedencia_minutos(sensor, leituras_do_sensor, eventos)
    relatorio.mostrar_linha_do_tempo(sensor, leituras_do_sensor, eventos, antecedencia)


def avaliar_evento_completo(sensores):
    """Mede o indicador de impacto em uma cheia inteira do Sarandi (simulada)."""
    if not os.path.exists(ARQ_EVENTO):
        print("dados/evento_completo.csv não encontrado. Rode: python gerar_dados.py")
        return
    leituras, _ = dados.carregar_leituras(ARQ_EVENTO)
    print()
    print("AVALIAÇÃO EM UMA CHEIA COMPLETA (da primeira chuva até a água baixar)")
    mostrar_linha(sensores["S01"], leituras["S01"])


def escolher_bairro(boletim):
    """Pede ao usuário um bairro e devolve o item do boletim (ou None)."""
    print()
    for numero, item in enumerate(boletim, start=1):
        print(f"  {numero}. {item['bairro']}")
    resposta = input("Número do bairro: ").strip()
    if not resposta.isdigit() or not 1 <= int(resposta) <= len(boletim):
        print("Opção inválida. Digite um dos números da lista.")
        return None
    return boletim[int(resposta) - 1]


def menu():
    """Menu de texto para usar o programa passo a passo."""
    sensores, leituras, descartadas, boletim = carregar_tudo()
    while True:
        print()
        print("=== AlertaCheia ===")
        print("1. Ver boletim de todos os bairros")
        print("2. Ver o que fazer agora")
        print("3. Ver detalhes de um bairro")
        print("4. Gerar gráfico de um bairro")
        print("5. Ver qualidade dos dados")
        print("6. Exportar boletim (JSON, CSV e site)")
        print("7. Ver linha do tempo de avisos de um bairro")
        print("8. Medir o indicador de impacto em uma cheia completa")
        print("0. Sair")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            relatorio.mostrar_boletim(boletim)
        elif opcao == "2":
            relatorio.mostrar_acoes(boletim)
        elif opcao == "3":
            item = escolher_bairro(boletim)
            if item:
                relatorio.mostrar_detalhes(item)
        elif opcao == "4":
            item = escolher_bairro(boletim)
            if item:
                sensor_id = item["sensor_id"]
                caminho = os.path.join(PASTA_SAIDA, f"grafico_{sensor_id}.png")
                relatorio.salvar_grafico(sensores[sensor_id], leituras[sensor_id], caminho)
                print(f"Gráfico salvo em saida/grafico_{sensor_id}.png")
        elif opcao == "5":
            relatorio.mostrar_qualidade(leituras, descartadas)
        elif opcao == "6":
            exportar(boletim)
        elif opcao == "7":
            item = escolher_bairro(boletim)
            if item:
                mostrar_linha(sensores[item["sensor_id"]], leituras[item["sensor_id"]])
        elif opcao == "8":
            avaliar_evento_completo(sensores)
        elif opcao == "0":
            print("Até logo. Em emergência, ligue 199 (Defesa Civil).")
            break
        else:
            print("Opção inválida. Digite um número de 0 a 8.")


def main():
    argumentos = argparse.ArgumentParser(description="AlertaCheia - boletim de cheias por bairro")
    argumentos.add_argument("--boletim", action="store_true",
                            help="mostra o boletim e as orientações e encerra")
    argumentos.add_argument("--historico", action="store_true",
                            help="mostra a linha do tempo de avisos de todos os bairros")
    argumentos.add_argument("--exportar", action="store_true",
                            help="salva o boletim e atualiza o site, sem abrir o menu")
    opcoes = argumentos.parse_args()

    if opcoes.boletim or opcoes.exportar or opcoes.historico:
        sensores, leituras, descartadas, boletim = carregar_tudo()
        if opcoes.historico:
            for sensor_id, sensor in sensores.items():
                mostrar_linha(sensor, leituras[sensor_id])
            avaliar_evento_completo(sensores)
        if opcoes.boletim:
            relatorio.mostrar_boletim(boletim)
            relatorio.mostrar_acoes(boletim)
            relatorio.mostrar_qualidade(leituras, descartadas)
        if opcoes.exportar:
            exportar(boletim)
    else:
        menu()


if __name__ == "__main__":
    main()
