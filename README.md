# Clicker humanizado com agendamento

Faz cliques em pontos fixos da tela, em horários marcados ou em intervalos, de um jeito parecido com uma pessoa.

## Instalação (Windows)

1. Instale o Python 3.10+ (marque **"Add Python to PATH"**).
2. Na pasta do projeto: `pip install -r requirements.txt`

## Passo a passo

1. Abra o navegador **sempre no mesmo lugar e tamanho** (maximizado) e com zoom 100%.
2. Rode `python capturar_posicao.py`, pare o mouse em cima de cada botão e anote o X e o Y.
3. Coloque as posições e os horários no `config.json`.
4. Teste uma vez agora: `python clicker.py --agora` (espera 3s e executa tudo).
5. Rode para valer: `python clicker.py`. Ele fica rodando até você parar.

## Como parar

- **Ctrl+C** no terminal, ou
- jogue o mouse no **canto superior esquerdo** da tela (failsafe), ou
- crie um arquivo chamado `PARAR` na pasta.

Tudo o que acontece fica salvo em `clicker.log`.

## O que deixa o clique "humano"

| Recurso | O que faz |
|---|---|
| Curva de Bézier | o mouse anda em curva, nunca em linha reta; cada trajeto é diferente |
| Velocidade variável | acelera no começo, desacelera perto do alvo; distância maior leva mais tempo (lei de Fitts) |
| Tremor | pequenos desvios de 1 px durante o movimento |
| Overshoot | às vezes passa um pouco do botão e corrige |
| Erro de mira (`raio`) | clica num ponto aleatório perto do centro, nunca exatamente no mesmo pixel |
| Tempo de clique | botão fica pressionado 50 a 140 ms |
| Deriva | depois do clique, às vezes a mão se mexe um pouco |
| Horário (`variacao_min`) | "08:30" com variação 7 dispara entre 08:23 e 08:37, segundos aleatórios |
| `chance_pular` | de vez em quando pula uma tarefa ou um clique, como alguém que esqueceu |

## Configuração (`config.json`)

**Tarefa em horário fixo**
```json
{
  "nome": "Atualizar painel",
  "horarios": ["08:30", "11:45"],
  "variacao_min": 7,
  "dias": ["seg", "ter", "qua", "qui", "sex"],
  "cliques": [
    { "nome": "botao", "x": 1210, "y": 340, "raio": 5,
      "espera_antes": [0.5, 2.0], "espera_depois": [1.0, 3.0] }
  ]
}
```

**Tarefa em intervalo** (ex.: a cada 12 a 25 min, só das 8h às 18h)
```json
{ "nome": "Manter sessao", "intervalo_min": [12, 25], "janela": ["08:00", "18:00"], "cliques": [ ... ] }
```

Opções de cada clique: `x`, `y`, `raio`, `espera_antes`, `espera_depois`, `botao` (`left`/`right`),
`duplo` (true/false), `texto` (digita com ritmo humano), `enter` (true/false), `chance_pular` (0 a 1).
Valores em `[min, max]` são sorteados a cada vez.

## Cuidados

- **O computador não pode bloquear/hibernar** e o navegador precisa ficar visível, na frente, no mesmo lugar.
  Clique por coordenada é "cego": se a janela mudar, ele clica no lugar errado.
- No Windows com escala de tela diferente de 100%, capture as posições com o `capturar_posicao.py`
  (ele já usa a mesma escala do clicker).
- Para iniciar sozinho com o Windows: crie um atalho para `pythonw clicker.py` na pasta
  `shell:startup`, ou use o Agendador de Tarefas.
