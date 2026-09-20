import random
import arcade

mapa_tiles = [
    'BBBBBBBBBBBBBBBBBBBB',
    'B.............E....B',
    'B.....E............B',
    'B............B.....B',
    'B..BBBBB.....B.....B',
    'B...B........B.....B',
    'B...B.........E....B',
    'B...B.......BBB....B',
    'B..................B',
    'B.....BBBB....E....B',
    'B.......E..........B',
    'B.............P....B',
    'B.............E....B',
    'B.....E.......E....B',
    'BBBBBBBBBBBBBBBBBBBB',
]

TAMANHO_TILE = 32  
ESCALA = 0.25
INTERVALO_MOVIMENTO_INIMIGO = 0.5  
DURACAO_FRAME_ANDANDO = 0.12  
TEMPO_PARA_VOLTAR_AO_IDLE = 0.3  

CAMINHO_PAREDE = "imagens_arcade/parede_tile.png"
CAMINHO_CHAO = "imagens_arcade/chao.png"
CAMINHO_JOGADOR_IDLE = "imagens_arcade/player/idle1.png"
CAMINHO_JOGADOR_UP = "imagens_arcade/player/up1.png"
CAMINHOS_JOGADOR_ANDANDO = [
    f"imagens_arcade/player/direita{i}.png"
    for i in range(1, 4)
]
CAMINHO_INIMIGO_PARADO = "imagens_arcade/inimigos/abobora/abobora1.png"
CAMINHO_INIMIGO_ANDANDO = "imagens_arcade/inimigos/abobora/abobora2.png"

XP_BASE_PARA_SUBIR = 20
VIDA_BASE_JOGADOR = 30
ATAQUE_BASE_JOGADOR = 6
VIDA_BASE_INIMIGO = 12
CHANCE_DROP_POCAO = 0.4
CURA_POCAO = 10


class Mundo:
    def __init__(self):
        self.grade = [list(linha) for linha in mapa_tiles]
        self.jogador_x = 0
        self.jogador_y = 0
        self.inimigos = []

        for y, linha in enumerate(self.grade):
            for x, celula in enumerate(linha):
                if celula == 'P':
                    self.jogador_x, self.jogador_y = x, y
                    self.grade[y][x] = '.'
                elif celula == 'E':
                    self.inimigos.append([x, y])
                    self.grade[y][x] = '.'

    def mover_jogador(self, dx, dy):
        novo_x = self.jogador_x + dx
        novo_y = self.jogador_y + dy

        if self.esta_bloqueado(novo_x, novo_y):
            return False
        if self.inimigo_em(novo_x, novo_y):
            return False

        self.jogador_x, self.jogador_y = novo_x, novo_y
        return True

    def esta_bloqueado(self, x, y):
        if y < 0 or y >= len(self.grade) or x < 0 or x >= len(self.grade[0]):
            return True
        return self.grade[y][x] == 'B'

    def inimigo_em(self, x, y):
        for inimigo in self.inimigos:
            if inimigo[0] == x and inimigo[1] == y:
                return inimigo
        return None

    def vagar_inimigos(self):
        for inimigo in self.inimigos:
            dx, dy = random.choice([(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)])
            nx, ny = inimigo[0] + dx, inimigo[1] + dy
            if not self.esta_bloqueado(nx, ny) and (nx, ny) != (self.jogador_x, self.jogador_y):
                if not self.inimigo_em(nx, ny):
                    inimigo[0], inimigo[1] = nx, ny


