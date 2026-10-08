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
| `videos/` | Coloque aqui os 3 vídeos (`video1.mp4`, `video2.mp4`, `video3.mp4`) |
| `docs/diagrama-ligacao.png` | Desenho de onde ligar os botões |

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

## Passo 2 — Colocar o programa e os vídeos no cartão (pelo computador)

Não é só copiar o sistema: ele **tem que ser gravado pelo Imager** (Passo 1).
Mas, depois disso, o programa e os vídeos **são só copiar e colar**:

1. Depois que o Imager terminar, **tire o cartão e coloque de novo** no computador.
2. Vai aparecer um disco chamado **`bootfs`**. Abra ele.
   - ⚠️ O Windows pode avisar *"É preciso formatar o disco antes de usá-lo"*.
     Esse aviso é sobre a outra parte do cartão, que é do Linux. **Clique em CANCELAR.**
     Nunca formate.
3. Coloque os 3 vídeos dentro da pasta `raspberry-video-botoes\videos` com estes nomes:

   | Botão | Nome do arquivo |
   |---|---|
   | Botão 1 | `video1.mp4` |
   | Botão 2 | `video2.mp4` |
   | Botão 3 | `video3.mp4` |

   - Os nomes devem ser **minúsculos, sem espaço e sem acento**.
   - O Windows costuma esconder o ".mp4". Se você renomear para `video1.mp4`
     com a extensão escondida, o arquivo vira `video1.mp4.mp4` e não funciona.
     Para ver a extensão, no Explorador vá em **Exibir → Mostrar → Extensões de nomes de arquivos**.
4. Copie a pasta **`raspberry-video-botoes`** inteira, já com os vídeos, para dentro do disco `bootfs`.
5. Clique com o botão direito no disco e escolha **Ejetar**. Depois tire o cartão.

**Espaço:** o `bootfs` costuma ter uns 300 MB livres (o Windows mostra o espaço livre do disco). Se os vídeos juntos passarem
disso, o Windows vai avisar que não há espaço. Nesse caso, copie a pasta para
um **pendrive** e veja a observação no fim do Passo 3.

**Formato recomendado dos vídeos:** MP4 com vídeo **H.264**, até **1920x1080 a 30 fps**.
A Pi 3 não consegue tocar H.265/HEVC nem 4K de forma fluida. Se um vídeo travar,
converta no **HandBrake** (preset *Fast 1080p30*) ou reduza para 720p.

## Passo 3 — Instalar na Raspberry (só uma vez)

1. Coloque o cartão na Raspberry. Ligue um **teclado USB**, a TV/monitor e,
   **por último**, a energia.
2. A Raspberry precisa de **internet** nessa etapa: use o Wi-Fi configurado no
   Imager ou um cabo de rede.
3. Espere aparecer `login:`. Digite o usuário (`pi`), Enter, e depois a senha, Enter.
   A senha não aparece enquanto você digita; isso é normal.
4. Digite exatamente isto e aperte Enter:

   ```
   bash /boot/firmware/raspberry-video-botoes/instalar.sh
   ```

5. Espere terminar (de 5 a 15 minutos). Ele instala tudo, passa os vídeos para
   `/home/pi/videos` e apaga a cópia temporária do `bootfs`.
6. Digite `sudo reboot`. A partir daí ela liga direto na tela preta.

> **Se os vídeos foram para um pendrive** (porque não couberam no cartão),
> coloque o pendrive na Pi e, no item 4, digite estes comandos no lugar:
>
> ```
> sudo mkdir -p /mnt/pendrive
> sudo mount /dev/sda1 /mnt/pendrive
> cp -r /mnt/pendrive/raspberry-video-botoes ~/
> sudo umount /mnt/pendrive
> bash ~/raspberry-video-botoes/instalar.sh
> ```

## Passo 4 — Ligar os botões

Veja o desenho em **`docs/diagrama-ligacao.png`**.


Cada botão tem 2 fios: um vai no seu pino de sinal e o outro vai no GND.
Os 3 botões podem dividir **um único fio de GND**, emendado nos três.
Não precisa de resistor, porque a Raspberry usa o resistor interno dela.

**Ligue com a Raspberry desligada da tomada.**

Segure a placa com as **portas USB para baixo**. A fileira de pinos fica na
**borda direita**. Conte os pinos de cima para baixo na **coluna de dentro**,
a que fica mais perto do centro da placa:

```
          coluna de DENTRO   coluna de FORA (borda)
  1º         pino 1              pino 2
  2º         pino 3              pino 4
  3º         pino 5              pino 6
  4º         pino 7              pino 8
  5º         pino 9  ← GND (fio comum dos 3 botões)
  6º         pino 11 ← BOTÃO 1
  7º         pino 13 ← BOTÃO 2
  8º         pino 15 ← BOTÃO 3
```

Se o botão tiver **4 perninhas** (botão pequeno quadrado), use duas perninhas
em **diagonal**, para garantir que são lados opostos do contato.

**Cuidado:** não ligue nada nos pinos 1, 2, 4 e 17. São alimentação de 3.3V e 5V
e podem queimar a placa se encostarem no GND.

Os pinos usados no programa são estes:

| Botão | GPIO | Pino físico |
|---|---|---|
| Botão 1 | GPIO17 | pino 11 |
| Botão 2 | GPIO27 | pino 13 |
| Botão 3 | GPIO22 | pino 15 |
| Outro fio de cada botão | GND | pinos 9, 14, 20, 25, 30, 34 ou 39 |

Para conferir se cada botão está funcionando, ou se ligou em outros pinos, rode:

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

## Trocar os vídeos pelo PC (sem tirar o cartão)

A Raspberry precisa estar ligada e na mesma rede do PC.

1. No PC, aperte **Windows + R**, digite `cmd` e Enter.
2. Envie o vídeo novo (troque o caminho pelo do seu arquivo):

   ```
   scp "C:\caminho\do\arquivo\video1.mp4" pi@192.168.0.95:~/videos/video1.mp4
   ```

   Digite a senha da Raspberry quando pedir. O arquivo antigo é substituído.
   Para o botão 2 ou 3, use `video2.mp4` ou `video3.mp4` no final do comando.
3. Pronto: no próximo aperto do botão já toca o vídeo novo.

Observações:

- O IP `192.168.0.95` pode mudar se o roteador reiniciar. Se o comando não
  conectar, tente `pi@ETBR.local` no lugar do IP.
- Se o modo somente leitura (Passo 5) estiver ativado, desative antes de trocar
  os vídeos. Senão a troca se perde ao reiniciar.

## Saída de som

Na placa desta instalação o conector P2 não funcionou, então o som foi
configurado para sair pela TV (`saida = hdmi` em `config.ini`). Para usar um
adaptador de som USB no futuro, é preciso ajustar `player.py`.

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
de fábrica e **só pode ser ligado usando um cartão SD uma vez**.

**Primeiro tente direto:** grave o sistema no pendrive (Passo 1), tire o cartão
da Pi, coloque o pendrive e ligue. Espere até 1 minuto. Se o sistema iniciar,
o recurso já estava ligado nessa placa e você não precisa fazer mais nada.
Se ficar só a tela colorida ou a tela preta, faça o procedimento abaixo:

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
