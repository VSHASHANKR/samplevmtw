"""
Navaratri Greeting App (single-file)

Features:
- Tkinter Canvas backend with an abstraction layer for drawing.
- 3 modes: Grid (3x3), Slideshow, Single Focus.
- Animated greeting screen and simple animations for goddess panels.
- Reusable vector drawing primitives (lotus, trident, crown, mandala, petals).
- Keyboard and mouse controls.

Run: python navaratri_app.py
Requires: Python 3.9+ (Tkinter built-in)
"""

from __future__ import annotations
import tkinter as tk
from tkinter import font as tkfont
from typing import Callable, Tuple, Dict, Optional, List
import math
import time
import sys

# ---------------------------
# Configuration / Constants
# ---------------------------
CANVAS_WIDTH = 1200
CANVAS_HEIGHT = 800
BG_COLOR = "#FFF3E6"  # warm pale (festival background)
PALETTE = {
    "saffron": "#F57C00",
    "red": "#C62828",
    "gold": "#FFD54F",
    "green": "#388E3C",
    "deep": "#7B1FA2",
    "white": "#FFFFFF",
    "black": "#000000",
    "dark": "#1B1B1B",
    "soft": "#FFE6CC",
}
FONT_FAMILY = "Helvetica"
TITLE_FONT = (FONT_FAMILY, 20, "bold")
SUBTITLE_FONT = (FONT_FAMILY, 12)
GREETING_FONT = (FONT_FAMILY, 36, "bold")
SLIDESHOW_INTERVAL_MS = 3500
ANIM_FRAME_MS = 50
MIN_CANVAS_WIDTH = 800
MIN_CANVAS_HEIGHT = 600

# ---------------------------
# Utility Types
# ---------------------------
Rect = Tuple[float, float, float, float]  # (x0, y0, x1, y1)
Point = Tuple[float, float]


# ---------------------------
# Backend Abstraction Layer
# ---------------------------
class DrawContext:
    """
    Drawing abstraction that wraps a concrete drawing backend (Tkinter Canvas by default).
    The context exposes high-level primitives used by goddess renderers.
    """

    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas

    # Basic primitives
    def oval(self, bbox: Rect, fill: str = "", outline: str = "", width: int = 1, tags: Optional[str] = None):
        return self.canvas.create_oval(*bbox, fill=fill, outline=outline or fill, width=width, tags=tags)

    def rect(self, bbox: Rect, fill: str = "", outline: str = "", width: int = 1, tags: Optional[str] = None):
        return self.canvas.create_rectangle(*bbox, fill=fill, outline=outline or fill, width=width, tags=tags)

    def polygon(self, points: List[Point], fill: str = "", outline: str = "", width: int = 1, tags: Optional[str] = None):
        flat = [coord for p in points for coord in p]
        return self.canvas.create_polygon(*flat, fill=fill, outline=outline or fill, width=width, tags=tags)

    def line(self, points: List[Point], fill: str = "", width: int = 1, dash: Optional[Tuple[int,int]] = None, tags: Optional[str] = None):
        flat = [coord for p in points for coord in p]
        return self.canvas.create_line(*flat, fill=fill, width=width, dash=dash, tags=tags)

    def text(self, pos: Point, text: str, font: Tuple[str, int, str] = ("Helvetica", 12), fill: str = "", tags: Optional[str] = None):
        return self.canvas.create_text(pos[0], pos[1], text=text, font=font, fill=fill, tags=tags)

    def clear_tag(self, tag: str):
        self.canvas.delete(tag)

    def set_opacity(self, item_id: int, alpha: float):
        # Tkinter doesn't support per-item alpha; we emulate with color blend if needed.
        pass

    def move(self, item_id: int, dx: float, dy: float):
        self.canvas.move(item_id, dx, dy)

    def rotate_coords(self, x: float, y: float, cx: float, cy: float, angle_rad: float) -> Point:
        """Utility used to compute rotated coordinates (returns new x,y)."""
        s = math.sin(angle_rad)
        c = math.cos(angle_rad)
        x -= cx
        y -= cy
        nx = x * c - y * s
        ny = x * s + y * c
        return nx + cx, ny + cy

    def scale_point(self, point: Point, cx: float, cy: float, scale: float) -> Point:
        x, y = point
        return cx + (x - cx) * scale, cy + (y - cy) * scale

