#!/usr/bin/env python3
"""Rendert die Einzelbilder der Boot-Intro als PNG-Sequenz.

Panel ist ein natives 720x1280 DSI-Hochformat-Display (kein 800x480 HDMI
wie urspruenglich angenommen - per `mpv --drm-mode=help` auf dem Geraet
bestaetigt: "Mode 0: 720x1280"). Die gesamte Komposition ist fuer dieses
Hochformat gebaut, kein nachtraegliches Rotieren/Stauchen mehr noetig.

Storyboard (Sekunden, insgesamt ~19s):
  0.0-0.4  Power-On          - einzelner Punkt zuendet mittig
  0.4-4.0  Grid Init         - Netzwerk-Gitter baut sich radial auf, Scanline-Sweep
  4.0-8.0  Wordmark          - "Luca's" wischt sich zuegig ein, "PROJECTS", Ladebalken
  8.0-14.5 Status-Handshake  - Statuszeilen (Typewriter) + Punktreihe + Prozentzaehler
  14.5-18.0 Connect/Handoff  - Flash, Punkte pulsen gruen, Wordmark schrumpft ins Eck
  18.0-19.0 Hold             - reiner Hintergrund, identisch zum BG der echten App

Uebergaenge sind bewusst strafer getaktet als in der ersten Fassung
(schnelleres Wipe/Stagger/Shrink), dazu durchgehend aktiv: driftende
Partikel, atmendes Wordmark-Glow, periodische Scanline-Sweeps und ein
Ken-Burns-Zoom - damit auf der grossen Flaeche sichtbar was los ist.

Farben aus pph_hub/pph71_ui.py (aktuelles PPH-7.1.0-Theme) uebernommen,
Beschriftung durch "Luca's / Projects" ersetzt.
"""
import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---- Konfiguration --------------------------------------------------------

WIDTH, HEIGHT = 720, 1280
FPS = 25
DURATION = 19.0
FRAME_COUNT = int(DURATION * FPS)

OUT_DIR = Path(__file__).parent / "build" / "frames"

# Palette (aus src/v7.1.0/pph71_ui.py)
BG = (0x07, 0x10, 0x0E)
SURFACE = (0x11, 0x1A, 0x17)
SURFACE2 = (0x1A, 0x25, 0x21)
BORDER = (0x31, 0x41, 0x39)
TEXT = (0xF7, 0xFA, 0xF5)
MUTED = (0x9A, 0xA7, 0x9E)
CYAN = (0x4F, 0xE3, 0xC1)
GREEN = (0xA6, 0xF0, 0x6A)

CENTER = (WIDTH // 2, 520)

FONT_CANDIDATES_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Raspberry Pi OS
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",  # Arch/CachyOS
]
FONT_CANDIDATES_MONO = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf",
]


def _load_font(candidates, size):
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


FONT_WORDMARK = lambda size: _load_font(FONT_CANDIDATES_BOLD, size)
FONT_MONO = lambda size: _load_font(FONT_CANDIDATES_MONO, size)


def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_out_expo(t):
    t = max(0.0, min(1.0, t))
    return 1.0 if t >= 1.0 else 1 - 2 ** (-10 * t)


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def blend_over(base, layer):
    """layer ist RGBA-Image, base RGB-Image gleicher Groesse."""
    base.paste(layer, (0, 0), layer)


# ---- Ambiente: driftende Partikel ------------------------------------------

_rng = random.Random(20260812)
PARTICLES = [
    {
        "x": _rng.uniform(0, WIDTH),
        "y": _rng.uniform(0, HEIGHT),
        "phase": _rng.uniform(0, math.tau),
        "speed": _rng.uniform(0.12, 0.32),
        "drift": _rng.uniform(8, 24),
        "size": _rng.uniform(0.9, 2.1),
    }
    for _ in range(110)
]


