"""
Render code editor and terminal frames as images for screen-recording style videos.
Uses Pillow to create dark-themed editor/terminal screenshots.
"""
import textwrap
from PIL import Image, ImageDraw, ImageFont
import config
import os

# Colors (dark theme)
BG_EDITOR = (30, 30, 30)        # VS Code dark
BG_TERMINAL = (12, 12, 12)      # Terminal black
BG_TITLEBAR = (50, 50, 50)      # Window title bar
TEXT_WHITE = (212, 212, 212)
TEXT_GREEN = (78, 201, 176)      # strings / success
TEXT_BLUE = (86, 156, 214)       # keywords
TEXT_YELLOW = (220, 220, 170)    # functions
TEXT_ORANGE = (206, 145, 120)    # strings
TEXT_PURPLE = (197, 134, 192)    # keywords alt
TEXT_GRAY = (106, 115, 125)      # comments
TEXT_COMMAND = (80, 250, 123)    # terminal prompt
HEADING_COLOR = (255, 255, 255)
LINE_NUM_COLOR = (80, 80, 80)
ACCENT_COLOR = (0, 122, 204)    # VS Code blue

# Frame dimensions (1080x1920 portrait)
WIDTH = config.VIDEO_WIDTH
HEIGHT = config.VIDEO_HEIGHT
PADDING = 40
CODE_TOP = 280  # y-offset where code starts
LINE_HEIGHT = 38
HEADING_SIZE = 48
CODE_FONT_SIZE = 28
TITLE_FONT_SIZE = 64
SUBTITLE_FONT_SIZE = 36


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a monospace font. Falls back gracefully."""
    font_paths = [
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    ]
    if bold:
        font_paths = [p.replace("Regular", "Bold") for p in font_paths] + font_paths

    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _get_sans_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a sans-serif font for headings."""
    font_paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_window_chrome(draw: ImageDraw.Draw, title: str, y_start: int = 160):
    """Draw a window title bar with traffic lights."""
    # Title bar background
    draw.rectangle([PADDING, y_start, WIDTH - PADDING, y_start + 45], fill=BG_TITLEBAR)

    # Traffic light dots
    for i, color in enumerate([(255, 95, 87), (255, 189, 46), (39, 201, 63)]):
        cx = PADDING + 25 + i * 25
        cy = y_start + 22
        draw.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=color)

    # Title text
    font = _get_sans_font(18)
    draw.text((PADDING + 110, y_start + 12), title, fill=TEXT_WHITE, font=font)


def _simple_syntax_color(line: str, language: str) -> list[tuple[str, tuple]]:
    """Very basic syntax coloring - returns list of (text, color) tuples."""
    # This is simplified; a real implementation would use a proper lexer
    parts = []

    if language == "python":
        keywords = ["from", "import", "def", "class", "return", "if", "else", "for",
                     "in", "with", "as", "try", "except", "True", "False", "None",
                     "and", "or", "not", "while", "yield", "raise", "lambda"]
        if line.strip().startswith("#"):
            return [(line, TEXT_GRAY)]
        if line.strip().startswith("print(") or line.strip().startswith("print ("):
            return [(line, TEXT_YELLOW)]
        # Simple keyword detection
        words = line.split(" ")
        for j, word in enumerate(words):
            clean = word.strip("(),:=[]{}\"'")
            if clean in keywords:
                parts.append((word + " ", TEXT_PURPLE))
            elif "'" in word or '"' in word:
                parts.append((word + " ", TEXT_ORANGE))
            elif word.strip().startswith("@"):
                parts.append((word + " ", TEXT_YELLOW))
            else:
                parts.append((word + " ", TEXT_WHITE))
        return parts

    elif language == "sql":
        sql_keywords = ["SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER",
                        "ON", "GROUP", "BY", "ORDER", "HAVING", "AS", "WITH", "AND",
                        "OR", "NOT", "NULL", "IS", "IN", "BETWEEN", "LIKE", "INSERT",
                        "INTO", "VALUES", "UPDATE", "SET", "DELETE", "CREATE", "TABLE",
                        "DROP", "ALTER", "INDEX", "USING", "CASE", "WHEN", "THEN",
                        "ELSE", "END", "COUNT", "SUM", "AVG", "MIN", "MAX", "DISTINCT"]
        if line.strip().startswith("--"):
            return [(line, TEXT_GRAY)]
        words = line.split(" ")
        for word in words:
            clean = word.strip("(),:=")
            if clean.upper() in sql_keywords:
                parts.append((word + " ", TEXT_BLUE))
            elif "'" in word:
                parts.append((word + " ", TEXT_ORANGE))
            else:
                parts.append((word + " ", TEXT_WHITE))
        return parts

    elif language == "yaml":
        stripped = line.lstrip()
        if stripped.startswith("#"):
            return [(line, TEXT_GRAY)]
        if ":" in line:
            key, _, val = line.partition(":")
            parts.append((key + ":", TEXT_BLUE))
            parts.append((val, TEXT_ORANGE if val.strip() else TEXT_WHITE))
            return parts
        if stripped.startswith("- "):
            return [(line, TEXT_GREEN)]

    # Default: all white
    return [(line, TEXT_WHITE)]


