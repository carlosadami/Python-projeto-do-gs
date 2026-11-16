"""Leitura e validação dos arquivos de dados (CSV)."""

import csv
from datetime import datetime

from alertacheia import config

FORMATO_DATA = "%Y-%m-%d %H:%M"


def carregar_sensores(caminho):
    """Lê o cadastro de sensores e devolve um dicionário {id: dados do sensor}."""
    sensores = {}
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            sensores[linha["id"]] = {
                "id": linha["id"],
                "bairro": linha["bairro"],
                "local": linha["local"],
                "limites": {
                    "ATENCAO": float(linha["atencao_cm"]),
                    "ALERTA": float(linha["alerta_cm"]),
                    "EMERGENCIA": float(linha["emergencia_cm"]),
                },
            }
    return sensores


def leitura_valida(texto_nivel):
    """Diz se o valor lido é um número dentro da faixa do sensor."""
    try:
        nivel = float(texto_nivel)
    except (TypeError, ValueError):
        return False
    return config.NIVEL_MINIMO_VALIDO <= nivel <= config.NIVEL_MAXIMO_VALIDO


def carregar_leituras(caminho):
    """Lê as leituras de nível.

    Devolve duas coisas:
    - um dicionário {id do sensor: lista de leituras em ordem de horário};
    - a lista de linhas descartadas, para o relatório de qualidade dos dados.
    """
    leituras = {}
    descartadas = []
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        for numero, linha in enumerate(csv.DictReader(arquivo), start=2):
            if not leitura_valida(linha["nivel_cm"]):
                descartadas.append({"linha": numero, "sensor": linha["sensor_id"],
                                    "valor": linha["nivel_cm"]})
                continue
            leitura = {
                "momento": datetime.strptime(linha["data_hora"], FORMATO_DATA),
                "nivel_cm": float(linha["nivel_cm"]),
            }
            leituras.setdefault(linha["sensor_id"], []).append(leitura)

    for lista in leituras.values():
        lista.sort(key=lambda leitura: leitura["momento"])
    return leituras, descartadas
