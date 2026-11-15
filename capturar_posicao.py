"""
Mostra a posicao atual do mouse em tempo real.
Posicione o mouse sobre o botao desejado, anote X e Y e coloque no config.json.
Pressione Ctrl+C para sair.
"""
import time

import pyautogui

print("Mova o mouse ate o ponto desejado. Ctrl+C para sair.\n")
try:
    while True:
        x, y = pyautogui.position()
        print(f"\rX: {x:5d}   Y: {y:5d}   ", end="", flush=True)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nOk.")