# ---------------------------
# Primitives Library
# ---------------------------
def draw_lotus(ctx: DrawContext, cx: float, cy: float, radius: float, fill: str, outline: str = "#000", petals: int = 8, tag: Optional[str] = None):
    """
    Draw a stylized lotus composed of petal shapes around a center.
    """
    items = []
    for i in range(petals):
        angle = 2 * math.pi * i / petals
        p1 = (cx + math.cos(angle) * radius * 0.15, cy + math.sin(angle) * radius * 0.15)
        p2 = (cx + math.cos(angle + 0.25) * radius, cy + math.sin(angle + 0.25) * radius)
        p3 = (cx + math.cos(angle - 0.25) * radius, cy + math.sin(angle - 0.25) * radius)
        items.append(ctx.polygon([p1, p2, p3], fill=fill, outline=outline, tags=tag))
    # center circle
    items.append(ctx.oval((cx - radius*0.12, cy - radius*0.12, cx + radius*0.12, cy + radius*0.12), fill=PALETTE["gold"], outline="", tags=tag))
    return items

def draw_trident(ctx: DrawContext, cx: float, cy: float, height: float, stroke: str = "#000", width: float = 3, tag: Optional[str] = None):
    """
    Draw simple trident: three prongs and a shaft.
    """
    prong_spacing = height * 0.15
    prong_height = height * 0.35
    base_y = cy + height * 0.3
    prong_y = base_y - prong_height
    # shaft
    ctx.line([(cx, base_y), (cx, base_y - height)], fill=stroke, width=int(width), tags=tag)
    # prongs
    for dx in (-prong_spacing, 0, prong_spacing):
        top = (cx + dx, prong_y)
        left = (cx + dx - prong_spacing*0.4, prong_y + prong_height*0.4)
        right = (cx + dx + prong_spacing*0.4, prong_y + prong_height*0.4)
        ctx.polygon([top, left, right], fill=stroke, outline=stroke, tags=tag)

def draw_crown(ctx: DrawContext, cx: float, cy: float, width: float, height: float, fill: str = PALETTE["gold"], outline: str = "#000", tag: Optional[str] = None):
    """
    Simple crown composed of triangles and orbs.
    """
    left = cx - width/2
    right = cx + width/2
    base_y = cy + height/3
    # Base rectangle
    ctx.rect((left, base_y, right, base_y + height*0.2), fill=fill, outline=outline, tags=tag)
    # Triangles
    spikes = 5
    for i in range(spikes):
        t_cx = left + (i + 0.5) * (width / spikes)
        ctx.polygon([(t_cx - width/spikes*0.4, base_y), (t_cx + width/spikes*0.4, base_y), (t_cx, base_y - height*0.5)], fill=fill, outline=outline, tags=tag)
        ctx.oval((t_cx - 6, base_y - height*0.5 - 6, t_cx + 6, base_y - height*0.5 + 6), fill=PALETTE["red"], outline="", tags=tag)

def draw_mandala(ctx: DrawContext, cx: float, cy: float, radius: float, rings: int = 4, tag: Optional[str] = None):
    """
    Geometric rotating mandala made of concentric shapes.
    """
    items = []
    for r in range(rings):
        rr = radius * (1 - r*0.18)
        petals = 6 + r*2
        color = PALETTE["saffron"] if r % 2 == 0 else PALETTE["gold"]
        for i in range(petals):
            ang = 2*math.pi*i/petals
            x1 = cx + math.cos(ang) * rr
            y1 = cy + math.sin(ang) * rr
            x2 = cx + math.cos(ang + math.pi/petals) * rr*0.6
            y2 = cy + math.sin(ang + math.pi/petals) * rr*0.6
            items.append(ctx.polygon([(cx, cy), (x1, y1), (x2, y2)], fill=color, outline="", tags=tag))
    items.append(ctx.oval((cx - radius*0.12, cy - radius*0.12, cx + radius*0.12, cy + radius*0.12), fill=PALETTE["red"], tags=tag))
    return items

