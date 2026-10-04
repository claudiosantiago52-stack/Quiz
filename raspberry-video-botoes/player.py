#!/usr/bin/env python3
"""
Player de vídeos por botões para Raspberry Pi.

- Ao ligar: tela preta, aguardando.
- Botão N apertado: toca o vídeo N (se outro vídeo estiver tocando, ele é
  interrompido e o novo começa).
- Fim do vídeo: volta para a tela preta e aguarda o próximo botão.

Usa um único processo do mpv que fica sempre aberto (tela preta quando ocioso)
e recebe comandos por um socket. Assim não aparece o terminal entre vídeos.
"""

import configparser
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time

from gpiozero import Button

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_CONFIG = os.path.join(PASTA_SCRIPT, "config.ini")
SOCKET_MPV = "/tmp/video-botoes-mpv.sock"

SAIDAS_AUDIO = {
    "p2": "alsa/plughw:CARD=Headphones,DEV=0",
    "hdmi": "alsa/plughw:CARD=vc4hdmi,DEV=0",
}


def log(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), msg, flush=True)


def ler_config():
    cfg = configparser.ConfigParser()
    if not cfg.read(ARQUIVO_CONFIG, encoding="utf-8"):
        sys.exit(f"Arquivo de configuração não encontrado: {ARQUIVO_CONFIG}")

    pasta = os.path.expanduser(cfg.get("videos", "pasta", fallback="~/videos"))
    botoes = []
    for n in (1, 2, 3):
        pino = cfg.getint("botoes", f"botao{n}")
        video = os.path.join(pasta, cfg.get("videos", f"video{n}"))
        botoes.append((n, pino, video))

    return {
        "botoes": botoes,
        "ligado_ao_gnd": cfg.getboolean("botoes", "ligado_ao_gnd", fallback=True),
        "saida_audio": cfg.get("audio", "saida", fallback="p2").strip().lower(),
        "volume": cfg.getint("audio", "volume", fallback=100),
    }


class Mpv:
    """Mantém um mpv aberto em tela cheia e envia comandos a ele."""

    def __init__(self, saida_audio, volume):
        self.saida_audio = saida_audio
        self.volume = volume
        self.proc = None
        self.lock = threading.Lock()

    def iniciar(self):
        if os.path.exists(SOCKET_MPV):
            os.remove(SOCKET_MPV)

        cmd = [
            "mpv",
            "--idle=yes",              # fica aberto mesmo sem vídeo
            "--force-window=yes",      # mantém a tela (preta) ocupada
            "--fullscreen",
            "--vo=gpu",
            "--gpu-context=drm",       # desenha direto na tela, sem desktop
            "--hwdec=auto-safe",       # decodificação por hardware quando possível
            "--no-osc",                # sem barra de controle / logo do mpv
            "--osd-level=0",
            "--no-input-default-bindings",
            "--input-vo-keyboard=no",
            "--cursor-autohide=always",
            "--keep-open=no",          # ao terminar, volta para a tela preta
            "--no-terminal",
            f"--volume={self.volume}",
            f"--input-ipc-server={SOCKET_MPV}",
        ]
        if self.saida_audio == "nenhum":
            cmd.append("--no-audio")
        elif self.saida_audio in SAIDAS_AUDIO:
            cmd.append(f"--audio-device={SAIDAS_AUDIO[self.saida_audio]}")

        log("Iniciando mpv...")
        self.proc = subprocess.Popen(cmd)

        for _ in range(100):  # espera até 10 s o socket aparecer
            if os.path.exists(SOCKET_MPV):
                log("mpv pronto (tela preta).")
                return
            if self.proc.poll() is not None:
                break
            time.sleep(0.1)
        log("AVISO: mpv não abriu o socket de controle.")

    def rodando(self):
        return self.proc is not None and self.proc.poll() is None

    def comando(self, *args):
        msg = json.dumps({"command": list(args)}) + "\n"
        with self.lock:
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect(SOCKET_MPV)
                    s.sendall(msg.encode("utf-8"))
            except OSError as e:
                log(f"Erro ao enviar comando ao mpv: {e}")

    def tocar(self, arquivo):
        # "replace" interrompe o vídeo atual (se houver) e começa o novo
        self.comando("loadfile", arquivo, "replace")

    def parar(self):
        if self.rodando():
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def main():
    cfg = ler_config()
    mpv = Mpv(cfg["saida_audio"], cfg["volume"])
    mpv.iniciar()

    botoes = []
    for n, pino, video in cfg["botoes"]:
        if not os.path.isfile(video):
            log(f"AVISO: vídeo do botão {n} não encontrado: {video}")

        botao = Button(pino, pull_up=cfg["ligado_ao_gnd"], bounce_time=0.05)

        def ao_apertar(n=n, video=video):
            log(f"Botão {n} apertado -> {os.path.basename(video)}")
            if os.path.isfile(video):
                mpv.tocar(video)
            else:
                log(f"ERRO: arquivo não existe: {video}")

        botao.when_pressed = ao_apertar
        botoes.append(botao)
        log(f"Botão {n}: GPIO{pino} -> {video}")

    def encerrar(*_):
        log("Encerrando...")
        mpv.parar()
        sys.exit(0)

    signal.signal(signal.SIGTERM, encerrar)
    signal.signal(signal.SIGINT, encerrar)

    log("Aguardando botões.")
    while True:
        if not mpv.rodando():
            log("mpv parou inesperadamente; reiniciando em 2 s.")
            time.sleep(2)
            mpv.iniciar()
        time.sleep(1)


if __name__ == "__main__":
    main()
