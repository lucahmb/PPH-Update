#!/usr/bin/env python3
"""Rendert die Einzelbilder der Boot-Intro als PNG-Sequenz.

Storyboard (Sekunden):
  0.0-0.5  Power-On          - einzelner Punkt zuendet mittig
  0.5-5.0  Grid Init         - Netzwerk-Gitter baut sich radial auf, Scanline-Sweep
  5.0-10.0 Wordmark          - "Luca's" wischt sich ein, "PROJECTS" faded, Ladebalken
  10.0-17.0 Status-Handshake - Statuszeilen (Typewriter) + Punktreihe + Prozentzaehler
  17.0-21.0 Connect/Handoff  - Flash, Punkte pulsen gruen, Wordmark schrumpft ins Eck, Grid loest sich auf
  21.0-22.0 Hold             - reiner Hintergrund, identisch zum BG der echten App

Durchgehend aktiv: driftende/twinkelnde Hintergrundpartikel, ein
"atmendes" Glow hinter dem Schriftzug, periodische leise Scanline-Sweeps
und ein sehr sanfter Ken-Burns-Zoom uebers gesamte Bild - macht die
Sequenz auch in den ruhigeren Phasen sichtbar lebendig statt statisch.

Farben aus pph_hub/pph71_ui.py (aktuelles PPH-7.1.0-Theme) uebernommen,
Beschriftung durch "Luca's / Projects" ersetzt.
"""
import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---- Konfiguration --------------------------------------------------------

WIDTH, HEIGHT = 800, 480
FPS = 25
DURATION = 22.0
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

CENTER = (WIDTH // 2, HEIGHT // 2 - 20)

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
        "drift": _rng.uniform(6, 20),
        "size": _rng.uniform(0.8, 1.9),
    }
    for _ in range(46)
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

GRID_STEP = 40
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
        if d > reach + 30:
            continue
        local_t = max(0.0, min(1.0, (reach - d) / 30 + 1))
        a = int(90 * local_t * base_alpha)
        if a <= 0:
            continue
        if x1 + GRID_STEP <= WIDTH:
            d2 = math.hypot(x1 + GRID_STEP - CENTER[0], y1 - CENTER[1])
            if d2 <= reach + 30:
                draw.line([(x1, y1), (x1 + GRID_STEP, y1)], fill=BORDER + (a,), width=1)
        if y1 + GRID_STEP <= HEIGHT:
            d2 = math.hypot(x1 - CENTER[0], y1 + GRID_STEP - CENTER[1])
            if d2 <= reach + 30:
                draw.line([(x1, y1), (x1, y1 + GRID_STEP)], fill=BORDER + (a,), width=1)

    # Knoten pulsieren an den Kreuzungen kurz nachdem die Wellenfront sie erreicht
    for (x, y) in GRID_POINTS:
        d = math.hypot(x - CENTER[0], y - CENTER[1])
        delta = reach - d
        if 0 <= delta <= 18:
            pulse_t = delta / 18
            r = 1.5 + 3.5 * math.sin(pulse_t * math.pi)
            a = int(220 * math.sin(pulse_t * math.pi) * base_alpha)
            if a > 0:
                draw.ellipse(
                    [x - r, y - r, x + r, y + r],
                    fill=CYAN + (a,),
                )
        elif delta > 18:
            a = int(70 * base_alpha)
            draw.ellipse([x - 1.4, y - 1.4, x + 1.4, y + 1.4], fill=BORDER + (a,))


def draw_scanline(draw, t, alpha_scale=1.0):
    """t: 0..1 einmaliger Sweep von oben nach unten."""
    if not (0.0 <= t <= 1.0):
        return
    y = int(HEIGHT * ease_in_out(t))
    band = 26
    for i in range(band):
        yy = y - band // 2 + i
        if 0 <= yy < HEIGHT:
            a = int(60 * (1 - abs(i - band / 2) / (band / 2)) * alpha_scale)
            if a > 0:
                draw.line([(0, yy), (WIDTH, yy)], fill=CYAN + (a,), width=1)


