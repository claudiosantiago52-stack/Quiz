#!/bin/bash
# Instala o player de vídeos por botões no Raspberry Pi OS Lite.
# Uso:  bash instalar.sh      (NÃO use sudo; o script pede quando precisa)
set -e

USUARIO="$(whoami)"
if [ "$USUARIO" = "root" ]; then
    echo "Rode sem sudo:  bash instalar.sh"
    exit 1
fi

ORIGEM="$(cd "$(dirname "$0")" && pwd)"
DESTINO="$HOME/video-botoes"
PASTA_VIDEOS="$HOME/videos"

echo "==> 1/6 Instalando programas (mpv, gpiozero)..."
sudo apt-get update
sudo apt-get install -y mpv python3-gpiozero python3-lgpio alsa-utils

echo "==> 2/6 Copiando arquivos para $DESTINO ..."
mkdir -p "$DESTINO" "$PASTA_VIDEOS"
if [ "$ORIGEM" != "$DESTINO" ]; then
    cp "$ORIGEM/player.py" "$ORIGEM/encontrar_pinos.py" "$DESTINO/"
    # não sobrescreve uma configuração já ajustada
    [ -f "$DESTINO/config.ini" ] || cp "$ORIGEM/config.ini" "$DESTINO/"
fi
# copia vídeos que vieram junto (pasta videos/ ao lado do script)
if compgen -G "$ORIGEM/videos/*.*" > /dev/null; then
    cp -v "$ORIGEM"/videos/*.* "$PASTA_VIDEOS/"
fi
# confere se os 3 vídeos esperados estão lá
for n in 1 2 3; do
    if [ ! -f "$PASTA_VIDEOS/video$n.mp4" ]; then
        echo "AVISO: não encontrei $PASTA_VIDEOS/video$n.mp4"
        echo "       (confira o nome: tudo minúsculo, sem espaço, e não 'video$n.mp4.mp4')"
    fi
done

echo "==> 3/6 Dando permissão de vídeo, som e GPIO ao usuário $USUARIO ..."
sudo usermod -aG video,render,audio,gpio "$USUARIO"

echo "==> 4/6 Criando o serviço que inicia sozinho ao ligar..."
sudo tee /etc/systemd/system/video-botoes.service > /dev/null <<EOF
[Unit]
Description=Player de videos por botoes
After=multi-user.target sound.target

[Service]
User=$USUARIO
WorkingDirectory=$DESTINO
ExecStart=/usr/bin/python3 $DESTINO/player.py
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable video-botoes.service

echo "==> 5/6 Escondendo textos de inicialização (tela limpa)..."
CMDLINE=/boot/firmware/cmdline.txt
[ -f "$CMDLINE" ] || CMDLINE=/boot/cmdline.txt
CONFIGTXT=/boot/firmware/config.txt
[ -f "$CONFIGTXT" ] || CONFIGTXT=/boot/config.txt
sudo cp -n "$CMDLINE" "$CMDLINE.original" || true
for opcao in quiet loglevel=3 logo.nologo vt.global_cursor_default=0 consoleblank=0; do
    grep -qw -- "$opcao" "$CMDLINE" || sudo sed -i "1 s/\$/ $opcao/" "$CMDLINE"
done
grep -q '^disable_splash=1' "$CONFIGTXT" || echo 'disable_splash=1' | sudo tee -a "$CONFIGTXT" > /dev/null

echo "==> 6/6 Volume da saída P2 no máximo..."
amixer -c Headphones sset PCM 100% > /dev/null 2>&1 || true

# se a pasta foi copiada para o cartão pelo Windows (partição de boot),
# apaga de lá no final, para liberar espaço
case "$ORIGEM" in
    /boot/*) echo "Removendo cópia temporária em $ORIGEM ..."; sudo rm -rf "$ORIGEM" ;;
esac

echo
echo "Instalação concluída."
echo "Vídeos devem estar em: $PASTA_VIDEOS"
ls -1 "$PASTA_VIDEOS" || true
echo
echo "Agora reinicie:  sudo reboot"
