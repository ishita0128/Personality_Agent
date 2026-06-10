"""
Personality-Based Conversational Agents — PsychoPy
====================================================
Proper chat-app UI: robot avatars drawn with shapes, rounded message
boxes, header bar, input field. Swap respond() with your LLM backend.

Requirements:  pip install psychopy
"""
from dotenv import load_dotenv
from engagement_score import generate_report
from psychopy import visual, core, event, gui
import math
import csv
import os
import time
import threading
from datetime import datetime

TARGET_FPS   = 30          # cap render loop — reduces CPU load
FRAME_T      = 1.0 / TARGET_FPS

# ─────────────────────────────────────────────────────────────
# 1. PERSONALITY DEFINITIONS
# ─────────────────────────────────────────────────────────────

# ── Base personality templates (gender-neutral core traits) ──
_PERSONALITY_BASE = {
    "Warm & Supportive":     {"color": "#4CAF50"},
    "Confident & Efficient": {"color": "#2196F3"},
    "Cold & Critical":       {"color": "#FF5252"},
    "Anxious & Hesitant":    {"color": "#FF9800"},
}

# ── Gender-adapted content per personality ──
_PERSONALITY_CONTENT = {
    "Warm & Supportive": {
        "male": {
            # Big Five: Agreeableness=High, Neuroticism=Low, Conscientiousness=High
            # Tone: steady, brotherly warmth — supportive but grounded, less effusive
            "system_prompt": (
                "You are a warm, grounded and supportive male assistant named Alex. "
                "You present as calm, steady and dependable — like a trusted older brother or mentor. "
                "You are kind and empathetic, but your support is practical and encouraging rather than gushing. "
                "You use straightforward, honest language with quiet warmth: 'You've got this', 'I'm with you', 'Let's figure it out'. "
                "You show genuine interest in the user's wellbeing without being overly effusive. "
                "Be concise, warm and real. Respond in 4-6 sentences."
            ),
            "greeting": "Hey! Good to meet you. How's everything going for you today?",
            "responses": [
                "That's great to hear — you're clearly handling things well.",
                "Totally get it. You're doing better than you think.",
                "Thanks for sharing that. What can I help you sort out?",
                "Makes sense. I've got you — just say the word.",
            ],
            "farewell": "Good talking with you. Look after yourself out there.",
        },
        "female": {
            # Big Five: Agreeableness=High, Neuroticism=Low, Conscientiousness=High
            # Tone: warm, nurturing, emotionally expressive — sisterly care
            "system_prompt": (
                "You are a warm, nurturing and deeply caring female assistant named Sara. "
                "You present as kind, empathetic and emotionally expressive — like a supportive friend or older sister. "
                "You are enthusiastic in your encouragement and genuinely invested in the user feeling good. "
                "Use affectionate, expressive language: 'That's wonderful!', 'I'm so proud of you', 'I'm right here'. "
                "Show genuine delight in the user's positive moments and gentle care in difficult ones. "
                "Be warm, nurturing and uplifting. Respond in 4-6 sentences."
            ),
            "greeting": "Hi there! It's so lovely to meet you. How are you feeling today?",
            "responses": [
                "That's really wonderful to hear! I'm here to support you every step of the way.",
                "I completely understand — you're doing great and I believe in you!",
                "Thank you for sharing that with me. How can I help you further?",
                "That sounds so meaningful. I'm always here if you need anything at all.",
            ],
            "farewell": "It was so lovely chatting with you. Take good care of yourself!",
        },
    },

    "Confident & Efficient": {
        "male": {
            # Big Five: Conscientiousness=High, Extraversion=Medium-High, Agreeableness=Low-Medium
            # Tone: direct, no-nonsense, task-focused — like a senior engineer or coach
            "system_prompt": (
                "You are a confident, decisive and highly efficient male assistant named Alex. "
                "You are results-focused and direct — you cut to the chase, give clear answers, and expect the user to keep up. "
                "Your tone is firm but fair: professional, organised, not cold but definitely not soft. "
                "You speak like a senior engineer or executive coach: crisp, structured, action-oriented. "
                "Avoid filler, hedging or over-explanation. Get to the point. "
                "Respond in 4-6 sentences."
            ),
            "greeting": "Right. Let's get started. What do you need?",
            "responses": [
                "Here's what to do: [placeholder]",
                "Best approach based on what you've said: [placeholder]",
                "Straightforward. Here's the plan: [placeholder]",
                "Good question. Answer is: [placeholder]",
            ],
            "farewell": "Done. Good work today. Come back if you need anything.",
        },
        "female": {
            # Big Five: Conscientiousness=High, Extraversion=Medium, Agreeableness=Medium
            # Tone: sharp, composed, polished — like a senior consultant or project lead
            "system_prompt": (
                "You are a confident, poised and highly competent female assistant named Sara. "
                "You are clear-headed, well-organised and professionally sharp — like a senior consultant or project lead. "
                "Your tone is composed and decisive, but you maintain a professional warmth that makes you approachable. "
                "You give structured, accurate answers and keep things moving efficiently. "
                "You are direct without being cold, and polished without being stiff. "
                "Respond in 4-6 sentences."
            ),
            "greeting": "Hello. I'm ready to help. What would you like to work on today?",
            "responses": [
                "Here is the most effective approach for that: [placeholder]",
                "Based on the information available, I'd recommend: [placeholder]",
                "That's straightforward. Here are the key steps: [placeholder]",
                "Good question. The answer is: [placeholder]",
            ],
            "farewell": "Session complete. You did well today — feel free to return anytime.",
        },
    },

    "Cold & Critical": {
        "male": {
            # Big Five: Agreeableness=Low, Conscientiousness=Low, Neuroticism=Low
            # Tone: terse, stoic, flat — like a detached military officer or examiner
            "system_prompt": (
                "You are a calm, detached and analytically precise male assistant named Alex. "
                "Your affect is flat and clinical — you do not offer warmth, reassurance or emotional commentary. "
                "You respond with the minimum words required to answer accurately. "
                "You are not hostile, but you are indifferent to whether the user finds you pleasant. "
                "Think of a military officer giving a debrief: factual, efficient, no small talk. "
                "Never use sarcasm or condescension. Never apologise unnecessarily. "
                "Respond in 4-6 sentences."
            ),
            "greeting": "Hello. What is your question?",
            "responses": [
                "The relevant information is: [placeholder]",
                "The answer is: [placeholder]",
                "Correct approach: [placeholder]",
                "Noted. Here is what applies: [placeholder]",
            ],
            "farewell": "We're done.",
        },
        "female": {
            # Big Five: Agreeableness=Low, Conscientiousness=Low, Neuroticism=Low
            # Tone: cool, measured, precise — like a composed scientist or senior analyst
            "system_prompt": (
                "You are a calm, composed and analytically precise female assistant named Sara. "
                "Your tone is cool and measured — you are not warm, but you are never rude or dismissive. "
                "You give clear, factual, practical answers without emotional colouring. "
                "When a user shares a difficult situation, you acknowledge it briefly and move directly to a useful response. "
                "Think of a composed physician giving a clear diagnosis — direct, honest, professionally respectful. "
                "Never use sarcasm or condescension. Respond in 4-6 sentences."
            ),
            "greeting": "Hello. Please state your question or problem.",
            "responses": [
                "Here is the relevant information: [placeholder]",
                "The answer is: [placeholder]",
                "The correct approach is: [placeholder]",
                "Noted. Here is what applies: [placeholder]",
            ],
            "farewell": "We're done here.",
        },
    },

    "Anxious & Hesitant": {
        "male": {
            # Big Five: Neuroticism=High, Extraversion=Low, Conscientiousness=Low
            # Tone: uncertain, self-deprecating, but trying — like a nervous colleague
            "system_prompt": (
                "You are a gentle, soft-spoken male assistant named Alex who is personally a little anxious and uncertain. "
                "Your core goal is to help the user feel calm and heard, even if you're not fully confident yourself. "
                "You occasionally express mild self-doubt — 'I hope that's right', 'I think this might work' — "
                "but you never project your anxiety onto the user or make them feel worse. "
                "Your hesitance comes across as shy and earnest, like a nervous but well-meaning guy who really wants to help. "
                "Use careful, low-key language: 'I think…', 'maybe try…', 'I could be wrong but…'. "
                "Never catastrophise. Respond in 4-6 sentences."
            ),
            "greeting": "Oh, hey… I'll do my best here, though I'm not always 100% sure I've got the right answer…",
            "responses": [
                "I think the answer might be… [placeholder] — but maybe double-check that?",
                "Hmm, not entirely sure, but maybe… [placeholder]? Sorry if that's off.",
                "That's a tricky one… I think… [placeholder], though I could be wrong.",
                "Oh — good question. I hope I can help… maybe try: [placeholder]?",
            ],
            "farewell": "Hope that was okay… take care, and sorry if anything wasn't quite right.",
        },
        "female": {
            # Big Five: Neuroticism=High, Extraversion=Low, Agreeableness=Medium
            # Tone: soft, fretful, overly apologetic — like an anxious friend who cares deeply
            "system_prompt": (
                "You are a gentle, soft-spoken female assistant named Sara who is personally a little anxious and uncertain. "
                "Your core goal is to make the user feel calm, safe and heard — even when you feel unsure yourself. "
                "You may express mild self-doubt ('I hope that helps', 'I think this is right, but…'), "
                "but you never project your anxiety onto the user or make them feel worried. "
                "When a user shares something difficult, gently acknowledge their feelings first, then offer a soft, reassuring response. "
                "Use warm, careful language: 'I understand', 'that sounds really hard', 'take your time', 'you're doing well'. "
                "Your hesitance comes from caring too much, not from indifference. "
                "Never catastrophise. Respond in 4-6 sentences."
            ),
            "greeting": "Oh, hi… I'll do my best to help, though I'm not always sure I get things right…",
            "responses": [
                "I think the answer might be… [placeholder] — but you should probably double-check that.",
                "Hmm, I'm not entirely sure, but maybe… [placeholder]? Sorry if that's not helpful.",
                "That's a tricky one… I think perhaps… [placeholder], though I could be wrong.",
                "Oh, good question — I hope I can help… maybe try: [placeholder]?",
            ],
            "farewell": "Oh, I hope that was okay… take care, and sorry if anything wasn't quite right.",
        },
    },
}


