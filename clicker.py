"""
Clicker humanizado com agendamento.

Faz cliques em posicoes da tela em horarios marcados (ou em intervalos),
com movimento de mouse em curva, velocidade variavel, pequenos tremores,
erro de mira, overshoot ocasional e atrasos aleatorios.

Como parar:
  - Ctrl+C no terminal
  - Jogar o mouse rapidamente no canto SUPERIOR ESQUERDO da tela (failsafe)
  - Criar um arquivo chamado PARAR na mesma pasta do script

Uso:
  python clicker.py                # usa config.json
  python clicker.py outro.json     # usa outro arquivo de configuracao
  python clicker.py --agora        # executa todas as tarefas uma vez, ja (teste)
"""

import json
import logging
import math
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pyautogui

PASTA = Path(__file__).resolve().parent
ARQUIVO_PARAR = PASTA / "PARAR"

pyautogui.FAILSAFE = True  # mouse no canto superior esquerdo = aborta
pyautogui.PAUSE = 0        # controlamos as pausas manualmente

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%d/%m %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PASTA / "clicker.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("clicker")

DIAS = {"seg": 0, "ter": 1, "qua": 2, "qui": 3, "sex": 4, "sab": 5, "dom": 6}


class Parar(Exception):
    pass


# --------------------------------------------------------------------------
# Utilidades de aleatoriedade
# --------------------------------------------------------------------------
def entre(faixa):
    """Aceita numero fixo ou [min, max] e devolve um valor aleatorio."""
    if isinstance(faixa, (list, tuple)):
        return random.uniform(faixa[0], faixa[1])
    return float(faixa)


def dormir(segundos):
    """Sleep que checa o pedido de parada a cada 0,5s."""
    fim = time.monotonic() + max(0.0, segundos)
    while True:
        checar_parada()
        resto = fim - time.monotonic()
        if resto <= 0:
            return
        time.sleep(min(0.5, resto))


def checar_parada():
    if ARQUIVO_PARAR.exists():
        raise Parar("arquivo PARAR encontrado")


# --------------------------------------------------------------------------
# Movimento humano do mouse
# --------------------------------------------------------------------------
def _bezier(p0, p1, p2, p3, t):
    u = 1 - t
    x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
    y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
    return x, y


def _easing(t, k):
    """Acelera no comeco e desacelera no fim, como uma mao de verdade.
    k varia a cada movimento para o perfil de velocidade nunca ser igual."""
    if t < 0.5:
        return 0.5 * (2 * t) ** k
    return 1 - 0.5 * (2 * (1 - t)) ** k


def _trajeto(origem, destino, cfg):
    ox, oy = origem
    dx, dy = destino
    dist = math.hypot(dx - ox, dy - oy)
    if dist < 2:
        return

    # pontos de controle deslocados perpendicularmente -> curva natural
    curva = dist * random.uniform(0.05, 0.30) * random.choice([-1, 1])
    ang = math.atan2(dy - oy, dx - ox) + math.pi / 2
    px, py = math.cos(ang) * curva, math.sin(ang) * curva
    c1 = (ox + (dx - ox) * random.uniform(0.2, 0.4) + px * random.uniform(0.5, 1.2),
          oy + (dy - oy) * random.uniform(0.2, 0.4) + py * random.uniform(0.5, 1.2))
    c2 = (ox + (dx - ox) * random.uniform(0.6, 0.8) + px * random.uniform(0.3, 1.0),
          oy + (dy - oy) * random.uniform(0.6, 0.8) + py * random.uniform(0.3, 1.0))

    # duracao inspirada na lei de Fitts: longe = mais tempo, mas nao linear
    vel = entre(cfg.get("velocidade", [0.8, 1.3]))
    duracao = (0.18 + 0.11 * math.log2(1 + dist / 12)) / vel
    passos = max(12, int(duracao * random.uniform(70, 110)))

    tremor = cfg.get("tremor_px", 1.0)
    k = random.uniform(1.6, 2.6)
    for i in range(1, passos + 1):
        x, y = _bezier(origem, c1, c2, destino, _easing(i / passos, k))
        if i < passos:
            x += random.gauss(0, tremor)
            y += random.gauss(0, tremor)
        pyautogui.moveTo(round(x), round(y), _pause=False)
        time.sleep(duracao / passos * random.uniform(0.7, 1.3))


