"""Cálculos e decisões: é aqui que os dados viram orientação para o morador."""

from alertacheia import config


def media(valores):
    """Média aritmética simples."""
    return sum(valores) / len(valores)


def nivel_atual(leituras):
    """Média das últimas leituras, para não reagir a um único valor com ruído."""
    ultimas = leituras[-config.LEITURAS_NA_MEDIA:]
    return media([leitura["nivel_cm"] for leitura in ultimas])


def taxa_de_subida(leituras):
    """Velocidade da água em cm por hora na última hora.

    Usa a inclinação da reta que melhor se ajusta aos pontos (mínimos
    quadrados). É a versão "com dados reais" da derivada estudada em
    Differentiated Problem Solving: quanto o nível muda por unidade de tempo.
    """
    fim = leituras[-1]["momento"]
    recentes = [
        leitura for leitura in leituras
        if (fim - leitura["momento"]).total_seconds() / 60 <= config.JANELA_TAXA_MIN
    ]
    if len(recentes) < 2:
        return 0.0

    horas = [(leitura["momento"] - recentes[0]["momento"]).total_seconds() / 3600
             for leitura in recentes]
    niveis = [leitura["nivel_cm"] for leitura in recentes]
    media_h = media(horas)
    media_n = media(niveis)

    numerador = sum((h - media_h) * (n - media_n) for h, n in zip(horas, niveis))
    denominador = sum((h - media_h) ** 2 for h in horas)
    if denominador == 0:
        return 0.0
    return numerador / denominador


def classificar(nivel, taxa, limites):
    """Decide o nível de risco a partir do nível da água e da velocidade."""
    if nivel >= limites["EMERGENCIA"]:
        risco = "EMERGENCIA"
    elif nivel >= limites["ALERTA"]:
        risco = "ALERTA"
    elif nivel >= limites["ATENCAO"]:
        risco = "ATENCAO"
    else:
        risco = "NORMAL"

    # Água subindo rápido: antecipa o aviso em um degrau.
    subida_rapida = taxa >= config.TAXA_SUBIDA_RAPIDA
    if subida_rapida and risco != "EMERGENCIA":
        risco = config.NIVEIS[config.NIVEIS.index(risco) + 1]
    return risco, subida_rapida


def minutos_ate_transbordar(nivel, taxa, limites):
    """Estima em quantos minutos a água chega ao nível de emergência.

    Devolve None quando a água não está subindo ou já transbordou.
    """
    falta = limites["EMERGENCIA"] - nivel
    if taxa <= 0 or falta <= 0:
        return None
    return round(falta / taxa * 60)


def tendencia(taxa):
    """Traduz a taxa em uma palavra que qualquer pessoa entende."""
    if taxa >= 5:
        return "subindo"
    if taxa <= -5:
        return "baixando"
    return "estável"


def analisar_sensor(sensor, leituras):
    """Junta todos os cálculos de um sensor em um único resultado."""
    nivel = nivel_atual(leituras)
    taxa = taxa_de_subida(leituras)
    risco, subida_rapida = classificar(nivel, taxa, sensor["limites"])
    niveis = [leitura["nivel_cm"] for leitura in leituras]
    return {
        "sensor_id": sensor["id"],
        "bairro": sensor["bairro"],
        "local": sensor["local"],
        "atualizado_em": leituras[-1]["momento"].strftime("%Y-%m-%d %H:%M"),
        "nivel_cm": round(nivel, 1),
        "taxa_cm_h": round(taxa, 1),
        "tendencia": tendencia(taxa),
        "risco": risco,
        "subida_rapida": subida_rapida,
        "minutos_ate_emergencia": minutos_ate_transbordar(nivel, taxa, sensor["limites"]),
        "acao": config.ACOES[risco],
        "maximo_cm": max(niveis),
        "minimo_cm": min(niveis),
        "media_cm": round(media(niveis), 1),
        "leituras_validas": len(leituras),
        "atencao_cm": sensor["limites"]["ATENCAO"],
        "alerta_cm": sensor["limites"]["ALERTA"],
        "emergencia_cm": sensor["limites"]["EMERGENCIA"],
        "historico": historico_recente(leituras),
    }


def gerar_boletim(sensores, leituras_por_sensor):
    """Analisa todos os sensores e ordena do mais grave para o mais tranquilo."""
    boletim = []
    for sensor_id, sensor in sensores.items():
        leituras = leituras_por_sensor.get(sensor_id, [])
        if leituras:
            boletim.append(analisar_sensor(sensor, leituras))

    def prioridade(item):
        gravidade = config.NIVEIS.index(item["risco"])
        tempo = item["minutos_ate_emergencia"]
        # Mais grave primeiro; no empate, quem transborda antes.
        return (-gravidade, tempo if tempo is not None else float("inf"))

    boletim.sort(key=prioridade)
    return boletim


# ----------------------------------------------------------------------
# Diferencial: linha do tempo e indicador de impacto medido nos dados
# ----------------------------------------------------------------------

def linha_do_tempo(sensor, leituras):
    """Refaz o histórico do sensor e registra cada mudança de risco.

    Para cada horário, analisa só as leituras que existiam até ali, como se
    o programa estivesse rodando ao vivo. Devolve uma lista de eventos
    {"momento", "de", "para", "nivel_cm"}.
    """
    eventos = []
    risco_anterior = "NORMAL"
    for fim in range(config.LEITURAS_NA_MEDIA, len(leituras) + 1):
        ate_agora = leituras[:fim]
        nivel = nivel_atual(ate_agora)
        taxa = taxa_de_subida(ate_agora)
        risco, _ = classificar(nivel, taxa, sensor["limites"])
        if risco != risco_anterior:
            eventos.append({
                "momento": ate_agora[-1]["momento"],
                "de": risco_anterior,
                "para": risco,
                "nivel_cm": round(nivel, 1),
            })
            risco_anterior = risco
    return eventos


def antecedencia_minutos(sensor, leituras, eventos):
    """Indicador de impacto: minutos entre o primeiro aviso e o transbordamento.

    O transbordamento é o primeiro horário em que o nível MEDIDO passa do
    limite de emergência. Devolve None se a água não transbordou no período.
    """
    primeiro_aviso = next((e["momento"] for e in eventos if e["para"] != "NORMAL"), None)
    transbordou = next((l["momento"] for l in leituras
                        if l["nivel_cm"] >= sensor["limites"]["EMERGENCIA"]), None)
    if primeiro_aviso is None or transbordou is None or transbordou < primeiro_aviso:
        return None
    return round((transbordou - primeiro_aviso).total_seconds() / 60)


def historico_recente(leituras, quantidade=24):
    """Últimas leituras em formato simples, para o gráfico do site."""
    return [{"hora": l["momento"].strftime("%H:%M"), "nivel_cm": l["nivel_cm"]}
            for l in leituras[-quantidade:]]
