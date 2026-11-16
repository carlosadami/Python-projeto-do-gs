"""Testes simples das regras de decisão.  Uso:  python testes.py"""

from datetime import datetime, timedelta

from alertacheia import analise, dados

LIMITES = {"ATENCAO": 120, "ALERTA": 180, "EMERGENCIA": 240}


def serie(niveis, minutos=15):
    """Monta uma lista de leituras a partir de uma lista de níveis."""
    inicio = datetime(2026, 11, 11, 12, 0)
    return [{"momento": inicio + timedelta(minutes=minutos * i), "nivel_cm": n}
            for i, n in enumerate(niveis)]


def testar():
    # Classificação pelos limites
    assert analise.classificar(100, 0, LIMITES) == ("NORMAL", False)
    assert analise.classificar(120, 0, LIMITES) == ("ATENCAO", False)
    assert analise.classificar(200, 0, LIMITES) == ("ALERTA", False)
    assert analise.classificar(250, 0, LIMITES) == ("EMERGENCIA", False)

    # Subida rápida antecipa um degrau, mas não passa de EMERGENCIA
    assert analise.classificar(100, 35, LIMITES) == ("ATENCAO", True)
    assert analise.classificar(250, 35, LIMITES) == ("EMERGENCIA", True)

    # Taxa: 10 cm a cada 15 min = 40 cm/h
    assert round(analise.taxa_de_subida(serie([100, 110, 120, 130, 140])), 1) == 40.0
    assert analise.taxa_de_subida(serie([100])) == 0.0

    # Previsão: faltam 40 cm a 40 cm/h = 60 min
    assert analise.minutos_ate_transbordar(200, 40, LIMITES) == 60
    assert analise.minutos_ate_transbordar(200, -5, LIMITES) is None

    # Validação das leituras
    assert dados.leitura_valida("153.2")
    assert not dados.leitura_valida("-1")
    assert not dados.leitura_valida("999")
    assert not dados.leitura_valida("")
    assert not dados.leitura_valida("erro")

    print("Todos os testes passaram.")


if __name__ == "__main__":
    testar()
