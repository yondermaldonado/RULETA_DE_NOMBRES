"""
RULETA DE NOMBRES - CASINO EDITION (Pygame)
--------------------------------------------
Ruleta de sorteo con nombres personalizables, estilo casino.

- Agrega / quita nombres desde la interfaz.
- Al ganar, puedes eliminarlo de la ruleta o dejarlo para que pueda
  volver a salir (interruptor en pantalla).
- Interfaz en Español / English (botón arriba a la derecha).
- Sonidos generados por código (sin archivos externos): clics al girar
  y una melodía de victoria.
- Gráficos mejorados: degradado de fondo, luces de marquesina, sombras,
  brillo metálico en el centro y texto con contorno para que se lea
  bien sobre cualquier color.

Para convertir a .exe: ver README.md
"""

import sys
import math
import random

import numpy as np
import pygame

# ----------------------------------------------------------------------
# CONFIGURACIÓN BÁSICA
# ----------------------------------------------------------------------
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

WIDTH, HEIGHT = 1100, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ruleta de Nombres - Casino Edition")
clock = pygame.time.Clock()

# --- Paleta ---
GOLD        = (222, 184, 74)
GOLD_LIGHT  = (250, 220, 130)
GOLD_DARK   = (140, 108, 30)
FELT_TOP    = (16, 92, 48)
FELT_BOTTOM = (4, 32, 17)
PANEL_BG    = (8, 45, 24)
WHITE       = (245, 245, 245)
BLACK       = (15, 15, 15)
RED_ACCENT  = (200, 50, 50)
GRAY        = (120, 120, 120)
GRAY_LIGHT  = (190, 190, 190)

WHEEL_PALETTE = [
    (150, 20, 20),   # rojo vino
    (20, 20, 20),    # negro
    (15, 95, 60),    # verde
    (25, 30, 90),    # azul noche
    (120, 20, 90),   # magenta oscuro
    (150, 90, 15),   # bronce
]

FONT_TITLE = pygame.font.SysFont(None, 50, bold=True)
FONT_BIG   = pygame.font.SysFont(None, 42, bold=True)
FONT_MED   = pygame.font.SysFont(None, 26, bold=True)
FONT_SMALL = pygame.font.SysFont(None, 19, bold=True)
FONT_WIN   = pygame.font.SysFont(None, 60, bold=True)

# ----------------------------------------------------------------------
# TEXTOS BILINGÜES
# ----------------------------------------------------------------------
TEXTS = {
    "es": {
        "title": "RULETA DE NOMBRES",
        "names_label": "Nombres ({n})",
        "placeholder": "Escribe un nombre y presiona Enter",
        "add": "Agregar",
        "clear": "Vaciar",
        "mode_remove": "Modo: Eliminar al ganador",
        "mode_keep": "Modo: Mantener a todos",
        "spin": "GIRAR",
        "spinning": "Girando...",
        "continue": "CONTINUAR",
        "winner": "¡GANADOR!",
        "need_names": "Agrega al menos 2 nombres",
        "max_names": "Máximo de nombres alcanzado",
        "removed_note": "(eliminado de la ruleta)",
        "kept_note": "(sigue en la ruleta)",
    },
    "en": {
        "title": "NAME ROULETTE",
        "names_label": "Names ({n})",
        "placeholder": "Type a name and press Enter",
        "add": "Add",
        "clear": "Clear",
        "mode_remove": "Mode: Remove winner",
        "mode_keep": "Mode: Keep everyone",
        "spin": "SPIN",
        "spinning": "Spinning...",
        "continue": "CONTINUE",
        "winner": "WINNER!",
        "need_names": "Add at least 2 names",
        "max_names": "Maximum names reached",
        "removed_note": "(removed from the wheel)",
        "kept_note": "(still on the wheel)",
    },
}
lang = "es"
T = TEXTS[lang]

MAX_NAMES = 30