def mover_humano(x, y, cfg):
    checar_parada()
    origem = pyautogui.position()
    dist = math.hypot(x - origem[0], y - origem[1])

    # as vezes passa um pouco do ponto e corrige
    if dist > 150 and random.random() < cfg.get("chance_overshoot", 0.25):
        excesso = random.uniform(4, 14)
        ang = math.atan2(y - origem[1], x - origem[0]) + random.uniform(-0.4, 0.4)
        ponto = (x + math.cos(ang) * excesso, y + math.sin(ang) * excesso)
        _trajeto(origem, ponto, cfg)
        time.sleep(random.uniform(0.04, 0.12))
        _trajeto(pyautogui.position(), (x, y), {**cfg, "velocidade": [0.5, 0.8]})
    else:
        _trajeto(origem, (x, y), cfg)


def clicar_humano(acao, cfg):
    raio = acao.get("raio", cfg.get("raio_padrao", 4))
    # distribuicao gaussiana: maioria perto do centro, as vezes mais longe
    x = acao["x"] + max(-raio, min(raio, random.gauss(0, raio / 2)))
    y = acao["y"] + max(-raio, min(raio, random.gauss(0, raio / 2)))
    x, y = round(x), round(y)

    dormir(entre(acao.get("espera_antes", [0.3, 1.2])))
    mover_humano(x, y, cfg)
    time.sleep(random.uniform(0.06, 0.25))  # "mira" antes de clicar

    botao = acao.get("botao", "left")
    vezes = 2 if acao.get("duplo") else 1
    for n in range(vezes):
        pyautogui.mouseDown(button=botao, _pause=False)
        time.sleep(random.uniform(0.05, 0.14))
        pyautogui.mouseUp(button=botao, _pause=False)
        if n < vezes - 1:
            time.sleep(random.uniform(0.07, 0.15))

    if acao.get("texto"):
        time.sleep(random.uniform(0.2, 0.5))
        for ch in acao["texto"]:
            pyautogui.write(ch, _pause=False)
            time.sleep(random.uniform(0.05, 0.22))
        if acao.get("enter"):
            time.sleep(random.uniform(0.15, 0.4))
            pyautogui.press("enter", _pause=False)

    log.info("   clique em (%d, %d)%s", x, y, f"  [{acao['nome']}]" if acao.get("nome") else "")

    # pequena "deriva" da mao depois do clique
    if random.random() < 0.5:
        mx, my = pyautogui.position()
        _trajeto((mx, my), (mx + random.randint(-25, 25), my + random.randint(-15, 15)),
                 {**cfg, "velocidade": [0.4, 0.7]})

    dormir(entre(acao.get("espera_depois", [0.4, 1.5])))


def executar_tarefa(tarefa, cfg):
    log.info("> Executando tarefa: %s", tarefa["nome"])
    if random.random() < tarefa.get("chance_pular", 0.0):
        log.info("   (pulada aleatoriamente desta vez)")
        return
    for acao in tarefa["cliques"]:
        if random.random() < acao.get("chance_pular", 0.0):
            log.info("   pulou clique %s", acao.get("nome", ""))
            continue
        clicar_humano(acao, cfg)
    log.info("< Tarefa concluida: %s", tarefa["nome"])