def draw_petals(ctx: DrawContext, cx: float, cy: float, radius: float, count: int = 12, fill: str = PALETTE["red"], tag: Optional[str] = None):
    """
    Generic petal ring.
    """
    items = []
    for i in range(count):
        ang = 2*math.pi*i/count
        p1 = (cx + math.cos(ang) * radius*0.3, cy + math.sin(ang) * radius*0.3)
        p2 = (cx + math.cos(ang) * radius, cy + math.sin(ang) * radius)
        p3 = (cx + math.cos(ang + 0.3) * radius*0.4, cy + math.sin(ang + 0.3) * radius*0.4)
        items.append(ctx.polygon([p1, p2, p3], fill=fill, outline="", tags=tag))
    return items

# ---------------------------
# Goddess Definitions
# ---------------------------
class Goddess:
    """
    Base goddess representation
    """
    def __init__(self, name: str, blessing: str, draw_fn: Callable[[DrawContext, Rect, Dict], None], palette: Dict[str,str]):
        self.name = name
        self.blessing = blessing
        self.draw_fn = draw_fn
        self.palette = palette

    def render(self, ctx: DrawContext, bbox: Rect, state: Dict):
        """
        Render goddess inside bbox. 'state' can contain animation progress, time, etc.
        """
        self.draw_fn(ctx, bbox, {"name": self.name, "blessing": self.blessing, "palette": self.palette, **state})

# Specific goddess draw functions
def goddess_shailaputri(ctx: DrawContext, bbox: Rect, options: Dict):
    x0, y0, x1, y1 = bbox
    cx, cy = (x0+x1)/2, (y0+y1)/2
    w = (x1-x0); h = (y1-y0)
    # background mount triangle
    ctx.polygon([(cx-w*0.35, y1), (cx, y0 + h*0.15), (cx+w*0.35, y1)], fill=PALETTE["green"], outline="")
    # trident silhouette
    tr_w = h*0.6
    draw_trident(ctx, cx, cy, tr_w, stroke=PALETTE["dark"], width=3, tag=options.get("tag"))
    # crescent moon accent
    r = h*0.08
    ctx.oval((cx - r*1.6, y0 + h*0.08 - r, cx - r*0.4, y0 + h*0.08 + r), fill=PALETTE["soft"], outline="")
    # title & blessing
    ctx.text((cx, y1 - 30), options["name"], font=TITLE_FONT, fill=PALETTE["deep"])
    ctx.text((cx, y1 - 12), options["blessing"], font=SUBTITLE_FONT, fill=PALETTE["dark"])

def goddess_brahmacharini(ctx: DrawContext, bbox: Rect, options: Dict):
    x0, y0, x1, y1 = bbox
    cx, cy = (x0+x1)/2, (y0+y1)/2
    w = x1-x0; h = y1-y0
    # soft halo
    ctx.oval((cx - w*0.35, cy - h*0.35, cx + w*0.35, cy + h*0.35), fill=PALETTE["soft"], outline="")
    # calm lotus
    draw_lotus(ctx, cx, cy, min(w,h)*0.22, PALETTE["saffron"], outline=PALETTE["red"], tag=options.get("tag"))
    ctx.text((cx, y1 - 30), options["name"], font=TITLE_FONT, fill=PALETTE["deep"])
    ctx.text((cx, y1 - 12), options["blessing"], font=SUBTITLE_FONT, fill=PALETTE["dark"])

def goddess_chandraghanta(ctx: DrawContext, bbox: Rect, options: Dict):
    x0, y0, x1, y1 = bbox
    cx, cy = (x0+x1)/2, (y0+y1)/2
    w = x1-x0; h = y1-y0
    # bell-shaped crown
    draw_crown(ctx, cx, cy - h*0.2, w*0.4, h*0.25, tag=options.get("tag"))
    # crescent moon
    ctx.oval((cx - w*0.12, cy - h*0.4, cx + w*0.02, cy - h*0.32), fill=PALETTE["white"], outline="")
    # bobbing bell (animate with offset)
    t = options.get("t", 0)
    bob = math.sin(t*1.8) * 6
    ctx.oval((cx - w*0.08, cy + bob - h*0.04, cx + w*0.08, cy + bob + h*0.02), fill=PALETTE["gold"], outline="", tags=options.get("tag"))
    ctx.text((cx, y1 - 30), options["name"], font=TITLE_FONT, fill=PALETTE["deep"])
    ctx.text((cx, y1 - 12), options["blessing"], font=SUBTITLE_FONT, fill=PALETTE["dark"])