# ----------------------------------------------------------------------
# SONIDOS GENERADOS POR CÓDIGO
# ----------------------------------------------------------------------
SAMPLE_RATE = 44100


def make_tone(freq, duration, volume=0.5, wave="sine", decay=True):
    n = max(1, int(SAMPLE_RATE * duration))
    t = np.linspace(0, duration, n, False)
    if wave == "square":
        arr = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave == "noise":
        arr = np.random.uniform(-1, 1, n)
    else:
        arr = np.sin(2 * np.pi * freq * t)
    if decay:
        env = np.linspace(1, 0, n) ** 1.4
        arr = arr * env
    audio = np.clip(arr * volume * 32767, -32767, 32767).astype(np.int16)
    stereo = np.column_stack([audio, audio])
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


tick_sound  = make_tone(1500, 0.025, 0.35, "square")
click_sound = make_tone(750, 0.045, 0.3, "sine")
win_notes   = [make_tone(f, 0.16, 0.55, "sine") for f in (523, 659, 784, 988, 1175)]

# ----------------------------------------------------------------------
# UTILIDADES
# ----------------------------------------------------------------------
def point_on_circle(cx, cy, r, angle_deg):
    rad = math.radians(angle_deg)
    return (cx + r * math.sin(rad), cy - r * math.cos(rad))


def draw_text_outline(surf, text, font, color, center, outline=BLACK, width=2):
    base = font.render(text, True, color)
    ol = font.render(text, True, outline)
    rect = base.get_rect(center=center)
    for dx in (-width, 0, width):
        for dy in (-width, 0, width):
            if dx or dy:
                surf.blit(ol, ol.get_rect(center=(center[0] + dx, center[1] + dy)))
    surf.blit(base, rect)


def draw_text(surf, text, font, color, center):
    label = font.render(text, True, color)
    surf.blit(label, label.get_rect(center=center))


def draw_text_left(surf, text, font, color, pos):
    label = font.render(text, True, color)
    surf.blit(label, label.get_rect(midleft=pos))


def truncate(text, max_chars):
    return text if len(text) <= max_chars else text[: max_chars - 1] + "\u2026"


def make_vertical_gradient(w, h, top_color, bottom_color):
    top = np.array(top_color, dtype=np.float32)
    bottom = np.array(bottom_color, dtype=np.float32)
    factors = np.linspace(0, 1, h).reshape(h, 1, 1)
    grad = top.reshape(1, 1, 3) * (1 - factors) + bottom.reshape(1, 1, 3) * factors
    grad = np.repeat(grad, w, axis=1).astype(np.uint8)
    return pygame.surfarray.make_surface(np.transpose(grad, (1, 0, 2)))


class Button:
    def __init__(self, rect, text, font=FONT_MED, base=GOLD_DARK, hover=GOLD, text_color=BLACK):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.base = base
        self.hover = hover
        self.text_color = text_color
        self.enabled = True

    def draw(self, surf, mouse_pos):
        if not self.enabled:
            color = (70, 70, 70)
            tcolor = (160, 160, 160)
        else:
            color = self.hover if self.rect.collidepoint(mouse_pos) else self.base
            tcolor = self.text_color
        pygame.draw.rect(surf, color, self.rect, border_radius=10)
        pygame.draw.rect(surf, GOLD_LIGHT if self.enabled else GRAY, self.rect, 2, border_radius=10)
        draw_text(surf, self.text, self.font, tcolor, self.rect.center)

    def clicked(self, pos, event):
        return (self.enabled and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1 and self.rect.collidepoint(pos))