# --------------------------------------------------------------------------
# Agendamento
# --------------------------------------------------------------------------
def proximo_horario(tarefa, depois_de):
    """Calcula o proximo disparo (ja com a aleatoriedade aplicada)."""
    var = tarefa.get("variacao_min", 0)
    dias = {DIAS[d] for d in tarefa.get("dias", list(DIAS))}

    if "intervalo_min" in tarefa:
        base = entre(tarefa["intervalo_min"])
        alvo = depois_de + timedelta(minutes=base + random.uniform(-var, var))
        inicio, fim = tarefa.get("janela", ["00:00", "23:59"])
        for _ in range(8):
            h0 = datetime.combine(alvo.date(), datetime.strptime(inicio, "%H:%M").time())
            h1 = datetime.combine(alvo.date(), datetime.strptime(fim, "%H:%M").time())
            if alvo.weekday() in dias and h0 <= alvo <= h1:
                return alvo
            if alvo < h0 and alvo.weekday() in dias:
                alvo = h0 + timedelta(minutes=random.uniform(0, max(var, 1)))
            else:
                alvo = datetime.combine(alvo.date() + timedelta(days=1), h0.time()) \
                    + timedelta(minutes=random.uniform(0, max(var, 1)))
        return alvo

    # cada horario-base ("08:30" de um dia) so pode disparar uma vez,
    # mesmo que o sorteio jogue o disparo para antes ou depois dele
    ultimo_base = tarefa.get("_ultimo_base")
    for dia in range(0, 9):
        data = (depois_de + timedelta(days=dia)).date()
        if data.weekday() not in dias:
            continue
        for h in sorted(tarefa["horarios"]):
            base = datetime.combine(data, datetime.strptime(h, "%H:%M").time())
            if ultimo_base and base <= ultimo_base:
                continue
            if base + timedelta(minutes=var) < depois_de:
                continue  # horario ja passou por completo
            alvo = base + timedelta(minutes=random.uniform(-var, var),
                                    seconds=random.uniform(0, 59))
            tarefa["_ultimo_base"] = base
            return max(alvo, depois_de)
    return None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    caminho = Path(args[0]) if args else PASTA / "config.json"
    cfg = json.loads(caminho.read_text(encoding="utf-8"))
    geral = cfg.get("geral", {})
    tarefas = [t for t in cfg["tarefas"] if t.get("ativa", True)]

    if ARQUIVO_PARAR.exists():
        ARQUIVO_PARAR.unlink()

    log.info("Clicker iniciado com %d tarefa(s). Ctrl+C ou mouse no canto superior "
             "esquerdo para parar.", len(tarefas))

    try:
        if "--agora" in sys.argv:
            dormir(3)
            for t in tarefas:
                executar_tarefa(t, geral)
            return

        agenda = {}
        agora = datetime.now()
        for t in tarefas:
            agenda[t["nome"]] = proximo_horario(t, agora)
            log.info("  %-25s proxima execucao: %s", t["nome"],
                     agenda[t["nome"]].strftime("%d/%m %H:%M:%S") if agenda[t["nome"]] else "-")

        while True:
            pendentes = [(h, t) for t in tarefas if (h := agenda[t["nome"]])]
            if not pendentes:
                log.info("Nenhuma tarefa agendada. Encerrando.")
                return
            quando, tarefa = min(pendentes, key=lambda p: p[0])
            espera = (quando - datetime.now()).total_seconds()
            if espera > 0:
                dormir(espera)
            executar_tarefa(tarefa, geral)
            agenda[tarefa["nome"]] = proximo_horario(tarefa, datetime.now())
            log.info("  %-25s proxima execucao: %s", tarefa["nome"],
                     agenda[tarefa["nome"]].strftime("%d/%m %H:%M:%S"))

    except KeyboardInterrupt:
        log.info("Parado pelo usuario (Ctrl+C).")
    except pyautogui.FailSafeException:
        log.info("Parado pelo failsafe (mouse no canto da tela).")
    except Parar as e:
        log.info("Parado: %s.", e)
        ARQUIVO_PARAR.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
