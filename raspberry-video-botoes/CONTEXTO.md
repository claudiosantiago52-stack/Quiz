# Contexto do projeto — Player de vídeos por botões (Raspberry Pi)

Resumo para retomar o trabalho numa conversa futura com o Claude.
Situação em 08/10/2026: **funcionando**.

## O que é

Raspberry Pi ligada a uma TV. Ao ligar, fica com tela preta. Cada um dos
3 botões dispara um vídeo; se outro botão for apertado durante um vídeo, troca
de vídeo; ao terminar, volta para a tela preta.

## Hardware

- **Placa:** Raspberry Pi 3 Model B V1.2, numa caixa preta.
- **TV:** Samsung The Frame (HDMI pela caixa One Connect). Antes de ligar a Pi,
  tire a TV do Modo Arte e selecione a entrada HDMI certa.
- **Cartão:** micro SD de 16 GB.
- **Botões:** um fio no pino de sinal e outro no GND comum (sem resistor):
  - Botão 1 → pino físico 11 (GPIO17) → `video1.mp4`
  - Botão 2 → pino físico 13 (GPIO27) → `video2.mp4`
  - Botão 3 → pino físico 15 (GPIO22) → `video3.mp4`
  - GND comum → pino físico 9
  - Diagrama: `docs/diagrama-ligacao.png`
- **Som:** o conector P2 (3,5 mm) da placa **não funciona**: testado com fone
  bom e sem nenhum erro de software, então provavelmente é defeito físico.
  O som sai **pela TV (HDMI)**: `saida = hdmi` em `config.ini`.
  Se um dia precisar de som separado: adaptador de som USB, que exige
  ajustar o `player.py`.
- **Energia:** o power bank causou "Undervoltage detected" e travamentos.
  Usar fonte de tomada de **5V e no mínimo 2,5A**, com cabo micro-USB curto.
  A energia fraca provavelmente foi o que estragou o cartão antigo.

## Sistema instalado

- Raspberry Pi OS **Lite 64-bit** (Debian 13 "Trixie"), gravado com o
  Raspberry Pi Imager 2.0.11.
- Hostname: `ETBR`. Usuário: `pi` (a senha fica só com o dono; nunca registrar aqui).
- SSH ativado. IP na última vez: **192.168.0.95** (pode mudar; tente também `ETBR.local`).
- Teclado: `br`. Fuso horário: `America/Sao_Paulo`.
- Programa em `/home/pi/video-botoes/` (`player.py`, `config.ini`, `encontrar_pinos.py`).
- Vídeos em `/home/pi/videos/` (`video1.mp4`, `video2.mp4`, `video3.mp4`).
  Os vídeos atuais são pequenos (cerca de 13 MB no total). O `video3.mp4` não tem áudio.
- Serviço systemd `video-botoes`, que inicia sozinho ao ligar. O player é o mpv
  (DRM, sem desktop), controlado por socket.
- O modo somente leitura (overlay) **ainda não foi ativado**. É recomendado
  ativar depois que os vídeos definitivos estiverem no lugar.

## Tarefas pendentes / próximos passos

1. **Trocar os vídeos** quando o cliente enviar os novos (MP4 H.264, até 1080p, com som).
   Pelo cmd do PC:
   `scp "C:\caminho\video1.mp4" pi@192.168.0.95:~/videos/video1.mp4`
2. Depois disso, ativar o modo somente leitura:
   `sudo raspi-config` → Performance Options → Overlay File System.
3. Trocar o power bank por uma fonte de tomada adequada, se ainda não foi feito.
4. Opcional: apagar `~/.asoundrc`, se tiver sido criado no teste de "som nos dois".

## Comandos úteis (via `ssh pi@192.168.0.95` no cmd do PC)

| O que fazer | Comando |
|---|---|
| Ver log / erros | `journalctl -u video-botoes -f` |
| Reiniciar o player | `sudo systemctl restart video-botoes` |
| Parar o player (libera a tela) | `sudo systemctl stop video-botoes` |
| Desligar com segurança | `sudo poweroff` |
| Testar som da TV | `mpv --no-video --audio-device=alsa/plughw:CARD=vc4hdmi,DEV=0 ~/videos/video1.mp4` |

## Onde está o código

Repositório `claudiosantiago52-stack/Quiz`, branch `claude/beautiful-dirac-7899vq`,
pasta `raspberry-video-botoes/`. O guia completo está em `LEIAME.md`.
