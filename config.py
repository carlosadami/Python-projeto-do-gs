"""Regras e textos usados em todo o programa.

Ficam em um único lugar para que o Python, o ESP32 e o site usem
exatamente os mesmos níveis de risco.
"""

# Ordem dos níveis de risco, do mais leve ao mais grave.
NIVEIS = ["NORMAL", "ATENCAO", "ALERTA", "EMERGENCIA"]

# Se a água sobe mais rápido que isso (cm por hora), o risco sobe um degrau.
TAXA_SUBIDA_RAPIDA = 30.0

# Quantos minutos para trás olhamos para calcular a velocidade da água.
JANELA_TAXA_MIN = 60

# Quantas leituras recentes entram na média do "nível atual".
LEITURAS_NA_MEDIA = 3

# Faixa de valores que o sensor ultrassônico consegue medir (cm).
NIVEL_MINIMO_VALIDO = 0.0
NIVEL_MAXIMO_VALIDO = 400.0

# O que o morador deve fazer em cada nível (linguagem simples).
ACOES = {
    "NORMAL": "Siga a rotina. Nenhuma ação necessária.",
    "ATENCAO": "Fique de olho no aplicativo e deixe documentos e remédios à mão.",
    "ALERTA": "Suba móveis e eletrodomésticos, avise os vizinhos e prepare a saída.",
    "EMERGENCIA": "Saia agora para o ponto de apoio mais próximo. Ligue 199 (Defesa Civil).",
}