def goddess_kushmanda(ctx: DrawContext, bbox: Rect, options: Dict):
    x0, y0, x1, y1 = bbox
    cx, cy = (x0+x1)/2, (y0+y1)/2
    radius = min(x1-x0, y1-y0)*0.26
    t = options.get("t", 0)
    # radiant orbs with slow pulsing
    pulse = 0.9 + 0.12 * math.sin(t * 1.2)
    draw_mandala(ctx, cx, cy, radius * pulse, rings=5, tag=options.get("tag"))
    ctx.text((cx, y1 - 30), options["name"], font=TITLE_FONT, fill=PALETTE["deep"])
    ctx.text((cx, y1 - 12), options["blessing"], font=SUBTITLE_FONT, fill=PALETTE["dark"])

def goddess_skandamata(ctx: DrawContext, bbox: Rect, options: Dict):
    x0, y0, x1, y1 = bbox
    cx, cy = (x0+x1)/2, (y0+y1)/2
    w = x1-x0; h = y1-y0
    # two linked shapes: mother & child silhouette
    ctx.oval((cx - w*0.12, cy - h*0.18, cx + w*0.12, cy + h*0.12), fill=PALETTE["red"], outline="")
    ctx.oval((cx - w*0.02, cy - h*0.05, cx + w*0.22, cy + h*0.18), fill=PALETTE["saffron"], outline="")
    draw_lotus(ctx, cx, cy + h*0.22, min(w,h)*0.12, PALETTE["gold"], tag=options.get("tag"))
    ctx.text((cx, y1 - 30), options["name"], font=TITLE_FONT, fill=PALETTE["deep"])
    ctx.text((cx, y1 - 12), options["blessing"], font=SUBTITLE_FONT, fill=PALETTE["dark"])

def goddess_katyayani(ctx: DrawContext, bbox: Rect, options: Dict):
    x0, y0, x1, y1 = bbox
    cx, cy = (x0+x1)/2, (y0+y1)/2
    w = x1-x0; h = y1-y0
    # sword motif
    blade_len = h*0.5
    ctx.line([(cx - blade_len*0.05, cy + blade_len*0.4), (cx, cy - blade_len*0.1), (cx + blade_len*0.05, cy + blade_len*0.4)],
             fill=PALETTE["deep"], width=4, tags=options.get("tag"))
    # angular decorations
    ctx.polygon([(cx - w*0.3, cy + h*0.08), (cx - w*0.08, cy - h*0.18), (cx - w*0.02, cy + h*0.1)], fill=PALETTE["saffron"], tags=options.get("tag"))
    ctx.polygon([(cx + w*0.3, cy + h*0.08), (cx + w*0.08, cy - h*0.18), (cx + w*0.02, cy + h*0.1)], fill=PALETTE["saffron"], tags=options.get("tag"))
    draw_petals(ctx, cx, cy + h*0.22, min(w,h)*0.16, count=8, fill=PALETTE["red"], tag=options.get("tag"))
    ctx.text((cx, y1 - 30), options["name"], font=TITLE_FONT, fill=PALETTE["deep"])
    ctx.text((cx, y1 - 12), options["blessing"], font=SUBTITLE_FONT, fill=PALETTE["dark"])

def goddess_kalaratri(ctx: DrawContext, bbox: Rect, options: Dict):
    x0, y0, x1, y1 = bbox
    cx, cy = (x0+x1)/2, (y0+y1)/2
    w = x1-x0; h = y1-y0
    # dark palette
    ctx.rect((x0, y0, x1, y1), fill="#0b0b0b", outline="")
    # bright eyes / star motifs
    for dx in (-w*0.12, w*0.12):
        ctx.oval((cx + dx - 8, cy - 10, cx + dx + 8, cy + 6), fill=PALETTE["gold"], tags=options.get("tag"))
    # subtle flicker (small stars)
    t = options.get("t", 0)
    flicker = 1 if math.sin(t*4) > 0 else 0
    if flicker:
        ctx.oval((cx - w*0.18, cy - h*0.3, cx - w*0.16, cy - h*0.28), fill=PALETTE["gold"], tags=options.get("tag"))
    ctx.text((cx, y1 - 30), options["name"], font=TITLE_FONT, fill=PALETTE["white"])
    ctx.text((cx, y1 - 12), options["blessing"], font=SUBTITLE_FONT, fill=PALETTE["white"])

