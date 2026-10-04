#!/usr/bin/env python3
"""
Descobre em quais pinos GPIO os botões estão ligados.

Uso:
    sudo systemctl stop video-botoes      # libera os pinos, se o player estiver rodando
    python3 encontrar_pinos.py            # botões ligados ao GND (mais comum)
    python3 encontrar_pinos.py --3v3      # se nada aparecer: botões ligados ao 3.3V

Aperte um botão de cada vez e anote o número GPIO mostrado.
Ctrl+C para sair.
"""

import signal
import sys

from gpiozero import Button

# Pino físico (1-40) de cada GPIO, para facilitar a conferência na placa
PINO_FISICO = {
    2: 3, 3: 5, 4: 7, 5: 29, 6: 31, 7: 26, 8: 24, 9: 21, 10: 19, 11: 23,
    12: 32, 13: 33, 14: 8, 15: 10, 16: 36, 17: 11, 18: 12, 19: 35, 20: 38,
    21: 40, 22: 15, 23: 16, 24: 18, 25: 22, 26: 37, 27: 13,
}

ligado_ao_gnd = "--3v3" not in sys.argv
modo = "GND" if ligado_ao_gnd else "3.3V"
print(f"Monitorando todos os GPIOs (botões ligados ao {modo}).")
print("Aperte cada botão, um de cada vez. Ctrl+C para sair.\n")

botoes = []
for gpio, fisico in PINO_FISICO.items():
    try:
        b = Button(gpio, pull_up=ligado_ao_gnd, bounce_time=0.05)
    except Exception as e:  # pino ocupado por outra função
        print(f"  (GPIO{gpio} ignorado: {e})")
        continue
    b.when_pressed = lambda g=gpio, f=fisico: print(
        f">>> Botão detectado no GPIO{g}  (pino físico {f})", flush=True
    )
    botoes.append(b)

signal.pause()
