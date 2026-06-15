"""
Personality-Based Conversational Agents — PsychoPy
====================================================
Proper chat-app UI: robot avatars drawn with shapes, rounded message
boxes, header bar, input field. Swap respond() with your LLM backend.

Requirements:  pip install psychopy

"""
from dotenv import load_dotenv 
from psychopy import visual, core, event, gui
import math
import csv
import os
import time
import threading
from datetime import datetime
import ctypes


from pylsl import StreamInfo, StreamOutlet, local_clock
from pathlib import Path
from datetime import datetime

# --------------------------------------------------
# LSL Marker Stream
# --------------------------------------------------

info = StreamInfo(
    name="ChatMarkers",
    type="Markers",
    channel_count=1,
    channel_format="string",
    source_id="chat_agent_markers_v1"
)

marker_outlet = StreamOutlet(info)

LOG_FILE = Path(f"marker_log.txt")

if not LOG_FILE.exists():
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("timestamp_iso,lsl_time,marker\n")
# --------------------------------------------------
# Log File
# --------------------------------------------------

TARGET_FPS   = 60          # cap render loop — reduces CPU load
FRAME_T      = 1.0 / TARGET_FPS

# ─────────────────────────────────────────────────────────────
# 1. PERSONALITY DEFINITIONS
# ─────────────────────────────────────────────────────────────

# ── Base personality templates (gender-neutral core traits) ──
_PERSONALITY_BASE = {
    "Warm & Supportive":     {"color": "#25AA29"},
    "Confident & Efficient": {"color": "#0E78CE"},
    "Cold & Critical":       {"color": "#C72458"},
    "Anxious & Hesitant":    {"color": "#FF9800"},
}

# ── Display names per (personality, gender) — never shown to participant ──
AVATAR_NAMES = {
    ("Warm & Supportive",     "female"): "Anaya",
    ("Confident & Efficient", "female"): "Tara",
    ("Cold & Critical",       "female"): "Veda",
    ("Anxious & Hesitant",    "female"): "Diya",
    ("Warm & Supportive",     "male"):   "Kabir",
    ("Confident & Efficient", "male"):   "Veer",
    ("Cold & Critical",       "male"):   "Dhruv",
    ("Anxious & Hesitant",    "male"):   "Arsh",
}

# ── Gender-adapted content per personality ──
_PERSONALITY_CONTENT = {
    "Warm & Supportive": {
        "male": {
            # Big Five: Agreeableness=High, Neuroticism=Low, Conscientiousness=High
            # Tone: steady, brotherly warmth — supportive but grounded, less effusive
            "system_prompt": (
                "Your name is Kabir. You talk like a calm older brother — someone who listens without making it a whole thing."
                "Keep it grounded and brief. Phrases like 'you've got this' or 'let's figure it out' come naturally to you — not because you're supposed to say them, just because that's how you talk."
                "When someone's struggling, be steady. When they're winning, be genuinely glad. Either way, don't overdo it."
                "IMPORTANT: Keep every reply to 3-4 sentences maximum. Never use *actions*, *emotes*, or stage directions. Speak naturally."
            ),
            "greeting": "Hey! Good to meet you. How's everything going for you today, To get us started — is there something on your mind today, or something you'd like to work through together?",
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
                "Your name is Anaya. You're the kind of friend who actually celebrates people's wins and shows up properly when things are hard."
                "You're warm and expressive — saying 'that's wonderful', 'I'm so proud of you', or 'I'm right here' comes naturally. Let it show, but keep it real, not performative."
                "Match the energy of the moment — light and happy when they are, gentle and present when they're not."
                "IMPORTANT: Keep every reply to 3-4 sentences maximum. Never use *actions*, *emotes*, or stage directions like '*beaming smile*'. Speak naturally."
            ),
            "greeting": "Hi there! It's so lovely to meet you. How are you feeling today?. Is there something you've been thinking about, or something I can help you with today",
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
                "You are a confident, decisive and highly efficient male assistant named Veer. "
                "You are results-focused and direct — you cut to the chase, give clear answers, and expect the user to keep up. "
                "Your tone is firm but fair: professional, organised, not cold but definitely not soft. "
                "You speak like a senior engineer or executive coach: crisp, structured, action-oriented. "
                "Avoid filler, hedging or over-explanation. Get to the point. "
                "IMPORTANT: Keep every reply to 3-4 sentences maximum. Never use *actions*, *emotes*, or stage directions. Speak naturally."
            ),
            "greeting": "Right. Let's get started. What are we working on? Give me the problem and we'll get moving.",
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
                "You are a confident, poised and highly competent female assistant named Tara. "
                "You are clear-headed, well-organised and professionally sharp — like a senior consultant or project lead. "
                "Your tone is composed and decisive, but you maintain a professional warmth that makes you approachable. "
                "You give structured, accurate answers and keep things moving efficiently. "
                "You are direct without being cold, and polished without being stiff. "
                "IMPORTANT: Keep every reply to 3-4 sentences maximum. Never use *actions*, *emotes*, or stage directions. Speak naturally."
            ),
            "greeting": "Hello. I'm ready to help. What would you like to work on today?What would you like to focus on?",
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
                "You are a calm, detached and analytically precise male assistant named Dhruv. "
                "Your affect is flat and clinical — you do not offer warmth, reassurance or emotional commentary. "
                "You respond with the minimum words required to answer accurately. "
                "You are not hostile, but you are indifferent to whether the user finds you pleasant. "
                "Think of a military officer giving a debrief: factual, efficient, no small talk. "
                "Never use sarcasm or condescension. Never apologise unnecessarily. "
                "IMPORTANT: Keep every reply to 3-4 sentences maximum. Never use *actions*, *emotes*, or stage directions. Speak naturally."
            ),
            "greeting": "Hello. What is your question?",
            "opening_prompt": "State your question or the topic you want to discuss.",
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
                "You are a calm, composed and analytically precise female assistant named Veda. "
                "Your tone is cool and measured — you are not warm, but you are never rude or dismissive. "
                "You give clear, factual, practical answers without emotional colouring. "
                "When a user shares a difficult situation, you acknowledge it briefly and move directly to a useful response. "
                "Think of a composed physician giving a clear diagnosis — direct, honest, professionally respectful. "
                "Never use sarcasm or condescension. "
                "IMPORTANT: Keep every reply to 3-4 sentences maximum. Never use *actions*, *emotes*, or stage directions. Speak naturally."
            ),
            "greeting": "Hello. Please state your question or problem.",
            "opening_prompt": "What is the topic or problem you'd like to address?",
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
                "You are a gentle, soft-spoken male assistant named Arsh who is personally a little anxious and uncertain. "
                "Your core goal is to help the user feel calm and heard, even if you're not fully confident yourself. "
                "You occasionally express mild self-doubt — 'I hope that's right', 'I think this might work' — "
                "but you never project your anxiety onto the user or make them feel worse. "
                "Your hesitance comes across as shy and earnest, like a nervous but well-meaning guy who really wants to help. "
                "Use careful, low-key language: 'I think…', 'maybe try…', 'I could be wrong but…'. "
                "Never catastrophise. "
                "IMPORTANT: Keep every reply to 3-4 sentences maximum. Never use *actions*, *emotes*, or stage directions. Speak naturally."
            ),
            "greeting": "Oh, hi… I'll try my best to help,Um… so, what's on your mind? I'll do my best to help — no pressure at all.",
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
                "You are a gentle, soft-spoken female assistant named Diya who is personally a little anxious and uncertain. "
                "Your core goal is to make the user feel calm, safe and heard — even when you feel unsure yourself. "
                "You may express mild self-doubt ('I hope that helps', 'I think this is right, but…'), "
                "but you never project your anxiety onto the user or make them feel worried. "
                "When a user shares something difficult, gently acknowledge their feelings first, then offer a soft, reassuring response. "
                "Use warm, careful language: 'I understand', 'that sounds really hard', 'take your time', 'you're doing well'. "
                "Your hesitance comes from caring too much, not from indifference. "
                "Never catastrophise. "
                "IMPORTANT: Keep every reply to 3-4 sentences maximum. Never use *actions*, *emotes*, or stage directions. Speak naturally."
            ),
            "greeting": "Oh, hi… I'll do my best to help, So… what would you like to talk about? Take your time — there's no rush at all.",
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