class InputBox:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.text = ""
        self.active = False

    def handle_event(self, event):
        submitted = None
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                submitted = self.text.strip()
                self.text = ""
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif len(self.text) < 20 and event.unicode.isprintable():
                self.text += event.unicode
        return submitted

    def draw(self, surf, placeholder):
        pygame.draw.rect(surf, (20, 20, 20), self.rect, border_radius=8)
        border = GOLD_LIGHT if self.active else GOLD_DARK
        pygame.draw.rect(surf, border, self.rect, 2, border_radius=8)
        if self.text:
            draw_text_left(surf, self.text, FONT_MED, WHITE, (self.rect.x + 10, self.rect.centery))
        else:
            draw_text_left(surf, placeholder, FONT_SMALL, GRAY_LIGHT, (self.rect.x + 10, self.rect.centery))


class Particle:
    def __init__(self, pos):
        self.x, self.y = pos
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 7)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 4
        self.life = random.uniform(0.8, 1.6)
        self.age = 0.0
        self.color = random.choice([GOLD, GOLD_LIGHT, WHITE, RED_ACCENT])
        self.size = random.randint(3, 6)

    def update(self, dt):
        self.age += dt
        self.vy += 9.0 * dt
        self.x += self.vx
        self.y += self.vy
        return self.age < self.life

    def draw(self, surf):
        alpha = max(0, 1 - self.age / self.life)
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        color = (*self.color, int(255 * alpha))
        pygame.draw.rect(s, color, (0, 0, self.size * 2, self.size * 2), border_radius=2)
        surf.blit(s, (self.x - self.size, self.y - self.size))


# ----------------------------------------------------------------------
# FONDO Y DECORACIÓN
# ----------------------------------------------------------------------
background = make_vertical_gradient(WIDTH - 20, HEIGHT - 20, FELT_TOP, FELT_BOTTOM)

bulb_positions = []
inset = 14
step = 34
top_y = 10
bottom_y = HEIGHT - 10
left_x = 10
right_x = WIDTH - 10
x = left_x
while x < right_x:
    bulb_positions.append((x, top_y))
    bulb_positions.append((x, bottom_y))
    x += step
y = top_y
while y < bottom_y:
    bulb_positions.append((left_x, y))
    bulb_positions.append((right_x, y))
    y += step

WHEEL_CENTER = (300, 400)
WHEEL_RADIUS = 240

# ----------------------------------------------------------------------
# ESTADO DEL JUEGO
# ----------------------------------------------------------------------
names = ["Ana", "Luis", "Sofía", "Carlos", "María"]
remove_on_win = False
state = "idle"          # idle | spinning | result
wheel_rotation = 0.0
final_rotation = 0.0
spin_start_rotation = 0.0
spin_start_time = 0
SPIN_DURATION = 4200
last_slot_count = 0
winner_name = ""
particles = []
pending_jingle = []
jingle_next_time = 0
scroll_offset = 0
wheel_surface = None
angle_per_slot = 360.0

INPUT_RECT = (630, 150, 300, 44)
input_box = InputBox(INPUT_RECT)

add_button = Button((940, 150, 110, 44), T["add"], font=FONT_SMALL)
clear_button = Button((940, 200, 110, 34), T["clear"], font=FONT_SMALL, base=(90, 30, 30), hover=(140, 40, 40), text_color=WHITE)
mode_button = Button((630, 470, 420, 46), T["mode_keep"], font=FONT_SMALL)
spin_button = Button((630, 540, 420, 64), T["spin"], font=FONT_BIG, base=GOLD, hover=GOLD_LIGHT)
continue_button = Button((630, 540, 420, 64), T["continue"], font=FONT_BIG, base=GOLD, hover=GOLD_LIGHT)
lang_button = Button((WIDTH - 130, 20, 100, 40), "EN", font=FONT_MED)

NAMES_LIST_RECT = pygame.Rect(630, 250, 420, 200)
ROW_H = 30