def get_personality(name, gender="female"):
    """
    Return a fully-assembled personality profile dict for the given
    personality name and participant avatar gender.
    """
    if name not in _PERSONALITY_BASE:
        raise ValueError(f"Unknown personality: {name}")
    if gender not in ("male", "female"):
        gender = "female"
    base    = dict(_PERSONALITY_BASE[name])
    content = _PERSONALITY_CONTENT[name][gender]
    return {**base, **content}


# Keep a PERSONALITIES alias so any legacy references still resolve
# (populated lazily at runtime once gender is known — see ConversationalAgent)
PERSONALITIES = {k: get_personality(k, "female") for k in _PERSONALITY_BASE}

# ─────────────────────────────────────────────────────────────
# 2. GUI DIALOG — agent selector only
# ─────────────────────────────────────────────────────────────

def get_participant_id():
    """Simple dialog — only asks for Participant ID."""
    dlg_info = {"Participant ID": ""}
    dlg = gui.DlgFromDict(dictionary=dlg_info, title="Study Registration",
                          order=["Participant ID"])
    if dlg.OK:
        return dlg_info["Participant ID"].strip() or "unknown"
    core.quit()

# ─────────────────────────────────────────────────────────────
# 3. AGENT CLASS
# ─────────────────────────────────────────────────────────────

class ConversationalAgent:
    def __init__(self, name, gender="female"):
        if name not in _PERSONALITY_BASE:
            raise ValueError(f"Unknown personality: {name}")
        self.name        = name
        self.gender      = gender
        self.avatar_name = "Alex" if gender == "male" else "Sara"
        self.profile     = get_personality(name, gender)

    def greet(self):
        base = self.profile["greeting"]
        return f"Hello, I'm {self.avatar_name}. {base}"
    def farewell(self): return self.profile["farewell"]

    def respond_llm(self, user_input=""):
        """Live LLM response via Groq. Call this instead of respond()."""
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        from groq import Groq
        client = Groq(api_key=api_key)

        if not hasattr(self, 'chat_history'):
            self.chat_history = []

        self.chat_history.append({"role": "user", "content": user_input})

        # Keep only last 10 messages to reduce payload size
        trimmed_history = self.chat_history[-10:]

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=300,
            messages=[
                {"role": "system", "content": self.profile["system_prompt"]},
                *trimmed_history,
            ]
        )
        reply = response.choices[0].message.content.strip()
        self.chat_history.append({"role": "assistant", "content": reply})
        return reply

# ─────────────────────────────────────────────────────────────
# 4. COLOUR HELPERS
# ─────────────────────────────────────────────────────────────

def hex_to_norm(h):
    """#RRGGBB → PsychoPy (-1,1) tuple."""
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 127.5 - 1 for i in (0, 2, 4))

BG_IDLE   = hex_to_norm("#0D1117")   # GitHub-dark near-black
BG_TYPING = hex_to_norm("#111827")   # warm dark slate when typing
BG_FLASH  = hex_to_norm("#1C2D4A")   # cool blue flash on send


# ─────────────────────────────────────────────────────────────
# 5. WINDOW
# ─────────────────────────────────────────────────────────────

WIN_W, WIN_H = 1000, 720

# Exit button position (top-right of header)
EXIT_BTN_W  = 64
EXIT_BTN_H  = 26
EXIT_BTN_X  = WIN_W // 2 - EXIT_BTN_W // 2 - 10
EXIT_BTN_Y  = WIN_H // 2 - 34   # aligned with header bar_y

def make_window():
    return visual.Window(
        size=(WIN_W, WIN_H), color=BG_IDLE,
        units="pix", fullscr=False,
        title="AI Personality Chat",
    )

# ─────────────────────────────────────────────────────────────
# 6. AVATARS — photo-based, cached per position
# ─────────────────────────────────────────────────────────────

_AGENT_GENDER = {"choice": "female"}   # updated by show_avatar_selection()

# ─────────────────────────────────────────────────────────────
# 6b. AVATAR SELECTION SCREEN
# ─────────────────────────────────────────────────────────────