def goddess_mahagauri(ctx: DrawContext, bbox: Rect, options: Dict):
    x0, y0, x1, y1 = bbox
    cx, cy = (x0+x1)/2, (y0+y1)/2
    w = x1-x0; h = y1-y0
    # flowing curves and halo
    ctx.oval((cx - w*0.3, cy - h*0.35, cx + w*0.3, cy + h*0.35), fill=PALETTE["white"], outline="")
    ctx.oval((cx - w*0.12, cy - h*0.12, cx + w*0.12, cy + h*0.12), fill=PALETTE["gold"], outline="")
    # gentle vertical motion
    t = options.get("t", 0)
    dy = math.sin(t*1.2) * 4
    ctx.oval((cx - w*0.08, cy - h*0.05 + dy, cx + w*0.08, cy + h*0.12 + dy), fill=PALETTE["saffron"], tags=options.get("tag"))
    ctx.text((cx, y1 - 30), options["name"], font=TITLE_FONT, fill=PALETTE["deep"])
    ctx.text((cx, y1 - 12), options["blessing"], font=SUBTITLE_FONT, fill=PALETTE["dark"])

def goddess_siddhidatri(ctx: DrawContext, bbox: Rect, options: Dict):
    x0, y0, x1, y1 = bbox
    cx, cy = (x0+x1)/2, (y0+y1)/2
    r = min(x1-x0, y1-y0) * 0.22
    t = options.get("t", 0)
    # rotating symmetry: draw petal rings rotated by t
    items = []
    for i in range(6):
        rot = t*0.15 + (2*math.pi*i/6)
        pts = []
        for k in range(5):
            ang = rot + k*(2*math.pi/5)
            pts.append((cx + math.cos(ang)*r*(0.6 + 0.2*k), cy + math.sin(ang)*r*(0.6 + 0.2*k)))
        items.append(ctx.polygon(pts, fill=PALETTE["gold"], tags=options.get("tag")))
    ctx.oval((cx - r*0.25, cy - r*0.25, cx + r*0.25, cy + r*0.25), fill=PALETTE["red"], tags=options.get("tag"))
    ctx.text((cx, y1 - 30), options["name"], font=TITLE_FONT, fill=PALETTE["deep"])
    ctx.text((cx, y1 - 12), options["blessing"], font=SUBTITLE_FONT, fill=PALETTE["dark"])


# ---------------------------
# Goddess Registry (names + blessings)
# ---------------------------
GODDESSES: List[Goddess] = [
    Goddess("Shailaputri", "Strength & stability", goddess_shailaputri, PALETTE),
    Goddess("Brahmacharini", "Calm & devotion", goddess_brahmacharini, PALETTE),
    Goddess("Chandraghanta", "Valor & balance", goddess_chandraghanta, PALETTE),
    Goddess("Kushmanda", "Health & radiance", goddess_kushmanda, PALETTE),
    Goddess("Skandamata", "Nurture & courage", goddess_skandamata, PALETTE),
    Goddess("Katyayani", "Power & victory", goddess_katyayani, PALETTE),
    Goddess("Kalaratri", "Protection & transformation", goddess_kalaratri, PALETTE),
    Goddess("Mahagauri", "Purity & grace", goddess_mahagauri, PALETTE),
    Goddess("Siddhidatri", "Wisdom & completion", goddess_siddhidatri, PALETTE),
]

