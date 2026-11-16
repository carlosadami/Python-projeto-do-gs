# AlertaCheia - lógica em Python

Entrega da disciplina **Computational Thinking with Python** (profa. Maria Clara Martins).

**Integrantes:** Carlos Alberto Adami da Silva Neto (RM571841), _nome completo 2_, _nome completo 3_

## Qual problema da cidade foi escolhido?

Os alagamentos em Porto Alegre. Em maio de 2024, o Guaíba chegou a 5,35 m e cerca de 160 mil pessoas foram afetadas na cidade. Quem mora perto de um arroio, como no Sarandi, costuma perceber o perigo só quando a água já está na porta. Falta um aviso antecipado, por bairro, que diga quanto tempo a pessoa tem.

## O que a solução proposta faz?

Responde à pergunta da atividade, *"Como os dados podem ajudar a compreender este problema da cidade e apoiar uma decisão ou ação?"*:

1. **Armazena e lê** as leituras de nível de cinco sensores (arquivos CSV).
2. **Valida** os dados: descarta leituras vazias, com texto ou fora da faixa do sensor, e informa quais foram descartadas.
3. **Calcula**, para cada bairro: nível atual (média das 3 últimas leituras), velocidade da água em cm/h (reta de mínimos quadrados da última hora), máximo, mínimo e média.
4. **Decide** o nível de risco (normal, atenção, alerta, emergência). Se a água sobe a 30 cm/h ou mais, o risco sobe um degrau.
5. **Prevê** em quantos minutos a água transborda, se continuar na mesma velocidade.
6. **Prioriza** os bairros do mais grave para o mais tranquilo e diz o que o morador deve fazer.
7. **Reconstrói a linha do tempo** de avisos de cada bairro, como se o programa estivesse rodando ao vivo, e **mede o indicador de impacto**: quantos minutos antes do transbordamento o primeiro aviso saiu.
8. **Exporta** o boletim em JSON e CSV e atualiza o site (`web/db.json`).

## Quickstart

Requisito: Python 3.10 ou mais novo.

```bash
pip install -r requirements.txt
python gerar_dados.py              # cria os dados simulados em dados/
python main.py                     # abre o menu
```

Sem menu:

```bash
python main.py --boletim           # mostra o boletim e as orientações
python main.py --historico         # linha do tempo de avisos e indicador de impacto
python main.py --exportar          # salva saida/boletim.json e .csv e atualiza o site
python testes.py                   # confere as regras de decisão
```

Exemplo de saída:

```
Bairro        Risco           Nível       Taxa  Tendência Previsão
Sarandi       EMERGÊNCIA   180.6 cm  +51.0 cm/h  subindo   transborda em cerca de 1 h 10 min
Navegantes    ATENÇÃO       93.4 cm  +36.0 cm/h  subindo   transborda em cerca de 3 h 48 min
Humaitá       ATENÇÃO      136.5 cm  +19.6 cm/h  subindo   transborda em cerca de 4 h 46 min
Menino Deus   ATENÇÃO      130.0 cm  -10.5 cm/h  baixando  sem previsão de transbordar
Cidade Baixa  NORMAL        65.1 cm   -1.6 cm/h  estável   sem previsão de transbordar
```

O Sarandi aparece em emergência com 180,6 cm (limite de alerta) porque a água sobe a 51 cm/h: a regra de subida rápida antecipa o aviso.

## Diferencial: o indicador de impacto é medido, não estimado

`python main.py --historico` repassa uma cheia completa do Sarandi (arquivo `dados/evento_completo.csv`) e registra cada mudança de aviso:

```
LINHA DO TEMPO - Sarandi
  ▃▃▄▄▅▆▆▇▇████████▇▇▇▇▆▆▆▆▅▅▅▅▅▅▄▄▄▄▄▄▄▄▃▃▃▃▃▃▃▃▃▃
  10/11 19:15  NORMAL     -> ATENÇÃO    (nível 107.6 cm)
  10/11 19:45  ATENÇÃO    -> ALERTA     (nível 131.1 cm)
  10/11 21:00  ALERTA     -> EMERGÊNCIA (nível 191.1 cm)
  11/11 02:45  EMERGÊNCIA -> ALERTA     (nível 236.7 cm)
  11/11 06:15  ALERTA     -> ATENÇÃO    (nível 177.6 cm)
  11/11 11:00  ATENÇÃO    -> NORMAL     (nível 119.1 cm)
  INDICADOR DE IMPACTO: o primeiro aviso saiu 180 min antes de a água transbordar.
```

O primeiro aviso sai com 107,6 cm, antes do limite de 120 cm, porque a regra de subida rápida antecipa um degrau. Resultado: 180 minutos de antecedência, três vezes a meta de 60 minutos do projeto.

O boletim exportado também leva as 24 últimas leituras de cada bairro, que o site usa no gráfico "Últimas horas".

## Estrutura

```
python/
  main.py               menu e opções de linha de comando
  gerar_dados.py        cria os dados simulados
  testes.py             testes das regras
  requirements.txt
  alertacheia/
    config.py           limites, textos e parâmetros
    dados.py            leitura e validação dos CSV
    analise.py          cálculos e decisões
    relatorio.py        tela, arquivos, gráfico e integração com o site
  dados/
    sensores.csv        cadastro: id, bairro, local e limites de cada sensor
    leituras.csv        data_hora, sensor_id, nivel_cm (485 linhas)
    evento_completo.csv cheia inteira do Sarandi, para medir o indicador
  saida/
    boletim.json, boletim.csv, grafico_S01.png
```

## Dados utilizados

Todos **simulados**, sem dados pessoais. O script `gerar_dados.py` cria 24 horas de leituras a cada 15 minutos para cinco sensores, usando a curva `h(t) = h0 + c·t²·e^(-t/tau)` estudada no relatório de matemática, com um pequeno ruído aleatório (semente fixa 2026, então os dados são sempre os mesmos). Quatro leituras defeituosas são inseridas de propósito para demonstrar a validação.

## Integração com as outras disciplinas

- **Edge Computing:** o formato das leituras é o mesmo que o ESP32 publica no ThingSpeak.
- **Differentiated Problem Solving:** a velocidade em cm/h é a derivada estimada com dados; a previsão é a aproximação pela reta tangente.
- **Front-end e Web Development:** o boletim alimenta a página inicial do site.
