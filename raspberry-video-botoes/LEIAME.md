# Player de vídeos por botões — Raspberry Pi 3 Model B

Funcionamento:

1. Ao ligar, a Raspberry inicia sozinha e fica com **tela preta**.
2. Apertou o **botão 1, 2 ou 3** → toca o **vídeo 1, 2 ou 3**.
3. Se apertar outro botão durante um vídeo, o vídeo atual é **interrompido** e o novo começa.
4. Quando o vídeo acaba, volta para a **tela preta** e espera o próximo botão.
5. O som sai pela **saída P2 (fone 3,5 mm)** da placa.

Arquivos:

| Arquivo | Para que serve |
|---|---|
| `player.py` | O programa principal |
| `config.ini` | Pinos dos botões, nomes dos vídeos e saída de som |
| `encontrar_pinos.py` | Descobre em quais pinos os botões estão ligados |
| `instalar.sh` | Instala tudo e configura para iniciar sozinho |
| `videos/` | Coloque aqui os 3 vídeos antes de copiar para o pendrive |

---

## Passo 1 — Gravar o sistema no cartão (ou pendrive)

1. No computador, instale o **Raspberry Pi Imager**: <https://www.raspberrypi.com/software/>
2. Abra o Imager e escolha:
   - **Dispositivo:** Raspberry Pi 3
   - **Sistema:** *Raspberry Pi OS (other)* → **Raspberry Pi OS Lite** (sem desktop)
   - **Armazenamento:** o cartão micro SD (ou pendrive, veja o fim deste arquivo)
3. Quando perguntar sobre personalizar, clique em **Editar configurações** e preencha:
   - Nome de usuário: `pi` e uma senha que você vá lembrar
   - Wi-Fi (nome e senha da rede). Ou ligue um cabo de rede na placa.
   - Fuso horário e teclado: `America/Sao_Paulo` e `br`
   - Na aba **Serviços**, ative o **SSH** (opcional, para mexer pelo computador)
4. Grave e espere terminar.

## Passo 2 — Preparar um pendrive com os arquivos

1. Copie a pasta `raspberry-video-botoes` inteira para um pendrive.
2. Coloque os 3 vídeos dentro de `raspberry-video-botoes/videos/` com os nomes
   `video1.mp4`, `video2.mp4` e `video3.mp4`.
   Se quiser outros nomes, altere em `config.ini`.

**Formato recomendado dos vídeos:** MP4 com vídeo **H.264**, até **1920x1080 a 30 fps**.
A Pi 3 não consegue tocar H.265/HEVC nem 4K de forma fluida. Se um vídeo travar,
converta no **HandBrake** (preset *Fast 1080p30*) ou reduza para 720p.

## Passo 3 — Instalar na Raspberry

1. Coloque o cartão na Raspberry, ligue um teclado, a TV/monitor e a energia.
2. Espere aparecer `login:`. Entre com o usuário e a senha que você criou.
3. Coloque o pendrive e digite (um comando por linha, Enter depois de cada):

   ```
   sudo mkdir -p /mnt/pendrive
   sudo mount /dev/sda1 /mnt/pendrive
   cp -r /mnt/pendrive/raspberry-video-botoes ~/
   sudo umount /mnt/pendrive
   bash ~/raspberry-video-botoes/instalar.sh
   ```

   A Raspberry precisa de internet nessa etapa, porque o instalador baixa o mpv.
4. Quando terminar, digite `sudo reboot`. A partir daí ela liga direto na tela preta.

## Passo 4 — Descobrir os pinos dos botões

Os pinos padrão são estes:

| Botão | GPIO | Pino físico |
|---|---|---|
| Botão 1 | GPIO17 | pino 11 |
| Botão 2 | GPIO27 | pino 13 |
| Botão 3 | GPIO22 | pino 15 |
| Outro fio de cada botão | GND | pinos 9, 14, 20, 25, 30, 34 ou 39 |

Se os seus botões já estão soldados em outros pinos, descubra quais são:

```
sudo systemctl stop video-botoes
python3 ~/video-botoes/encontrar_pinos.py
```

Aperte cada botão, um de cada vez, e anote o GPIO que aparecer. Para sair, aperte **Ctrl+C**.
Se nada aparecer, os botões podem estar ligados ao 3.3V. Nesse caso, rode:
`python3 ~/video-botoes/encontrar_pinos.py --3v3`

Depois coloque os números no arquivo de configuração:

```
nano ~/video-botoes/config.ini
```

- Altere `botao1`, `botao2` e `botao3`.
- Se os botões estão no 3.3V, troque `ligado_ao_gnd = true` para `false`.
- Para salvar: **Ctrl+O**, depois Enter, depois **Ctrl+X**.

Por fim: `sudo systemctl restart video-botoes`

> Numeração dos pinos físicos: o pino 1 fica no canto da fileira dupla mais perto
> do texto "GPIO" da placa, na fileira de dentro. A fileira de dentro tem os pinos
> ímpares (1, 3, 5...) e a de fora tem os pares (2, 4, 6...).

## Comandos úteis

| O que fazer | Comando |
|---|---|
| Ver o que o programa está fazendo / erros | `journalctl -u video-botoes -f` |
| Reiniciar o programa | `sudo systemctl restart video-botoes` |
| Parar o programa | `sudo systemctl stop video-botoes` |
| Ver os vídeos instalados | `ls ~/videos` |
| Testar o som do P2 | `speaker-test -D plughw:CARD=Headphones -c 2 -t wav` |
| Ajustar o volume do P2 | `alsamixer -c Headphones` |

Para trocar um vídeo: copie o novo arquivo para `~/videos` com o mesmo nome,
ou mude o nome em `config.ini`, e reinicie o programa.

## Passo 5 (recomendado) — Proteger o cartão contra desligamentos bruscos

Cartões SD costumam corromper quando a energia é cortada sem desligar o sistema.
Isso provavelmente foi o que estragou o cartão antigo. Quando **tudo estiver
funcionando**, ative o modo somente leitura:

```
sudo raspi-config
```

Vá em **Performance Options → Overlay File System → Yes** (e *Yes* para proteger
a partição de boot) e reinicie.

Com isso, nada é gravado no cartão, e desligar da tomada passa a ser seguro.
Para trocar vídeos ou configurações depois, desative o modo pelo mesmo menu,
faça as alterações e ative de novo.

---

## Iniciar por pendrive em vez do cartão (Raspberry Pi 3 Model B)

A **Pi 3 Model B** consegue iniciar por pendrive, mas esse recurso vem desligado
de fábrica e **só pode ser ligado usando um cartão SD uma vez**:

1. Grave o Raspberry Pi OS Lite em um cartão (Passo 1) e inicie a Pi por ele.
2. Digite:
   ```
   echo program_usb_boot_mode=1 | sudo tee -a /boot/firmware/config.txt
   sudo reboot
   ```
3. Depois de reiniciar, confira:
   ```
   vcgencmd otp_dump | grep 17:
   ```
   Se aparecer `17:3020000a`, o boot por USB está ativado. A mudança é **permanente**
   e fica gravada na placa.
4. Grave o sistema no pendrive pelo Imager (Passo 1, escolhendo o pendrive),
   tire o cartão e ligue a Pi só com o pendrive.

Observações:

- Sem cartão, a Pi leva alguns segundos a mais para iniciar.
- Alguns pendrives não são reconhecidos no boot. Se não funcionar, teste outra marca.
- O pendrive também corrompe com desligamentos bruscos. O Passo 5 vale para ele também.