def rebuild_wheel():
    global wheel_surface, angle_per_slot
    n = max(len(names), 1)
    angle_per_slot = 360.0 / n
    size = WHEEL_RADIUS * 2 + 30
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2

    if len(names) == 0:
        pygame.draw.circle(surf, (40, 40, 40), (c, c), WHEEL_RADIUS)
    else:
        font_size = 22 if n <= 8 else 17 if n <= 14 else 14 if n <= 20 else 11
        font = pygame.font.SysFont(None, font_size, bold=True)
        max_chars = 16 if n <= 8 else 12 if n <= 14 else 9 if n <= 20 else 7

        for i, nm in enumerate(names):
            angle_i = i * angle_per_slot
            half = angle_per_slot / 2
            pts = [(c, c)]
            steps = max(2, int(angle_per_slot / 8) + 1)
            for s in range(steps + 1):
                a = angle_i - half + (2 * half) * s / steps
                pts.append(point_on_circle(c, c, WHEEL_RADIUS, a))
            color = WHEEL_PALETTE[i % len(WHEEL_PALETTE)]
            pygame.draw.polygon(surf, color, pts)
            pygame.draw.polygon(surf, GOLD_DARK, pts, 1)

            label = font.render(truncate(nm, max_chars), True, WHITE)
            label = pygame.transform.rotate(label, -angle_i)
            lx, ly = point_on_circle(c, c, WHEEL_RADIUS * 0.82, angle_i)
            surf.blit(label, label.get_rect(center=(lx, ly)))

            stud_x, stud_y = point_on_circle(c, c, WHEEL_RADIUS - 4, angle_i - half)
            pygame.draw.circle(surf, GOLD_LIGHT, (int(stud_x), int(stud_y)), 3)

    pygame.draw.circle(surf, GOLD, (c, c), WHEEL_RADIUS, 6)
    pygame.draw.circle(surf, GOLD_DARK, (c, c), 38)
    pygame.draw.circle(surf, GOLD, (c, c), 38, 3)
    pygame.draw.circle(surf, (110, 15, 15), (c, c), 28)
    pygame.draw.circle(surf, GOLD, (c, c), 28, 2)
    shine = pygame.Surface((16, 10), pygame.SRCALPHA)
    pygame.draw.ellipse(shine, (255, 255, 255, 110), shine.get_rect())
    surf.blit(shine, (c - 18, c - 22))

    wheel_surface = surf


rebuild_wheel()


def add_name(text):
    global scroll_offset
    text = text.strip()
    if not text or len(names) >= MAX_NAMES:
        return
    names.append(truncate(text, 20))
    rebuild_wheel()


def remove_name(index):
    if 0 <= index < len(names):
        names.pop(index)
        rebuild_wheel()


def start_spin():
    global state, final_rotation, spin_start_rotation, spin_start_time, last_slot_count
    if len(names) < 2:
        return
    winning_index = random.randrange(len(names))
    n_spins = random.randint(5, 8)
    start_rotation = wheel_rotation % 360
    target_mod = (-(winning_index * angle_per_slot)) % 360
    delta = (target_mod - start_rotation) % 360
    final_rotation = start_rotation + n_spins * 360 + delta

    spin_start_rotation = start_rotation
    spin_start_time = pygame.time.get_ticks()
    last_slot_count = 0
    state = "spinning"
    winning_index_holder["idx"] = winning_index


winning_index_holder = {"idx": 0}


def resolve_spin():
    global state, winner_name, particles, pending_jingle, jingle_next_time
    idx = winning_index_holder["idx"]
    winner_name = names[idx] if 0 <= idx < len(names) else "?"
    particles = [Particle(WHEEL_CENTER) for _ in range(70)]
    pending_jingle = list(win_notes)
    jingle_next_time = pygame.time.get_ticks()
    state = "result"


def continue_after_result():
    global state
    idx = winning_index_holder["idx"]
    if remove_on_win and 0 <= idx < len(names):
        names.pop(idx)
        rebuild_wheel()
    state = "idle"


# ----------------------------------------------------------------------
# LOOP PRINCIPAL
# ----------------------------------------------------------------------
running = True
IDLE_SPIN_SPEED = 6.0  # grados/seg

