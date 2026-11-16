"""Saídas do programa: tela, arquivos e integração com o site."""

import csv
import json
import os

ROTULOS = {
    "NORMAL": "NORMAL",
    "ATENCAO": "ATENÇÃO",
    "ALERTA": "ALERTA",
    "EMERGENCIA": "EMERGÊNCIA",
}


def texto_previsao(item):
    """Frase curta sobre o tempo que falta para a água transbordar."""
    minutos = item["minutos_ate_emergencia"]
    if item["risco"] == "EMERGENCIA" and minutos is None:
        return "nível de emergência atingido"
    if minutos is None:
        return "sem previsão de transbordar"
    if minutos < 60:
        return f"transborda em cerca de {minutos} min"
    return f"transborda em cerca de {minutos // 60} h {minutos % 60:02d} min"


def mostrar_boletim(boletim):
    """Imprime o boletim em formato de tabela no terminal."""
    print()
    print("BOLETIM ALERTACHEIA - situação por bairro (mais grave primeiro)")
    print("-" * 86)
    print(f"{'Bairro':<14}{'Risco':<12}{'Nível':>9}{'Taxa':>11}  {'Tendência':<10}Previsão")
    print("-" * 86)
    for item in boletim:
        print(f"{item['bairro']:<14}{ROTULOS[item['risco']]:<12}"
              f"{item['nivel_cm']:>6.1f} cm{item['taxa_cm_h']:>+7.1f} cm/h  "
              f"{item['tendencia']:<10}{texto_previsao(item)}")
    print("-" * 86)


def mostrar_acoes(boletim):
    """Lista, para cada bairro fora do normal, o que o morador deve fazer."""
    fora_do_normal = [item for item in boletim if item["risco"] != "NORMAL"]
    print()
    if not fora_do_normal:
        print("Todos os bairros monitorados estão em situação normal.")
        return
    print("O QUE FAZER AGORA")
    for item in fora_do_normal:
        aviso = " (água subindo rápido)" if item["subida_rapida"] else ""
        print(f"- {item['bairro']} [{ROTULOS[item['risco']]}]{aviso}: {item['acao']}")


def mostrar_detalhes(item):
    """Mostra as estatísticas completas de um bairro."""
    print()
    print(f"{item['bairro']} - {item['local']}")
    print(f"  Atualizado em ....... {item['atualizado_em']}")
    print(f"  Risco ............... {ROTULOS[item['risco']]}")
    print(f"  Nível atual ......... {item['nivel_cm']} cm")
    print(f"  Velocidade .......... {item['taxa_cm_h']:+} cm/h ({item['tendencia']})")
    print(f"  Previsão ............ {texto_previsao(item)}")
    print(f"  Máximo no período ... {item['maximo_cm']} cm")
    print(f"  Mínimo no período ... {item['minimo_cm']} cm")
    print(f"  Média no período .... {item['media_cm']} cm")
    print(f"  Leituras válidas .... {item['leituras_validas']}")
    print(f"  Orientação .......... {item['acao']}")


def mostrar_qualidade(leituras_por_sensor, descartadas):
    """Resume quantas leituras foram aproveitadas e quantas foram descartadas."""
    total_validas = sum(len(lista) for lista in leituras_por_sensor.values())
    print()
    print(f"Leituras aproveitadas: {total_validas}")
    print(f"Leituras descartadas:  {len(descartadas)}")
    for item in descartadas:
        valor = item["valor"] if item["valor"] != "" else "(vazio)"
        print(f"  linha {item['linha']}: sensor {item['sensor']} enviou {valor}")


BARRAS = "▁▂▃▄▅▆▇█"