def render_code_frame(heading: str, code: str, language: str = "python") -> str:
    """Render a code editor frame. Returns path to saved image."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_EDITOR)
    draw = ImageDraw.Draw(img)

    # Section heading at top
    heading_font = _get_sans_font(HEADING_SIZE, bold=True)
    draw.text((PADDING, 60), heading, fill=HEADING_COLOR, font=heading_font)

    # Accent line under heading
    draw.rectangle([PADDING, 130, PADDING + 200, 134], fill=ACCENT_COLOR)

    # Window chrome
    _draw_window_chrome(draw, f"{language} — editor", y_start=160)

    # Code area background
    draw.rectangle([PADDING, 205, WIDTH - PADDING, HEIGHT - 80], fill=BG_EDITOR)

    # Render code lines with line numbers and syntax coloring
    code_font = _get_font(CODE_FONT_SIZE)
    lines = code.split("\n")
    y = CODE_TOP
    for i, line in enumerate(lines):
        if y > HEIGHT - 120:
            break

        # Line number
        line_num = str(i + 1).rjust(3)
        draw.text((PADDING + 10, y), line_num, fill=LINE_NUM_COLOR, font=code_font)

        # Syntax colored code
        x = PADDING + 65
        colored_parts = _simple_syntax_color(line, language)
        for text, color in colored_parts:
            draw.text((x, y), text, fill=color, font=code_font)
            bbox = code_font.getbbox(text)
            x += bbox[2] - bbox[0]

        y += LINE_HEIGHT

    # Save
    path = os.path.join(config.TEMP_DIR, f"code_frame_{hash(heading) % 10000}.png")
    img.save(path, "PNG")
    return path


def render_terminal_frame(heading: str, content: str) -> str:
    """Render a terminal frame. Returns path to saved image."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_TERMINAL)
    draw = ImageDraw.Draw(img)

    # Section heading
    heading_font = _get_sans_font(HEADING_SIZE, bold=True)
    draw.text((PADDING, 60), heading, fill=HEADING_COLOR, font=heading_font)

    # Accent line
    draw.rectangle([PADDING, 130, PADDING + 200, 134], fill=TEXT_GREEN)

    # Window chrome
    _draw_window_chrome(draw, "terminal — bash", y_start=160)

    # Terminal background
    draw.rectangle([PADDING, 205, WIDTH - PADDING, HEIGHT - 80], fill=BG_TERMINAL)

    # Render terminal lines
    code_font = _get_font(CODE_FONT_SIZE)
    lines = content.split("\n")
    y = CODE_TOP
    for line in lines:
        if y > HEIGHT - 120:
            break

        # Wrap long lines
        if len(line) > 50:
            wrapped = textwrap.wrap(line, width=50)
        else:
            wrapped = [line]

        for wline in wrapped:
            if y > HEIGHT - 120:
                break
            if wline.startswith("$"):
                # Command line: green prompt
                draw.text((PADDING + 15, y), "$ ", fill=TEXT_COMMAND, font=code_font)
                draw.text((PADDING + 50, y), wline[2:], fill=TEXT_WHITE, font=code_font)
            elif wline.startswith("["):
                # Log line
                draw.text((PADDING + 15, y), wline, fill=TEXT_GREEN, font=code_font)
            elif "ERROR" in wline or "FAIL" in wline:
                draw.text((PADDING + 15, y), wline, fill=(255, 85, 85), font=code_font)
            elif "OK" in wline or "PASS" in wline or "success" in wline.lower():
                draw.text((PADDING + 15, y), wline, fill=TEXT_GREEN, font=code_font)
            else:
                draw.text((PADDING + 15, y), wline, fill=TEXT_GRAY, font=code_font)
            y += LINE_HEIGHT

    path = os.path.join(config.TEMP_DIR, f"terminal_frame_{hash(heading) % 10000}.png")
    img.save(path, "PNG")
    return path


def render_title_card(heading: str, subheading: str = "") -> str:
    """Render a title/section card. Returns path to saved image."""
    img = Image.new("RGB", (WIDTH, HEIGHT), (18, 18, 40))
    draw = ImageDraw.Draw(img)

    # Accent bar
    draw.rectangle([0, HEIGHT // 2 - 200, WIDTH, HEIGHT // 2 - 196], fill=ACCENT_COLOR)
    draw.rectangle([0, HEIGHT // 2 + 120, WIDTH, HEIGHT // 2 + 124], fill=ACCENT_COLOR)

    # Main title
    title_font = _get_sans_font(TITLE_FONT_SIZE, bold=True)
    # Wrap title
    wrapped_title = textwrap.fill(heading, width=20)
    # Center it
    bbox = draw.multiline_textbbox((0, 0), wrapped_title, font=title_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (WIDTH - text_w) // 2
    y = (HEIGHT - text_h) // 2 - 60
    draw.multiline_text((x, y), wrapped_title, fill=HEADING_COLOR, font=title_font, align="center")

    # Subtitle
    if subheading:
        sub_font = _get_sans_font(SUBTITLE_FONT_SIZE)
        bbox = draw.textbbox((0, 0), subheading, font=sub_font)
        sw = bbox[2] - bbox[0]
        draw.text(((WIDTH - sw) // 2, y + text_h + 40), subheading, fill=ACCENT_COLOR, font=sub_font)

    path = os.path.join(config.TEMP_DIR, f"title_{hash(heading) % 10000}.png")
    img.save(path, "PNG")
    return path