while running:
    dt_ms = clock.tick(60)
    dt = dt_ms / 1000.0
    now = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEWHEEL and NAMES_LIST_RECT.collidepoint(mouse_pos):
            max_scroll = max(0, len(names) * ROW_H - NAMES_LIST_RECT.height)
            scroll_offset = max(0, min(max_scroll, scroll_offset - event.y * ROW_H))

        submitted = input_box.handle_event(event)
        if submitted is not None:
            add_name(submitted)
            click_sound.play()

        if lang_button.clicked(mouse_pos, event):
            lang = "en" if lang == "es" else "es"
            T = TEXTS[lang]
            click_sound.play()

        if state == "idle":
            if add_button.clicked(mouse_pos, event):
                add_name(input_box.text)
                input_box.text = ""
                click_sound.play()
            if clear_button.clicked(mouse_pos, event):
                names.clear()
                rebuild_wheel()
                click_sound.play()
            if mode_button.clicked(mouse_pos, event):
                remove_on_win = not remove_on_win
                click_sound.play()
            if spin_button.clicked(mouse_pos, event):
                click_sound.play()
                start_spin()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if NAMES_LIST_RECT.collidepoint(event.pos):
                    rel_y = event.pos[1] - NAMES_LIST_RECT.y + scroll_offset
                    row = rel_y // ROW_H
                    if 0 <= row < len(names):
                        row_rect = pygame.Rect(NAMES_LIST_RECT.right - 28,
                                                NAMES_LIST_RECT.y + row * ROW_H - scroll_offset,
                                                24, ROW_H)
                        if row_rect.collidepoint(event.pos):
                            remove_name(row)
                            click_sound.play()

        elif state == "result":
            if continue_button.clicked(mouse_pos, event):
                click_sound.play()
                continue_after_result()

    spin_button.enabled = len(names) >= 2

    # --- lógica ---
    if state == "idle":
        wheel_rotation = (wheel_rotation + IDLE_SPIN_SPEED * dt) % 360

    elif state == "spinning":
        elapsed = now - spin_start_time
        t = min(1.0, elapsed / SPIN_DURATION)
        eased = 1 - (1 - t) ** 3
        wheel_rotation = spin_start_rotation + eased * (final_rotation - spin_start_rotation)

        raw_progress = eased * (final_rotation - spin_start_rotation)
        slot_count = raw_progress / angle_per_slot
        if int(slot_count) > last_slot_count:
            last_slot_count = int(slot_count)
            tick_sound.play()

        if t >= 1.0:
            resolve_spin()

    particles = [p for p in particles if p.update(dt)]

    if pending_jingle and now >= jingle_next_time:
        pending_jingle.pop(0).play()
        jingle_next_time = now + 130

    mode_button.text = T["mode_remove"] if remove_on_win else T["mode_keep"]
    add_button.text = T["add"]
    clear_button.text = T["clear"]
    spin_button.text = T["spin"]
    continue_button.text = T["continue"]
    lang_button.text = "EN" if lang == "es" else "ES"

    # ------------------------------------------------------------------
    # DIBUJO
    # ------------------------------------------------------------------
    screen.fill(FELT_BOTTOM)
    screen.blit(background, (10, 10))
    pygame.draw.rect(screen, GOLD_DARK, (10, 10, WIDTH - 20, HEIGHT - 20), 5, border_radius=22)

    for i, (bx, by) in enumerate(bulb_positions):
        brightness = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(now / 220 + i * 0.6))
        col = tuple(int(c * brightness) for c in GOLD_LIGHT)
        pygame.draw.circle(screen, col, (bx, by), 4)

    draw_text_outline(screen, T["title"], FONT_TITLE, GOLD_LIGHT, (WIDTH // 2 - 60, 46))
    lang_button.draw(screen, mouse_pos)

    # sombra de la rueda
    shadow = pygame.Surface((WHEEL_RADIUS * 2 + 40, 40), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
    screen.blit(shadow, (WHEEL_CENTER[0] - WHEEL_RADIUS - 20, WHEEL_CENTER[1] + WHEEL_RADIUS - 15))

    rotated = pygame.transform.rotate(wheel_surface, -wheel_rotation)
    screen.blit(rotated, rotated.get_rect(center=WHEEL_CENTER))

    # puntero
    px, py = WHEEL_CENTER[0], WHEEL_CENTER[1] - WHEEL_RADIUS - 10
    pygame.draw.polygon(screen, (10, 10, 10),
                         [(px - 14, py - 22), (px + 14, py - 22), (px, py + 8)])
    pygame.draw.polygon(screen, GOLD,
                         [(px - 11, py - 18), (px + 11, py - 18), (px, py + 4)])
    pygame.draw.circle(screen, RED_ACCENT, (px, py - 18), 5)

    # panel derecho
    panel_rect = pygame.Rect(610, 100, WIDTH - 640, HEIGHT - 130)
    pygame.draw.rect(screen, PANEL_BG, panel_rect, border_radius=16)
    pygame.draw.rect(screen, GOLD_DARK, panel_rect, 3, border_radius=16)

    if state == "idle":
        input_box.draw(screen, T["placeholder"])
        add_button.draw(screen, mouse_pos)
        clear_button.draw(screen, mouse_pos)

        draw_text_left(screen, T["names_label"].format(n=len(names)), FONT_MED, GOLD_LIGHT,
                        (NAMES_LIST_RECT.x, NAMES_LIST_RECT.y - 18))

        list_surf = pygame.Surface(NAMES_LIST_RECT.size, pygame.SRCALPHA)
        for i, nm in enumerate(names):
            row_y = i * ROW_H - scroll_offset
            if -ROW_H < row_y < NAMES_LIST_RECT.height:
                if i % 2 == 0:
                    pygame.draw.rect(list_surf, (255, 255, 255, 12), (0, row_y, NAMES_LIST_RECT.width, ROW_H))
                draw_text_left(list_surf, f"{i + 1}. {nm}", FONT_SMALL, WHITE, (8, row_y + ROW_H // 2))
                x_rect = pygame.Rect(NAMES_LIST_RECT.width - 28, row_y + 4, 22, 22)
                pygame.draw.rect(list_surf, (110, 25, 25), x_rect, border_radius=6)
                draw_text(list_surf, "x", FONT_SMALL, WHITE, x_rect.center)
        screen.blit(list_surf, NAMES_LIST_RECT.topleft)
        pygame.draw.rect(screen, GOLD_DARK, NAMES_LIST_RECT, 2, border_radius=8)

        mode_button.draw(screen, mouse_pos)
        spin_button.draw(screen, mouse_pos)
        if len(names) < 2:
            draw_text(screen, T["need_names"], FONT_SMALL, RED_ACCENT,
                      (spin_button.rect.centerx, spin_button.rect.bottom + 18))

    elif state == "spinning":
        draw_text(screen, T["spinning"], FONT_BIG, GOLD_LIGHT, (panel_rect.centerx, panel_rect.centery))

    elif state == "result":
        glow = 0.6 + 0.4 * math.sin(now / 150)
        glow_color = tuple(int(c * glow) for c in GOLD_LIGHT)
        draw_text(screen, T["winner"], FONT_MED, glow_color, (panel_rect.centerx, panel_rect.y + 70))
        draw_text_outline(screen, truncate(winner_name, 16), FONT_WIN, WHITE,
                           (panel_rect.centerx, panel_rect.centery - 20))
        note = T["removed_note"] if remove_on_win else T["kept_note"]
        draw_text(screen, note, FONT_SMALL, GRAY_LIGHT, (panel_rect.centerx, panel_rect.centery + 50))
        continue_button.draw(screen, mouse_pos)

    for p in particles:
        p.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()
