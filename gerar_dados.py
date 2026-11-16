"""Gera os dados SIMULADOS usados pelo AlertaCheia.

Nenhum dado real ou pessoal é usado. As leituras imitam o que os sensores
ultrassônicos (projeto de Edge Computing) enviariam durante uma chuva forte.
A curva de subida é a mesma estudada em Differentiated Problem Solving:

    h(t) = h0 + c * t^2 * e^(-t/tau)      (t em horas, h em cm)

Uso:  python gerar_dados.py
"""

import csv
import math
import random
from datetime import datetime, timedelta

# Semente fixa: quem rodar o script obtém exatamente os mesmos dados.
random.seed(2026)

INICIO = datetime(2026, 11, 10, 18, 0)
FIM = datetime(2026, 11, 11, 18, 0)
INTERVALO = timedelta(minutes=15)

# Cadastro dos sensores e parâmetros da curva de cada um.
# horas_desde_chuva: há quantas horas (em relação ao FIM) a água começou a subir.
SENSORES = [
    {"id": "S01", "bairro": "Sarandi", "local": "Arroio Sarandi - Vila Elizabeth",
     "limites": (120, 180, 240), "h0": 80, "c": 37, "tau": 3.0, "horas_desde_chuva": 2.75},
    {"id": "S02", "bairro": "Humaitá", "local": "Canal da Av. A. J. Renner",
     "limites": (110, 170, 230), "h0": 70, "c": 12, "tau": 4.0, "horas_desde_chuva": 4.0},
    {"id": "S03", "bairro": "Navegantes", "local": "Casa de bombas - Rua Voluntários",
     "limites": (110, 170, 230), "h0": 60, "c": 36, "tau": 2.5, "horas_desde_chuva": 1.5},
    {"id": "S04", "bairro": "Menino Deus", "local": "Arroio Dilúvio - Av. Ipiranga",
     "limites": (120, 180, 240), "h0": 75, "c": 20, "tau": 3.0, "horas_desde_chuva": 12.0},
    {"id": "S05", "bairro": "Cidade Baixa", "local": "Rua João Alfredo",
     "limites": (120, 180, 240), "h0": 65, "c": 0, "tau": 3.0, "horas_desde_chuva": 0.0},
]

# Leituras defeituosas colocadas de propósito para testar a validação.
DEFEITOS = {("S02", 20): "-1", ("S04", 55): "", ("S01", 70): "999", ("S05", 33): "erro"}


def nivel_modelo(sensor, momento):
    """Nível (cm) previsto pela curva do sensor em um certo momento."""
    comeco_chuva = FIM - timedelta(hours=sensor["horas_desde_chuva"])
    t = (momento - comeco_chuva).total_seconds() / 3600
    if t <= 0:
        return sensor["h0"]
    return sensor["h0"] + sensor["c"] * t ** 2 * math.exp(-t / sensor["tau"])


def main():
    with open("dados/sensores.csv", "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["id", "bairro", "local", "atencao_cm", "alerta_cm", "emergencia_cm"])
        for s in SENSORES:
            escritor.writerow([s["id"], s["bairro"], s["local"], *s["limites"]])

    total = 0
    with open("dados/leituras.csv", "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["data_hora", "sensor_id", "nivel_cm"])
        for s in SENSORES:
            momento = INICIO
            indice = 0
            while momento <= FIM:
                ruido = random.gauss(0, 1.0)  # pequena variação, como num sensor real
                valor = f"{nivel_modelo(s, momento) + ruido:.1f}"
                valor = DEFEITOS.get((s["id"], indice), valor)
                escritor.writerow([momento.strftime("%Y-%m-%d %H:%M"), s["id"], valor])
                momento += INTERVALO
                indice += 1
                total += 1

    # Evento completo do Sarandi (da primeira gota até a água baixar), usado
    # para medir o indicador de impacto: quanto tempo antes o aviso saiu.
    sarandi = dict(SENSORES[0], horas_desde_chuva=24.0)
    with open("dados/evento_completo.csv", "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["data_hora", "sensor_id", "nivel_cm"])
        momento = INICIO
        while momento <= FIM:
            valor = nivel_modelo(sarandi, momento) + random.gauss(0, 1.0)
            escritor.writerow([momento.strftime("%Y-%m-%d %H:%M"), "S01", f"{valor:.1f}"])
            momento += INTERVALO

    print(f"Gerados {len(SENSORES)} sensores e {total} leituras na pasta dados/.")


if __name__ == "__main__":
    main()