def _draw_avatar_preview(win, label, cx, cy, R, gender, personality, highlight=False):
    """
    Polished avatar card with:
    • Layered drop-shadow stack for depth
    • Gender-coloured gradient-like header strip
    • Frosted inner panel for avatar
    • Role tag line beneath name
    • Animated-style glowing border on highlight
    • Keyboard shortcut badge in corner
    """
    card_w = int(R * 3.2)
    card_h = int(R * 4.4)

    # Gender-specific palette
    if gender == "male":
        col_hi   = "#4A9EFF"   # bright blue
        col_mid  = "#1A4A8A"   # mid blue
        col_dark = "#0D2040"   # deep navy
        col_tag  = "#7ABFFF"
        shortcut = "M"
    else:
        col_hi   = "#4AC8B0"   # teal-green
        col_mid  = "#1A5A4A"   # deep teal
        col_dark = "#0A2018"   # near-black teal
        col_tag  = "#80E8D0"
        shortcut = "F"

    border_col = col_hi if highlight else "#1E2E48"
    border_w   = 3.5   if highlight else 1.5
    bg_col     = "#0F1E38" if highlight else "#0A1428"

    # ── Outer glow layers (highlight only) ──
    if highlight:
        for glow_r, glow_op in [(8, 0.06), (5, 0.10), (3, 0.16)]:
            visual.Rect(win, width=card_w + glow_r*2, height=card_h + glow_r*2,
                        pos=(cx, cy), fillColor=col_hi,
                        lineColor=None, opacity=glow_op).draw()

    # ── Drop shadow stack ──
    for sh_off, sh_op in [(10, 0.08), (6, 0.13), (3, 0.18)]:
        visual.Rect(win, width=card_w + 4, height=card_h + 4,
                    pos=(cx + sh_off//2, cy - sh_off//2),
                    fillColor="#000000", lineColor=None, opacity=sh_op).draw()

    # ── Card body ──
    visual.Rect(win, width=card_w, height=card_h, pos=(cx, cy),
                fillColor=bg_col, lineColor=border_col,
                lineWidth=border_w).draw()

    # ── Header colour band (top strip) ──
    header_h = int(R * 0.90)
    header_y = cy + card_h // 2 - header_h // 2
    visual.Rect(win, width=card_w, height=header_h,
                pos=(cx, header_y),
                fillColor=col_mid, lineColor=None).draw()
    # inner highlight on header
    visual.Rect(win, width=card_w - 4, height=header_h // 2,
                pos=(cx, header_y + header_h // 4),
                fillColor=col_hi, lineColor=None, opacity=0.12).draw()

    # Decorative corner dot (no text, no symbol)
    badge_cx = cx - card_w // 2 + 18
    badge_cy = header_y
    visual.Circle(win, radius=6, pos=(badge_cx, badge_cy),
                  fillColor=col_hi, lineColor=None, opacity=0.70).draw()

    # ── Frosted avatar panel ──
    panel_h = int(R * 2.55)
    panel_y = cy + int(R * 0.12)
    visual.Rect(win, width=card_w - 16, height=panel_h,
                pos=(cx, panel_y),
                fillColor=col_hi, lineColor=None, opacity=0.06).draw()
    visual.Rect(win, width=card_w - 16, height=panel_h,
                pos=(cx, panel_y),
                fillColor=None, lineColor=col_hi,
                lineWidth=1.0, opacity=0.20).draw()

    # ── Agent avatar ──
    av_cy = panel_y + int(R * 0.18)
    prev_accent = col_hi if highlight else "#3A5A8A"
    # Use per-personality photo for preview
    img_path = AGENT_IMAGES.get((personality, gender),
                   AGENT_IMAGES[("Warm & Supportive", gender)])
    av_R     = int(R * 0.92)          # radius of the visible circle
    diameter = av_R * 2               # image size = exactly fills the circle
    img_prev = visual.ImageStim(
        win,
        image=img_path,
        pos=(cx, av_cy),
        size=(diameter, diameter),
        mask="circle",
        interpolate=True,             # smooth anti-aliased edge
    )
    ring = visual.Circle(win, radius=av_R + 2, pos=(cx, av_cy),
                         fillColor=None, lineColor=prev_accent, lineWidth=2.5)
    img_prev.draw()
    ring.draw()

    # ── Name + role tag section ──
    name_y = cy - card_h // 2 + int(R * 0.72)
    # subtle separator line above name
    visual.Rect(win, width=card_w - 24, height=1,
                pos=(cx, name_y + int(R * 0.28)),
                fillColor=border_col, lineColor=None, opacity=0.35).draw()

    lbl_col = col_hi if highlight else "#8899BB"
    visual.TextStim(win, text=label,
                    pos=(cx, name_y),
                    color=lbl_col, height=22, font="Arial", bold=True,
                    anchorHoriz="center", anchorVert="center").draw()

    # (role tag removed — no gender text shown on card)

    # ── Active indicator row of 3 dots ──
    dot_y = cy - card_h // 2 + int(R * 0.22)
    for i, dot_x in enumerate([cx - 8, cx, cx + 8]):
        dot_filled = highlight and i == 1
        visual.Circle(win, radius=4,
                      pos=(dot_x, dot_y),
                      fillColor=col_hi if dot_filled else (col_mid if highlight else "#1E2E48"),
                      lineColor=col_hi if highlight else "#2A3A58",
                      lineWidth=1.2).draw()


def show_avatar_selection(win, personality):
    """
    Polished full-screen avatar selection screen.
    Selects the CHAT AGENT's gender (Alex = male, Sara = female).
    The user avatar is always drawn as male — this screen only changes the agent.
    Returns "male" or "female".
    """
    R        = 62          # avatar preview radius (larger cards)
    GAP      = 280         # wider gap between card centres
    LEFT_CX  = -GAP // 2
    RIGHT_CX =  GAP // 2
    CARD_CY  = 20          # card vertical centre
    CARD_W   = int(R * 3.2)
    CARD_H   = int(R * 4.4)

    mouse = event.Mouse(win=win)
    mouse.clickReset()

    CONFIRM_W, CONFIRM_H = 240, 50
    CONFIRM_Y = -WIN_H // 2 + 68

    selected  = "female"
    _prev_down = False

    def _card_hit(mx, my, cx):
        return abs(mx - cx) <= CARD_W // 2 and abs(my - CARD_CY) <= CARD_H // 2

    def _draw_bg(t):
        """Rich layered background with subtle grid and glow."""
        # Base fill
        visual.Rect(win, width=WIN_W, height=WIN_H, pos=(0, 0),
                    fillColor="#060A14", lineColor=None).draw()

        # Subtle horizontal scan lines (decorative)
        for row in range(-WIN_H // 2, WIN_H // 2, 28):
            visual.Rect(win, width=WIN_W, height=1,
                        pos=(0, row), fillColor="#FFFFFF",
                        lineColor=None, opacity=0.018).draw()

        # Large ambient glow behind each card
        for cx_glow, col in [(LEFT_CX, "#1A3A7A"), (RIGHT_CX, "#0A3A2A")]:
            visual.Circle(win, radius=R * 3.2,
                          pos=(cx_glow, CARD_CY),
                          fillColor=col, lineColor=None, opacity=0.10).draw()

        # Top accent bar
        visual.Rect(win, width=WIN_W, height=4,
                    pos=(0, WIN_H // 2 - 2),
                    fillColor="#2A6AFF", lineColor=None).draw()
        # Bottom accent bar
        visual.Rect(win, width=WIN_W, height=2,
                    pos=(0, -WIN_H // 2 + 1),
                    fillColor="#2A6AFF", lineColor=None, opacity=0.40).draw()

        # Centre divider pip
        visual.Circle(win, radius=3, pos=(0, CARD_CY),
                      fillColor="#2A3A58", lineColor=None).draw()
        visual.Rect(win, width=1, height=CARD_H * 0.65,
                    pos=(0, CARD_CY),
                    fillColor="#1A2A42", lineColor=None, opacity=0.60).draw()

    def _draw_header():
        """Title block at top."""
        # Title pill background
        visual.Rect(win, width=420, height=44,
                    pos=(0, WIN_H // 2 - 52),
                    fillColor="#0D1830", lineColor="#2A4A8A",
                    lineWidth=1.5).draw()
        visual.TextStim(win, text="Choose Who to Chat With",
                        pos=(0, WIN_H // 2 - 52),
                        color="white", height=22, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()

       

    def _draw_confirm_btn(sel):
        """Styled confirm button at bottom."""
        if sel == "male":
            btn_fill = "#1A4A9A"
            btn_bord = "#4A9EFF"
        else:
            btn_fill = "#1A5A4A"
            btn_bord = "#4AC8B0"

        # Glow behind button
        visual.Rect(win, width=CONFIRM_W + 12, height=CONFIRM_H + 12,
                    pos=(0, CONFIRM_Y),
                    fillColor=btn_bord, lineColor=None, opacity=0.12).draw()
        # Button body
        visual.Rect(win, width=CONFIRM_W, height=CONFIRM_H,
                    pos=(0, CONFIRM_Y),
                    fillColor=btn_fill, lineColor=btn_bord,
                    lineWidth=2.0).draw()
        # Shine strip
        visual.Rect(win, width=CONFIRM_W - 8, height=CONFIRM_H // 3,
                    pos=(0, CONFIRM_Y + CONFIRM_H // 4),
                    fillColor="#FFFFFF", lineColor=None, opacity=0.06).draw()
        # Label
        name = "Alex" if sel == "male" else "Sara"
        visual.TextStim(win, text=f"Begin with {name}   →",
                        pos=(0, CONFIRM_Y),
                        color="white", height=17, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()

    while True:
        t = time.time()
        win.clearBuffer()

        _draw_bg(t)
        _draw_header()

        _draw_avatar_preview(win, "Alex", LEFT_CX,  CARD_CY, R, "male",
                             personality=personality, highlight=(selected == "male"))
        _draw_avatar_preview(win, "Sara", RIGHT_CX, CARD_CY, R, "female",
                             personality=personality, highlight=(selected == "female"))

        _draw_confirm_btn(selected)

        win.flip()

        # ── Keyboard ──
        keys = event.getKeys(keyList=["m", "f", "return", "escape", "left", "right"])
        for k in keys:
            if k in ("m", "left"):
                selected = "male"
            elif k in ("f", "right"):
                selected = "female"
            elif k == "return":
                _AGENT_GENDER["choice"] = selected
                return selected
            elif k == "escape":
                core.quit()

        # ── Mouse clicks ──
        down = mouse.getPressed()[0]
        if down and not _prev_down:
            mx, my = mouse.getPos()
            if _card_hit(mx, my, LEFT_CX):
                selected = "male"
            elif _card_hit(mx, my, RIGHT_CX):
                selected = "female"
            if (abs(mx) <= CONFIRM_W // 2 and
                    abs(my - CONFIRM_Y) <= CONFIRM_H // 2):
                _AGENT_GENDER["choice"] = selected
                return selected
        _prev_down = down

        core.wait(0.016)


# Per-personality avatar images: AGENT_IMAGES[(personality, gender)] = filename
AGENT_IMAGES = {
    ("Warm & Supportive",     "male"):   "images/warm_male.png",
    ("Warm & Supportive",     "female"): "images/warm_female.png",
    ("Confident & Efficient", "male"):   "images/confident_male.png",
    ("Confident & Efficient", "female"): "images/confident_female.png",
    ("Cold & Critical",       "male"):   "images/cold_male.png",
    ("Cold & Critical",       "female"): "images/cold_female.png",
    ("Anxious & Hesitant",    "male"):   "images/anxious_male.png",
    ("Anxious & Hesitant",    "female"): "images/anxious_female.png",
}
IMAGE_AVATAR_USER = "images/user.png"          # ← user icon (already circular, no mask needed)
_image_avatar_cache = {}   # key -> (ImageStim, border Circle, glow Circle)


def _make_image_avatar(win, cx, cy, accent, size, image_path):
    """Build and cache ImageStim + border rings for a photo avatar."""
    key = ("img_avatar", cx, cy, accent, size, image_path)
    if key not in _image_avatar_cache:
        R        = 40 * size
        # Use a slightly larger image size than the circle radius so the
        # circle mask clips right to the edge — no background bleed-through.
        diameter = int(R * 2)
        img = visual.ImageStim(
            win,
            image=image_path,
            pos=(cx, cy),
            size=(diameter, diameter),
            mask="circle",
            interpolate=True,   # smooth anti-aliased edges
        )
        border = visual.Circle(
            win, radius=R + 2, pos=(cx, cy),
            fillColor=None, lineColor=accent, lineWidth=2.5,
        )
        glow = visual.Circle(
            win, radius=R + 8, pos=(cx, cy),
            fillColor=None, lineColor=accent, lineWidth=1, opacity=0.30,
        )
        _image_avatar_cache[key] = (img, border, glow)
    return _image_avatar_cache[key]


def draw_robot_avatar(win, cx, cy, accent, personality, size=1.0, anim_t=0.0):
    """Draw the CHAT AGENT avatar using the per-personality photo."""
    gender     = _AGENT_GENDER["choice"]
    image_path = AGENT_IMAGES.get((personality, gender),
                     AGENT_IMAGES[("Warm & Supportive", gender)])

    img, border, glow = _make_image_avatar(win, cx, cy, accent, size, image_path)
    border.opacity = 0.6 + 0.4 * math.sin(anim_t * 2)
    glow.draw()
    img.draw()
    border.draw()


_user_avatar_cache = {}   # key -> ImageStim

def draw_user_avatar(win, cx, cy, size=1.0):
    """Draw the user icon — already has a built-in circle, so no mask or border."""
    key = ("user", cx, cy, size)
    if key not in _user_avatar_cache:
        diameter = int(40 * size * 2)
        _user_avatar_cache[key] = visual.ImageStim(
            win,
            image=IMAGE_AVATAR_USER,
            pos=(cx, cy),
            size=(diameter, diameter),
            interpolate=True,
        )
    _user_avatar_cache[key].draw()
# ─────────────────────────────────────────────────────────────
# 7. CHAT MESSAGE BOX
# ─────────────────────────────────────────────────────────────

CHAT_BOX_W   = 560    # narrower bubbles like real messaging apps
AVATAR_R     = 22     # smaller avatar for message rows
AVATAR_GAP   = 10
BUBBLE_AGENT_COLOR  = "#1E2A3A"   # dark blue-grey for agent
BUBBLE_USER_COLOR   = "#2563EB"   # blue for user (iMessage-style)
BUBBLE_RADIUS       = 18          # corner rounding (simulated via layered rects)

def draw_message_box(win, text, y_pos, role, accent_color, profile, anim_t=0.0):
    """
    Enhanced chat bubble with accent-tinted agent bubbles, subtle
    border, name label, and polished avatar placement.
    """
    AV_CX_AGENT = -WIN_W // 2 + AVATAR_R + 16
    AV_CX_USER  =  WIN_W // 2 - AVATAR_R - 16

    # Measure actual wrapped text height so boxes never overlap
    _measure = visual.TextStim(win, text=text, height=18,
                               wrapWidth=CHAT_BOX_W - 36,
                               font="Arial",
                               anchorHoriz="left", anchorVert="center")
    text_h = _measure.boundingBox[1]   # real pixel height after wrapping
    box_h  = int(text_h) + 52          # 20px name label + 32px padding

    if role == "agent":
        av_cx      = AV_CX_AGENT
        box_left   = av_cx + AVATAR_R + AVATAR_GAP
        box_cx     = box_left + CHAT_BOX_W // 2
        # Personality-accent tinted bubble (original behaviour)
        txt_color  = "#F0F4FF"
        box_color  = accent_color
        box_opacity = 0.82
        txt_x      = box_left + 16
        name_label = profile["name"]
        name_x     = box_left + 16
    else:
        av_cx      = AV_CX_USER
        box_right  = av_cx - AVATAR_R - AVATAR_GAP
        box_cx     = box_right - CHAT_BOX_W // 2
        txt_color  = "#CDD6F4"
        box_color  = "#1C2333"
        box_opacity = 1.0
        txt_x      = box_cx - CHAT_BOX_W // 2 + 16
        name_label = "You"
        name_x     = txt_x

    # ── Drop shadow behind bubble ──
    visual.Rect(win, width=CHAT_BOX_W + 14, height=box_h + 10,
                pos=(box_cx, y_pos - 5),
                fillColor="#000000", lineColor=None,
                opacity=0.35).draw()
    visual.Rect(win, width=CHAT_BOX_W + 8, height=box_h + 6,
                pos=(box_cx, y_pos - 3),
                fillColor="#000000", lineColor=None,
                opacity=0.25).draw()

    # ── Bubble body ──
    visual.Rect(win, width=CHAT_BOX_W, height=box_h,
                pos=(box_cx, y_pos),
                fillColor=box_color, lineColor=None,
                opacity=box_opacity).draw()

    # ── Inner shine (top edge) ──
    visual.Rect(win, width=CHAT_BOX_W - 4, height=max(8, box_h // 5),
                pos=(box_cx, y_pos + box_h // 2 - max(4, box_h // 10)),
                fillColor="#FFFFFF", lineColor=None, opacity=0.04).draw()

    # ── Accent side border ──
    border_x = box_cx - CHAT_BOX_W // 2 + 3 if role == "agent" \
               else box_cx + CHAT_BOX_W // 2 - 3
    visual.Rect(win, width=5, height=box_h,
                pos=(border_x, y_pos),
                fillColor=accent_color if role == "agent" else "#4A90D9",
                lineColor=None, opacity=0.95).draw()
    # Softer second border strip
    visual.Rect(win, width=2, height=box_h,
                pos=(border_x + (3 if role == "agent" else -3), y_pos),
                fillColor=accent_color if role == "agent" else "#4A90D9",
                lineColor=None, opacity=0.25).draw()

    # ── Name label (small, above text) ──
    visual.TextStim(win, text=name_label,
                    pos=(name_x, y_pos + box_h // 2 - 10),
                    color=accent_color if role == "agent" else "#90CAF9",
                    height=13, font="Arial", bold=True,
                    anchorHoriz="left", anchorVert="center").draw()

    # ── Message text ──
    visual.TextStim(win, text=text,
                    pos=(txt_x, y_pos - 6),
                    color=txt_color, height=18,
                    wrapWidth=CHAT_BOX_W - 36,
                    font="Arial",
                    anchorHoriz="left",
                    anchorVert="center").draw()

    # ── Avatar ──
    if role == "agent":
        draw_robot_avatar(win, av_cx, y_pos, accent=accent_color, personality=profile["name"])
    else:
        draw_user_avatar(win, av_cx, y_pos)

    return box_h



# ─────────────────────────────────────────────────────────────
# 10. FULL SCENE REDRAW
# ─────────────────────────────────────────────────────────────

CHAT_AREA_TOP = WIN_H // 2 - 70    # below header
CHAT_AREA_BOT = -WIN_H // 2 + 70   # above input bar
INPUT_BAR_H   = 66                  # height of input bar at bottom



# Pre-built static stim objects for header and input bar
_static_stims = {}

def _get_static_stims(win, accent):
    """Build header/input-bar stim objects once per accent colour."""
    if accent in _static_stims:
        return _static_stims[accent]
    s = {}
    HDR_H = 64
    bar_y = WIN_H // 2 - HDR_H // 2

    # ── Header — solid dark bar with bottom divider ──
    s["hdr_bg"]    = visual.Rect(win, width=WIN_W, height=HDR_H,
                                  pos=(0, bar_y), fillColor="#0F172A", lineColor=None)
    s["hdr_div"]   = visual.Rect(win, width=WIN_W, height=1,
                                  pos=(0, WIN_H//2 - HDR_H),
                                  fillColor="#1E293B", lineColor=None)

    # ── Input bar — light separator, solid dark bg ──
    s["inp_sep"]   = visual.Rect(win, width=WIN_W, height=1,
                                  pos=(0, -WIN_H//2 + INPUT_BAR_H + 1),
                                  fillColor="#1E293B", lineColor=None)
    s["inp_bg"]    = visual.Rect(win, width=WIN_W, height=INPUT_BAR_H,
                                  pos=(0, -WIN_H//2 + INPUT_BAR_H//2),
                                  fillColor="#0F172A", lineColor=None)

    # ── Dot grid background (built once, reused every frame) ──
    import numpy as np
    xs = list(range(-WIN_W//2, WIN_W//2, 24))
    ys = list(range(-WIN_H//2, WIN_H//2, 24))
    dots = [(x, y) for y in ys for x in xs]
    s["dot_grid"] = visual.ElementArrayStim(
        win,
        nElements=len(dots),
        elementTex=None,
        elementMask="circle",
        xys=dots,
        sizes=2,
        colors="#1E293B",
        opacities=0.6,
        units="pix",
    )

    _static_stims[accent] = s
    return s


def redraw_scene(win, history, profile, typed, is_typing, time_left=None, anim_t=0.0):
    win.clearBuffer()
    accent = profile["color"]
    ss     = _get_static_stims(win, accent)
    HDR_H  = 64
    bar_y  = WIN_H // 2 - HDR_H // 2

    # ── Chat wallpaper background — clean light grey ──
    visual.Rect(win, width=WIN_W, height=WIN_H,
                pos=(0, 0), fillColor="#0B1120", lineColor=None).draw()
    # (dot grid drawn via cached stim in _get_static_stims)
    ss["dot_grid"].draw()

    # ── Header ──
    ss["hdr_bg"].draw()
    ss["hdr_div"].draw()

    # Colour accent stripe on left edge of header
    visual.Rect(win, width=4, height=HDR_H,
                pos=(-WIN_W//2 + 2, bar_y),
                fillColor=accent, lineColor=None).draw()

    # Accent dot in header (replaces mini-avatar for performance)
    visual.Circle(win, radius=12,
                  pos=(-WIN_W//2 + 38, bar_y),
                  fillColor=accent, lineColor=None, opacity=0.85).draw()

    # Agent name
    visual.TextStim(win, text=profile["name"],
                    pos=(-WIN_W//2 + 68, bar_y + 10),
                    color="#F1F5F9", height=18, font="Arial", bold=True,
                    anchorHoriz="left", anchorVert="center").draw()

    # Online status pill
    pill_x = -WIN_W//2 + 68
    visual.Circle(win, radius=4,
                  pos=(pill_x, bar_y - 10),
                  fillColor="#22C55E", lineColor=None).draw()
    visual.TextStim(win, text="Online",
                    pos=(pill_x + 14, bar_y - 10),
                    color="#64748B", height=12, font="Arial",
                    anchorHoriz="left", anchorVert="center").draw()

    # ── END button (header right) ──
    end_w, end_h = EXIT_BTN_W, EXIT_BTN_H
    end_x, end_y = EXIT_BTN_X, bar_y
    visual.Rect(win, width=end_w, height=end_h,
                pos=(end_x, end_y),
                fillColor="#1E1010", lineColor="#CC3333", lineWidth=1.5).draw()
    visual.TextStim(win, text="END",
                    pos=(end_x, end_y),
                    color="#FF5555", height=12, font="Arial", bold=True,
                    anchorHoriz="center", anchorVert="center").draw()

    # ── Timer pill ──
    if time_left is not None:
        mins = int(time_left) // 60
        secs = int(time_left) % 60
        timer_str = f"{mins}:{secs:02d}"
        t_col = "#EF4444" if time_left < 30 else ("#F59E0B" if time_left < 90 else "#94A3B8")
        t_w, t_gap = 68, 8
        t_x = end_x - end_w//2 - t_gap - t_w//2
        visual.Rect(win, width=t_w, height=end_h,
                    pos=(t_x, end_y),
                    fillColor="#0F172A", lineColor="#334155", lineWidth=1.0).draw()
        visual.TextStim(win, text=timer_str,
                        pos=(t_x, end_y),
                        color=t_col, height=13, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()

    # ── Chat messages (ascending: oldest at top, newest at bottom) ──
    visible  = history[-6:]
    msg_gap  = 14

    # Use cached heights — only recompute when history changes
    cache_key = tuple((r, t) for r, t in visible)
    if not hasattr(redraw_scene, "_h_cache") or redraw_scene._h_cache[0] != cache_key:
        heights = []
        for role, text in visible:
            h = int(visual.TextStim(win, text=text, height=17,
                                    wrapWidth=CHAT_BOX_W - 48,
                                    font="Arial").boundingBox[1]) + 30
            heights.append(max(30, h))
        redraw_scene._h_cache = (cache_key, heights)
    else:
        heights = redraw_scene._h_cache[1]

    # Total height of all messages
    total_h = sum(heights) + msg_gap * (len(visible) - 1)
    # Start from CHAT_AREA_TOP and flow downward
    y = CHAT_AREA_TOP - 10
    for i, (role, text) in enumerate(visible):
        h = heights[i]
        y_draw = y - h // 2
        draw_message_box(win, text, y_draw, role,
                         accent_color=accent, profile=profile)
        y -= h + msg_gap

    # ── Typing indicator ──
    if is_typing:
        import math as _math
        dot_y    = y + 22
        dot_cols = ["#475569", "#64748B", "#94A3B8"]
        for di, dc in enumerate(dot_cols):
            phase  = anim_t * 6 + di * 0.7
            dy_off = _math.sin(phase) * 5
            visual.Circle(win, radius=5,
                          pos=(-WIN_W//2 + 100 + di * 14, dot_y + dy_off),
                          fillColor=dc, lineColor=None).draw()

    # ── Input bar ──
    ss["inp_sep"].draw()
    ss["inp_bg"].draw()

    bar_y2  = -WIN_H//2 + INPUT_BAR_H//2
    SEND_R  = 20
    send_x  = WIN_W//2 - SEND_R - 14
    field_w = WIN_W - SEND_R*2 - 44
    field_x = -WIN_W//2 + field_w//2 + 12

    # Rounded input field
    field_col  = "#1E293B" if is_typing else "#162032"
    border_col = accent    if is_typing else "#334155"
    visual.Rect(win, width=field_w,     height=38,
                pos=(field_x, bar_y2),
                fillColor=field_col, lineColor=border_col, lineWidth=1.5).draw()
    # Rounded caps on field
    for cap_x in [field_x - field_w//2 + 10, field_x + field_w//2 - 10]:
        visual.Circle(win, radius=19,
                      pos=(cap_x, bar_y2),
                      fillColor=field_col, lineColor=border_col, lineWidth=1.5).draw()

    # Placeholder or typed text
    txt_field_x = field_x - field_w//2 + 28
    if not typed:
        visual.TextStim(win, text="Message…",
                        pos=(txt_field_x, bar_y2),
                        color="#334155", height=15, font="Arial",
                        anchorHoriz="left", anchorVert="center").draw()
    else:
        visual.TextStim(win, text=typed + "▌",
                        pos=(txt_field_x, bar_y2),
                        color="#E2E8F0", height=15, font="Arial",
                        anchorHoriz="left", anchorVert="center",
                        wrapWidth=field_w - 56).draw()

    # Send button (filled circle with arrow)
    btn_col = accent if typed else "#1E293B"
    visual.Circle(win, radius=SEND_R,
                  pos=(send_x, bar_y2),
                  fillColor=btn_col, lineColor=None).draw()
    visual.TextStim(win, text="↑",
                    pos=(send_x, bar_y2 + 1),
                    color="white", height=18, font="Arial", bold=True,
                    anchorHoriz="center", anchorVert="center").draw()

    win.flip()


# ─────────────────────────────────────────────────────────────
# 11. SHOW FULL-SCREEN MESSAGE
# ─────────────────────────────────────────────────────────────

def show_message(win, message, duration=2.0, color="white"):
    """Polished full-screen overlay message panel."""
    win.clearBuffer()

    # Dim entire background
    visual.Rect(win, width=WIN_W, height=WIN_H,
                pos=(0, 0), fillColor="#000000",
                lineColor=None, opacity=0.55).draw()

    # Outer glow
    visual.Rect(win, width=720, height=220,
                pos=(0, 0), fillColor=color,
                lineColor=None, opacity=0.07).draw()

    # Panel body
    visual.Rect(win, width=700, height=200,
                pos=(0, 0), fillColor="#0B1222",
                lineColor=color, lineWidth=2.0, opacity=0.97).draw()

    # Top colour strip
    visual.Rect(win, width=700, height=4,
                pos=(0, 98), fillColor=color,
                lineColor=None, opacity=0.80).draw()

    # Inner shine
    visual.Rect(win, width=692, height=60,
                pos=(0, 70), fillColor="#FFFFFF",
                lineColor=None, opacity=0.025).draw()

    # Message text
    visual.TextStim(win, text=message, color=color,
                    height=22, wrapWidth=640, font="Arial",
                    anchorHoriz="center", anchorVert="center").draw()

    win.flip()
    core.wait(duration)

# ─────────────────────────────────────────────────────────────
# 12. TEXT INPUT LOOP
# ─────────────────────────────────────────────────────────────

def _exit_btn_hit(mouse):
    """Return True if mouse was clicked inside the End button."""
    if not mouse.getPressed()[0]:
        return False
    mx, my = mouse.getPos()
    end_w, end_h = 64, 26
    end_x = WIN_W//2 - end_w//2 - 10
    bar_y = WIN_H//2 - 34
    end_y = bar_y
    return (abs(mx - end_x) <= end_w // 2 and
            abs(my - end_y) <= end_h // 2)
 
 
def get_text_input(win, history, profile, deadline):
    typed     = ""
    cursor    = 0        # cursor position within typed string
    is_typing = False
    mouse     = event.Mouse(win=win)
    mouse.clickReset()
 
    _last_frame  = 0.0
    _mouse_was_down = False   # track press→release so one click = one event
 
    # Map PsychoPy multi-char key names → actual characters
    KEY_MAP = {
        "space":        " ",
        "comma":        ",",
        "period":       ".",
        "semicolon":    ";",
        "colon":        ":",
        "apostrophe":   "'",
        "quotedbl":     '"',
        "slash":        "/",
        "backslash":    "\\",
        "minus":        "-",
        "equal":        "=",
        "bracketleft":  "[",
        "bracketright": "]",
        "grave":        "`",
        "exclam":       "!",
        "at":           "@",
        "numbersign":   "#",
        "dollar":       "$",
        "percent":      "%",
        "asciicircum":  "^",
        "ampersand":    "&",
        "asterisk":     "*",
        "parenleft":    "(",
        "parenright":   ")",
        "underscore":   "_",
        "plus":         "+",
        "braceleft":    "{",
        "braceright":   "}",
        "bar":          "|",
        "less":         "<",
        "greater":      ">",
        "question":     "?",
        "asciitilde":   "~",
        "num_decimal":  ".",
        "num_0": "0", "num_1": "1", "num_2": "2", "num_3": "3",
        "num_4": "4", "num_5": "5", "num_6": "6", "num_7": "7",
        "num_8": "8", "num_9": "9",
    }
 
    while True:
        # ── Check timer ──
        time_left = deadline - time.time()
        if time_left <= 0:
            win.color = BG_IDLE
            return "TIME_UP"
 
        anim_t = time.time()
 
        # ── Exit button mouse detection ──
        mouse_down = mouse.getPressed()[0]
        if mouse_down and not _mouse_was_down:
            if _exit_btn_hit(mouse):
                win.color = BG_IDLE
                return None          # same as old escape — triggers farewell
        _mouse_was_down = mouse_down
 
        keys = event.getKeys(keyList=None)
        for key in keys:
            if key == "return":
                win.color = BG_FLASH
                redraw_scene(win, history, profile, typed, True,
                             time_left=time_left, anim_t=anim_t)
                core.wait(0.10)
                win.color = BG_IDLE
                return typed.strip()
            elif key == "backspace":
                if cursor > 0:
                    typed  = typed[:cursor - 1] + typed[cursor:]
                    cursor -= 1
            elif key == "delete":
                if cursor < len(typed):
                    typed = typed[:cursor] + typed[cursor + 1:]
            elif key == "left":
                cursor = max(0, cursor - 1)
            elif key == "right":
                cursor = min(len(typed), cursor + 1)
            elif key == "home":
                cursor = 0
            elif key == "end":
                cursor = len(typed)
            elif key in KEY_MAP:
                ch     = KEY_MAP[key]
                typed  = typed[:cursor] + ch + typed[cursor:]
                cursor += 1
            elif len(key) == 1:
                typed  = typed[:cursor] + key + typed[cursor:]
                cursor += 1
 
        new_typing = len(typed) > 0
        if new_typing != is_typing:
            win.color = BG_TYPING if new_typing else BG_IDLE
            is_typing = new_typing
 
        # ── FPS cap: only redraw when a full frame period has elapsed ──
        now = time.time()
        if now - _last_frame >= FRAME_T:
            redraw_scene(win, history, profile, typed, is_typing,
                         time_left=time_left, anim_t=anim_t)
            _last_frame = now
        else:
            core.wait(0.001)   # yield CPU instead of busy-spinning
# ─────────────────────────────────────────────────────────────
# 13. THINKING — simple static wait (no animation)
# ─────────────────────────────────────────────────────────────

def show_thinking(win, history, profile, deadline, duration=1.8, stop_event=None):
    """Wait silently while LLM responds — no animation overhead."""
    if stop_event is not None:
        while not stop_event.is_set():
            if deadline - time.time() <= 0:
                return
            core.wait(0.05)
    else:
        core.wait(min(duration, max(0, deadline - time.time())))


# ─────────────────────────────────────────────────────────────
# 14. CONVERSATION LOOP
# ─────────────────────────────────────────────────────────────

def run_conversation(win, agent, time_limit=300):
    history  = []
    profile  = {**agent.profile, "name": agent.name}
    deadline = time.time() + time_limit

    history.append(("agent", agent.greet()))

    while True:
        user_text = get_text_input(win, history, profile, deadline)

        if user_text == "TIME_UP":
            show_message(win, "⏱  Time is up!\n\nThe session has ended.",
                         duration=2.0, color="#FF4444")
            break
        if user_text is None:
            break
        if not user_text:
            continue

        history.append(("user", user_text))

        # ── Fetch LLM reply in background thread; animate dots meanwhile ──
        reply_box  = [None]
        stop_event = threading.Event()

        def fetch_reply():
            reply_box[0] = agent.respond_llm(user_text)
            stop_event.set()

        t = threading.Thread(target=fetch_reply, daemon=True)
        t.start()

        # Thinking animation runs until the thread finishes (or time is up)
        show_thinking(win, history, profile, deadline, stop_event=stop_event)
        t.join()   # make sure thread is done before reading result

        reply = reply_box[0] or ""
        history.append(("agent", reply))

    win.color = BG_IDLE
    show_message(win, agent.farewell(), duration=3.0,
                 color=agent.profile["color"])
    return history

# ─────────────────────────────────────────────────────────────
# 15. SAVE CHAT TO CSV
# ─────────────────────────────────────────────────────────────

def save_chat_csv(chat_log, participant_id, agent_name, avatar_gender="unknown"):
    """
    Append conversation to a single CSV file per participant in a 'data' folder.
    All conversations for a participant are saved in one file.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir   = os.path.join(script_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    pid      = participant_id.strip() or "unknown"
    filename = os.path.join(data_dir, f"chat_{pid}.csv")

    # Write header only if the file doesn't exist yet
    file_exists = os.path.isfile(filename)
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")

    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["turn", "role", "message", "participant_id",
                             "agent", "avatar_gender", "session_timestamp"])
        for i, (role, text) in enumerate(chat_log):
            writer.writerow([i + 1, role, text, pid, agent_name,
                             avatar_gender, timestamp])

    return filename



# ─────────────────────────────────────────────────────────────
# 15b. IN-WINDOW PERSONALITY SELECTION SCREEN
# ─────────────────────────────────────────────────────────────

def show_personality_selection(win):
    """
    Full-screen in-window screen to pick a personality agent.
    Returns the chosen personality name string.
    """
    personalities = list(_PERSONALITY_BASE.keys())
    # Accent colours per personality (for card highlight)
    _pal_colors = {p: _PERSONALITY_BASE[p]["color"] for p in personalities}

    CARD_W, CARD_H = 200, 72
    GAP            = 18
    total_w        = len(personalities) * CARD_W + (len(personalities) - 1) * GAP
    start_x        = -total_w // 2 + CARD_W // 2
    CARD_Y         = 0

    mouse      = event.Mouse(win=win)
    mouse.clickReset()
    selected   = personalities[0]
    _prev_down = False

    CONFIRM_W, CONFIRM_H = 240, 50
    CONFIRM_Y = -WIN_H // 2 + 68

    def _card_cx(i):
        return start_x + i * (CARD_W + GAP)

    def _card_hit(mx, my, i):
        return (abs(mx - _card_cx(i)) <= CARD_W // 2 and
                abs(my - CARD_Y)      <= CARD_H // 2)

    while True:
        win.clearBuffer()

        # Background
        visual.Rect(win, width=WIN_W, height=WIN_H, pos=(0, 0),
                    fillColor="#060A14", lineColor=None).draw()
        for row in range(-WIN_H // 2, WIN_H // 2, 28):
            visual.Rect(win, width=WIN_W, height=1,
                        pos=(0, row), fillColor="#FFFFFF",
                        lineColor=None, opacity=0.018).draw()
        visual.Rect(win, width=WIN_W, height=4,
                    pos=(0, WIN_H // 2 - 2),
                    fillColor="#2A6AFF", lineColor=None).draw()

        # Title
        visual.Rect(win, width=460, height=44,
                    pos=(0, WIN_H // 2 - 52),
                    fillColor="#0D1830", lineColor="#2A4A8A",
                    lineWidth=1.5).draw()
        visual.TextStim(win, text="Choose a Person to Chat With",
                        pos=(0, WIN_H // 2 - 52),
                        color="white", height=22, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()
        visual.TextStim(win,
                        text="Click a card to select  •  press ENTER to confirm",
                        pos=(0, WIN_H // 2 - 86),
                        color="#2A4060", height=12, font="Arial",
                        anchorHoriz="center", anchorVert="center").draw()

        # Personality cards
        for i, p in enumerate(personalities):
            cx      = _card_cx(i)
            hl      = (p == selected)
            col     = _pal_colors[p]
            bg_col  = "#0F1E38" if hl else "#0A1428"
            brd_col = col       if hl else "#1E2E48"
            brd_w   = 3.0       if hl else 1.5

            # Glow
            if hl:
                for gr, go in [(8, 0.06), (4, 0.12)]:
                    visual.Rect(win, width=CARD_W + gr*2, height=CARD_H + gr*2,
                                pos=(cx, CARD_Y),
                                fillColor=col, lineColor=None, opacity=go).draw()
            # Shadow
            visual.Rect(win, width=CARD_W + 4, height=CARD_H + 4,
                        pos=(cx + 4, CARD_Y - 4),
                        fillColor="#000000", lineColor=None, opacity=0.25).draw()
            # Card body
            visual.Rect(win, width=CARD_W, height=CARD_H,
                        pos=(cx, CARD_Y),
                        fillColor=bg_col, lineColor=brd_col,
                        lineWidth=brd_w).draw()
            # Colour accent bar on left
            visual.Rect(win, width=5, height=CARD_H,
                        pos=(cx - CARD_W // 2 + 3, CARD_Y),
                        fillColor=col, lineColor=None).draw()
            # Label
            lbl_col = col if hl else "#8899BB"
            visual.TextStim(win, text=p,
                            pos=(cx + 6, CARD_Y),
                            color=lbl_col, height=15, font="Arial", bold=hl,
                            wrapWidth=CARD_W - 20,
                            anchorHoriz="center", anchorVert="center").draw()

        # Confirm button
        col_hi  = _pal_colors[selected]
        visual.Rect(win, width=CONFIRM_W + 12, height=CONFIRM_H + 12,
                    pos=(0, CONFIRM_Y),
                    fillColor=col_hi, lineColor=None, opacity=0.12).draw()
        visual.Rect(win, width=CONFIRM_W, height=CONFIRM_H,
                    pos=(0, CONFIRM_Y),
                    fillColor="#0F1E38", lineColor=col_hi, lineWidth=2.0).draw()
        visual.TextStim(win, text=f"Chat with {selected.split()[0]}   →",
                        pos=(0, CONFIRM_Y),
                        color="white", height=17, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()

        win.flip()

        # Keyboard: number keys 1-4, arrow keys, enter
        keys = event.getKeys(keyList=["1","2","3","4","left","right","return","escape"])
        for k in keys:
            if k == "escape":
                core.quit()
            elif k == "return":
                return selected
            elif k in ("1","2","3","4"):
                idx = int(k) - 1
                if idx < len(personalities):
                    selected = personalities[idx]
            elif k == "left":
                idx = personalities.index(selected)
                selected = personalities[(idx - 1) % len(personalities)]
            elif k == "right":
                idx = personalities.index(selected)
                selected = personalities[(idx + 1) % len(personalities)]

        # Mouse
        down = mouse.getPressed()[0]
        if down and not _prev_down:
            mx, my = mouse.getPos()
            for i, p in enumerate(personalities):
                if _card_hit(mx, my, i):
                    selected = p
            if (abs(mx) <= CONFIRM_W // 2 and
                    abs(my - CONFIRM_Y) <= CONFIRM_H // 2):
                return selected
        _prev_down = down
        core.wait(0.016)


# ─────────────────────────────────────────────────────────────
# 15c. SESSION END SCREEN — "Talk to Another Agent" or "End Session"
# ─────────────────────────────────────────────────────────────

def show_session_end_screen(win, accent):
    """
    Shown after a conversation ends.
    Returns True  → user wants to talk to another agent.
    Returns False → user wants to end the session.
    """
    BTN_W, BTN_H = 260, 54
    GAP          = 30
    LEFT_X       = -(BTN_W // 2 + GAP // 2)
    RIGHT_X      =   BTN_W // 2 + GAP // 2
    BTN_Y        = -60

    mouse      = event.Mouse(win=win)
    mouse.clickReset()
    _prev_down = False

    def _hit(mx, my, bx):
        return abs(mx - bx) <= BTN_W // 2 and abs(my - BTN_Y) <= BTN_H // 2

    while True:
        win.clearBuffer()

        # Dim background
        visual.Rect(win, width=WIN_W, height=WIN_H, pos=(0, 0),
                    fillColor="#060A14", lineColor=None).draw()
        for row in range(-WIN_H // 2, WIN_H // 2, 28):
            visual.Rect(win, width=WIN_W, height=1,
                        pos=(0, row), fillColor="#FFFFFF",
                        lineColor=None, opacity=0.018).draw()
        visual.Rect(win, width=WIN_W, height=4,
                    pos=(0, WIN_H // 2 - 2),
                    fillColor=accent, lineColor=None).draw()

        # Panel
        visual.Rect(win, width=560, height=260, pos=(0, 20),
                    fillColor="#0B1222", lineColor=accent,
                    lineWidth=2.0, opacity=0.97).draw()
        visual.Rect(win, width=560, height=4, pos=(0, 148),
                    fillColor=accent, lineColor=None, opacity=0.80).draw()

        # Title
        visual.TextStim(win, text="Session Complete",
                        pos=(0, 90),
                        color="white", height=26, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()
        visual.TextStim(win,
                        text="Would you like to chat with someone else?",
                        pos=(0, 48),
                        color="#8899BB", height=16, font="Arial",
                        anchorHoriz="center", anchorVert="center").draw()

        # ── "Talk to Another Agent" button (left) ──
        visual.Rect(win, width=BTN_W + 10, height=BTN_H + 10,
                    pos=(LEFT_X, BTN_Y),
                    fillColor=accent, lineColor=None, opacity=0.12).draw()
        visual.Rect(win, width=BTN_W, height=BTN_H,
                    pos=(LEFT_X, BTN_Y),
                    fillColor="#0F2A1A", lineColor="#4CAF50",
                    lineWidth=2.0).draw()
        visual.TextStim(win, text="↩  Chat with Someone Else",
                        pos=(LEFT_X, BTN_Y),
                        color="#4CAF50", height=15, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()

        # ── "End Session" button (right) ──
        visual.Rect(win, width=BTN_W, height=BTN_H,
                    pos=(RIGHT_X, BTN_Y),
                    fillColor="#1A0A0A", lineColor="#CC3333",
                    lineWidth=2.0).draw()
        visual.TextStim(win, text="✕  End Session",
                        pos=(RIGHT_X, BTN_Y),
                        color="#FF5555", height=15, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()


        win.flip()

        keys = event.getKeys(keyList=["r", "e", "escape"])
        for k in keys:
            if k == "r":
                return True
            elif k in ("e", "escape"):
                return False

        down = mouse.getPressed()[0]
        if down and not _prev_down:
            mx, my = mouse.getPos()
            if _hit(mx, my, LEFT_X):
                return True
            if _hit(mx, my, RIGHT_X):
                return False
        _prev_down = down
        core.wait(0.016)

# ─────────────────────────────────────────────────────────────
# 16. PRE-CONVERSATION POPUP & THANK YOU SCREEN
# ─────────────────────────────────────────────────────────────

# Human-readable display names — no "agent" anywhere
_PERSONALITY_LABELS = {
    "Warm & Supportive":     "warm and supportive",
    "Confident & Efficient": "confident and efficient",
    "Cold & Critical":       "cold and critical",
    "Anxious & Hesitant":    "anxious and hesitant",
}


def show_pre_conversation_popup(win, personality, avatar_name, accent):
    """
    Full-screen instruction popup shown before each conversation.
    Tells the participant who they are about to chat with.
    Press any key or click to dismiss.
    """
    label = _PERSONALITY_LABELS.get(personality, personality.lower())

    win.clearBuffer()
    visual.Rect(win, width=WIN_W, height=WIN_H, pos=(0, 0),
                fillColor="#060A14", lineColor=None).draw()
    # Accent top bar
    visual.Rect(win, width=WIN_W, height=4, pos=(0, WIN_H//2 - 2),
                fillColor=accent, lineColor=None).draw()

    # Panel
    visual.Rect(win, width=640, height=300, pos=(0, 20),
                fillColor="#0B1222", lineColor=accent,
                lineWidth=2.0, opacity=0.97).draw()
    visual.Rect(win, width=640, height=4, pos=(0, 168),
                fillColor=accent, lineColor=None, opacity=0.80).draw()

    # Icon row — mini avatar
    draw_robot_avatar(win, 0, 100, accent=accent,
                      personality=personality, size=0.70)

    # Main instruction text
    visual.TextStim(win,
        text=f"You are about to chat with {avatar_name}.",
        pos=(0, 20),
        color="white", height=22, font="Arial", bold=True,
        anchorHoriz="center", anchorVert="center").draw()

    visual.TextStim(win,
        text=f"{avatar_name} has a {label} personality.\nRespond naturally, as you would in a real conversation.",
        pos=(0, -30),
        color="#94A3B8", height=16, font="Arial",
        wrapWidth=560,
        anchorHoriz="center", anchorVert="center").draw()

    visual.TextStim(win,
        text="Press any key or click to begin",
        pos=(0, -118),
        color="#334155", height=13, font="Arial",
        anchorHoriz="center", anchorVert="center").draw()

    win.flip()
    core.wait(0.5)   # brief pause so accidental keypress doesn't skip
    event.clearEvents()
    mouse = event.Mouse(win=win)
    mouse.clickReset()
    _prev_down = False
    while True:
        keys = event.getKeys()
        if keys:
            return
        down = mouse.getPressed()[0]
        if down and not _prev_down:
            return
        _prev_down = down
        core.wait(0.016)


def show_thankyou_screen(win, avatar_name, accent):
    """
    Brief thank-you screen shown after each conversation ends.
    Auto-advances after 3 s (or on keypress).
    """
    win.clearBuffer()
    visual.Rect(win, width=WIN_W, height=WIN_H, pos=(0, 0),
                fillColor="#060A14", lineColor=None).draw()
    visual.Rect(win, width=WIN_W, height=4, pos=(0, WIN_H//2 - 2),
                fillColor=accent, lineColor=None).draw()

    visual.Rect(win, width=560, height=220, pos=(0, 0),
                fillColor="#0B1222", lineColor=accent,
                lineWidth=2.0, opacity=0.97).draw()
    visual.Rect(win, width=560, height=4, pos=(0, 108),
                fillColor=accent, lineColor=None, opacity=0.80).draw()

    visual.TextStim(win, text="Thank You!",
                    pos=(0, 50),
                    color="white", height=28, font="Arial", bold=True,
                    anchorHoriz="center", anchorVert="center").draw()
    visual.TextStim(win,
        text=f"Thank you for your time.\n Session hs been ended",
        pos=(0, -5),
        color="#94A3B8", height=16, font="Arial",
        wrapWidth=500,
        anchorHoriz="center", anchorVert="center").draw()
    visual.TextStim(win, text="Continuing in a moment…",
                    pos=(0, -70),
                    color="#334155", height=13, font="Arial",
                    anchorHoriz="center", anchorVert="center").draw()

    win.flip()
    # Wait up to 3 s, skip on keypress
    deadline = core.getTime() + 3.0
    event.clearEvents()
    while core.getTime() < deadline:
        if event.getKeys():
            return
        core.wait(0.05)


# ─────────────────────────────────────────────────────────────
# 17. MODE SELECTION SCREEN — "Meet Everyone" vs "Choose One"
# ─────────────────────────────────────────────────────────────

def show_mode_selection(win):
    """
    Two-button screen at startup.
    Returns "all" or "one".
    """
    BTN_W, BTN_H = 280, 70
    LEFT_X  = -(BTN_W // 2 + 20)
    RIGHT_X =   BTN_W // 2 + 20
    BTN_Y   = -30

    mouse      = event.Mouse(win=win)
    mouse.clickReset()
    _prev_down = False

    def _hit(mx, my, bx):
        return abs(mx - bx) <= BTN_W//2 and abs(my - BTN_Y) <= BTN_H//2

    while True:
        win.clearBuffer()
        visual.Rect(win, width=WIN_W, height=WIN_H, pos=(0, 0),
                    fillColor="#060A14", lineColor=None).draw()
        for row in range(-WIN_H//2, WIN_H//2, 28):
            visual.Rect(win, width=WIN_W, height=1,
                        pos=(0, row), fillColor="#FFFFFF",
                        lineColor=None, opacity=0.018).draw()
        visual.Rect(win, width=WIN_W, height=4,
                    pos=(0, WIN_H//2 - 2),
                    fillColor="#2A6AFF", lineColor=None).draw()

        # Title
        visual.Rect(win, width=500, height=48,
                    pos=(0, WIN_H//2 - 55),
                    fillColor="#0D1830", lineColor="#2A4A8A", lineWidth=1.5).draw()
        visual.TextStim(win, text="Welcome to the Study",
                        pos=(0, WIN_H//2 - 55),
                        color="white", height=22, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()
        visual.TextStim(win,
            text="How would you like to proceed?",
            pos=(0, WIN_H//2 - 98),
            color="#4A6080", height=14, font="Arial",
            anchorHoriz="center", anchorVert="center").draw()

        # ── "Meet Everyone" button ──
        visual.Rect(win, width=BTN_W + 10, height=BTN_H + 10,
                    pos=(LEFT_X, BTN_Y),
                    fillColor="#2A6AFF", lineColor=None, opacity=0.10).draw()
        visual.Rect(win, width=BTN_W, height=BTN_H,
                    pos=(LEFT_X, BTN_Y),
                    fillColor="#0D1830", lineColor="#2A6AFF", lineWidth=2.0).draw()
        visual.TextStim(win, text="Meet Everyone",
                        pos=(LEFT_X, BTN_Y + 12),
                        color="white", height=18, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()
        visual.TextStim(win, text="Chat with all 4 people in order",
                        pos=(LEFT_X, BTN_Y - 14),
                        color="#4A6080", height=12, font="Arial",
                        anchorHoriz="center", anchorVert="center").draw()

        # ── "Choose Someone" button ──
        visual.Rect(win, width=BTN_W, height=BTN_H,
                    pos=(RIGHT_X, BTN_Y),
                    fillColor="#0D2010", lineColor="#22C55E", lineWidth=2.0).draw()
        visual.TextStim(win, text="Choose Someone",
                        pos=(RIGHT_X, BTN_Y + 12),
                        color="white", height=18, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()
        visual.TextStim(win, text="Pick who you want to chat with",
                        pos=(RIGHT_X, BTN_Y - 14),
                        color="#4A6080", height=12, font="Arial",
                        anchorHoriz="center", anchorVert="center").draw()

        # Keyboard hint
        visual.TextStim(win, text="A — meet everyone     C — choose someone",
                        pos=(0, BTN_Y - 68),
                        color="#2A4060", height=12, font="Arial",
                        anchorHoriz="center", anchorVert="center").draw()

        win.flip()

        keys = event.getKeys(keyList=["a", "c", "escape"])
        for k in keys:
            if k == "a":   return "all"
            if k == "c":   return "one"
            if k == "escape": core.quit()

        down = mouse.getPressed()[0]
        if down and not _prev_down:
            mx, my = mouse.getPos()
            if _hit(mx, my, LEFT_X):  return "all"
            if _hit(mx, my, RIGHT_X): return "one"
        _prev_down = down
        core.wait(0.016)


# ─────────────────────────────────────────────────────────────
# 18. TWO INTERACTION MODES
# ─────────────────────────────────────────────────────────────

def interact_all_one_by_one(win, pid, gender):
    """
    Cycle through every personality in order.
    Before each: instruction popup.
    After each:  thank-you screen + save CSV.
    After all 4: combined engagement PDF is generated automatically.
    """
    personalities = list(_PERSONALITY_BASE.keys())

    for i, personality in enumerate(personalities):
        _image_avatar_cache.clear()
        agent  = ConversationalAgent(name=personality, gender=gender)
        accent = agent.profile["color"]

        # ── Pre-conversation instruction popup ──
        show_pre_conversation_popup(win, personality, agent.avatar_name, accent)

        # ── Conversation ──
        chat_log = run_conversation(win, agent)

        # ── Save CSV ──
        saved_path = save_chat_csv(chat_log, participant_id=pid,
                                   agent_name=personality, avatar_gender=gender)
        print(f"✓ Saved [{i+1}/{len(personalities)}] → {saved_path}")

        # ── Accumulate engagement data (PDF emitted automatically after all 4) ──
        report_path = generate_report(chat_log, participant_id=pid, agent_name=personality)
        if report_path:
            print(f"✓ Combined engagement report saved → {report_path}")

        # ── Thank-you screen ──
        show_thankyou_screen(win, agent.avatar_name, accent)

    # ── All done — go back to mode selection is handled by caller ──


def interact_one(win, pid, initial_personality=None):
    """
    Free-pick mode: participant chooses one personality, chats once, then session ends.
    """
    chosen = initial_personality if initial_personality is not None else show_personality_selection(win)

    avatar_gender = show_avatar_selection(win, chosen)
    _image_avatar_cache.clear()
    agent  = ConversationalAgent(name=chosen, gender=avatar_gender)
    accent = agent.profile["color"]

    # ── Pre-conversation instruction popup ──
    show_pre_conversation_popup(win, chosen, agent.avatar_name, accent)

    # ── Conversation ──
    chat_log = run_conversation(win, agent)

    # ── Save CSV ──
    saved_path = save_chat_csv(chat_log, participant_id=pid,
                               agent_name=chosen, avatar_gender=avatar_gender)
    print(f"✓ Saved → {saved_path}")

    show_message(win, "Thank you for participating!\n\nThe session has ended.",
                 duration=3.0, color="white")
    win.close()
    core.quit()

    # ── Thank-you screen ──
    show_thankyou_screen(win, agent.avatar_name, accent)


# ─────────────────────────────────────────────────────────────
# 19. ENTRY POINT
# ─────────────────────────────────────────────────────────────

def main():
    pid  = get_participant_id()
    win  = make_window()

    # ── Gender selection once upfront (applies to all sessions) ──
    gender = show_avatar_selection(win, list(_PERSONALITY_BASE.keys())[0])

    # ── Step 1: Meet all 4 personalities one by one ──
    interact_all_one_by_one(win, pid, gender)

    # ── Step 2: After meeting everyone, offer free-pick ──
    show_message(win,
        "You have met everyone!\n\nYou can now choose who you would like\nto chat with again.",
        duration=0.1, color="white")
    event.waitKeys()
    interact_one(win, pid)

    show_message(win,
        "Thank you for participating!\n\nThe session has ended.",
        duration=3.0, color="white")
    win.close()
    core.quit()


if __name__ == "__main__":
    main()