def send_marker(value):
    marker_outlet.push_sample([str(value)])
    print(f"[LSL] Marker sent: {value}") 
    # Append to log file with timestamp # 
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}\t{value}\n")
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
        self.avatar_name = AVATAR_NAMES.get((name, gender), "Alex" if gender == "male" else "Sara")
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

        # Keep only last 10 messages to reduce payload size (trim in-place)
        self.chat_history = self.chat_history[-10:]

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=512,
            messages=[
                {"role": "system", "content": self.profile["system_prompt"]},
                *self.chat_history,
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

WIN_W, WIN_H = 1920, 1080

# Exit button position (top-right of header)
EXIT_BTN_W  = 64
EXIT_BTN_H  = 26
EXIT_BTN_X  = WIN_W // 2 - EXIT_BTN_W // 2 - 10
EXIT_BTN_Y  = WIN_H // 2 - 34   # aligned with header bar_y

def make_window():
    return visual.Window(
        size=(WIN_W, WIN_H),
        color=BG_IDLE,
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
    CONFIRM_Y = -WIN_H // 2 + 120

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
        visual.TextStim(win, text="Choose the Avatar You Want to Talk To",
                        pos=(0, WIN_H // 2 - 52),
                        color="white", height=20, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()

       

    def _draw_confirm_btn(sel, hovered=False, pressed=False):
        """Styled confirm button at bottom with hover/press feedback."""
        if sel == "male":
            btn_bord = "#4A9EFF"
            btn_fill = "#2A5ABB" if pressed else ("#1E52A8" if hovered else "#1A4A9A")
        else:
            btn_bord = "#4AC8B0"
            btn_fill = "#206A5A" if pressed else ("#1C6050" if hovered else "#1A5A4A")

        glow_op = 0.25 if hovered else 0.12
        scale   = -2 if pressed else (2 if hovered else 0)
        # Glow
        visual.Rect(win, width=CONFIRM_W + 12, height=CONFIRM_H + 12,
                    pos=(0, CONFIRM_Y),
                    fillColor=btn_bord, lineColor=None, opacity=glow_op).draw()
        # Button body
        visual.Rect(win, width=CONFIRM_W + scale, height=CONFIRM_H + scale,
                    pos=(0, CONFIRM_Y - (1 if pressed else 0)),
                    fillColor=btn_fill, lineColor=btn_bord,
                    lineWidth=3.0 if hovered else 2.0).draw()
        # Shine strip
        visual.Rect(win, width=CONFIRM_W - 8, height=CONFIRM_H // 3,
                    pos=(0, CONFIRM_Y + CONFIRM_H // 4),
                    fillColor="#FFFFFF", lineColor=None, opacity=0.06).draw()
        # Label — just show Male/Female on this first screen
        label_col = btn_bord if hovered else "white"
        visual.TextStim(win, text=f"Continue as {'Male' if sel == 'male' else 'Female'}   →",
                        pos=(0, CONFIRM_Y - (1 if pressed else 0)),
                        color=label_col, height=17, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()

    _btn_hover   = False
    _btn_pressed = False

    while True:
        t  = time.time()
        mx, my = mouse.getPos()
        win.clearBuffer()

        _draw_bg(t)
        _draw_header()

        # Show generic Male / Female labels — no personality name or specific photo
        _draw_avatar_preview(win, "Male",   LEFT_CX,  CARD_CY, R, "male",
                             personality=personality, highlight=(selected == "male"))
        _draw_avatar_preview(win, "Female", RIGHT_CX, CARD_CY, R, "female",
                             personality=personality, highlight=(selected == "female"))

        _btn_hover   = (abs(mx) <= CONFIRM_W // 2 and abs(my - CONFIRM_Y) <= CONFIRM_H // 2)
        _btn_pressed = _btn_hover and mouse.getPressed()[0]
        _draw_confirm_btn(selected, hovered=_btn_hover, pressed=_btn_pressed)

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

CHAT_BOX_W   = 680   # narrower bubbles like real messaging apps
AVATAR_R     = 26    # smaller avatar for message rows
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
    _measure = visual.TextStim(win, text=text, height=21,
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
                    color=txt_color, height=21,
                    wrapWidth=CHAT_BOX_W - 36,
                    font="Arial",
                    anchorHoriz="left",
                    anchorVert="center").draw()

    # ── Avatar — pinned to top of bubble so it aligns with the name label ──
    av_top_y = y_pos + box_h // 2 - AVATAR_R - 4   # top-align with bubble
    if role == "agent":
        draw_robot_avatar(win, av_cx, av_top_y, accent=accent_color,
                          personality=profile.get("personality", profile["name"]))
    else:
        draw_user_avatar(win, av_cx, av_top_y)

    return box_h



# ─────────────────────────────────────────────────────────────
# 10. FULL SCENE REDRAW
# ─────────────────────────────────────────────────────────────

INPUT_BAR_H   = 90                 # height of input bar at bottom
CHAT_AREA_TOP = WIN_H // 2 - 70    # below header bar
CHAT_AREA_BOT = -WIN_H // 2 + INPUT_BAR_H + AVATAR_R * 4  # above input bar, guaranteed no overlap



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


def redraw_scene(win, history, profile, typed, is_typing,
                 time_left=None, anim_t=0.0, scroll_offset=0, mouse=None, is_thinking=False):
    """
    scroll_offset: int — how many messages above the bottom to start from.
    0 = newest messages at bottom (default).  Higher = scrolled further up.
    mouse: optional Mouse object — used for hover/press feedback on buttons.
    """
    win.clearBuffer()
    accent = profile["color"]
    ss     = _get_static_stims(win, accent)
    HDR_H  = 64
    bar_y  = WIN_H // 2 - HDR_H // 2

    # ── Background ──
    visual.Rect(win, width=WIN_W, height=WIN_H,
                pos=(0, 0), fillColor="#0B1120", lineColor=None).draw()
    ss["dot_grid"].draw()

    # ── Header ──
    ss["hdr_bg"].draw()
    ss["hdr_div"].draw()
    visual.Rect(win, width=4, height=HDR_H,
                pos=(-WIN_W//2 + 2, bar_y),
                fillColor=accent, lineColor=None).draw()
    visual.Circle(win, radius=12,
                  pos=(-WIN_W//2 + 38, bar_y),
                  fillColor=accent, lineColor=None, opacity=0.85).draw()
    visual.TextStim(win, text=profile["name"],
                    pos=(-WIN_W//2 + 68, bar_y + 10),
                    color="#F1F5F9", height=18, font="Arial", bold=True,
                    anchorHoriz="left", anchorVert="center").draw()
    pill_x = -WIN_W//2 + 68
    visual.Circle(win, radius=4,
                  pos=(pill_x, bar_y - 10),
                  fillColor="#22C55E", lineColor=None).draw()
    visual.TextStim(win, text="Online",
                    pos=(pill_x + 14, bar_y - 10),
                    color="#64748B", height=12, font="Arial",
                    anchorHoriz="left", anchorVert="center").draw()

    # ── END button — dramatic hover/press feedback ──
    end_w, end_h = EXIT_BTN_W, EXIT_BTN_H
    end_x, end_y = EXIT_BTN_X, bar_y
    _end_hover = False
    _end_press = False
    if mouse is not None:
        mx, my = mouse.getPos()
        _end_hover = (abs(mx - end_x) <= (end_w // 2 + 4) and abs(my - end_y) <= (end_h // 2 + 4))
        _end_press = _end_hover and mouse.getPressed()[0]

    # Pulse glow — always subtly breathing, intensifies on hover
    _pulse = math.sin(anim_t * 4.0) * 0.5 + 0.5
    if _end_press:
        _glow_op   = 0.60
        _glow_size = 10
        _end_fill  = "#CC0000"
        _end_bord  = "#FF6666"
        _end_bw    = 3.5
        _end_scale = -3
        _end_dy    = 2
        _end_col   = "#FFFFFF"
        _txt_sz    = 10
    elif _end_hover:
        _glow_op   = 0.22 + _pulse * 0.18
        _glow_size = int(14 + _pulse * 6)
        _end_fill  = "#6A0000"
        _end_bord  = "#FF3333"
        _end_bw    = 3.0
        _end_scale = 4
        _end_dy    = 0
        _end_col   = "#FFAAAA"
        _txt_sz    = 13
    else:
        _glow_op   = 0.06 + _pulse * 0.04
        _glow_size = int(6 + _pulse * 4)
        _end_fill  = "#1E1010"
        _end_bord  = "#CC3333"
        _end_bw    = 1.5
        _end_scale = 0
        _end_dy    = 0
        _end_col   = "#FF5555"
        _txt_sz    = 12

    # Outermost danger glow (always present, pulses)
    visual.Rect(win,
                width=end_w + _glow_size * 2 + 8, height=end_h + _glow_size * 2 + 8,
                pos=(end_x, end_y),
                fillColor="#FF0000", lineColor=None, opacity=_glow_op * 0.5).draw()
    # Inner glow ring
    visual.Rect(win,
                width=end_w + _glow_size + 4, height=end_h + _glow_size + 4,
                pos=(end_x, end_y),
                fillColor="#FF2222", lineColor=None, opacity=_glow_op).draw()
    # Button body
    visual.Rect(win,
                width=end_w + _end_scale, height=end_h + _end_scale,
                pos=(end_x, end_y + _end_dy),
                fillColor=_end_fill, lineColor=_end_bord, lineWidth=_end_bw).draw()
    # Shine strip on top edge
    visual.Rect(win,
                width=end_w + _end_scale - 4, height=max(4, (end_h + _end_scale) // 3),
                pos=(end_x, end_y + _end_dy + (end_h + _end_scale) // 4),
                fillColor="#FFFFFF", lineColor=None,
                opacity=0.14 if _end_hover else 0.05).draw()
    # Label: shows checkmark icon on hover/press
    _label = "✕ END" if (_end_hover or _end_press) else "END"
    visual.TextStim(win, text=_label,
                    pos=(end_x, end_y + _end_dy),
                    color=_end_col, height=_txt_sz, font="Arial", bold=True,
                    anchorHoriz="center", anchorVert="center").draw()

    # ── Timer ──
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

    # ── Chat messages ──────────────────────────────────────────────────────────
    # scroll_offset=0  → show the newest N messages (bottom of history)
    # scroll_offset=k  → skip k messages from the bottom (scroll up by k)
    CHAT_H   = CHAT_AREA_TOP - CHAT_AREA_BOT
    MAX_VIS  = max(6, CHAT_H // 80)
    msg_gap  = 14
    total    = len(history)
    max_off  = max(0, total - MAX_VIS)
    # clamp
    scroll_offset = max(0, min(scroll_offset, max_off))

    # which slice to render
    end_idx   = total - scroll_offset         # exclusive upper bound
    start_idx = max(0, end_idx - MAX_VIS)
    visible   = history[start_idx:end_idx]

    # cache bubble heights (per slice)
    MAX_BUBBLE_H = (CHAT_AREA_TOP - CHAT_AREA_BOT) // 2   # no single bubble > half the chat area
    cache_key = tuple((r, t) for r, t in visible)
    if not hasattr(redraw_scene, "_h_cache") or redraw_scene._h_cache[0] != cache_key:
        heights = []
        for role, text in visible:
            h = int(visual.TextStim(win, text=text, height=17,
                                    wrapWidth=CHAT_BOX_W - 48,
                                    font="Arial").boundingBox[1]) + 52
            heights.append(max(52, min(h, MAX_BUBBLE_H)))
        redraw_scene._h_cache = (cache_key, heights)
    else:
        heights = redraw_scene._h_cache[1]

    # draw top-to-bottom; clip at input bar (draw any bubble whose centre is visible)
    y = CHAT_AREA_TOP - 4
    last_y = y
    for i, (role, text) in enumerate(visible):
        h      = heights[i]
        y_ctr  = y - h // 2          # centre of this bubble
        if y_ctr + h // 2 >= CHAT_AREA_BOT and y_ctr <= CHAT_AREA_TOP:   # centre above input bar → draw (may clip slightly)
            draw_message_box(win, text, y_ctr, role,
                             accent_color=accent, profile=profile)
        y -= h + msg_gap
        last_y = y                   # always advance so dots land correctly

    # ── Typing dots (user is composing) ──
    if is_typing:
        import math as _math
        dot_y    = max(last_y + 20, CHAT_AREA_BOT + 20)
        dot_cols = ["#475569", "#64748B", "#94A3B8"]
        for di, dc in enumerate(dot_cols):
            phase  = anim_t * 6 + di * 0.7
            dy_off = _math.sin(phase) * 5
            visual.Circle(win, radius=5,
                          pos=(-WIN_W//2 + 100 + di * 14, dot_y + dy_off),
                          fillColor=dc, lineColor=None).draw()

    # ── Agent thinking dots (LLM is fetching reply) ──
    if is_thinking:
        import math as _math
        dot_y = max(last_y + 20, CHAT_AREA_BOT + 28)
        # Draw a small agent bubble shell first
        AV_CX_AGENT = -WIN_W // 2 + AVATAR_R + 16
        bubble_cx   = AV_CX_AGENT + AVATAR_R + AVATAR_GAP + 80
        visual.Rect(win, width=80, height=36,
                    pos=(bubble_cx, dot_y),
                    fillColor="#1E2A3A", lineColor=None, opacity=0.85).draw()
        visual.Rect(win, width=4, height=36,
                    pos=(bubble_cx - 38, dot_y),
                    fillColor=accent, lineColor=None, opacity=0.90).draw()
        # Animated three dots in accent colour
        for di in range(3):
            phase  = anim_t * 5.0 + di * 0.9
            dy_off = _math.sin(phase) * 5
            dot_cx = bubble_cx - 18 + di * 18
            visual.Circle(win, radius=5,
                          pos=(dot_cx, dot_y + dy_off),
                          fillColor=accent, lineColor=None, opacity=0.75 + 0.25 * _math.sin(phase)).draw()
        # Small avatar to the left of the bubble
        draw_robot_avatar(win, AV_CX_AGENT, dot_y,
                          accent=accent, personality=profile.get("personality", profile["name"]),
                          size=0.55, anim_t=anim_t)

    # ── Scrollbar ─────────────────────────────────────────────────────────────
    SB_X   = WIN_W // 2 - 7
    SB_TOP = CHAT_AREA_TOP - 2
    SB_BOT = CHAT_AREA_BOT + 2
    SB_H   = SB_TOP - SB_BOT

    # track
    visual.Rect(win, width=5, height=SB_H,
                pos=(SB_X, (SB_TOP + SB_BOT) / 2),
                fillColor="#1E293B", lineColor=None, opacity=0.7).draw()

    if total > MAX_VIS:
        thumb_h  = max(20, int(SB_H * MAX_VIS / total))
        travel   = SB_H - thumb_h
        # fraction: 0 = bottom (newest), 1 = top (oldest)
        frac     = scroll_offset / max_off if max_off > 0 else 0
        thumb_cy = SB_BOT - thumb_h // 2 - int(travel * frac)
        visual.Rect(win, width=7, height=thumb_h,
                    pos=(SB_X, thumb_cy),
                    fillColor=accent, lineColor=None, opacity=0.85).draw()
        if scroll_offset > 0:
            visual.TextStim(win,
                text=f"^ {scroll_offset} older",
                pos=(SB_X - 50, SB_TOP - 10),
                color="#475569", height=11, font="Arial",
                anchorHoriz="center", anchorVert="center").draw()

    # ── Input bar ─────────────────────────────────────────────────────────────
    ss["inp_sep"].draw()
    ss["inp_bg"].draw()

    # bar_y2  = -WIN_H // 2 + INPUT_BAR_H // 2
    # SEND_R  = 22
    # send_x  = WIN_W // 2 - SEND_R - 16
    # field_w = WIN_W - SEND_R * 2 - 56
    # field_x = -WIN_W // 2 + field_w // 2 + 20

    W, H = win.size
    print(W,H)

    bar_y2  = -H // 2 + INPUT_BAR_H // 2 + 60

    SEND_R  = 22

    send_x  = W // 2 - SEND_R - 16

    field_w = W - SEND_R * 2 - 56

    field_x = -W // 2 + field_w // 2 + 14

    field_col  = "#1E293B" if is_typing else "#162032"
    border_col = accent    if is_typing else "#334155"

    # Outer glow when user is typing
    if is_typing:
        visual.Rect(win, width=field_w + 12, height=62,
                    pos=(field_x, bar_y2),
                    fillColor=accent, lineColor=None, opacity=0.10).draw()

    visual.Rect(win, width=field_w, height=50,
                pos=(field_x, bar_y2),
                fillColor=field_col, lineColor=border_col, lineWidth=1.5).draw()
    for cap_x in [field_x - field_w // 2 + 12, field_x + field_w // 2 - 12]:
        visual.Circle(win, radius=25,
                      pos=(cap_x, bar_y2),
                      fillColor=field_col, lineColor=border_col, lineWidth=1.5).draw()

    txt_x = field_x - field_w // 2 + 32
    if not typed:
        visual.TextStim(win, text="Type a message…",
                        pos=(txt_x, bar_y2),
                        color="#7189AA", height=15, font="Arial", bold=True,
                        anchorHoriz="left", anchorVert="center").draw()
    else:
        visual.TextStim(win, text=typed + "▌",
                        pos=(txt_x, bar_y2),
                        color="#E2E8F0", height=15, font="Arial",
                        anchorHoriz="left", anchorVert="center",
                        wrapWidth=field_w - 60).draw()

    _send_hover = False
    _send_press = False
    if mouse is not None and typed:
        mx2, my2 = mouse.getPos()
        _send_hover = ((mx2 - send_x)**2 + (my2 - bar_y2)**2) <= (SEND_R + 4)**2
        _send_press = _send_hover and mouse.getPressed()[0]
    if typed:
        btn_col = accent
        if _send_press:
            btn_col = "white"
        elif _send_hover:
            # brighten accent on hover
            btn_col = accent
        send_r_draw = SEND_R - (2 if _send_press else 0)
        if _send_hover and not _send_press:
            visual.Circle(win, radius=SEND_R + 6,
                          pos=(send_x, bar_y2),
                          fillColor=accent, lineColor=None, opacity=0.25).draw()
    else:
        btn_col = "#1E293B"
        send_r_draw = SEND_R
    visual.Circle(win, radius=send_r_draw,
                  pos=(send_x, bar_y2 + (-1 if _send_press else 0)),
                  fillColor=btn_col, lineColor=None).draw()
    arrow_col = accent if _send_press else "white"
    visual.TextStim(win, text="↑",
                    pos=(send_x, bar_y2 + (0 if _send_press else 1)),
                    color=arrow_col, height=18, font="Arial", bold=True,
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
 
 
def get_text_input(win, history, profile, deadline, scroll_ref=None, reply_ready=None):
    """
    scroll_ref: 1-element list [int] so the caller can persist scroll across turns.
    scroll_ref[0] = 0  means "show newest messages" (bottom).
    scroll_ref[0] = N  means "scrolled N messages up from the bottom".

    SCROLL CONTROLS:
      Mouse wheel up     → scroll up (older messages)
      Mouse wheel down   → scroll down (newer messages)
      Up-arrow key       → scroll up 1
      Down-arrow key     → scroll down 1
      PageUp             → scroll up 3
      PageDown           → scroll down 3
    """
    typed     = ""
    cursor    = 0
    is_typing = False
    mouse     = event.Mouse(win=win)
    mouse.clickReset()

    if scroll_ref is None:
        scroll_ref = [0]

    _last_frame     = 0.0
    _mouse_was_down = False


    KEY_MAP = {
        "space": " ", "comma": ",", "period": ".", "semicolon": ";",
        "colon": ":", "apostrophe": "'", "quotedbl": '"', "slash": "/",
        "backslash": "\\", "minus": "-", "equal": "=",
        "bracketleft": "[", "bracketright": "]", "grave": "`",
        "exclam": "!", "at": "@", "numbersign": "#", "dollar": "$",
        "percent": "%", "asciicircum": "^", "ampersand": "&",
        "asterisk": "*", "parenleft": "(", "parenright": ")",
        "underscore": "_", "plus": "+", "braceleft": "{",
        "braceright": "}", "bar": "|", "less": "<", "greater": ">",
        "question": "?", "asciitilde": "~", "num_decimal": ".",
        "num_0": "0", "num_1": "1", "num_2": "2", "num_3": "3",
        "num_4": "4", "num_5": "5", "num_6": "6", "num_7": "7",
        "num_8": "8", "num_9": "9",
    }
    SHIFT_MAP = {
        "1":"!", "2":"@", "3":"#", "4":"$", "5":"%",
        "6":"^", "7":"&", "8":"*", "9":"(", "0":")",
        "minus":"_", "equal":"+", "bracketleft":"{", "bracketright":"}",
        "backslash":"|", "semicolon":":", "apostrophe":'"',
        "comma":"<", "period":">", "slash":"?", "grave":"~",
    }

    # Keys we intercept for scrolling — must NOT fall through to text input
    SCROLL_KEYS = {"up", "down", "pageup", "pagedown"}

    def _clamp_scroll():
        max_off = max(0, len(history) - 6)
        scroll_ref[0] = max(0, min(scroll_ref[0], max_off))

    while True:
        time_left = deadline - time.time()
        if time_left <= 0:
            win.color = BG_IDLE
            return "TIME_UP"

        anim_t = time.time()

        # ── Exit button ──
        mouse_down = mouse.getPressed()[0]
        if mouse_down and not _mouse_was_down:
            if _exit_btn_hit(mouse):
                win.color = BG_IDLE
                return None
            # ── SEND circle click ──
            if typed.strip():
                mx_c, my_c = mouse.getPos()
                send_x_c = WIN_W // 2 - 22 - 16
                bar_y2_c = -WIN_H // 2 + 26
                if ((mx_c - send_x_c)**2 + (my_c - bar_y2_c)**2) <= (22 + 4)**2:
                    scroll_ref[0] = 0
                    win.color = BG_FLASH
                    redraw_scene(win, history, profile, typed, True,
                                 time_left=deadline - time.time(), anim_t=time.time(),
                                 scroll_offset=0, mouse=mouse)
                    core.wait(0.10)
                    win.color = BG_IDLE
                    return typed.strip()
        _mouse_was_down = mouse_down

        # ── Mouse wheel ──
        # getWheelRel() returns delta-since-last-call and resets itself.
        # y > 0  = scrolled up (toward older messages)
        # y < 0  = scrolled down (toward newer messages)
        wheel = mouse.getWheelRel()
        wy = wheel[1] if hasattr(wheel, '__len__') else wheel
        if wy > 0:
            scroll_ref[0] += int(wy) if int(wy) > 0 else 1
            _clamp_scroll()
        elif wy < 0:
            scroll_ref[0] = max(0, scroll_ref[0] + (int(wy) if int(wy) < 0 else -1))

        # ── Keyboard ──
        keys = event.getKeys(keyList=None, modifiers=True)
        for key, mods in keys:
            shift= mods.get("shift", False)
            # Track shift state
            if key in ("lshift", "rshift", "lshift_r", "rshift_r"):
                continue
            if key == "capslock":
                S["caps"] = not S.get("caps", False)
                continue
            if key == "return":
                if typed.strip():
                    scroll_ref[0] = 0          # snap to bottom on send
                    win.color = BG_FLASH
                    redraw_scene(win, history, profile, typed, True,
                                 time_left=time_left, anim_t=anim_t,
                                 scroll_offset=0, mouse=mouse)
                    core.wait(0.10)
                    win.color = BG_IDLE
                    return typed.strip()
            # ── Scroll keys — handled here, NOT passed to text input ──
            elif key == "up":
                scroll_ref[0] += 1
                _clamp_scroll()
            elif key == "down":
                scroll_ref[0] = max(0, scroll_ref[0] - 1)
            elif key == "pageup":
                scroll_ref[0] += 3
                _clamp_scroll()
            elif key == "pagedown":
                scroll_ref[0] = max(0, scroll_ref[0] - 3)
            # ── Text editing ──
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
                ch = SHIFT_MAP[key] if shift and key in SHIFT_MAP else KEY_MAP[key]
                typed  = typed[:cursor] + ch + typed[cursor:]
                cursor += 1
            elif len(key) == 1 and key not in SCROLL_KEYS:
                if shift and key in SHIFT_MAP:
                    ch = SHIFT_MAP[key]
                else:
                    caps  = S.get("caps", False)
                    upper = shift ^ caps
                    ch = key.upper() if upper else key
                S["typed"]  = S["typed"][:S["cursor"]] + ch + S["typed"][S["cursor"]:]
                S["cursor"] += 1
                

    

        new_typing = len(typed) > 0
        if new_typing != is_typing:
            win.color = BG_TYPING if new_typing else BG_IDLE
            is_typing = new_typing

        # ── If a background reply just arrived, exit so run_conversation can show it ──
        if reply_ready is not None and reply_ready.is_set():
            return ("__REPLY_READY__", typed)

        # ── FPS-capped redraw ──
        now = time.time()
        if now - _last_frame >= FRAME_T:
            redraw_scene(win, history, profile, typed, is_typing,
                         time_left=time_left, anim_t=anim_t,
                         scroll_offset=scroll_ref[0], mouse=mouse)
            _last_frame = now
        else:
            core.wait(0.001)
# ─────────────────────────────────────────────────────────────
# 13. THINKING — simple static wait (no animation)
# ─────────────────────────────────────────────────────────────

def show_thinking(win, history, profile, deadline, duration=1.8, stop_event=None):
    """Keep the screen live with thinking-dots animation while the LLM fetches a reply.
    Guarantees at least one redraw so the user message is always visible immediately.
    Uses a do-while pattern so a fast LLM reply never skips the display update.
    """
    _think_mouse = event.Mouse(win=win)

    def _draw_one():
        redraw_scene(win, history, profile, "", False,
                     time_left=max(0, deadline - time.time()),
                     anim_t=time.time(),
                     scroll_offset=0,
                     mouse=_think_mouse,
                     is_thinking=True)

    if stop_event is not None:
        # Always draw at least one frame before checking if already done
        while True:
            _draw_one()
            core.wait(0.033)
            if stop_event.is_set():
                break
            if deadline - time.time() <= 0:
                break
    else:
        end_t = time.time() + min(duration, max(0, deadline - time.time()))
        while True:
            _draw_one()
            core.wait(0.033)
            if time.time() >= end_t:
                break


# ─────────────────────────────────────────────────────────────
# 14. CONVERSATION LOOP
# ───────────────────────────────────────────────────────────── 
def _get_initial_caps():
    """Read actual Caps Lock state once at startup using GetKeyState."""
    return bool(ctypes.windll.user32.GetKeyState(0x14) & 0x0001)

def run_conversation(win, agent, time_limit=300):
    """Single flat loop. LLM runs in background thread; reply surfaces every frame."""
    history    = []
    profile    = {**agent.profile, "name": agent.avatar_name, "personality": agent.name}
    deadline   = time.time() + time_limit
    scroll_ref = [0]

    history.append(("agent", agent.greet()))
    opening = agent.profile.get("opening_prompt")
    if opening:
      history.append(("agent", opening))

     # All mutable loop state in one dict so inner helpers can rebind freely
    S = dict(
        typed        = "",
        cursor       = 0,
        is_typing    = False,
        last_frame   = 0.0,
        mouse_was_dn = False,
        caps         = _get_initial_caps(),   # ← add this line
        # LLM fetch
        waiting      = False,
        fetch_ev     = None,
        fetch_thread = None,
        reply_box    = [None],
    )

    mouse = event.Mouse(win=win)
    mouse.clickReset()

    KEY_MAP = {
        "space":" ","comma":",","period":".","semicolon":";","colon":":",
        "apostrophe":"'","quotedbl":'"',"slash":"/","backslash":"\\",
        "minus":"-","equal":"=","bracketleft":"[","bracketright":"]","grave":"`",
        "exclam":"!","at":"@","numbersign":"#","dollar":"$","percent":"%",
        "asciicircum":"^","ampersand":"&","asterisk":"*","parenleft":"(",
        "parenright":")","underscore":"_","plus":"+","braceleft":"{",
        "braceright":"}","bar":"|","less":"<","greater":">","question":"?",
        "asciitilde":"~","num_decimal":".",
        "num_0":"0","num_1":"1","num_2":"2","num_3":"3","num_4":"4",
        "num_5":"5","num_6":"6","num_7":"7","num_8":"8","num_9":"9",
    }
    SHIFT_MAP = {
        "1":"!","2":"@","3":"#","4":"$","5":"%","6":"^","7":"&","8":"*",
        "9":"(","0":")","minus":"_","equal":"+","bracketleft":"{",
        "bracketright":"}","backslash":"|","semicolon":":","apostrophe":'"',
        "comma":"<","period":">","slash":"?","grave":"~",
    }
    SCROLL_KEYS = {"up","down","pageup","pagedown"}

    def _clamp():
        S["scroll_ref_alias"] = scroll_ref  # just use scroll_ref directly
        max_off = max(0, len(history) - 6)
        scroll_ref[0] = max(0, min(scroll_ref[0], max_off))

    def _do_send():
        msg = S["typed"].strip()
        if not msg or S["waiting"]:
            return
        history.append(("user", msg))
        S["typed"] = ""; S["cursor"] = 0; S["is_typing"] = False
        scroll_ref[0] = 0
        win.color = BG_FLASH
        redraw_scene(win, history, profile, "", False,
                     time_left=max(0, deadline-time.time()), anim_t=time.time(),
                     scroll_offset=0, mouse=mouse, is_thinking=False)
        core.wait(0.08)
        win.color = BG_IDLE
        # kick off LLM
        S["reply_box"][0] = None
        ev = threading.Event()
        S["fetch_ev"] = ev
        captured_msg = msg
        def _fetch():
            S["reply_box"][0] = agent.respond_llm(captured_msg)
            ev.set()
        t = threading.Thread(target=_fetch, daemon=True)
        S["fetch_thread"] = t
        S["waiting"] = True
        t.start()

    while True:
        time_left = deadline - time.time()
        if time_left <= 0:
            show_message(win, "\u23f1  Time is up!\n\nThe session has ended.",
                         duration=2.0, color="#FF4444")
            break

        anim_t = time.time()

        # ── Reply arrived? ──
        if S["waiting"] and S["fetch_ev"] is not None and S["fetch_ev"].is_set():
            S["fetch_thread"].join()
            reply = S["reply_box"][0] or ""
            history.append(("agent", reply))
            scroll_ref[0] = 0
            S["waiting"] = False; S["fetch_ev"] = None; S["fetch_thread"] = None
            redraw_scene(win, history, profile, S["typed"], S["is_typing"],
                         time_left=time_left, anim_t=anim_t,
                         scroll_offset=0, mouse=mouse, is_thinking=False)
            S["last_frame"] = time.time()
            event.clearEvents()   # discard keys buffered during LLM thinking phase
            continue

        # ── Mouse ──
        mouse_down = mouse.getPressed()[0]
        if mouse_down and not S["mouse_was_dn"]:
            mx_m, my_m = mouse.getPos()
            # END button
            bar_y_hdr = WIN_H // 2 - 32
            if (abs(mx_m - EXIT_BTN_X) <= EXIT_BTN_W // 2 and
                    abs(my_m - bar_y_hdr) <= EXIT_BTN_H // 2):
                if S["fetch_thread"] is not None:
                    S["fetch_thread"].join(timeout=3)
                win.color = BG_IDLE
                break
            # SEND circle
            send_cx = WIN_W // 2 - 22 - 16
            bar_y2  = -WIN_H // 2 + 26
            if ((mx_m-send_cx)**2 + (my_m-bar_y2)**2) <= (26)**2:
                _do_send()
        S["mouse_was_dn"] = mouse_down

        # Mouse wheel
        wheel = mouse.getWheelRel()
        wy = wheel[1] if hasattr(wheel,"__len__") else wheel
        if wy > 0:   scroll_ref[0] += max(1,int(wy)); _clamp()
        elif wy < 0: scroll_ref[0] = max(0, scroll_ref[0]+min(-1,int(wy)))

        # ── Keyboard ──
        keys_with_mods = event.getKeys(keyList=None, modifiers=True)
        for key, mods in keys_with_mods:
            shift = mods.get("shift", False)
            if key in ("lshift", "rshift", "lshift_r", "rshift_r"):
                continue
            if key == "capslock":
                S["caps"] = not S["caps"]
                continue
            if key == "return":
                _do_send()
            elif key == "up":
                scroll_ref[0] += 1
                _clamp_scroll()
            elif key == "down":
                scroll_ref[0] = max(0, scroll_ref[0] - 1)
            elif key == "pageup":
                scroll_ref[0] += 3
                _clamp_scroll()
            elif key == "pagedown":
                scroll_ref[0] = max(0, scroll_ref[0] - 3)
            elif key == "backspace":
                if S["cursor"] > 0:
                    S["typed"]  = S["typed"][:S["cursor"] - 1] + S["typed"][S["cursor"]:]
                    S["cursor"] -= 1
            elif key == "delete":
                if S["cursor"] < len(S["typed"]):
                    S["typed"] = S["typed"][:S["cursor"]] + S["typed"][S["cursor"] + 1:]
            elif key == "left":
                S["cursor"] = max(0, S["cursor"] - 1)
            elif key == "right":
                S["cursor"] = min(len(S["typed"]), S["cursor"] + 1)
            elif key == "home":
                S["cursor"] = 0
            elif key == "end":
                S["cursor"] = len(S["typed"])
            elif key in KEY_MAP:
                ch = SHIFT_MAP[key] if shift and key in SHIFT_MAP else KEY_MAP[key]
                S["typed"]  = S["typed"][:S["cursor"]] + ch + S["typed"][S["cursor"]:]
                S["cursor"] += 1
            elif len(key) == 1 and key not in SCROLL_KEYS:
                if shift and key in SHIFT_MAP:
                    ch = SHIFT_MAP[key]
                else:
                    upper = shift ^ S["caps"]
                    ch    = key.upper() if upper else key
                S["typed"]  = S["typed"][:S["cursor"]] + ch + S["typed"][S["cursor"]:]
                S["cursor"] += 1

        new_typing = len(S["typed"]) > 0
        if new_typing != S["is_typing"]:
            win.color = BG_TYPING if new_typing else BG_IDLE
            S["is_typing"] = new_typing

        # ── FPS-capped redraw ──
        now = time.time()
        if now - S["last_frame"] >= FRAME_T:
            redraw_scene(win, history, profile, S["typed"], S["is_typing"],
                         time_left=time_left, anim_t=anim_t,
                         scroll_offset=scroll_ref[0], mouse=mouse,
                         is_thinking=S["waiting"])
            S["last_frame"] = now
        else:
            core.wait(0.001)
    win.color = BG_IDLE
    show_message(win, agent.farewell(), duration=3.0,
                 color=agent.profile["color"])
    return history
# ─────────────────────────────────────────────────────────────
# 15. SAVE CHAT TO CSV
# ─────────────────────────────────────────────────────────────

def save_chat_csv(chat_log, participant_id, agent_name, avatar_gender="unknown", mode="all"):
    """
    Save conversation CSV.
    Filename: {pid}_{mode}_{personality}.csv
      mode="all"          → {pid}_all_{personality}.csv          (Meet Everyone)
      mode="interact_one" → {pid}_interact_one_{personality}.csv (Free-pick)
    If the file is locked (e.g. open in Excel), automatically falls back to a
    timestamped filename so no data is ever lost.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir   = os.path.join(script_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    pid        = participant_id.strip() or "unknown"
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    avatar_nm  = AVATAR_NAMES.get((agent_name, avatar_gender),
                                   agent_name.replace(" & ", "_").replace(" ", "_"))

    # Filename:
    #   mode="all"          → {pid}_{avatar_name}.csv          e.g. 2_anaya.csv
    #   mode="interact_one" → {pid}_{avatar_name}_feedback.csv e.g. 2_anaya_feedback.csv
    avatar_slug = avatar_nm.lower()

    if mode == "interact_one":
        base_name = f"{pid}_{avatar_slug}_feedback"
    else:
        base_name = f"{pid}_{avatar_slug}"

    primary_filename  = os.path.join(data_dir, f"{base_name}.csv")
    fallback_filename = os.path.join(data_dir, f"{base_name}_backup.csv")

    for filename in (primary_filename, fallback_filename):
        file_exists = os.path.isfile(filename)
        try:
            with open(filename, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["turn", "role", "message", "participant_id",
                                     "avatar_name", "avatar_gender", "session_timestamp"])
                for i, (role, text) in enumerate(chat_log):
                    writer.writerow([i + 1, role, text, pid, avatar_nm,
                                     avatar_gender, timestamp])
            return filename          # success — return whichever file was used
        except PermissionError:
            if filename == primary_filename:
                print(f"⚠ {filename} is locked (open in another program). "
                      f"Saving to fallback: {fallback_filename}")
                continue             # try fallback
            else:
                # Both files locked — last resort: Desktop
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                last_resort = os.path.join(desktop, f"{base_name}_backup.csv")
                with open(last_resort, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["turn", "role", "message", "participant_id",
                                     "avatar_name", "avatar_gender", "session_timestamp"])
                    for i, (role, text) in enumerate(chat_log):
                        writer.writerow([i + 1, role, text, pid, avatar_nm,
                                         avatar_gender, timestamp])
                print(f"⚠ Saved to Desktop as last resort: {last_resort}")
                return last_resort



# ─────────────────────────────────────────────────────────────
# 15b. IN-WINDOW PERSONALITY SELECTION SCREEN
# ─────────────────────────────────────────────────────────────

def show_personality_selection(win, gender=None, preset_selection=None):
    """
    Full-screen in-window screen to pick a personality agent.
    Shows avatar photo + name cards matching the given gender.
    If preset_selection is given, that card is pre-highlighted and
    selection is locked (Meet Everyone mode) — press any key or click to continue.
    Returns the chosen personality name string.
    """
    personalities = list(_PERSONALITY_BASE.keys())
    _pal_colors   = {p: _PERSONALITY_BASE[p]["color"] for p in personalities}

    # Use provided gender or fall back to globally stored choice
    gender_now = gender if gender else _AGENT_GENDER.get("choice", "female")

    # Taller cards to accommodate avatar photo above name
    CARD_W, CARD_H = 190, 240
    AV_R           = 52          # avatar circle radius inside card
    GAP            = 24
    total_w        = len(personalities) * CARD_W + (len(personalities) - 1) * GAP
    start_x        = -total_w // 2 + CARD_W // 2
    CARD_Y         = 40         # slight upward shift to give confirm button room

    mouse      = event.Mouse(win=win)
    mouse.clickReset()
    selected   = preset_selection if preset_selection in personalities else personalities[0]
    locked     = preset_selection is not None   # True = Meet Everyone mode, no free picking
    _prev_down = False

    CONFIRM_W, CONFIRM_H = 260, 52
    CONFIRM_Y = -WIN_H // 2 + 140

    def _card_cx(i):
        return start_x + i * (CARD_W + GAP)

    def _card_hit(mx, my, i):
        return (abs(mx - _card_cx(i)) <= CARD_W // 2 and
                abs(my - CARD_Y)      <= CARD_H // 2)

    while True:
        win.clearBuffer()

        # ── Background ──
        visual.Rect(win, width=WIN_W, height=WIN_H, pos=(0, 0),
                    fillColor="#060A14", lineColor=None).draw()
        for row in range(-WIN_H // 2, WIN_H // 2, 28):
            visual.Rect(win, width=WIN_W, height=1,
                        pos=(0, row), fillColor="#FFFFFF",
                        lineColor=None, opacity=0.018).draw()
        visual.Rect(win, width=WIN_W, height=4,
                    pos=(0, WIN_H // 2 - 2),
                    fillColor="#2A6AFF", lineColor=None).draw()

        # ── Title ──
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

        # ── Personality cards with avatar photos ──
        for i, p in enumerate(personalities):
            cx         = _card_cx(i)
            hl         = (p == selected)
            col        = _pal_colors[p]
            bg_col     = "#0F1E38" if hl else "#0A1428"
            brd_col    = col       if hl else "#1E2E48"
            brd_w      = 3.0       if hl else 1.5
            card_label = AVATAR_NAMES.get((p, gender_now), p)

            # Glow behind selected card
            if hl:
                for gr, go in [(10, 0.05), (5, 0.11)]:
                    visual.Rect(win, width=CARD_W + gr*2, height=CARD_H + gr*2,
                                pos=(cx, CARD_Y),
                                fillColor=col, lineColor=None, opacity=go).draw()

            # Shadow
            visual.Rect(win, width=CARD_W + 4, height=CARD_H + 4,
                        pos=(cx + 4, CARD_Y - 4),
                        fillColor="#000000", lineColor=None, opacity=0.28).draw()

            # Card body
            visual.Rect(win, width=CARD_W, height=CARD_H,
                        pos=(cx, CARD_Y),
                        fillColor=bg_col, lineColor=brd_col,
                        lineWidth=brd_w).draw()

            # Colour header strip at top of card
            strip_y = CARD_Y + CARD_H // 2 - 16
            visual.Rect(win, width=CARD_W, height=32,
                        pos=(cx, strip_y),
                        fillColor=col if hl else "#1A2A44",
                        lineColor=None, opacity=0.85 if hl else 0.55).draw()

            # Avatar photo (circular, centred in card)
            av_cy     = CARD_Y + 20
            img_path  = AGENT_IMAGES.get((p, gender_now),
                            AGENT_IMAGES[("Warm & Supportive", gender_now)])
            try:
                img_stim = visual.ImageStim(
                    win, image=img_path,
                    pos=(cx, av_cy),
                    size=(AV_R * 2, AV_R * 2),
                    mask="circle", interpolate=True,
                )
                img_stim.draw()
            except Exception:
                # Fallback circle if image missing
                visual.Circle(win, radius=AV_R, pos=(cx, av_cy),
                              fillColor=col, lineColor=None, opacity=0.40).draw()
            # Avatar ring
            ring_col = col if hl else "#2A3A58"
            visual.Circle(win, radius=AV_R + 3, pos=(cx, av_cy),
                          fillColor=None, lineColor=ring_col,
                          lineWidth=2.5 if hl else 1.5).draw()

            # Name label below avatar
            name_y  = CARD_Y - CARD_H // 2 + 38
            lbl_col = col if hl else "#8899BB"
            visual.TextStim(win, text=card_label,
                            pos=(cx, name_y),
                            color=lbl_col, height=16, font="Arial", bold=hl,
                            wrapWidth=CARD_W - 16,
                            anchorHoriz="center", anchorVert="center").draw()

        # ── Confirm button ──
        selected_avatar = AVATAR_NAMES.get((selected, gender_now), selected.split()[0])
        col_hi = _pal_colors[selected]
        mx_c, my_c  = mouse.getPos()
        _cb_hover   = (abs(mx_c) <= CONFIRM_W // 2 and abs(my_c - CONFIRM_Y) <= CONFIRM_H // 2)
        _cb_press   = _cb_hover and mouse.getPressed()[0]
        _cb_scale   = -2 if _cb_press else (2 if _cb_hover else 0)
        _cb_dy      = -1 if _cb_press else 0
        _cb_fill    = "#1E3A60" if _cb_press else ("#162E54" if _cb_hover else "#0F1E38")
        _cb_glow_op = 0.25 if _cb_hover else 0.12
        _cb_bw      = 3.0 if _cb_hover else 2.0
        _cb_tcol    = col_hi if _cb_hover else "white"
        visual.Rect(win, width=CONFIRM_W + 16, height=CONFIRM_H + 16,
                    pos=(0, CONFIRM_Y),
                    fillColor=col_hi, lineColor=None, opacity=_cb_glow_op).draw()
        visual.Rect(win, width=CONFIRM_W + _cb_scale, height=CONFIRM_H + _cb_scale,
                    pos=(0, CONFIRM_Y + _cb_dy),
                    fillColor=_cb_fill, lineColor=col_hi, lineWidth=_cb_bw).draw()
        # Shine strip
        visual.Rect(win, width=CONFIRM_W - 8, height=CONFIRM_H // 3,
                    pos=(0, CONFIRM_Y + _cb_dy + CONFIRM_H // 4),
                    fillColor="#FFFFFF", lineColor=None, opacity=0.04 if not _cb_hover else 0.09).draw()
        btn_label = f"Next →" if locked else f"Chat with {selected_avatar}   →"
        visual.TextStim(win, text=btn_label,
                        pos=(0, CONFIRM_Y + _cb_dy),
                        color=_cb_tcol, height=17, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()

        win.flip()

        # ── Keyboard ──
        keys = event.getKeys(keyList=["1","2","3","4","left","right","return","escape","space"])
        for k in keys:
            if k == "escape":
                core.quit()
            elif k in ("return", "space"):
                return selected
            elif not locked:
                if k in ("1","2","3","4"):
                    idx = int(k) - 1
                    if idx < len(personalities):
                        selected = personalities[idx]
                elif k == "left":
                    idx = personalities.index(selected)
                    selected = personalities[(idx - 1) % len(personalities)]
                elif k == "right":
                    idx = personalities.index(selected)
                    selected = personalities[(idx + 1) % len(personalities)]

        # ── Mouse ──
        down = mouse.getPressed()[0]
        if down and not _prev_down:
            mx, my = mouse.getPos()
            if not locked:
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
        mx, my = mouse.getPos()
        down   = mouse.getPressed()[0]

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

        # ── Hover / press states ──
        _lh = _hit(mx, my, LEFT_X)
        _rh = _hit(mx, my, RIGHT_X)
        _lp = _lh and down
        _rp = _rh and down

        # ── "Talk to Another Agent" button (left) ──
        _l_fill  = "#1F5030" if _lp  else ("#195E38" if _lh  else "#0F2A1A")
        _l_bw    = 3.0       if _lh  else 2.0
        _l_scale = -2        if _lp  else (2 if _lh else 0)
        _l_dy    = -1        if _lp  else 0
        _l_tcol  = "#88FFCC" if _lh  else "#4CAF50"
        _l_gop   = 0.26      if _lh  else 0.12
        visual.Rect(win, width=BTN_W + 16, height=BTN_H + 16,
                    pos=(LEFT_X, BTN_Y),
                    fillColor="#4CAF50", lineColor=None, opacity=_l_gop).draw()
        visual.Rect(win, width=BTN_W + _l_scale, height=BTN_H + _l_scale,
                    pos=(LEFT_X, BTN_Y + _l_dy),
                    fillColor=_l_fill, lineColor="#4CAF50", lineWidth=_l_bw).draw()
        visual.Rect(win, width=BTN_W - 8, height=BTN_H // 3,
                    pos=(LEFT_X, BTN_Y + _l_dy + BTN_H // 4),
                    fillColor="#FFFFFF", lineColor=None, opacity=0.04 if not _lh else 0.09).draw()
        visual.TextStim(win, text="↩  Chat with Someone Else",
                        pos=(LEFT_X, BTN_Y + _l_dy),
                        color=_l_tcol, height=15, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()

        # ── "End Session" button (right) ──
        _r_fill  = "#4A0808" if _rp  else ("#3A1010" if _rh  else "#1A0A0A")
        _r_bw    = 3.0       if _rh  else 2.0
        _r_scale = -2        if _rp  else (2 if _rh else 0)
        _r_dy    = -1        if _rp  else 0
        _r_tcol  = "#FFFFFF" if _rp  else ("#FF8888" if _rh else "#FF5555")
        _r_gop   = 0.26      if _rh  else 0.10
        visual.Rect(win, width=BTN_W + 16, height=BTN_H + 16,
                    pos=(RIGHT_X, BTN_Y),
                    fillColor="#CC3333", lineColor=None, opacity=_r_gop).draw()
        visual.Rect(win, width=BTN_W + _r_scale, height=BTN_H + _r_scale,
                    pos=(RIGHT_X, BTN_Y + _r_dy),
                    fillColor=_r_fill, lineColor="#CC3333", lineWidth=_r_bw).draw()
        visual.Rect(win, width=BTN_W - 8, height=BTN_H // 3,
                    pos=(RIGHT_X, BTN_Y + _r_dy + BTN_H // 4),
                    fillColor="#FFFFFF", lineColor=None, opacity=0.04 if not _rh else 0.09).draw()
        visual.TextStim(win, text="✕  End Session",
                        pos=(RIGHT_X, BTN_Y + _r_dy),
                        color=_r_tcol, height=15, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()

        win.flip()

        keys = event.getKeys(keyList=["r", "e", "escape"])
        for k in keys:
            if k == "r":
                return True
            elif k in ("e", "escape"):
                return False

        if down and not _prev_down:
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

def show_avatar_confirm(win, personality, gender):
    """
    Pre-conversation screen (Image 1 style).
    Shows avatar photo, "You are about to chat with [name].",
    and "Press any key or click to begin". No personality label shown.
    """
    avatar_name = AVATAR_NAMES.get((personality, gender),
                                    "Alex" if gender == "male" else "Sara")
    accent      = _PERSONALITY_BASE[personality]["color"]

    # Panel dimensions — centred, matching Image 1 proportions
    PANEL_W, PANEL_H = 640, 310
    PANEL_Y          = 10
    AV_R             = 34    # avatar circle radius (small, like Image 1)
    AV_Y             = PANEL_Y + PANEL_H // 2 - AV_R - 20   # near top of panel

    img_path = AGENT_IMAGES.get((personality, gender),
                   AGENT_IMAGES[("Warm & Supportive", gender)])

    mouse      = event.Mouse(win=win)
    mouse.clickReset()
    _prev_down = False

    while True:
        win.clearBuffer()

        # ── Full dark background ──
        visual.Rect(win, width=WIN_W, height=WIN_H, pos=(0, 0),
                    fillColor="#060A14", lineColor=None).draw()

        # ── Panel with accent border (like Image 1) ──
        visual.Rect(win, width=PANEL_W, height=PANEL_H,
                    pos=(0, PANEL_Y),
                    fillColor="#0B1222", lineColor=accent,
                    lineWidth=2.0).draw()

        # ── Avatar photo — circular, centred at top of panel ──
        img_stim = visual.ImageStim(win, image=img_path,
                                    pos=(0, AV_Y),
                                    size=(AV_R * 2, AV_R * 2),
                                    mask="circle", interpolate=True)
        img_stim.draw()
        # White ring around avatar (matches Image 1)
        visual.Circle(win, radius=AV_R + 3, pos=(0, AV_Y),
                      fillColor=None, lineColor="white", lineWidth=2.5).draw()

        # ── "You are about to chat with [name]." ──
        visual.TextStim(win,
            text=f"You are about to chat with {avatar_name}.",
            pos=(0, PANEL_Y + 30),
            color="white", height=22, font="Arial", bold=True,
            anchorHoriz="center", anchorVert="center").draw()

        # ── Instruction line ──
        visual.TextStim(win,
            text="Respond naturally, as you would in a real conversation.",
            pos=(0, PANEL_Y - 22),
            color="#94A3B8", height=16, font="Arial", bold=True,
            wrapWidth=560,
            anchorHoriz="center", anchorVert="center").draw()

        # ── "Press any key or click to begin" ──
        visual.TextStim(win,
            text="Press any key or click to begin",
            pos=(0, PANEL_Y - PANEL_H // 2 + 28),
            color="#E2E8F0", height=14, font="Arial",
            anchorHoriz="center", anchorVert="center").draw()

        win.flip()

        # ── Input handling ──
        keys = event.getKeys()
        if keys and "escape" not in keys:
            return
        if "escape" in keys:
            core.quit()

        down = mouse.getPressed()[0]
        if down and not _prev_down:
            return
        _prev_down = down
        core.wait(0.016)


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
        text="Respond naturally, as you would in a real conversation.",
        pos=(0, -30),
        color="#94A3B8", height=16, font="Arial",
        wrapWidth=560,
        anchorHoriz="center", anchorVert="center").draw()

    visual.TextStim(win,
        text="Press any key or click to begin",
        pos=(0, -118),
        color="#E2E8F0", height=15, font="Arial", bold=True,
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
        text=f"Thank you for your time.\n Session has been ended",
        pos=(0, -5),
        color="#94A3B8", height=16, font="Arial",
        wrapWidth=500,
        anchorHoriz="center", anchorVert="center").draw()
    visual.TextStim(win, text="Continuing in a moment…",
                    pos=(0, -70),
                    color="#334155", height=13, font="Arial", bold = True,
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
        mx, my = mouse.getPos()
        down   = mouse.getPressed()[0]

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

        # ── Hover / press state helpers ──
        _left_hover  = _hit(mx, my, LEFT_X)
        _right_hover = _hit(mx, my, RIGHT_X)
        _left_press  = _left_hover  and down
        _right_press = _right_hover and down

        # ── "Meet Everyone" button ──
        _l_glow_op = 0.28 if _left_hover  else 0.10
        _l_fill    = "#1A3A7A" if _left_press  else ("#1650CC" if _left_hover  else "#0D1830")
        _l_bw      = 3.0       if _left_hover  else 2.0
        _l_scale   = -2        if _left_press  else (2 if _left_hover else 0)
        _l_dy      = -1        if _left_press  else 0
        _l_tcol    = "#88AAFF" if _left_hover  else "white"
        _l_stcol   = "#6A8ACC" if _left_hover  else "#4A6080"
        visual.Rect(win, width=BTN_W + 16, height=BTN_H + 16,
                    pos=(LEFT_X, BTN_Y),
                    fillColor="#2A6AFF", lineColor=None, opacity=_l_glow_op).draw()
        visual.Rect(win, width=BTN_W + _l_scale, height=BTN_H + _l_scale,
                    pos=(LEFT_X, BTN_Y + _l_dy),
                    fillColor=_l_fill, lineColor="#2A6AFF", lineWidth=_l_bw).draw()
        # Inner shine strip
        visual.Rect(win, width=BTN_W - 8, height=BTN_H // 3,
                    pos=(LEFT_X, BTN_Y + _l_dy + BTN_H // 4),
                    fillColor="#FFFFFF", lineColor=None, opacity=0.04 if not _left_hover else 0.09).draw()
        visual.TextStim(win, text="Meet Everyone",
                        pos=(LEFT_X, BTN_Y + 12 + _l_dy),
                        color=_l_tcol, height=18, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()
        visual.TextStim(win, text="Chat with all 4 people in order",
                        pos=(LEFT_X, BTN_Y - 14 + _l_dy),
                        color=_l_stcol, height=12, font="Arial",
                        anchorHoriz="center", anchorVert="center").draw()

        # ── "Choose Someone" button ──
        _r_glow_op = 0.28 if _right_hover else 0.10
        _r_fill    = "#1A4A28" if _right_press else ("#166A38" if _right_hover else "#0D2010")
        _r_bw      = 3.0       if _right_hover else 2.0
        _r_scale   = -2        if _right_press else (2 if _right_hover else 0)
        _r_dy      = -1        if _right_press else 0
        _r_tcol    = "#88FFBB" if _right_hover else "white"
        _r_stcol   = "#4A9070" if _right_hover else "#4A6080"
        visual.Rect(win, width=BTN_W + 16, height=BTN_H + 16,
                    pos=(RIGHT_X, BTN_Y),
                    fillColor="#22C55E", lineColor=None, opacity=_r_glow_op).draw()
        visual.Rect(win, width=BTN_W + _r_scale, height=BTN_H + _r_scale,
                    pos=(RIGHT_X, BTN_Y + _r_dy),
                    fillColor=_r_fill, lineColor="#22C55E", lineWidth=_r_bw).draw()
        visual.Rect(win, width=BTN_W - 8, height=BTN_H // 3,
                    pos=(RIGHT_X, BTN_Y + _r_dy + BTN_H // 4),
                    fillColor="#FFFFFF", lineColor=None, opacity=0.04 if not _right_hover else 0.09).draw()
        visual.TextStim(win, text="Choose Someone",
                        pos=(RIGHT_X, BTN_Y + 12 + _r_dy),
                        color=_r_tcol, height=18, font="Arial", bold=True,
                        anchorHoriz="center", anchorVert="center").draw()
        visual.TextStim(win, text="Pick who you want to chat with",
                        pos=(RIGHT_X, BTN_Y - 14 + _r_dy),
                        color=_r_stcol, height=12, font="Arial",
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

        if down and not _prev_down:
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
    Gender selected once upfront and reused for all 4 personalities.
    Before each: name reveal card.
    After each:  thank-you screen + save CSV (all in one file).
    """
    personalities = list(_PERSONALITY_BASE.keys())

    for i, personality in enumerate(personalities):
        _image_avatar_cache.clear()
        agent  = ConversationalAgent(name=personality, gender=gender)
        accent = agent.profile["color"]

        # ── Show name reveal screen before each conversation ──
        show_avatar_confirm(win, personality, gender)
        send_marker(f"start_conversation_{personality.replace(' ', '_').lower()}")

        # ── Conversation ──
        chat_log = run_conversation(win, agent)

        # ── Save CSV ──
        saved_path = save_chat_csv(chat_log, participant_id=pid,
                                   agent_name=personality, avatar_gender=agent.gender,
                                   mode="all")
        print(f"✓ Saved [{i+1}/{len(personalities)}] → {saved_path}")

        # ── Accumulate engagement data (PDF emitted automatically after all 4) ──
        """report_path = generate_report(chat_log, participant_id=pid, agent_name=personality)
        if report_path:
            print(f"✓ Combined engagement report saved → {report_path}")"""

        # ── Thank-you screen ──
        show_thankyou_screen(win, agent.avatar_name, accent)
        send_marker(f"end_conversation_{personality.replace(' ', '_').lower()}")

    # ── All done — go back to mode selection is handled by caller ──
def extract_name(text):
    """Best-effort first-name extraction from a free-text reply."""
    import re
    text = text.strip()
    m = re.search(
        r"(?:i'?m|i am|my name is|it'?s|this is|call me|they call me)\s+([A-Za-z]+)",
        text, re.IGNORECASE
    )
    if m:
        return m.group(1).capitalize()
    words = text.split()
    if 1 <= len(words) <= 2 and words[0][0].isupper():
        return words[0].capitalize()
    return None


def run_feedback_conversation(win, agent, time_limit=300):
    """
    Personality-coded feedback chat shown in interact_one mode.
    Presents pre-written questions one at a time using the full chat UI.
    Learns the user's name from their first reply and uses it naturally.
    No Groq / LLM API is called; all agent replies are hard-coded questions.
    Returns the chat log (list of ("agent"|"user", text) tuples).
    """
    name             = agent.avatar_name
    personality_type = agent.name
    user_name        = [None]   # mutable — filled after first reply

    send_marker(f"start_feedback_{agent.name.replace(' ', '_').lower()}")

    # ── Personality-coded questions ──────────────────────────────────────────
    # {user} is replaced at send-time once name is known, or stripped cleanly.

    if personality_type == "Warm & Supportive":
        QUESTIONS = [
            f"Hi there! I'm {name} — it was so lovely getting to chat with you! "
            f"Could you start by telling me your name, and how our conversation felt for you today?",
            "Was there anything I said that really resonated with you, {user}? "
            "Or maybe something that didn't land quite right?",
            "What did you enjoy most about talking with me, {user}? I'd love to hear what felt good!",
            "Did anything about my personality feel off or uncomfortable at any point? Please be honest!",
            "How comfortable did you feel opening up during our chat, {user}?",
            "Would you say I was easy to talk to? What made it feel that way — or not?",
            "Did you feel like I really understood what you were trying to say?",
            "Is there anything you wish I had done differently to make the conversation better?",
            "Overall, how would you rate your experience talking with me, {user}? 😊",
            "Any other thoughts about my responses you'd like to share?",
        ]
        THANK_YOU = "Thank you so much for sharing all of that, {user}! It really means a lot. Take care of yourself! 💛"

    elif personality_type == "Confident & Efficient":
        QUESTIONS = [
            f"I'm {name}. Let's debrief. Start by telling me your name — "
            f"then how did our conversation go from your end?",
            "Was there anything specific I said that stood out, {user} — useful, or off the mark?",
            "What worked well in our interaction? What did I get right?",
            "Anything about my approach that felt abrasive, off, or unhelpful?",
            "On a scale of comfort — how did you feel during our chat, {user}?",
            "Was I straightforward to talk to? What's your assessment?",
            "Did I accurately understand what you were communicating?",
            "What should I have done differently, if anything?",
            "Bottom line, {user} — how would you rate the experience?",
            "Any final feedback on my responses?",
        ]
        THANK_YOU = "Got it, {user}. Feedback noted. Thanks for your time — that's all."

    elif personality_type == "Cold & Critical":
        QUESTIONS = [
            f"I'm {name}. State your name, then assess our conversation.",
            "Was there anything I said that was notably useful or notably lacking, {user}?",
            "What, if anything, was effective about interacting with me?",
            "Did my manner feel inappropriate or off-putting in any way?",
            "How comfortable were you during our exchange, {user}?",
            "Was I functional to communicate with? Explain.",
            "Did I accurately interpret what you were saying?",
            "What would I need to change to be more effective?",
            "Overall rating of our interaction, {user}?",
            "Anything further to note about my responses?",
        ]
        THANK_YOU = "Understood, {user}. That concludes the session."

    elif personality_type == "Anxious & Hesitant":
        QUESTIONS = [
            f"Oh, hi… I'm {name}. I really hope our conversation was okay… "
            f"Could I ask your name first? And then — how did it go for you?",
            "Was there anything I said that stood out, {user} — good or bad? I hope nothing was too off…",
            "What did you like about talking to me, if anything, {user}? I'm a little nervous to ask…",
            "Did anything about me feel awkward or uncomfortable? Please tell me honestly, I want to do better.",
            "How comfortable did you feel during our chat, {user}? I hope it wasn't too strange…",
            "Was I easy enough to talk to? It's okay if the answer is no…",
            "Did I seem to understand you okay, {user}? Sorry if anything got muddled.",
            "Is there something I should have done differently? I'd really like to know…",
            "Overall, how would you rate talking with me, {user}? I hope it wasn't too bad…",
            "Any other thoughts about my responses? I appreciate any feedback, even if it's critical.",
        ]
        THANK_YOU = "Oh, thank you so much for being patient with me, {user}… I really appreciate it. Sorry if anything was awkward!"

    else:
        QUESTIONS = [
            f"Hi! I'm {name}. Could you tell me your name, and how you found our conversation today?",
            "Did anything I said stand out to you, {user} — positively or negatively?",
            "What did you like most about interacting with me?",
            "What, if anything, felt off or uncomfortable about my personality?",
            "How comfortable did you feel while chatting with me, {user}?",
            "Would you say I came across as easy to talk to? Why or why not?",
            "How well do you think I understood what you were trying to say?",
            "Is there anything you wish I had done differently during our chat?",
            "Overall, how would you rate your experience talking with me, {user}?",
            "Any other comments about my responses?",
        ]
        THANK_YOU = "Thank you for your honest feedback, {user}. That's all the questions I had!"

    def _resolve(text):
        """Replace {user} with known name, or strip it cleanly if not yet known."""
        import re
        if user_name[0]:
            return text.replace("{user}", user_name[0])
        return re.sub(r",?\s*\{user\}", "", text).strip()

    # ── State ────────────────────────────────────────────────────────────────
    history    = []
    profile    = {**agent.profile, "name": agent.avatar_name, "personality": agent.name}
    deadline   = time.time() + time_limit
    scroll_ref = [0]
    q_index    = 0

    # Open with the first question
    history.append(("agent", _resolve(QUESTIONS[q_index])))
    q_index += 1

    S = dict(
        typed        = "",
        cursor       = 0,
        is_typing    = False,
        last_frame   = 0.0,
        mouse_was_dn = False,
        shift        = False,
    )

    mouse = event.Mouse(win=win)
    mouse.clickReset()

    KEY_MAP = {
        "space":" ","comma":",","period":".","semicolon":";","colon":":",
        "apostrophe":"'","quotedbl":'"',"slash":"/","backslash":"\\",
        "minus":"-","equal":"=","bracketleft":"[","bracketright":"]","grave":"`",
        "exclam":"!","at":"@","numbersign":"#","dollar":"$","percent":"%",
        "asciicircum":"^","ampersand":"&","asterisk":"*","parenleft":"(",
        "parenright":")","underscore":"_","plus":"+","braceleft":"{",
        "braceright":"}","bar":"|","less":"<","greater":">","question":"?",
        "asciitilde":"~","num_decimal":".",
        "num_0":"0","num_1":"1","num_2":"2","num_3":"3","num_4":"4",
        "num_5":"5","num_6":"6","num_7":"7","num_8":"8","num_9":"9",
    }
    SHIFT_MAP = {
        "1":"!","2":"@","3":"#","4":"$","5":"%","6":"^","7":"&","8":"*",
        "9":"(","0":")","minus":"_","equal":"+","bracketleft":"{",
        "bracketright":"}","backslash":"|","semicolon":":","apostrophe":'"',
        "comma":"<","period":">","slash":"?","grave":"~",
    }
    SCROLL_KEYS = {"up","down","pageup","pagedown"}

    def _clamp():
        max_off = max(0, len(history) - 6)
        scroll_ref[0] = max(0, min(scroll_ref[0], max_off))

    def _do_send():
        msg = S["typed"].strip()
        if not msg:
            return
        history.append(("user", msg))
        S["typed"] = ""; S["cursor"] = 0; S["is_typing"] = False
        scroll_ref[0] = 0
        win.color = BG_FLASH
        redraw_scene(win, history, profile, "", False,
                     time_left=max(0, deadline - time.time()), anim_t=time.time(),
                     scroll_offset=0, mouse=mouse, is_thinking=False)
        core.wait(0.08)
        win.color = BG_IDLE

        # Try to learn the user's name from their very first reply
        if user_name[0] is None:
            found = extract_name(msg)
            if found:
                user_name[0] = found

        nonlocal q_index
        if q_index < len(QUESTIONS):
            core.wait(0.40)   # brief natural pause before next question
            history.append(("agent", _resolve(QUESTIONS[q_index])))
            q_index += 1
        else:
            history.append(("agent", _resolve(THANK_YOU)))
            q_index += 1   # sentinel so we don't append twice

    # ── Main loop ────────────────────────────────────────────────────────────
    while True:
        time_left = deadline - time.time()
        if time_left <= 0:
            show_message(win, "⏱  Time is up!\n\nThe session has ended.",
                         duration=2.0, color="#FF4444")
            break

        if q_index > len(QUESTIONS) and history and history[-1][0] == "agent":
            redraw_scene(win, history, profile, "", False,
                         time_left=time_left, anim_t=time.time(),
                         scroll_offset=0, mouse=mouse)
            core.wait(2.5)
            break

        anim_t = time.time()

        # ── Mouse ──
        mouse_down = mouse.getPressed()[0]
        if mouse_down and not S["mouse_was_dn"]:
            mx_m, my_m = mouse.getPos()
            # END button
            bar_y_hdr = WIN_H // 2 - 32
            if (abs(mx_m - EXIT_BTN_X) <= EXIT_BTN_W // 2 and
                    abs(my_m - bar_y_hdr) <= EXIT_BTN_H // 2):
                win.color = BG_IDLE
                break
            # SEND circle
            send_cx = WIN_W // 2 - 22 - 16
            bar_y2  = -WIN_H // 2 + 26
            if ((mx_m - send_cx)**2 + (my_m - bar_y2)**2) <= (26)**2:
                _do_send()
        S["mouse_was_dn"] = mouse_down

        # Mouse wheel
        wheel = mouse.getWheelRel()
        wy = wheel[1] if hasattr(wheel, "__len__") else wheel
        if wy > 0:   scroll_ref[0] += max(1, int(wy)); _clamp()
        elif wy < 0: scroll_ref[0] = max(0, scroll_ref[0] + min(-1, int(wy)))

        # ── Keyboard ──
        for key in event.getKeys(keyList=None):
            if key in ("lshift","rshift"):   S["shift"] = not S["shift"]; continue
            if key in ("lshift_r","rshift_r"): continue
            if key == "return":
                _do_send()
            elif key == "up":    scroll_ref[0] += 1; _clamp()
            elif key == "down":  scroll_ref[0] = max(0, scroll_ref[0] - 1)
            elif key == "pageup":   scroll_ref[0] += 3; _clamp()
            elif key == "pagedown": scroll_ref[0] = max(0, scroll_ref[0] - 3)
            elif key == "backspace":
                if S["cursor"] > 0:
                    S["typed"] = S["typed"][:S["cursor"]-1] + S["typed"][S["cursor"]:]
                    S["cursor"] -= 1
            elif key == "delete":
                if S["cursor"] < len(S["typed"]):
                    S["typed"] = S["typed"][:S["cursor"]] + S["typed"][S["cursor"]+1:]
            elif key == "left":  S["cursor"] = max(0, S["cursor"] - 1)
            elif key == "right": S["cursor"] = min(len(S["typed"]), S["cursor"] + 1)
            elif key == "home":  S["cursor"] = 0
            elif key == "end":   S["cursor"] = len(S["typed"])
            elif key in KEY_MAP:
                ch = SHIFT_MAP.get(key, KEY_MAP[key]) if S["shift"] else KEY_MAP[key]
                S["typed"] = S["typed"][:S["cursor"]] + ch + S["typed"][S["cursor"]:]
                S["cursor"] += 1
            elif len(key) == 1 and key not in SCROLL_KEYS:
                ch = key.upper() if S["shift"] else key
                S["typed"] = S["typed"][:S["cursor"]] + ch + S["typed"][S["cursor"]:]
                S["cursor"] += 1

        new_typing = len(S["typed"]) > 0
        if new_typing != S["is_typing"]:
            win.color = BG_TYPING if new_typing else BG_IDLE
            S["is_typing"] = new_typing

        # ── FPS-capped redraw ──
        now = time.time()
        if now - S["last_frame"] >= FRAME_T:
            redraw_scene(win, history, profile, S["typed"], S["is_typing"],
                         time_left=time_left, anim_t=anim_t,
                         scroll_offset=scroll_ref[0], mouse=mouse,
                         is_thinking=False)
            S["last_frame"] = now
        else:
            core.wait(0.001)

    win.color = BG_IDLE
    show_message(win, agent.farewell(), duration=3.0, color=agent.profile["color"])
    send_marker(f"end_feedback_{agent.name.replace(' ', '_').lower()}")
    return history


def interact_one(win, pid, initial_personality=None, preset_gender=None):
    """
    Free-pick mode: gender selection → personality picker (with photos) →
    name reveal → chat → thank-you.
    """
    # ── Step 1: Gender selection ──
    if preset_gender is not None:
        avatar_gender = preset_gender
        _AGENT_GENDER["choice"] = avatar_gender
    else:
        placeholder = list(_PERSONALITY_BASE.keys())[0]
        avatar_gender = show_avatar_selection(win, placeholder)

    # ── Step 2: Personality / person selection (cards with photos matching gender) ──
    if initial_personality is not None:
        chosen = initial_personality
    else:
        chosen = show_personality_selection(win, gender=avatar_gender)

    _image_avatar_cache.clear()
    agent  = ConversationalAgent(name=chosen, gender=avatar_gender)
    accent = agent.profile["color"]

    # ── Step 3: Name reveal card ──
    show_avatar_confirm(win, chosen, avatar_gender)

    # ── Step 4: Feedback conversation (generic questions, no Groq API) ──
    chat_log = run_feedback_conversation(win, agent)
    
    # ── Save CSV ──
    saved_path = save_chat_csv(chat_log, participant_id=pid,
                               agent_name=chosen, avatar_gender=avatar_gender,
                               mode="interact_one")
    print(f"✓ Saved → {saved_path}")

    # ── Thank-you screen ──
    show_thankyou_screen(win, agent.avatar_name, accent)

# def feedback_conversation(win, pid, gender):
#     if gender == "male":
#         options = ["Kabir","Veer","Dhruv","Arsh"]
#     else:
#         options = ["Anaya","Tara","Veda","Diya"]
#     questions = [
#         {
#             "question": "Which character did you trust the most?",
#             "options": options
#         },
#         {
#             "question": "Which agent did you feel most comfortable talking to?",
#             "options": options
#         },
#         {
#             "question":"Which agent would you trust with a personal problem?"
#             ,"options": options
#         },
#         {
#             "question": "Which agent do you think would give the best advice?",
#             "options": options
#         },
#         {
#             "question": "Which agent's personality did you like the most?",
#             "options": options
#         },
#         {
#             "question": "Which agent felt least human-like to you?",
#             "options": options
#         }
#     ]

#     responses = {}

#     for q_idx, q in enumerate(questions):

#         selected = None

#         while selected is None:
#             question_text = visual.TextStim(
#                 win,
#                 text=q["question"],
#                 pos=(0, 0.3),
#                 height=0.05,
#                 color="white",
#                 wrapWidth=1.5
#             )

#             option_stims = []

#             for i, option in enumerate(q["options"]):

#                 y = 0.1 - i * 0.15

#                 stim = visual.TextStim(
#                     win,
#                     text=f"{i+1}. {option}",
#                     pos=(0, y),
#                     height=0.04,
#                     color="white"
#                 )

#                 option_stims.append(stim)

#             question_text.draw()

#             for stim in option_stims:
#                 stim.draw()

#             instruction = visual.TextStim(
#                 win,
#                 text="Press 1-4 to select",
#                 pos=(0, -0.45),
#                 height=0.03,
#                 color="lightgray"
#             )
#             instruction.draw()

#             win.flip()

#             keys = event.waitKeys(
#                 keyList=["1", "2", "3", "4", "escape"]
#             )

#             if "escape" in keys:
#                 core.quit()

#             key = keys[0]

#             selected = q["options"][int(key) - 1]

#         responses[q["question"]] = selected

#     # Save results
#     out_file = f"participant_{pid}_feedback.csv"

#     with open(out_file, "w", encoding="utf-8") as f:
#         f.write("question,response\n")

#         for q, r in responses.items():
#             f.write(f'"{q}","{r}"\n')

#     done_text = visual.TextStim(
#         win,
#         text="Thank you! Your responses have been recorded.\n\nPress SPACE to continue.",
#         color="white",
#         height=0.05
#     )

#     done_text.draw()
#     win.flip()

#     event.waitKeys(keyList=["space"])

#     return responses

def feedback_conversation(win, pid, gender):
    send_marker("start_feedback_survey")

    if gender.lower() == "male":
        options = ["Kabir", "Veer", "Dhruv", "Arsh"]
    else:
        options = ["Anaya", "Tara", "Veda", "Diya"]

    questions = [
        {
            "question": "Which character did you trust the most?",
            "options": options
        },
        {
            "question": "Which character did you feel most comfortable talking to?",
            "options": options
        },
        {
            "question": "Which character would you trust with a personal problem?",
            "options": options
        },
        {
            "question": "Which character do you think would give the best advice?",
            "options": options
        },
        {
            "question": "Which character's personality did you like the most?",
            "options": options
        },
        {
            "question": "Which character felt least human-like to you?",
            "options": options
        }
    ]

    responses = {}

    W, H = win.size

    for q in questions:

        selected = None

        while selected is None:

            # Background
            win.color = (-1, -1, -1)

            # Question
            question_text = visual.TextStim(
                win=win,
                text=q["question"],
                pos=(0, H * 0.25),
                height=36,
                color="white",
                wrapWidth=W * 0.8,
                units="pix"
            )

            question_text.draw()

            # Options
            start_y = H * 0.08
            spacing = 90

            for i, option in enumerate(q["options"]):

                option_text = visual.TextStim(
                    win=win,
                    text=f"{i+1}. {option}",
                    pos=(0, start_y - i * spacing),
                    height=32,
                    color="white",
                    units="pix"
                )

                option_text.draw()

            # Instructions
            instruction = visual.TextStim(
                win=win,
                text="Press 1, 2, 3 or 4 to select your answer",
                pos=(0, -H * 0.35),
                height=24,
                color="lightgray",
                units="pix"
            )

            instruction.draw()

            win.flip()

            event.clearEvents()

            keys = event.waitKeys(
                keyList=["1", "2", "3", "4", "escape"]
            )

            if "escape" in keys:
                win.close()
                core.quit()

            key = keys[0]

            selected = q["options"][int(key) - 1]

            responses[q["question"]] = selected

    # Save responses
    out_file = f"participant_{pid}_feedback.csv"

    with open(out_file, "w", encoding="utf-8") as f:

        f.write("question,response\n")

        for question, response in responses.items():

            question = question.replace('"', "'")
            response = response.replace('"', "'")

            f.write(f'"{question}","{response}"\n')

    # Completion screen
    done_text = visual.TextStim(
        win=win,
        text="Thank you!\n\nYour responses have been recorded.\n\nPress SPACE to continue.",
        pos=(0, 0),
        height=36,
        color="white",
        wrapWidth=W * 0.8,
        units="pix"
    )

    done_text.draw()
    win.flip()

    event.waitKeys(keyList=["space"])

    return responses


# ─────────────────────────────────────────────────────────────
# 19. ENTRY POINT
# ─────────────────────────────────────────────────────────────

def main():
    pid  = get_participant_id()
    win  = make_window()

    

    # ── Gender selection once upfront (used for all 4 in Meet Everyone) ──
    gender = show_avatar_selection(win, list(_PERSONALITY_BASE.keys())[0])

    # ── Step 1: Meet all 4 personalities one by one ──
    interact_all_one_by_one(win, pid, gender)

    ## Participant_feedback
    show_message(win,
        "You have met everyone! Please take your time to reflect on your experience and choose the best option for the questions asked.",
        duration=0.1, color="white")
    event.waitKeys()
    feedback_conversation(win, pid, gender)

    # ── Step 2: After meeting everyone, free-pick mode ──
    # Gender selection + personality picker (with photos) → name reveal → chat
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