def draw_particles(draw, t, alpha_mult=1.0):
    if alpha_mult <= 0:
        return
    for p in PARTICLES:
        twinkle = 0.5 + 0.5 * math.sin(t * p["speed"] * math.tau + p["phase"])
        a = int(75 * twinkle * alpha_mult)
        if a <= 1:
            continue
        x = p["x"] + math.sin(t * 0.09 + p["phase"]) * p["drift"]
        y = p["y"] + math.cos(t * 0.07 + p["phase"] * 1.3) * p["drift"] * 0.6
        r = p["size"]
        draw.ellipse([x - r, y - r, x + r, y + r], fill=CYAN + (a,))


# ---- Phase 1: Grid ---------------------------------------------------------

GRID_STEP = 60
GRID_POINTS = [
    (x, y)
    for x in range(0, WIDTH + 1, GRID_STEP)
    for y in range(0, HEIGHT + 1, GRID_STEP)
]


def draw_grid(draw, t_grid, base_alpha=1.0):
    """t_grid: 0..1 Aufbau-Fortschritt (radial von CENTER aus)."""
    max_dist = math.hypot(WIDTH, HEIGHT) / 2
    reach = max_dist * ease_out_cubic(t_grid)

    for (x1, y1) in GRID_POINTS:
        d = math.hypot(x1 - CENTER[0], y1 - CENTER[1])
        if d > reach + 40:
            continue
        local_t = max(0.0, min(1.0, (reach - d) / 40 + 1))
        a = int(90 * local_t * base_alpha)
        if a <= 0:
            continue
        if x1 + GRID_STEP <= WIDTH:
            d2 = math.hypot(x1 + GRID_STEP - CENTER[0], y1 - CENTER[1])
            if d2 <= reach + 40:
                draw.line([(x1, y1), (x1 + GRID_STEP, y1)], fill=BORDER + (a,), width=1)
        if y1 + GRID_STEP <= HEIGHT:
            d2 = math.hypot(x1 - CENTER[0], y1 + GRID_STEP - CENTER[1])
            if d2 <= reach + 40:
                draw.line([(x1, y1), (x1, y1 + GRID_STEP)], fill=BORDER + (a,), width=1)

    # Knoten pulsieren an den Kreuzungen kurz nachdem die Wellenfront sie erreicht
    for (x, y) in GRID_POINTS:
        d = math.hypot(x - CENTER[0], y - CENTER[1])
        delta = reach - d
        if 0 <= delta <= 22:
            pulse_t = delta / 22
            r = 1.8 + 4.2 * math.sin(pulse_t * math.pi)
            a = int(220 * math.sin(pulse_t * math.pi) * base_alpha)
            if a > 0:
                draw.ellipse(
                    [x - r, y - r, x + r, y + r],
                    fill=CYAN + (a,),
                )
        elif delta > 22:
            a = int(70 * base_alpha)
            draw.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=BORDER + (a,))


def draw_scanline(draw, t, alpha_scale=1.0):
    """t: 0..1 einmaliger Sweep von oben nach unten."""
    if not (0.0 <= t <= 1.0):
        return
    y = int(HEIGHT * ease_in_out(t))
    band = 40
    for i in range(band):
        yy = y - band // 2 + i
        if 0 <= yy < HEIGHT:
            a = int(60 * (1 - abs(i - band / 2) / (band / 2)) * alpha_scale)
            if a > 0:
                draw.line([(0, yy), (WIDTH, yy)], fill=CYAN + (a,), width=1)


def draw_periodic_sweep(draw, t, period=3.2, active_frac=0.35, alpha_scale=0.4):
    """Wiederkehrender, leiser Scanline-Sweep, damit das Grid im
    Hintergrund waehrend der ruhigeren Phasen in Bewegung bleibt."""
    phase = (t % period) / period
    if phase < active_frac:
        draw_scanline(draw, phase / active_frac, alpha_scale=alpha_scale)


# ---- Phase 2: Wordmark -----------------------------------------------------

WORDMARK = "Luca's"
TAGLINE = "P R O J E C T S"