# ---------------------------
# UI / App Controller
# ---------------------------
class NavaratriApp:
    """
    Main application class. Manages views, mode transitions, animation loop, and input handling.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Navaratri Greetings")
        self.width = max(CANVAS_WIDTH, MIN_CANVAS_WIDTH)
        self.height = max(CANVAS_HEIGHT, MIN_CANVAS_HEIGHT)
        # Canvas setup
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        # Keep reference fonts
        self.font_title = tkfont.Font(family=FONT_FAMILY, size=18, weight="bold")
        self.font_greet = tkfont.Font(family=FONT_FAMILY, size=36, weight="bold")
        # Drawing context wrapper
        self.ctx = DrawContext(self.canvas)
        # State
        self.mode = "greeting"  # 'greeting', 'grid', 'slideshow', 'focus'
        self.current_index = 0
        self.slideshow_playing = False
        self.last_frame_time = time.time()
        self.t = 0.0  # animation time in seconds
        # Bind events
        self.root.bind("<Configure>", self._on_resize)
        self.root.bind("<Key>", self._on_key)
        self.canvas.bind("<Button-1>", self._on_click)
        # Kick off render loop
        self._validate_canvas_size()
        self._render_initial()
        self._animate()

    # ---------------------------
    # Event handlers
    # ---------------------------
    def _on_resize(self, event):
        # Update canvas size
        self.width = max(event.width, MIN_CANVAS_WIDTH)
        self.height = max(event.height, MIN_CANVAS_HEIGHT)
        self.canvas.config(width=self.width, height=self.height)
        # Force re-render
        self._render()

    def _on_key(self, event):
        key = event.keysym.lower()
        if key in ("m", "escape"):
            self._switch_mode("greeting")
        elif key == "g":
            self._switch_mode("grid")
        elif key == "s":
            self._switch_mode("slideshow")
            self._start_slideshow()
        elif key == "f":
            # toggle focus
            if self.mode == "focus":
                self._switch_mode("grid")
            else:
                self._switch_mode("focus")
        elif key == "space":
            # play/pause slideshow
            if self.slideshow_playing:
                self._stop_slideshow()
            else:
                self._start_slideshow()
        elif key in ("left", "kp_left"):
            self._prev_slide()
        elif key in ("right", "kp_right"):
            self._next_slide()

    def _on_click(self, event):
        if self.mode == "grid":
            # Determine which panel clicked (3x3)
            cells = 3
            cell_w = self.width / cells
            cell_h = self.height / cells
            col = int(event.x / cell_w)
            row = int(event.y / cell_h)
            idx = row * cells + col
            if 0 <= idx < len(GODDESSES):
                self.current_index = idx
                self._switch_mode("focus")
        elif self.mode in ("greeting",):
            # go to grid on click
            self._switch_mode("grid")

    # ---------------------------
    # Mode control
    # ---------------------------
    def _switch_mode(self, mode: str):
        self.mode = mode
        if mode == "greeting":
            self.slideshow_playing = False
        self._render()

    def _start_slideshow(self):
        self.slideshow_playing = True
        self._switch_mode("slideshow")

    def _stop_slideshow(self):
        self.slideshow_playing = False

    def _prev_slide(self):
        self.current_index = (self.current_index - 1) % len(GODDESSES)
        self._render()

    def _next_slide(self):
        self.current_index = (self.current_index + 1) % len(GODDESSES)
        self._render()

    # ---------------------------
    # Rendering orchestration
    # ---------------------------
    def _validate_canvas_size(self):
        if self.width < MIN_CANVAS_WIDTH or self.height < MIN_CANVAS_HEIGHT:
            # graceful fallback: show warning and resize
            self.canvas.delete("all")
            self.canvas.create_text(self.width/2, self.height/2, text="Window too small for full visuals.\nPlease enlarge the window.", font=TITLE_FONT, fill=PALETTE["deep"])
            return False
        return True

    def _render_initial(self):
        self.canvas.delete("all")
        # Greeting screen initial
        self._draw_greeting()

    def _render(self):
        self.canvas.delete("all")
        if not self._validate_canvas_size():
            return
        if self.mode == "greeting":
            self._draw_greeting()
        elif self.mode == "grid":
            self._draw_grid()
        elif self.mode == "slideshow":
            self._draw_focus(self.current_index)
        elif self.mode == "focus":
            self._draw_focus(self.current_index)
        else:
            self._draw_greeting()

    def _draw_greeting(self):
        # festive background (radial-ish)
        w, h = self.width, self.height
        # gradient-ish approach using broad ovals
        for i, scale in enumerate((1.2, 0.9, 0.6, 0.35)):
            color = PALETTE["soft"] if i % 2 == 0 else PALETTE["saffron"]
            self.ctx.oval((w*0.1* (1-scale), h*0.1*(1-scale), w - w*0.1*(1-scale), h - h*0.1*(1-scale)), fill=color, outline="")
        # Animated greeting text (pulsing/rotating)
        greet = "Happy Navaratri"
        sub = "May the nine forms of Durga bless you with courage, prosperity, and wisdom."
        # pulse scale with time
        pulse = 1.0 + 0.04 * math.sin(self.t * 2.0)
        self.ctx.text((w/2, h/2 - 40), greet, font=(FONT_FAMILY, int(36*pulse), "bold"), fill=PALETTE["deep"])
        self.ctx.text((w/2, h/2 + 10), sub, font=(FONT_FAMILY, 16), fill=PALETTE["dark"])
        # small instruction
        self.ctx.text((w/2, h - 40), "Click to view goddesses • Press G:Grid • S:Slideshow • Esc/M:Main", font=(FONT_FAMILY, 12), fill=PALETTE["dark"])
        # subtle motif: small lotus at bottom
        draw_lotus(self.ctx, w*0.5, h*0.75, 60, PALETTE["gold"], outline=PALETTE["red"])

    def _draw_grid(self):
        cells = 3
        cell_w = self.width / cells
        cell_h = self.height / cells
        for i, goddess in enumerate(GODDESSES):
            row = i // cells
            col = i % cells
            x0 = col * cell_w + 8
            y0 = row * cell_h + 8
            x1 = (col + 1) * cell_w - 8
            y1 = (row + 1) * cell_h - 8
            # panel rounded rect (simple rectangle here)
            self.ctx.rect((x0, y0, x1, y1), fill=PALETTE["white"], outline=PALETTE["saffron"])
            # each goddess draws into its box; provide animation time
            goddess.render(self.ctx, (x0, y0, x1, y1), {"t": self.t, "tag": f"g{ i }"})
        # footer instructions
        self.ctx.text((self.width/2, self.height - 18), "Click a panel to focus • ←/→ to navigate • Space to play slideshow", font=(FONT_FAMILY, 12), fill=PALETTE["dark"])

    def _draw_focus(self, index: int):
        # Focus a single goddess (large panel)
        g = GODDESSES[index]
        pad = 40
        x0, y0 = pad, pad
        x1, y1 = self.width - pad, self.height - pad - 40
        # background soft
        self.ctx.rect((x0, y0, x1, y1), fill=PALETTE["soft"], outline=PALETTE["saffron"])
        g.render(self.ctx, (x0+20, y0+20, x1-20, y1-20), {"t": self.t, "tag": f"focus_{index}"})
        # caption and nav
        self.ctx.text((self.width/2, y1 + 16), f"{g.name} — {g.blessing}", font=(FONT_FAMILY, 16, "bold"), fill=PALETTE["deep"])
        self.ctx.text((self.width/2, self.height - 10), "← Prev  •  → Next  •  Space Play/Pause  •  M Main", font=(FONT_FAMILY, 11), fill=PALETTE["dark"])

    # ---------------------------
    # Animation Loop
    # ---------------------------
    def _animate(self):
        now = time.time()
        dt = now - self.last_frame_time
        self.last_frame_time = now
        self.t += dt
        # Advance slideshow if playing
        if self.slideshow_playing:
            # if exceeded interval, move to next
            if int(self.t * 1000) % SLIDESHOW_INTERVAL_MS < (dt * 1000):
                self._next_slide()
        # Re-render small dynamic parts: we render whole canvas each frame for simplicity
        self._render()
        # schedule next frame
        self.root.after(ANIM_FRAME_MS, self._animate)

# ---------------------------
# Start script & error handling
# ---------------------------
def main():
    root = tk.Tk()
    # Make window sizeable
    try:
        app = NavaratriApp(root)
    except Exception as e:
        tk.messagebox.showerror("Error", f"Failed to start Navaratri app: {e}")
        sys.exit(1)
    # Start mainloop
    root.mainloop()

if __name__ == "__main__":
    main()