class JanelaJogo(arcade.Window):

    def __init__(self):
        super().__init__(640, 480, "RPG em Python")

        self.jogador = arcade.Sprite(
            "imagens_arcade/player/idle1.png",
            scale=0.25
        )
        self.jogador.center_x = 320
        self.jogador.center_y = 240
        self.mundo = Mundo()
        self.sprites_jogador = arcade.SpriteList()
        self.sprites_jogador.append(self.jogador)

        self.sprites_cenario = arcade.SpriteList()
        self.sprites_jogador = arcade.SpriteList()
        self.sprite_jogador = None
        self.sprites_inimigos = arcade.SpriteList()
        self.tempo_desde_ultimo_passo_inimigo = 0.0

        self.texturas_andando = [arcade.load_texture(caminho) for caminho in CAMINHOS_JOGADOR_ANDANDO]
        self.textura_idle = arcade.load_texture(CAMINHO_JOGADOR_IDLE)
        self.textura_up = arcade.load_texture(CAMINHO_JOGADOR_UP)
        self.textura_inimigo_parado = arcade.load_texture(CAMINHO_INIMIGO_PARADO)   
        self.textura_inimigo_andando = arcade.load_texture(CAMINHO_INIMIGO_ANDANDO)
        self.indice_frame_andando = 0
        self.tempo_desde_ultimo_frame = 0.0
        self.tempo_desde_ultimo_movimento_jogador = 999.0

        self.direcao_horizontal = 1       
        self.ultimo_tipo_movimento = None
        self.montar_cenario()
        self.montar_personagens()

        self.pos_inicial_jogador = (self.mundo.jogador_x, self.mundo.jogador_y)
        self.jogador_nivel = 1
        self.jogador_vida_max = VIDA_BASE_JOGADOR
        self.jogador_vida = self.jogador_vida_max
        self.jogador_ataque = ATAQUE_BASE_JOGADOR
        self.jogador_xp = 0
        self.jogador_xp_para_subir = XP_BASE_PARA_SUBIR
        self.jogador_pocoes = 0

        self.em_batalha = False
        self.em_game_over = False
        self.jogador_pocoes = 0
        self.total_inimigos_derrotados = 0

        # Esses aqui serão úteis para a tela de batalha
        self.batalha_alvo_indice = None
        self.batalha_inimigo_vida = 0
        self.batalha_inimigo_vida_max = 0
        self.batalha_inimigo_ataque = 0
        self.batalha_resultado = None
        self.batalha_mensagem = ""
        self.batalha_botoes = []
        self.game_over_botoes = []


    def desenhar_hud(self):
        arcade.draw_rect_filled(arcade.XYWH(100, 452, 190, 62), (20, 20, 30, 180))
        arcade.draw_rect_outline(arcade.XYWH(100, 452, 190, 62), arcade.color.WHITE, 1)

        arcade.draw_text(f"Nível {self.jogador_nivel}", 15, 468, arcade.color.WHITE, 12)
        arcade.draw_text(f"XP: {self.jogador_xp}/{self.jogador_xp_para_subir}",
                        15, 450, arcade.color.LIGHT_GREEN, 12)

        largura_barra = 160
        altura_barra = 14
        centro_x = 100
        y_barra = 430
        x_esquerda = centro_x - largura_barra / 2
        largura_atual = largura_barra * max(0.0, min(1.0, self.jogador_vida / self.jogador_vida_max))

        arcade.draw_rect_filled(arcade.XYWH(centro_x, y_barra, largura_barra, altura_barra), arcade.color.DARK_RED)
        arcade.draw_rect_filled(
            arcade.XYWH(x_esquerda + largura_atual / 2, y_barra, largura_atual, altura_barra),
            arcade.color.GREEN
        )
        arcade.draw_rect_outline(arcade.XYWH(centro_x, y_barra, largura_barra, altura_barra), arcade.color.WHITE, 1)
        arcade.draw_text(f"{self.jogador_vida}/{self.jogador_vida_max}", centro_x, y_barra,
                        arcade.color.WHITE, 10, anchor_x="center", anchor_y="center")

    def on_draw(self):
        self.clear()
        self.sprites_cenario.draw()
        self.sprites_inimigos.draw()
        self.sprites_jogador.draw()
        self.desenhar_hud()
        if self.em_batalha:
            self.desenhar_batalha()

    def para_tela_x(self, x):
        return x * TAMANHO_TILE + TAMANHO_TILE / 2

    def para_tela_y(self, y):
        num_linhas = len(self.mundo.grade)
        return (num_linhas - 1 - y) * TAMANHO_TILE + TAMANHO_TILE / 2

    def montar_cenario(self):
        for y, linha in enumerate(self.mundo.grade):
            for x, celula in enumerate(linha):
                caminho = CAMINHO_PAREDE if celula == 'B' else CAMINHO_CHAO
                sprite = arcade.Sprite(caminho, scale=ESCALA)
                sprite.center_x = self.para_tela_x(x)
                sprite.center_y = self.para_tela_y(y)
                self.sprites_cenario.append(sprite)

    def atualizar_posicao_sprite(self, sprite, grade_x, grade_y):
        sprite.center_x = self.para_tela_x(grade_x)
        sprite.center_y = self.para_tela_y(grade_y)

    def montar_personagens(self):
        self.sprite_jogador = arcade.Sprite(CAMINHO_JOGADOR_IDLE, scale=ESCALA)
        self.atualizar_posicao_sprite(self.sprite_jogador, self.mundo.jogador_x, self.mundo.jogador_y)
        self.sprites_jogador.append(self.sprite_jogador)
        for inimigo in self.mundo.inimigos:
            sprite = arcade.Sprite(CAMINHO_INIMIGO_PARADO, scale=ESCALA)
            self.atualizar_posicao_sprite(sprite, inimigo[0], inimigo[1])
            self.sprites_inimigos.append(sprite)

    def on_key_press(self, key, modifiers):

        if key == arcade.key.Q or key == arcade.key.ESCAPE:
            arcade.close_window()
            return

        if self.em_game_over:
            return

        if self.em_batalha:
            return

        if key in (arcade.key.W, arcade.key.UP):
            self.tentar_mover(0, -1, 'cima')

        elif key in (arcade.key.S, arcade.key.DOWN):
            self.tentar_mover(0, 1, 'baixo')

        elif key in (arcade.key.A, arcade.key.LEFT):
            self.tentar_mover(-1, 0, 'lateral')

        elif key in (arcade.key.D, arcade.key.RIGHT):
            self.tentar_mover(1, 0, 'lateral')

    def tentar_mover(self, dx, dy, tipo):

        nx = self.mundo.jogador_x + dx
        ny = self.mundo.jogador_y + dy

        if not self.mundo.esta_bloqueado(nx, ny):

            inimigo = self.mundo.inimigo_em(nx, ny)

            if inimigo:
                indice = self.mundo.inimigos.index(inimigo)
                self.iniciar_batalha(indice)
                return

        moveu = self.mundo.mover_jogador(dx, dy)

        if moveu:
            if tipo == 'lateral':
                self.direcao_horizontal = 1 if dx > 0 else -1

            self.ultimo_tipo_movimento = tipo

            self.atualizar_posicao_sprite(
                self.sprite_jogador,
                self.mundo.jogador_x,
                self.mundo.jogador_y
            )

            self.tempo_desde_ultimo_movimento_jogador = 0.0
            self.atualizar_textura_jogador()
    def on_update(self, delta_time):
        self.tempo_desde_ultimo_movimento_jogador += delta_time
        if self.tempo_desde_ultimo_movimento_jogador < TEMPO_PARA_VOLTAR_AO_IDLE:
            if self.ultimo_tipo_movimento == 'lateral':
                self.tempo_desde_ultimo_frame += delta_time
                if self.tempo_desde_ultimo_frame >= DURACAO_FRAME_ANDANDO:
                    self.tempo_desde_ultimo_frame = 0.0
                    self.indice_frame_andando = (self.indice_frame_andando + 1) % len(self.texturas_andando)
                    self.sprite_jogador.texture = self.texturas_andando[self.indice_frame_andando]
        else:
            self.sprite_jogador.texture = self.textura_idle
            self.ultimo_tipo_movimento = None

        self.tempo_desde_ultimo_passo_inimigo += delta_time
        if self.tempo_desde_ultimo_passo_inimigo >= INTERVALO_MOVIMENTO_INIMIGO:
            posicoes_antigas = [list(inimigo) for inimigo in self.mundo.inimigos]
            self.mundo.vagar_inimigos()

            for i in range(len(self.mundo.inimigos)):
                sprite = self.sprites_inimigos[i]
                inimigo = self.mundo.inimigos[i]
                posicao_antiga = posicoes_antigas[i]

                dx = inimigo[0] - posicao_antiga[0]
                if dx > 0:
                    sprite.scale_x = abs(sprite.scale_x)
                elif dx < 0:
                    sprite.scale_x = -abs(sprite.scale_x)
                self.atualizar_posicao_sprite(sprite, inimigo[0], inimigo[1])
                sprite.texture = self.textura_inimigo_andando

            self.tempo_desde_ultimo_passo_inimigo = 0.0
        elif self.tempo_desde_ultimo_passo_inimigo >= INTERVALO_MOVIMENTO_INIMIGO / 2:
            for sprite in self.sprites_inimigos:
                sprite.texture = self.textura_inimigo_parado

    def atualizar_textura_jogador(self):
        if self.ultimo_tipo_movimento == 'lateral':
            self.sprite_jogador.scale_x = self.direcao_horizontal * abs(self.sprite_jogador.scale_x)
            self.tempo_desde_ultimo_frame = 0.0
            self.indice_frame_andando = (self.indice_frame_andando + 1) % len(self.texturas_andando)
            self.sprite_jogador.texture = self.texturas_andando[self.indice_frame_andando]
        elif self.ultimo_tipo_movimento == 'cima':
            self.sprite_jogador.texture = self.textura_up
        elif self.ultimo_tipo_movimento == 'baixo':
            self.sprite_jogador.texture = self.textura_idle

    def desenhar_batalha(self):
        arcade.draw_rect_filled(arcade.XYWH(320, 240, 560, 360), (20, 20, 30, 230))
        arcade.draw_text("Batalha!", 320, 400, arcade.color.WHITE, 22,
                          anchor_x="center", bold=True)
        arcade.draw_text(
            f"Nível {self.jogador_nivel}   Vida: {self.jogador_vida}/{self.jogador_vida_max}   "
            f"XP: {self.jogador_xp}/{self.jogador_xp_para_subir}   Poções: {self.jogador_pocoes}",
            320, 360, arcade.color.LIGHT_GREEN, 14, anchor_x="center"
        )
        arcade.draw_text(
            f"Abóbora selvagem - Vida: {self.batalha_inimigo_vida}/{self.batalha_inimigo_vida_max}",
            320, 330, arcade.color.ORANGE, 14, anchor_x="center"
        )

        if self.batalha_mensagem:
            arcade.draw_text(
                self.batalha_mensagem, 320, 260, arcade.color.WHITE, 13,
                anchor_x="center", width=500, align="center", multiline=True
            )
        for botao in self.batalha_botoes:
            retangulo = arcade.XYWH(botao["x"], botao["y"], botao["w"], botao["h"])
            arcade.draw_rect_filled(retangulo, arcade.color.DARK_SLATE_GRAY)
            arcade.draw_rect_outline(retangulo, arcade.color.WHITE, 2)
            arcade.draw_text(botao["texto"], botao["x"], botao["y"], arcade.color.WHITE, 16,
                              anchor_x="center", anchor_y="center")

    def iniciar_batalha(self, indice_inimigo):
        self.em_batalha = True
        self.batalha_alvo_indice = indice_inimigo
        self.batalha_inimigo_vida_max = VIDA_BASE_INIMIGO + (self.jogador_nivel - 1) * 3
        self.batalha_inimigo_vida = self.batalha_inimigo_vida_max
        self.batalha_inimigo_ataque = random.randint(2, 10) + (self.jogador_nivel - 1)
        self.batalha_resultado = None
        self.batalha_mensagem = "Uma abóbora selvagem apareceu!"
        self.montar_botoes_escolha()

    def montar_botoes_escolha(self):
        botoes = [
            {"x": 160, "y": 90, "w": 130, "h": 50, "texto": "Atacar", "acao": self.atacar},
        ]
        botoes.append({
                "x": 320, "y": 90, "w": 130, "h": 50,
                "texto": f"Poção ({self.jogador_pocoes})", "acao": self.usar_pocao
        })
        botoes.append({"x": 480, "y": 90, "w": 130, "h": 50, "texto": "Fugir", "acao": self.fugir})
        self.batalha_botoes = botoes

    def montar_botao_continuar(self):
        self.batalha_botoes = [
            {"x": 320, "y": 90, "w": 160, "h": 50, "texto": "Continuar", "acao": self.continuar_apos_batalha},
        ]
    def verificar_subida_nivel(self):
        subiu = False
        while self.jogador_xp >= self.jogador_xp_para_subir:
            self.jogador_xp -= self.jogador_xp_para_subir
            self.jogador_nivel += 1
            self.jogador_vida_max += 5
            self.jogador_ataque += 2
            self.jogador_xp_para_subir += 10
            subiu = True
        return subiu
    def atacar(self):
        dano = max(1, random.randint(self.jogador_ataque - 2, self.jogador_ataque + 2))
        self.batalha_inimigo_vida -= dano
        mensagem = f"Você atacou e causou {dano} de dano!"

        if self.batalha_inimigo_vida <= 0:
            self.batalha_inimigo_vida = 0
            xp_ganho = 10 + self.jogador_nivel * 2
            self.jogador_xp += xp_ganho
            mensagem += f"Você derrotou a abóbora! +{xp_ganho} XP"

            if random.random() < CHANCE_DROP_POCAO:
                self.jogador_pocoes += 1
                mensagem += "A abóbora deixou cair uma poção!"

            if self.verificar_subida_nivel():
                mensagem += f"Você subiu para o nível {self.jogador_nivel}!"
            self.batalha_resultado = "vitoria"
            self.montar_botao_continuar()
        else:
            dano_recebido = max(1, random.randint(self.batalha_inimigo_ataque - 1, self.batalha_inimigo_ataque + 1))
            self.jogador_vida -= dano_recebido
            mensagem += f"A abóbora revidou causando {dano_recebido} de dano!"
            if self.jogador_vida <= 0:
                self.jogador_vida = 0
                mensagem += "Você foi derrotado..."
                self.batalha_resultado = "derrota"
                self.montar_botao_continuar()
            else:
                self.batalha_resultado = None
                self.montar_botoes_escolha()

        self.batalha_mensagem = mensagem

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.em_batalha:
            return
        for botao in self.batalha_botoes:
            meio_w = botao["w"] / 2
            meio_h = botao["h"] / 2
            if botao["x"] - meio_w <= x <= botao["x"] + meio_w and \
               botao["y"] - meio_h <= y <= botao["y"] + meio_h:
                botao["acao"]()
                break
    def continuar_apos_batalha(self):
        if self.batalha_resultado == "vitoria":
            self.total_inimigos_derrotados += 1
            indice = self.batalha_alvo_indice
            if 0 <= indice < len(self.mundo.inimigos):
                del self.mundo.inimigos[indice]
                sprite = self.sprites_inimigos[indice]
                sprite.remove_from_sprite_lists()
            self.em_batalha = False
            self.batalha_resultado = None
            self.batalha_mensagem = ""
            self.batalha_botoes = []

        elif self.batalha_resultado == "derrota":
            arcade.close_window()
        else:
            self.em_batalha = False
            self.batalha_resultado = None
            self.batalha_mensagem = ""
            self.batalha_botoes = []
    def fugir(self):
        if random.random() < 0.5:
            self.batalha_mensagem = "Você fugiu com sucesso!"
            self.batalha_resultado = "fuga"
            self.montar_botao_continuar()
        else:
            dano_recebido = random.randint(1, 5)
            self.jogador_vida -= dano_recebido
            mensagem = f"Não conseguiu fugir! A abóbora causou {dano_recebido} de  dano."
            if self.jogador_vida <= 0:
                self.jogador_vida = 0
                mensagem += "Você foi derrotado..."
                self.batalha_resultado = "derrota"
                self.montar_botao_continuar()
            else:
                self.batalha_resultado = None
                self.montar_botoes_escolha()
            self.batalha_mensagem = mensagem
    def usar_pocao(self):
        if self.jogador_pocoes <= 0:
            return

        self.jogador_pocoes -= 1
        cura = min(CURA_POCAO, self.jogador_vida_max - self.jogador_vida)
        self.jogador_vida += cura
        mensagem = f"Você usou uma poção e recuperou {cura} de vida!"

        dano_recebido = max(1, random.randint(self.batalha_inimigo_ataque - 1, self.batalha_inimigo_ataque + 1))
        self.jogador_vida -= dano_recebido
        mensagem += f"A abóbora aproveitou a deixa e causou {dano_recebido} de dano!"

        if self.jogador_vida <= 0:
            self.jogador_vida = 0
            mensagem += "Você foi derrotado..."
            self.batalha_resultado = "derrota"
            self.montar_botao_continuar()
        else:
            self.batalha_resultado = None
            self.montar_botoes_escolha()

        self.batalha_mensagem = mensagem
janela = JanelaJogo()
arcade.run()