def draw_wordmark_glow(img, t, scale=1.0, offset=(0, 0)):
    """Atmendes Glow hinter dem Schriftzug - haelt die Wordmark-Phase
    sichtbar in Bewegung statt eingefroren zu wirken."""
    breathe = 0.5 + 0.5 * math.sin(t * 1.1)
    radius = (95 + 20 * breathe) * scale
    alpha = int((55 + 28 * breathe))
    cx = CENTER[0] + offset[0]
    cy = CENTER[1] - 8 * scale + offset[1]
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ldraw = ImageDraw.Draw(layer)
    ldraw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=CYAN + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(26 * scale + 6))
    blend_over(img, layer)


def draw_wordmark(img, draw, wipe_t, tagline_a, bar_t, scale=1.0, offset=(0, 0), t=0.0):
    font = FONT_WORDMARK(int(66 * scale))
    tag_font = FONT_WORDMARK(int(15 * scale))

    bbox = draw.textbbox((0, 0), WORDMARK, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = CENTER[0] - w / 2 - bbox[0] + offset[0]
    y = CENTER[1] - h / 2 - bbox[1] - 20 * scale + offset[1]

    if wipe_t > 0:
        text_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        tdraw = ImageDraw.Draw(text_layer)
        glow_a = int(90 * min(1.0, wipe_t * 2))
        tdraw.text((x, y), WORDMARK, font=font, fill=CYAN + (glow_a,))
        text_layer = text_layer.filter(ImageFilter.GaussianBlur(7))
        tdraw2 = ImageDraw.Draw(text_layer)
        tdraw2.text((x, y), WORDMARK, font=font, fill=TEXT + (255,))

        reveal_w = int(w * ease_out_expo(wipe_t)) + 4
        mask = Image.new("L", img.size, 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rectangle([x - 4, 0, x + reveal_w, img.size[1]], fill=255)
        text_layer.putalpha(Image.composite(text_layer.split()[3], Image.new("L", img.size, 0), mask))
        blend_over(img, text_layer)

    if tagline_a > 0:
        tbbox = draw.textbbox((0, 0), TAGLINE, font=tag_font)
        tw, th = tbbox[2] - tbbox[0], tbbox[3] - tbbox[1]
        tx = CENTER[0] - tw / 2 - tbbox[0] + offset[0]
        ty = y + h + 16 * scale
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ldraw = ImageDraw.Draw(layer)
        ldraw.text((tx, ty), TAGLINE, font=tag_font, fill=MUTED + (int(255 * tagline_a),))
        blend_over(img, layer)

        if bar_t > 0:
            bar_w = 210 * scale
            bar_x = CENTER[0] - bar_w / 2 + offset[0]
            bar_y = ty + th + 16 * scale
            layer2 = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ldraw2 = ImageDraw.Draw(layer2)
            ldraw2.rectangle(
                [bar_x, bar_y, bar_x + bar_w, bar_y + 3 * scale], fill=BORDER + (200,)
            )
            fill_w = bar_w * ease_out_expo(bar_t)
            ldraw2.rectangle(
                [bar_x, bar_y, bar_x + fill_w, bar_y + 3 * scale],
                fill=CYAN + (255,),
            )
            if bar_t >= 0.999:
                # Ladebalken ist fertig - ein Comet laeuft weiter drueber,
                # damit die Statuszeile nicht wie eingefroren wirkt.
                pos = (math.sin(t * 1.7) + 1) / 2
                comet_x = bar_x + bar_w * pos
                cr = 5.5 * scale
                comet = Image.new("RGBA", img.size, (0, 0, 0, 0))
                cdraw = ImageDraw.Draw(comet)
                cdraw.ellipse(
                    [comet_x - cr, bar_y - cr + 1.5 * scale, comet_x + cr, bar_y + cr + 1.5 * scale],
                    fill=TEXT + (220,),
                )
                comet = comet.filter(ImageFilter.GaussianBlur(3))
                blend_over(layer2, comet)
            blend_over(img, layer2)

    return x, y, w, h


# ---- Phase 3: Status-Handshake ---------------------------------------------

STATUS_LINES = ["SYSTEM INIT", "STORAGE MOUNT", "SERVICES", "PROJECTS READY"]
DOT_COUNT = 6


def draw_status(draw, t_phase):
    """t_phase: 0..1 Fortschritt innerhalb Phase 3. Zeilen werden per
    Typewriter-Effekt Zeichen fuer Zeichen aufgebaut."""
    font = FONT_MONO(16)
    line_h = 28
    start_x, start_y = 44, HEIGHT - 90 - line_h * len(STATUS_LINES)

    stagger = 1.0 / (len(STATUS_LINES) + 0.6)
    for i, label in enumerate(STATUS_LINES):
        appear_t = (t_phase - i * stagger) / stagger
        if appear_t <= 0:
            continue
        appear_t = min(1.0, appear_t)
        y = start_y + i * line_h
        dots = "." * max(3, 24 - len(label))
        full = f"{label} {dots}"
        type_t = min(1.0, appear_t * 1.9)
        n_chars = max(1, int(round(len(full) * ease_out_cubic(type_t))))
        shown = full[:n_chars]
        draw.text((start_x, y), shown, font=font, fill=TEXT + (255,))
        ok_t = min(1.0, max(0.0, (appear_t - 0.65) / 0.35))
        if ok_t > 0 and n_chars >= len(full):
            ok_color = lerp_color(MUTED, GREEN, ok_t)
            bbox = draw.textbbox((start_x, y), full + " ", font=font)
            draw.text((bbox[2], y), "OK", font=font, fill=ok_color + (255,))

    dot_stagger = 1.0 / (DOT_COUNT + 0.6)
    dot_y = start_y - 40
    dot_r = 6
    dot_gap = 26
    dots_w = dot_gap * (DOT_COUNT - 1)
    dot_x0 = WIDTH - 44 - dots_w
    for i in range(DOT_COUNT):
        lit_t = (t_phase - i * dot_stagger) / dot_stagger
        lit_t = max(0.0, min(1.0, lit_t))
        color = lerp_color(BORDER, CYAN, ease_out_cubic(lit_t))
        r = dot_r + 2.4 * ease_out_cubic(lit_t) * (1 - lit_t) * 2
        x = dot_x0 + i * dot_gap
        draw.ellipse([x - r, dot_y - r, x + r, dot_y + r], fill=color + (255,))

    pct = int(100 * ease_out_cubic(t_phase))
    pfont = FONT_MONO(19)
    draw.text((WIDTH - 100, 56), f"{pct:>3d}%", font=pfont, fill=CYAN + (255,))


# ---- Hauptschleife -----------------------------------------------------

P0, P1, P2, P3, P4, P5 = 0.4, 4.0, 8.0, 14.5, 18.0, DURATION


def render():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for frame_idx in range(FRAME_COUNT):
        t = frame_idx / FPS
        img = Image.new("RGB", (WIDTH, HEIGHT), BG)

        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)

        particle_alpha = max(0.0, min(1.0, (t - 0.3) / 0.4))

        if t < P0:
            # Phase 0: Power-On Punkt waechst ein
            p = ease_out_cubic(t / P0)
            r = 2 + 4 * p
            a = int(255 * p)
            odraw.ellipse(
                [CENTER[0] - r, CENTER[1] - r, CENTER[0] + r, CENTER[1] + r],
                fill=CYAN + (a,),
            )

        elif t < P1:
            draw_particles(odraw, t, particle_alpha)
            tp = (t - P0) / (P1 - P0)
            draw_grid(odraw, tp)
            if tp < 0.5:
                draw_scanline(odraw, tp / 0.5)

        elif t < P2:
            draw_particles(odraw, t, particle_alpha)
            draw_grid(odraw, 1.0, base_alpha=0.24)
            draw_periodic_sweep(odraw, t - P1)
            tp = (t - P1) / (P2 - P1)
            wipe_t = min(1.0, tp / 0.32)
            tagline_a = max(0.0, min(1.0, (tp - 0.30) / 0.25))
            bar_t = max(0.0, min(1.0, (tp - 0.42) / 0.35))
            if wipe_t > 0.05:
                draw_wordmark_glow(img, t)
            draw_wordmark(img, odraw, wipe_t, tagline_a, bar_t, t=t)

        elif t < P3:
            draw_particles(odraw, t, particle_alpha)
            draw_grid(odraw, 1.0, base_alpha=0.24)
            draw_periodic_sweep(odraw, t - P1)
            draw_wordmark_glow(img, t)
            draw_wordmark(img, odraw, 1.0, 1.0, 1.0, t=t)
            tp = (t - P2) / (P3 - P2)
            draw_status(odraw, tp)

        elif t < P4:
            tp = (t - P3) / (P4 - P3)
            grid_alpha = max(0.0, 0.24 * (1 - min(1.0, tp / 0.5)))
            draw_grid(odraw, 1.0, base_alpha=grid_alpha)
            draw_particles(odraw, t, particle_alpha * (1 - min(1.0, tp / 0.5)))

            # Flash + synchrones Gruen-Pulsieren der Punkte kurz zu Beginn
            if tp < 0.22:
                flash_t = tp / 0.22
                flash_a = int(140 * math.sin(flash_t * math.pi))
                odraw.rectangle([0, 0, WIDTH, HEIGHT], fill=CYAN + (max(0, flash_a),))
                pulse = math.sin(flash_t * math.pi)
                dot_y = HEIGHT - 90 - 28 * len(STATUS_LINES) - 40
                dot_gap = 26
                dots_w = dot_gap * (DOT_COUNT - 1)
                dot_x0 = WIDTH - 44 - dots_w
                for i in range(DOT_COUNT):
                    x = dot_x0 + i * dot_gap
                    r = 6 + 3.5 * pulse
                    odraw.ellipse(
                        [x - r, dot_y - r, x + r, dot_y + r],
                        fill=GREEN + (int(255 * (0.5 + 0.5 * pulse)),),
                    )
                draw_status(odraw, 1.0)

            # Wordmark schrumpft und wandert Richtung oben-links (App-Header-Position)
            shrink_t = ease_in_out(min(1.0, tp / 0.7))
            scale = lerp(1.0, 0.4, shrink_t)
            target_offset = (
                -CENTER[0] + 100,
                -CENTER[1] + 60,
            )
            offset = (target_offset[0] * shrink_t, target_offset[1] * shrink_t)
            wm_alpha_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            wdraw = ImageDraw.Draw(wm_alpha_layer)
            draw_wordmark(img, wdraw, 1.0, 1.0, 1.0, scale=scale, offset=offset, t=t)
            blend_over(img, wm_alpha_layer)

            # Restliches Overlay (Grid/Flash) ausblenden lassen ueber base image
            final_fade = max(0.0, min(1.0, (tp - 0.72) / 0.28))
            if final_fade > 0:
                fadeover = Image.new("RGBA", (WIDTH, HEIGHT), BG + (int(255 * final_fade),))
                blend_over(img, fadeover)

        else:
            pass  # Phase 5: reiner BG-Hintergrund, identisch zur echten App

        blend_over(img, overlay)

        # Sanfter Ken-Burns-Zoom uebers gesamte Video.
        zoom = 1.0 + 0.055 * (t / DURATION)
        if zoom > 1.0005:
            nw, nh = int(WIDTH * zoom), int(HEIGHT * zoom)
            big = img.resize((nw, nh), Image.LANCZOS)
            left, top = (nw - WIDTH) // 2, (nh - HEIGHT) // 2
            img = big.crop((left, top, left + WIDTH, top + HEIGHT))

        img.save(OUT_DIR / f"frame_{frame_idx:05d}.png")

    print(f"{FRAME_COUNT} Frames geschrieben nach {OUT_DIR}")


if __name__ == "__main__":
    render()