def minigrafico(leituras, teto, largura=48):
    """Desenha o nível ao longo do tempo com caracteres, direto no terminal.

    A escala vai de zero até o limite de emergência (teto): barra cheia
    significa que a água chegou ao nível de transbordamento.
    """
    niveis = [l["nivel_cm"] for l in leituras]
    passo = max(1, len(niveis) // largura)
    amostra = niveis[::passo]
    return "".join(BARRAS[min(len(BARRAS) - 1, int(n / teto * (len(BARRAS) - 1)))]
                   for n in amostra)


def mostrar_linha_do_tempo(sensor, leituras, eventos, antecedencia):
    """Mostra o histórico de avisos de um bairro e o indicador de impacto."""
    print()
    print(f"LINHA DO TEMPO - {sensor['bairro']}")
    print(f"  {minigrafico(leituras, sensor['limites']['EMERGENCIA'])}")
    print(f"  de {leituras[0]['momento']:%d/%m %H:%M} até {leituras[-1]['momento']:%d/%m %H:%M}")
    if not eventos:
        print("  Nenhuma mudança de risco no período.")
    for evento in eventos:
        print(f"  {evento['momento']:%d/%m %H:%M}  {ROTULOS[evento['de']]:<10} -> "
              f"{ROTULOS[evento['para']]:<10} (nível {evento['nivel_cm']} cm)")
    if antecedencia is not None:
        print(f"  INDICADOR DE IMPACTO: o primeiro aviso saiu {antecedencia} min "
              f"antes de a água transbordar.")
    else:
        print("  A água não transbordou neste período.")


def salvar_json(boletim, caminho):
    """Grava o boletim em JSON (formato que o site consegue ler)."""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(boletim, arquivo, ensure_ascii=False, indent=2)


def salvar_csv(boletim, caminho):
    """Grava o boletim em CSV (abre no Excel ou Google Planilhas)."""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        # O histórico é uma lista e não cabe em uma célula: fica só no JSON.
        colunas = [coluna for coluna in boletim[0].keys() if coluna != "historico"]
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(boletim)


def exportar_para_site(boletim, caminho_db):
    """Atualiza a lista "bairros" do db.json usado pelo json-server do site.

    As outras listas do arquivo (relatos, abrigos) são mantidas como estão.
    """
    with open(caminho_db, encoding="utf-8") as arquivo:
        banco = json.load(arquivo)

    banco["bairros"] = []
    for item in boletim:
        registro = dict(item)
        registro["id"] = item["sensor_id"]
        banco["bairros"].append(registro)

    with open(caminho_db, "w", encoding="utf-8") as arquivo:
        json.dump(banco, arquivo, ensure_ascii=False, indent=2)
        arquivo.write("\n")


def salvar_grafico(sensor, leituras, caminho):
    """Desenha o nível ao longo do tempo com as linhas de cada limite."""
    import matplotlib
    matplotlib.use("Agg")  # gera o arquivo sem precisar abrir janela
    import matplotlib.pyplot as plt

    momentos = [leitura["momento"] for leitura in leituras]
    niveis = [leitura["nivel_cm"] for leitura in leituras]
    estilos = {"ATENCAO": ("#8A5A00", ":"), "ALERTA": ("#C2500B", "--"),
               "EMERGENCIA": ("#B3261E", "-")}

    figura, eixo = plt.subplots(figsize=(9, 4.5))
    eixo.plot(momentos, niveis, color="#0F5C7A", linewidth=2, label="Nível medido")
    for nome, (cor, traco) in estilos.items():
        eixo.axhline(sensor["limites"][nome], color=cor, linestyle=traco,
                     label=f"{ROTULOS[nome].capitalize()} ({sensor['limites'][nome]:.0f} cm)")
    eixo.set_title(f"Nível da água - {sensor['bairro']} ({sensor['local']})")
    eixo.set_xlabel("Data e hora")
    eixo.set_ylabel("Nível (cm)")
    eixo.grid(alpha=0.3)
    eixo.legend(loc="upper left")
    figura.autofmt_xdate()
    figura.tight_layout()
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    figura.savefig(caminho, dpi=130)
    plt.close(figura)