def draw_periodic_sweep(draw, t, period=4.5, active_frac=0.3, alpha_scale=0.35):
    """Leiser, wiederkehrender Scanline-Sweep, damit das Grid im Hintergrund
    waehrend der ruhigeren Phasen nicht komplett statisch wirkt."""
    phase = (t % period) / period
    if phase < active_frac:
        draw_scanline(draw, phase / active_frac, alpha_scale=alpha_scale)


# ---- Phase 2: Wordmark -----------------------------------------------------

WORDMARK = "Luca's"
TAGLINE = "P R O J E C T S"


def draw_wordmark_glow(img, t, scale=1.0, offset=(0, 0)):
    """Langsam atmendes Glow hinter dem Schriftzug - haelt die sonst
    ruhige Wordmark-Phase sichtbar in Bewegung."""
    breathe = 0.5 + 0.5 * math.sin(t * 0.9)
    radius = (70 + 14 * breathe) * scale
    alpha = int((50 + 25 * breathe))
    cx = CENTER[0] + offset[0]
    cy = CENTER[1] - 6 * scale + offset[1]
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ldraw = ImageDraw.Draw(layer)
    ldraw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=CYAN + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(22 * scale + 6))
    blend_over(img, layer)


def draw_wordmark(img, draw, wipe_t, tagline_a, bar_t, scale=1.0, offset=(0, 0), t=0.0):
    font = FONT_WORDMARK(int(58 * scale))
    tag_font = FONT_WORDMARK(int(13 * scale))

    bbox = draw.textbbox((0, 0), WORDMARK, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = CENTER[0] - w / 2 - bbox[0] + offset[0]
    y = CENTER[1] - h / 2 - bbox[1] - 18 * scale + offset[1]

    if wipe_t > 0:
        text_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        tdraw = ImageDraw.Draw(text_layer)
        glow_a = int(90 * min(1.0, wipe_t * 2))
        tdraw.text((x, y), WORDMARK, font=font, fill=CYAN + (glow_a,))
        text_layer = text_layer.filter(ImageFilter.GaussianBlur(6))
        tdraw2 = ImageDraw.Draw(text_layer)
        tdraw2.text((x, y), WORDMARK, font=font, fill=TEXT + (255,))

        reveal_w = int(w * ease_out_cubic(wipe_t)) + 4
        mask = Image.new("L", img.size, 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rectangle([x - 4, 0, x + reveal_w, img.size[1]], fill=255)
        text_layer.putalpha(Image.composite(text_layer.split()[3], Image.new("L", img.size, 0), mask))
        blend_over(img, text_layer)

    if tagline_a > 0:
        tbbox = draw.textbbox((0, 0), TAGLINE, font=tag_font)
        tw, th = tbbox[2] - tbbox[0], tbbox[3] - tbbox[1]
        tx = CENTER[0] - tw / 2 - tbbox[0] + offset[0]
        ty = y + h + 14 * scale
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ldraw = ImageDraw.Draw(layer)
        ldraw.text((tx, ty), TAGLINE, font=tag_font, fill=MUTED + (int(255 * tagline_a),))
        blend_over(img, layer)

        if bar_t > 0:
            bar_w = 160 * scale
            bar_x = CENTER[0] - bar_w / 2 + offset[0]
            bar_y = ty + th + 14 * scale
            layer2 = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ldraw2 = ImageDraw.Draw(layer2)
            ldraw2.rectangle(
                [bar_x, bar_y, bar_x + bar_w, bar_y + 3 * scale], fill=BORDER + (200,)
            )
            fill_w = bar_w * ease_out_cubic(bar_t)
            ldraw2.rectangle(
                [bar_x, bar_y, bar_x + fill_w, bar_y + 3 * scale],
                fill=CYAN + (255,),
            )
            if bar_t >= 0.999:
                # Ladebalken ist fertig - ein leiser Comet laeuft weiter drueber,
                # damit die Statuszeile nicht wie eingefroren wirkt.
                pos = (math.sin(t * 1.3) + 1) / 2
                comet_x = bar_x + bar_w * pos
                cr = 5 * scale
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
    font = FONT_MONO(13)
    line_h = 22
    start_x, start_y = 36, HEIGHT - 36 - line_h * len(STATUS_LINES)

    stagger = 1.0 / (len(STATUS_LINES) + 1)
    for i, label in enumerate(STATUS_LINES):
        appear_t = (t_phase - i * stagger) / stagger
        if appear_t <= 0:
            continue
        appear_t = min(1.0, appear_t)
        y = start_y + i * line_h
        dots = "." * max(3, 22 - len(label))
        full = f"{label} {dots}"
        type_t = min(1.0, appear_t * 1.6)
        n_chars = max(1, int(round(len(full) * ease_out_cubic(type_t))))
        shown = full[:n_chars]
        draw.text((start_x, y), shown, font=font, fill=TEXT + (255,))
        ok_t = min(1.0, max(0.0, (appear_t - 0.7) / 0.3))
        if ok_t > 0 and n_chars >= len(full):
            ok_color = lerp_color(MUTED, GREEN, ok_t)
            bbox = draw.textbbox((start_x, y), full + " ", font=font)
            draw.text((bbox[2], y), "OK", font=font, fill=ok_color + (255,))

    dot_stagger = 1.0 / (DOT_COUNT + 1)
    dot_y = start_y - 30
    dot_r = 5
    dot_gap = 22
    dots_w = dot_gap * (DOT_COUNT - 1)
    dot_x0 = WIDTH - 36 - dots_w
    for i in range(DOT_COUNT):
        lit_t = (t_phase - i * dot_stagger) / dot_stagger
        lit_t = max(0.0, min(1.0, lit_t))
        color = lerp_color(BORDER, CYAN, ease_out_cubic(lit_t))
        r = dot_r + 2 * ease_out_cubic(lit_t) * (1 - lit_t) * 2
        x = dot_x0 + i * dot_gap
        draw.ellipse([x - r, dot_y - r, x + r, dot_y + r], fill=color + (255,))

    pct = int(100 * ease_out_cubic(t_phase))
    pfont = FONT_MONO(15)
    draw.text((WIDTH - 70, 30), f"{pct:>3d}%", font=pfont, fill=CYAN + (255,))


# ---- Hauptschleife -----------------------------------------------------


def render():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for frame_idx in range(FRAME_COUNT):
        t = frame_idx / FPS
        img = Image.new("RGB", (WIDTH, HEIGHT), BG)

        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)

        particle_alpha = max(0.0, min(1.0, (t - 0.4) / 0.6))

        if t < 0.5:
            # Phase 0: Power-On Punkt waechst ein
            p = ease_out_cubic(t / 0.5)
            r = 2 + 4 * p
            a = int(255 * p)
            odraw.ellipse(
                [CENTER[0] - r, CENTER[1] - r, CENTER[0] + r, CENTER[1] + r],
                fill=CYAN + (a,),
            )

        elif t < 5.0:
            draw_particles(odraw, t, particle_alpha)
            tp = (t - 0.5) / 4.5
            draw_grid(odraw, tp)
            if tp < 0.55:
                draw_scanline(odraw, tp / 0.55)

        elif t < 10.0:
            draw_particles(odraw, t, particle_alpha)
            draw_grid(odraw, 1.0, base_alpha=0.22)
            draw_periodic_sweep(odraw, t - 5.0)
            tp = (t - 5.0) / 5.0
            wipe_t = min(1.0, tp / 0.5)
            tagline_a = max(0.0, min(1.0, (tp - 0.45) / 0.35))
            bar_t = max(0.0, min(1.0, (tp - 0.55) / 0.45))
            if wipe_t > 0.05:
                draw_wordmark_glow(img, t)
            draw_wordmark(img, odraw, wipe_t, tagline_a, bar_t, t=t)

        elif t < 17.0:
            draw_particles(odraw, t, particle_alpha)
            draw_grid(odraw, 1.0, base_alpha=0.22)
            draw_periodic_sweep(odraw, t - 5.0)
            draw_wordmark_glow(img, t)
            draw_wordmark(img, odraw, 1.0, 1.0, 1.0, t=t)
            tp = (t - 10.0) / 7.0
            draw_status(odraw, tp)

        elif t < 21.0:
            tp = (t - 17.0) / 4.0
            grid_alpha = max(0.0, 0.22 * (1 - min(1.0, tp / 0.6)))
            draw_grid(odraw, 1.0, base_alpha=grid_alpha)
            draw_particles(odraw, t, particle_alpha * (1 - min(1.0, tp / 0.6)))

            # Flash + synchrones Gruen-Pulsieren der Punkte kurz zu Beginn
            if tp < 0.3:
                flash_t = tp / 0.3
                flash_a = int(140 * math.sin(flash_t * math.pi))
                odraw.rectangle([0, 0, WIDTH, HEIGHT], fill=CYAN + (max(0, flash_a),))
                pulse = math.sin(flash_t * math.pi)
                dot_y = HEIGHT - 36 - 22 * len(STATUS_LINES) - 30
                dot_gap = 22
                dots_w = dot_gap * (DOT_COUNT - 1)
                dot_x0 = WIDTH - 36 - dots_w
                for i in range(DOT_COUNT):
                    x = dot_x0 + i * dot_gap
                    r = 5 + 3 * pulse
                    odraw.ellipse(
                        [x - r, dot_y - r, x + r, dot_y + r],
                        fill=GREEN + (int(255 * (0.5 + 0.5 * pulse)),),
                    )
                draw_status(odraw, 1.0)

            # Wordmark schrumpft und wandert Richtung oben-links (App-Header-Position)
            shrink_t = ease_in_out(min(1.0, tp / 0.85))
            scale = lerp(1.0, 0.34, shrink_t)
            target_offset = (
                -CENTER[0] + 70,
                -CENTER[1] + 30,
            )
            offset = (target_offset[0] * shrink_t, target_offset[1] * shrink_t)
            wm_alpha_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            wdraw = ImageDraw.Draw(wm_alpha_layer)
            draw_wordmark(img, wdraw, 1.0, 1.0, 1.0, scale=scale, offset=offset, t=t)
            blend_over(img, wm_alpha_layer)

            # Restliches Overlay (Grid/Flash) ausblenden lassen ueber base image
            final_fade = max(0.0, min(1.0, (tp - 0.8) / 0.2))
            if final_fade > 0:
                fadeover = Image.new("RGBA", (WIDTH, HEIGHT), BG + (int(255 * final_fade),))
                blend_over(img, fadeover)

        else:
            pass  # Phase 5: reiner BG-Hintergrund, identisch zur echten App

        blend_over(img, overlay)

        # Sehr sanfter Ken-Burns-Zoom uebers gesamte Video, damit das Bild
        # auch in ruhigen Momenten nie ganz stillsteht.
        zoom = 1.0 + 0.045 * (t / DURATION)
        if zoom > 1.0005:
            nw, nh = int(WIDTH * zoom), int(HEIGHT * zoom)
            big = img.resize((nw, nh), Image.LANCZOS)
            left, top = (nw - WIDTH) // 2, (nh - HEIGHT) // 2
            img = big.crop((left, top, left + WIDTH, top + HEIGHT))

        img.save(OUT_DIR / f"frame_{frame_idx:05d}.png")

    print(f"{FRAME_COUNT} Frames geschrieben nach {OUT_DIR}")


if __name__ == "__main__":
    render()
