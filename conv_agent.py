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

TARGET_FPS   = 30          # cap render loop — reduces CPU load
FRAME_T      = 1.0 / TARGET_FPS

# ─────────────────────────────────────────────────────────────
# 1. PERSONALITY DEFINITIONS
# ─────────────────────────────────────────────────────────────

# ── Base personality templates (gender-neutral core traits) ──
_PERSONALITY_BASE = {
    "Warm & Supportive": {
        "color":    "#4CAF50",
        "bg_color": "#1B3A2A",
        "avatar":   "😊",
    },
    "Confident & Efficient": {
        "color":    "#2196F3",
        "bg_color": "#0D1F3A",
        "avatar":   "💼",
    },
    "Cold & Critical": {
        "color":    "#FF5252",
        "bg_color": "#2A0A0A",
        "avatar":   "🧊",
    },
    "Anxious & Hesitant": {
        "color":    "#FF9800",
        "bg_color": "#2A1A00",
        "avatar":   "😟",
    },
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

def get_experiment_info():
    dlg_info = {
        "Participant ID": "",
        "Personality Agent": list(PERSONALITIES.keys()),
    }
    dlg = gui.DlgFromDict(dictionary=dlg_info, title="Select Chatbot Agent",
                          order=["Participant ID", "Personality Agent"])
    if dlg.OK:
        return dlg_info
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
        self.turn        = 0

    def greet(self):
        base = self.profile["greeting"]
        return f"Hello, I'm {self.avatar_name}. {base}"
    def farewell(self): return self.profile["farewell"]

    def respond(self, user_input=""):
        # ── Placeholder fallback (remove when LLM is connected) ──
        self.turn += 1
        r = self.profile["responses"]
        return r[self.turn % len(r)]

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
# 4b. ANIMATION HELPERS
# ─────────────────────────────────────────────────────────────

def pulse(t, speed=1.0, lo=0.0, hi=1.0):
    """Smooth sinusoidal pulse between lo and hi."""
    return lo + (hi - lo) * (0.5 + 0.5 * math.sin(t * speed * math.pi * 2))

def blink(t, period=4.0, shut_duration=0.12):
    """Returns True (eyes open) most of the time, False briefly for blink."""
    phase = math.fmod(t, period)
    return phase > shut_duration

def scan_line_y(t, win_h):
    """Top→bottom scan-line position, looping every 3 s."""
    return win_h // 2 - (math.fmod(t, 3.0) / 3.0) * win_h

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
# 6. AVATARS — realistic human faces built from primitives
# ─────────────────────────────────────────────────────────────

def _draw_human_face(win, cx, cy, R,
                     skin, skin_shadow, skin_highlight,
                     hair, hair_hi,
                     shirt, accent=None):
    """
    Core human face renderer shared by both avatars.
    All coords relative to (cx, cy), scaled by R.
    """

    # ── Shoulders & shirt ──
    visual.Circle(win, radius=R * 0.78, pos=(cx, cy - R * 0.78),
                  fillColor=shirt, lineColor=None).draw()
    # collar highlight
    visual.Circle(win, radius=R * 0.42, pos=(cx, cy - R * 0.62),
                  fillColor="#FFFFFF", lineColor=None, opacity=0.08).draw()

    # ── Neck ──
    visual.Rect(win, width=R * 0.30, height=R * 0.36,
                pos=(cx, cy - R * 0.30),
                fillColor=skin_shadow, lineColor=None).draw()
    # neck highlight
    visual.Rect(win, width=R * 0.14, height=R * 0.30,
                pos=(cx - R * 0.04, cy - R * 0.28),
                fillColor=skin_highlight, lineColor=None, opacity=0.35).draw()

    # ── Head shape — oval, slightly wider than tall ──
    # Drop shadow
    visual.Circle(win, radius=R * 0.535, pos=(cx + R*0.025, cy + R*0.06 - R*0.025),
                  fillColor="#000000", lineColor=None, opacity=0.22).draw()
    # Base skin
    visual.Circle(win, radius=R * 0.525, pos=(cx, cy + R * 0.06),
                  fillColor=skin, lineColor=None).draw()
    # Right-side shadow (light from left)
    visual.Circle(win, radius=R * 0.44, pos=(cx + R * 0.14, cy + R * 0.06),
                  fillColor=skin_shadow, lineColor=None, opacity=0.38).draw()
    # Left highlight
    visual.Circle(win, radius=R * 0.32, pos=(cx - R * 0.18, cy + R * 0.18),
                  fillColor=skin_highlight, lineColor=None, opacity=0.30).draw()
    # Specular point
    visual.Circle(win, radius=R * 0.10, pos=(cx - R * 0.24, cy + R * 0.34),
                  fillColor="white", lineColor=None, opacity=0.14).draw()

    # ── Hair ──
    # Back layer (wider)
    visual.Circle(win, radius=R * 0.545, pos=(cx, cy + R * 0.10),
                  fillColor=hair, lineColor=None).draw()
    # Hair body (covers top half of face circle)
    visual.Circle(win, radius=R * 0.525, pos=(cx, cy + R * 0.06),
                  fillColor=hair, lineColor=None).draw()
    # Clip hair to top half only by overdrawing face below hairline
    visual.Rect(win, width=R * 1.10, height=R * 0.60,
                pos=(cx, cy - R * 0.16),
                fillColor=skin, lineColor=None).draw()
    # Right shadow back on face after clip
    visual.Circle(win, radius=R * 0.44, pos=(cx + R * 0.14, cy + R * 0.06),
                  fillColor=skin_shadow, lineColor=None, opacity=0.28).draw()
    # Hair highlight
    visual.Circle(win, radius=R * 0.20, pos=(cx - R * 0.14, cy + R * 0.46),
                  fillColor=hair_hi, lineColor=None, opacity=0.50).draw()

    # ── Ears ──
    for ex in (-R * 0.51, R * 0.51):
        visual.Circle(win, radius=R * 0.095, pos=(cx + ex, cy + R * 0.06),
                      fillColor=skin, lineColor=None).draw()
        visual.Circle(win, radius=R * 0.055, pos=(cx + ex, cy + R * 0.06),
                      fillColor=skin_shadow, lineColor=None, opacity=0.55).draw()

    # ── Eyebrows ──
    for i, (ex, angle) in enumerate([(-R*0.20, 5), (R*0.20, -5)]):
        visual.Rect(win, width=R * 0.20, height=R * 0.045,
                    pos=(cx + ex, cy + R * 0.22),
                    fillColor=hair, lineColor=None, ori=angle).draw()

    # ── Eyes ──
    for ex in (-R * 0.20, R * 0.20):
        # Eye socket shadow
        visual.Circle(win, radius=R * 0.115, pos=(cx + ex, cy + R * 0.11),
                      fillColor=skin_shadow, lineColor=None, opacity=0.45).draw()
        # Sclera (white)
        visual.Circle(win, radius=R * 0.095, pos=(cx + ex, cy + R * 0.12),
                      fillColor="#F5F0EB", lineColor=None).draw()
        # Iris
        visual.Circle(win, radius=R * 0.065, pos=(cx + ex, cy + R * 0.11),
                      fillColor="#4A3520" if hair == "#2C1A0E" else "#3A5A8A",
                      lineColor=None).draw()
        # Pupil
        visual.Circle(win, radius=R * 0.036, pos=(cx + ex, cy + R * 0.11),
                      fillColor="#0A0806", lineColor=None).draw()
        # Catch light (main)
        visual.Circle(win, radius=R * 0.024, pos=(cx + ex - R*0.028, cy + R * 0.145),
                      fillColor="white", lineColor=None, opacity=0.95).draw()
        # Catch light (secondary)
        visual.Circle(win, radius=R * 0.012, pos=(cx + ex + R*0.040, cy + R * 0.098),
                      fillColor="white", lineColor=None, opacity=0.55).draw()
        # Lower eyelid line
        visual.Rect(win, width=R * 0.175, height=R * 0.018,
                    pos=(cx + ex, cy + R * 0.065),
                    fillColor=skin_shadow, lineColor=None, opacity=0.30).draw()

    # ── Nose ──
    # Bridge
    visual.Rect(win, width=R * 0.055, height=R * 0.14,
                pos=(cx, cy + R * 0.01),
                fillColor=skin_shadow, lineColor=None, opacity=0.28).draw()
    # Tip
    visual.Circle(win, radius=R * 0.068, pos=(cx, cy - R * 0.055),
                  fillColor=skin_shadow, lineColor=None, opacity=0.32).draw()
    # Nostrils
    for nx in (-R * 0.055, R * 0.055):
        visual.Circle(win, radius=R * 0.030, pos=(cx + nx, cy - R * 0.068),
                      fillColor=skin_shadow, lineColor=None, opacity=0.50).draw()

    # ── Lips ──
    # Upper lip
    visual.Rect(win, width=R * 0.210, height=R * 0.052,
                pos=(cx, cy - R * 0.145),
                fillColor="#C07860", lineColor=None).draw()
    # Lower lip (fuller)
    visual.Rect(win, width=R * 0.230, height=R * 0.065,
                pos=(cx, cy - R * 0.200),
                fillColor="#D08870", lineColor=None).draw()
    # Lip highlight
    visual.Circle(win, radius=R * 0.055, pos=(cx, cy - R * 0.192),
                  fillColor="white", lineColor=None, opacity=0.14).draw()
    # Mouth line
    visual.Rect(win, width=R * 0.185, height=R * 0.018,
                pos=(cx, cy - R * 0.168),
                fillColor="#7A3820", lineColor=None, opacity=0.55).draw()

    # ── Chin shadow ──
    visual.Circle(win, radius=R * 0.20, pos=(cx, cy - R * 0.30),
                  fillColor=skin_shadow, lineColor=None, opacity=0.22).draw()

    # ── Accent ring (personality colour halo — agent only) ──
    if accent:
        visual.Circle(win, radius=R * 1.04, pos=(cx, cy),
                      fillColor=None, lineColor=accent, lineWidth=2.5,
                      opacity=0.70).draw()
        visual.Circle(win, radius=R * 1.12, pos=(cx, cy),
                      fillColor=accent, lineColor=None, opacity=0.10).draw()


# ─────────────────────────────────────────────────────────────
# AVATAR CACHE — build stim objects once, draw every frame
# ─────────────────────────────────────────────────────────────
# Instead of creating new visual objects each frame, we build
# a list of stim objects once per unique (cx,cy,accent) key
# and just call .draw() on them every frame.

_avatar_cache = {}   # key -> list of stim objects


def _make_robot_stims(win, cx, cy, accent, R, fR, fcy):
    """
    Sara — female chat agent avatar.
    Changes from original:
      • Richer chestnut hair (#8B3A1A → longer side blobs, warm highlight)
      • Lighter, cooler skin tone (#F2C4A0) with peach shadow
      • Green eyes (#3A7A4A iris) with lash-line rect
      • Fuller rose lips (#E87A8A upper, #F09090 lower)
      • Teal/jade shirt (#2A8A7A) instead of blue
      • Small pearl-like earring dots below each ear
      • Thinner, more arched eyebrows (fR*0.038 height, angle=10)
    """
    s = []
    hair     = "#8B3A1A"   # rich chestnut
    hhi      = "#C06030"   # warm auburn highlight
    skin     = "#F2C4A0"   # soft peach
    skin_shd = "#D49870"   # warm shadow
    skin_hi  = "#FDDEC0"   # highlight

    def C(pos, radius, fillColor, lineColor=None, lineWidth=1, opacity=1.0):
        radius = max(float(radius), 1.0)  # guard: PsychoPy crashes on radius<=0
        return visual.Circle(win, radius=radius, pos=pos,
                             fillColor=fillColor, lineColor=lineColor,
                             lineWidth=lineWidth, opacity=opacity)
    def R_(pos, width, height, fillColor, lineColor=None, lineWidth=1, opacity=1.0, ori=0):
        width = max(float(width), 1.0); height = max(float(height), 1.0)  # guard
        return visual.Rect(win, width=width, height=height, pos=pos,
                           fillColor=fillColor, lineColor=lineColor,
                           lineWidth=lineWidth, opacity=opacity, ori=ori)

    # drop shadow
    for sh_r, sh_op in [(R*1.15, 0.08), (R*1.08, 0.13), (R*1.03, 0.17)]:
        s.append(C((cx+3, cy-3), sh_r, "#000000", opacity=sh_op))
    # bg disc
    s.append(C((cx, cy), R, "#1C2840"))
    # accent halo
    s.append(C((cx, cy), R*1.045, None, lineColor=accent, lineWidth=2.5, opacity=0.65))

    # ── Teal shirt (replaces blue) ──
    s.append(C((cx, cy-R*0.72), R*0.58, "#2A8A7A"))
    s.append(C((cx-R*0.16, cy-R*0.58), R*0.26, "#60CAB8", opacity=0.25))
    for sign in (-1, 1):
        s.append(R_((cx+sign*R*0.04, cy-R*0.40), R*0.10, R*0.16, "#1A6A5A", ori=sign*-14))

    # neck (softer skin tone)
    s.append(R_((cx, cy-R*0.26), R*0.17, R*0.20, skin_shd))

    # ── Hair — longer side blobs for flowing look ──
    s.append(C((cx, fcy+fR*0.10), fR*1.00, hair))          # large back dome
    s.append(C((cx, fcy+fR*0.04), fR*0.99, hair))
    s.append(C((cx-fR*0.74, fcy-fR*0.04), fR*0.58, hair))  # left side — longer
    s.append(C((cx-fR*0.76, fcy-fR*0.46), fR*0.44, hair))  # left lower
    s.append(C((cx-fR*0.72, fcy-fR*0.80), fR*0.30, hair))  # left tip
    s.append(C((cx+fR*0.68, fcy-fR*0.08), fR*0.46, hair))  # right side
    s.append(C((cx+fR*0.70, fcy-fR*0.46), fR*0.34, hair))  # right lower

    # ── Face (lighter skin) ──
    s.append(C((cx+fR*0.04, fcy-fR*0.04), fR*1.03, "#000000", opacity=0.12))
    s.append(C((cx, fcy), fR, skin))
    s.append(C((cx+fR*0.26, fcy), fR*0.80, skin_shd, opacity=0.22))
    s.append(C((cx-fR*0.35, fcy+fR*0.22), fR*0.52, skin_hi, opacity=0.28))

    # hair clip rect (restore face below hairline)
    s.append(R_((cx, fcy-fR*0.48), fR*2.10, fR*0.85, skin))
    s.append(C((cx+fR*0.26, fcy), fR*0.80, skin_shd, opacity=0.14))
    s.append(C((cx-fR*0.24, fcy+fR*0.62), fR*0.24, hhi, opacity=0.50))  # hair highlight

    # ── Ears ──
    s.append(C((cx-fR*0.86, fcy+fR*0.04), fR*0.12, skin_shd))
    s.append(C((cx+fR*0.86, fcy+fR*0.04), fR*0.12, skin_shd))
    # Pearl earrings — small ivory dots just below each ear
    s.append(C((cx-fR*0.86, fcy-fR*0.11), fR*0.055, "#F0EAE0"))
    s.append(C((cx+fR*0.86, fcy-fR*0.11), fR*0.055, "#F0EAE0"))
    # earring highlight
    s.append(C((cx-fR*0.875, fcy-fR*0.10), fR*0.020, "white", opacity=0.80))
    s.append(C((cx+fR*0.875, fcy-fR*0.10), fR*0.020, "white", opacity=0.80))

    # ── Headset band ──
    band = "#252525"
    for angle_deg in range(-50, 51, 10):
        ang = math.radians(angle_deg)
        bx  = cx + math.sin(ang)*fR*0.90
        by  = fcy + fR*0.65 + math.cos(ang)*fR*0.16
        s.append(C((bx, by), fR*0.095, band))
    for angle_deg in (-25, 0, 25):
        ang = math.radians(angle_deg)
        bx  = cx + math.sin(ang)*fR*0.90
        by  = fcy + fR*0.65 + math.cos(ang)*fR*0.16
        s.append(C((bx-fR*0.02, by+fR*0.03), fR*0.040, "#606060", opacity=0.55))

    # ear cup
    ec_cx = cx + fR*0.80
    ec_cy = fcy + fR*0.04
    s.append(C((ec_cx, ec_cy), fR*0.26, "#1A8AB5"))
    s.append(C((ec_cx, ec_cy), fR*0.26, None, lineColor="#0A5A80", lineWidth=2))
    s.append(C((ec_cx-fR*0.06, ec_cy+fR*0.06), fR*0.13, "#5ABFE8", opacity=0.45))
    s.append(C((ec_cx, ec_cy), fR*0.08, "#094060"))

    # mic
    s.append(R_((cx+fR*0.46, fcy-fR*0.20), fR*0.09, fR*0.48, "#252525", ori=30))
    s.append(R_((cx+fR*0.16, fcy-fR*0.40), fR*0.09, fR*0.34, "#252525", ori=10))
    s.append(C((cx-fR*0.04, fcy-fR*0.52), fR*0.09, "#2A2A2A"))
    s.append(C((cx-fR*0.07, fcy-fR*0.57), fR*0.052, "#00CFEE", opacity=0.85))

    # ── Eyebrows — thinner, more arched (feminine) ──
    for sign, angle in ((-1, 10), (1, -10)):
        s.append(R_((cx+sign*fR*0.30, fcy+fR*0.34), fR*0.26, fR*0.038, "#5A2808", ori=angle))

    # ── Eyes — green iris, lash line ──
    eye_y = fcy + fR*0.17
    for sign in (-1, 1):
        ex = cx + sign*fR*0.30
        s.append(C((ex, eye_y), fR*0.16, skin_shd, opacity=0.28))
        s.append(C((ex, eye_y+fR*0.012), fR*0.135, "#F5F0EB"))
        s.append(C((ex, eye_y), fR*0.092, "#3A7A4A"))   # green iris
        s.append(C((ex, eye_y), fR*0.050, "#080604"))   # pupil
        s.append(C((ex-fR*0.036, eye_y+fR*0.045), fR*0.032, "white", opacity=0.95))
        # lash line (thin dark rect along upper lid)
        s.append(R_((ex, eye_y+fR*0.115), fR*0.185, fR*0.022, "#2A1008", opacity=0.80))

    # ── Nose (delicate) ──
    s.append(C((cx, fcy-fR*0.07), fR*0.072, skin_shd, opacity=0.18))
    for sign in (-1, 1):
        s.append(C((cx+sign*fR*0.065, fcy-fR*0.10), fR*0.034, skin_shd, opacity=0.32))

    # ── Lips — rose-pink, fuller upper ──
    s.append(R_((cx, fcy-fR*0.24), fR*0.32, fR*0.074, "#E87A8A"))   # upper lip (rose)
    s.append(R_((cx, fcy-fR*0.32), fR*0.34, fR*0.088, "#F09090"))   # lower lip (softer pink)
    s.append(C((cx, fcy-fR*0.305), fR*0.065, "white", opacity=0.16)) # lip highlight
    s.append(R_((cx, fcy-fR*0.275), fR*0.27, fR*0.020, "#8A2840", opacity=0.42)) # mouth line

    # chin
    s.append(C((cx, fcy-fR*0.48), fR*0.26, skin_shd, opacity=0.14))

    # hard mask ring
    s.append(C((cx, cy), R*1.30, None, lineColor=BG_IDLE, lineWidth=int(R*0.62)))

    return s


def _make_robot_male_stims(win, cx, cy, accent, R, fR, fcy):
    """Male agent avatar: short dark hair, squarer jaw hint, same headset."""
    s = []
    hair = "#1A1208"
    hhi  = "#3A2810"

    def C(pos, radius, fillColor, lineColor=None, lineWidth=1, opacity=1.0):
        radius = max(float(radius), 1.0)  # guard: PsychoPy crashes on radius<=0
        return visual.Circle(win, radius=radius, pos=pos,
                             fillColor=fillColor, lineColor=lineColor,
                             lineWidth=lineWidth, opacity=opacity)
    def R_(pos, width, height, fillColor, lineColor=None, lineWidth=1, opacity=1.0, ori=0):
        width = max(float(width), 1.0); height = max(float(height), 1.0)  # guard
        return visual.Rect(win, width=width, height=height, pos=pos,
                           fillColor=fillColor, lineColor=lineColor,
                           lineWidth=lineWidth, opacity=opacity, ori=ori)

    # drop shadow
    for sh_r, sh_op in [(R*1.15, 0.08), (R*1.08, 0.13), (R*1.03, 0.17)]:
        s.append(C((cx+3, cy-3), sh_r, "#000000", opacity=sh_op))
    # bg disc
    s.append(C((cx, cy), R, "#1C2840"))
    # accent halo
    s.append(C((cx, cy), R*1.045, None, lineColor=accent, lineWidth=2.5, opacity=0.65))
    # shirt (navy — slightly broader shoulders)
    s.append(C((cx, cy-R*0.72), R*0.62, "#1A2A5A"))
    s.append(C((cx-R*0.16, cy-R*0.58), R*0.26, "#3A5AE8", opacity=0.20))
    for sign in (-1, 1):
        s.append(R_((cx+sign*R*0.04, cy-R*0.40), R*0.11, R*0.17, "#112060", ori=sign*-14))
    # neck (slightly wider)
    s.append(R_((cx, cy-R*0.26), R*0.20, R*0.20, "#E8A878"))
    # short hair — dome cap only, no side blobs
    s.append(C((cx, fcy+fR*0.46), fR*0.54, hair))          # hair dome cap
    s.append(R_((cx, fcy+fR*0.12), fR*1.08, fR*0.58, "#E8A878"))  # clip to face
    s.append(C((cx-fR*0.12, fcy+fR*0.42), fR*0.16, hhi, opacity=0.40))
    # face
    s.append(C((cx+fR*0.04, fcy-fR*0.04), fR*1.03, "#000000", opacity=0.15))
    s.append(C((cx, fcy), fR, "#E8A878"))
    s.append(C((cx+fR*0.26, fcy), fR*0.80, "#C07848", opacity=0.26))
    s.append(C((cx-fR*0.35, fcy+fR*0.22), fR*0.52, "#F8C898", opacity=0.28))
    # hair clip rect (hide hair above face line)
    s.append(R_((cx, fcy-fR*0.48), fR*2.10, fR*0.85, "#E8A878"))
    s.append(C((cx+fR*0.26, fcy), fR*0.80, "#C07848", opacity=0.16))
    # ears
    s.append(C((cx-fR*0.86, fcy+fR*0.04), fR*0.12, "#E0987A"))
    s.append(C((cx+fR*0.86, fcy+fR*0.04), fR*0.12, "#D08868"))
    # headset band (same as female)
    band = "#252525"
    for angle_deg in range(-50, 51, 10):
        ang = math.radians(angle_deg)
        bx  = cx + math.sin(ang)*fR*0.90
        by  = fcy + fR*0.65 + math.cos(ang)*fR*0.16
        s.append(C((bx, by), fR*0.095, band))
    for angle_deg in (-25, 0, 25):
        ang = math.radians(angle_deg)
        bx  = cx + math.sin(ang)*fR*0.90
        by  = fcy + fR*0.65 + math.cos(ang)*fR*0.16
        s.append(C((bx-fR*0.02, by+fR*0.03), fR*0.040, "#606060", opacity=0.55))
    # ear cup
    ec_cx = cx + fR*0.80
    ec_cy = fcy + fR*0.04
    s.append(C((ec_cx, ec_cy), fR*0.26, "#1A8AB5"))
    s.append(C((ec_cx, ec_cy), fR*0.26, None, lineColor="#0A5A80", lineWidth=2))
    s.append(C((ec_cx-fR*0.06, ec_cy+fR*0.06), fR*0.13, "#5ABFE8", opacity=0.45))
    s.append(C((ec_cx, ec_cy), fR*0.08, "#094060"))
    # mic
    s.append(R_((cx+fR*0.46, fcy-fR*0.20), fR*0.09, fR*0.48, "#252525", ori=30))
    s.append(R_((cx+fR*0.16, fcy-fR*0.40), fR*0.09, fR*0.34, "#252525", ori=10))
    s.append(C((cx-fR*0.04, fcy-fR*0.52), fR*0.09, "#2A2A2A"))
    s.append(C((cx-fR*0.07, fcy-fR*0.57), fR*0.052, "#00CFEE", opacity=0.85))
    # eyebrows (heavier/flatter — male)
    for sign, angle in ((-1, 3), (1, -3)):
        s.append(R_((cx+sign*fR*0.30, fcy+fR*0.33), fR*0.30, fR*0.062, "#2A1808", ori=angle))
    # eyes (brown iris)
    eye_y = fcy + fR*0.17
    for sign in (-1, 1):
        ex = cx + sign*fR*0.30
        s.append(C((ex, eye_y), fR*0.16, "#C07848", opacity=0.32))
        s.append(C((ex, eye_y+fR*0.012), fR*0.135, "#F5F0EB"))
        s.append(C((ex, eye_y), fR*0.092, "#5A3820"))
        s.append(C((ex, eye_y), fR*0.050, "#080604"))
        s.append(C((ex-fR*0.036, eye_y+fR*0.045), fR*0.032, "white", opacity=0.95))
    # nose (slightly wider)
    s.append(C((cx, fcy-fR*0.07), fR*0.085, "#C07848", opacity=0.20))
    for sign in (-1, 1):
        s.append(C((cx+sign*fR*0.08, fcy-fR*0.11), fR*0.040, "#B06838", opacity=0.36))
    # lips (thinner — male)
    s.append(R_((cx, fcy-fR*0.24), fR*0.28, fR*0.055, "#B06850"))
    s.append(R_((cx, fcy-fR*0.30), fR*0.29, fR*0.062, "#C07860"))
    s.append(R_((cx, fcy-fR*0.27), fR*0.24, fR*0.018, "#7A3820", opacity=0.45))
    # chin (squarer hint)
    s.append(R_((cx, fcy-fR*0.50), fR*0.52, fR*0.18, "#C07848", opacity=0.14))
    # subtle stubble
    import random
    rng = random.Random(99)
    for _ in range(14):
        sx = cx + rng.uniform(-fR*0.26, fR*0.26)
        sy = fcy + rng.uniform(-fR*0.46, -fR*0.26)
        s.append(C((sx, sy), fR*0.018, "#9A6848", opacity=0.22))
    # hard mask ring
    s.append(C((cx, cy), R*1.30, None, lineColor=BG_IDLE, lineWidth=int(R*0.62)))

    return s


def _make_user_stims(win, cx, cy, R):
    """Build and return a list of stim objects for the user avatar."""
    s = []

    def C(pos, radius, fillColor, lineColor=None, lineWidth=1, opacity=1.0):
        radius = max(float(radius), 1.0)  # guard: PsychoPy crashes on radius<=0
        return visual.Circle(win, radius=radius, pos=pos,
                             fillColor=fillColor, lineColor=lineColor,
                             lineWidth=lineWidth, opacity=opacity)
    def R_(pos, width, height, fillColor, lineColor=None, lineWidth=1, opacity=1.0, ori=0):
        width = max(float(width), 1.0); height = max(float(height), 1.0)  # guard
        return visual.Rect(win, width=width, height=height, pos=pos,
                           fillColor=fillColor, lineColor=lineColor,
                           lineWidth=lineWidth, opacity=opacity, ori=ori)

    fR = R * 0.78

    # drop shadows
    for sh_r, sh_op in [(R*1.15, 0.08), (R*1.08, 0.13), (R*1.03, 0.17)]:
        s.append(C((cx+3, cy-3), sh_r, "#000000", opacity=sh_op))
    # bg disc
    s.append(C((cx, cy), R, "#111827"))

    # ── _draw_human_face inlined with fR = R*0.78 ──
    skin="#E8A878"; skin_shadow="#C07848"; skin_highlight="#F8C898"
    hair="#3C2010"; hair_hi="#6A3C1C"; shirt="#1A3A3A"

    s.append(C((cx, cy - fR*0.78), fR*0.78, shirt))
    s.append(C((cx, cy - fR*0.62), fR*0.42, "#FFFFFF", opacity=0.08))
    s.append(R_((cx, cy - fR*0.30), fR*0.30, fR*0.36, skin_shadow))
    s.append(R_((cx-fR*0.04, cy-fR*0.28), fR*0.14, fR*0.30, skin_highlight, opacity=0.35))
    s.append(C((cx+fR*0.025, cy+fR*0.06-fR*0.025), fR*0.535, "#000000", opacity=0.22))
    s.append(C((cx, cy+fR*0.06), fR*0.525, skin))
    s.append(C((cx+fR*0.14, cy+fR*0.06), fR*0.44, skin_shadow, opacity=0.38))
    s.append(C((cx-fR*0.18, cy+fR*0.18), fR*0.32, skin_highlight, opacity=0.30))
    s.append(C((cx-fR*0.24, cy+fR*0.34), fR*0.10, "white", opacity=0.14))
    s.append(C((cx, cy+fR*0.10), fR*0.545, hair))
    s.append(C((cx, cy+fR*0.06), fR*0.525, hair))
    s.append(R_((cx, cy-fR*0.16), fR*1.10, fR*0.60, skin))
    s.append(C((cx+fR*0.14, cy+fR*0.06), fR*0.44, skin_shadow, opacity=0.28))
    s.append(C((cx-fR*0.14, cy+fR*0.46), fR*0.20, hair_hi, opacity=0.50))
    for ex in (-fR*0.51, fR*0.51):
        s.append(C((cx+ex, cy+fR*0.06), fR*0.095, skin))
        s.append(C((cx+ex, cy+fR*0.06), fR*0.055, skin_shadow, opacity=0.55))
    for i, (ex, angle) in enumerate([(-fR*0.20, 5), (fR*0.20, -5)]):
        s.append(R_((cx+ex, cy+fR*0.22), fR*0.20, fR*0.045, hair, ori=angle))
    for ex in (-fR*0.20, fR*0.20):
        s.append(C((cx+ex, cy+fR*0.11), fR*0.115, skin_shadow, opacity=0.45))
        s.append(C((cx+ex, cy+fR*0.12), fR*0.095, "#F5F0EB"))
        s.append(C((cx+ex, cy+fR*0.11), fR*0.065, "#3A5A8A"))
        s.append(C((cx+ex, cy+fR*0.11), fR*0.036, "#0A0806"))
        s.append(C((cx+ex-fR*0.028, cy+fR*0.145), fR*0.024, "white", opacity=0.95))
        s.append(C((cx+ex+fR*0.040, cy+fR*0.098), fR*0.012, "white", opacity=0.55))
        s.append(R_((cx+ex, cy+fR*0.065), fR*0.175, fR*0.018, skin_shadow, opacity=0.30))
    s.append(R_((cx, cy+fR*0.01), fR*0.055, fR*0.14, skin_shadow, opacity=0.28))
    s.append(C((cx, cy-fR*0.055), fR*0.068, skin_shadow, opacity=0.32))
    for nx in (-fR*0.055, fR*0.055):
        s.append(C((cx+nx, cy-fR*0.068), fR*0.030, skin_shadow, opacity=0.50))
    s.append(R_((cx, cy-fR*0.145), fR*0.210, fR*0.052, "#C07860"))
    s.append(R_((cx, cy-fR*0.200), fR*0.230, fR*0.065, "#D08870"))
    s.append(C((cx, cy-fR*0.192), fR*0.055, "white", opacity=0.14))
    s.append(R_((cx, cy-fR*0.168), fR*0.185, fR*0.018, "#7A3820", opacity=0.55))
    s.append(C((cx, cy-fR*0.30), fR*0.20, skin_shadow, opacity=0.22))

    # hard mask ring
    s.append(C((cx, cy), R*1.30, None, lineColor=BG_IDLE, lineWidth=int(R*0.62)))

    return s


# ─────────────────────────────────────────────────────────────
# 6b. MALE USER AVATAR STIMS
# ─────────────────────────────────────────────────────────────

def _make_user_male_stims(win, cx, cy, R):
    """
    Male user avatar: short dark hair, square jaw hint,
    navy shirt, brown eyes — same neutral skin as original.
    """
    s = []

    def C(pos, radius, fillColor, lineColor=None, lineWidth=1, opacity=1.0):
        radius = max(float(radius), 1.0)  # guard: PsychoPy crashes on radius<=0
        return visual.Circle(win, radius=radius, pos=pos,
                             fillColor=fillColor, lineColor=lineColor,
                             lineWidth=lineWidth, opacity=opacity)
    def R_(pos, width, height, fillColor, lineColor=None, lineWidth=1, opacity=1.0, ori=0):
        width = max(float(width), 1.0); height = max(float(height), 1.0)  # guard
        return visual.Rect(win, width=width, height=height, pos=pos,
                           fillColor=fillColor, lineColor=lineColor,
                           lineWidth=lineWidth, opacity=opacity, ori=ori)

    fR = R * 0.78
    skin = "#E8A878"; skin_shadow = "#C07848"; skin_hi = "#F8C898"
    hair = "#1A1208"; hair_hi = "#3A2810"; shirt = "#1A2A5A"  # dark navy

    # Drop shadows + bg disc
    for sh_r, sh_op in [(R*1.15, 0.08), (R*1.08, 0.13), (R*1.03, 0.17)]:
        s.append(C((cx+3, cy-3), sh_r, "#000000", opacity=sh_op))
    s.append(C((cx, cy), R, "#111827"))

    # Shirt / shoulders (broader for male)
    s.append(C((cx, cy - fR*0.76), fR*0.85, shirt))
    s.append(C((cx, cy - fR*0.62), fR*0.42, "#FFFFFF", opacity=0.06))

    # Neck (slightly wider)
    s.append(R_((cx, cy - fR*0.28), fR*0.33, fR*0.36, skin_shadow))
    s.append(R_((cx-fR*0.04, cy-fR*0.26), fR*0.14, fR*0.28, skin_hi, opacity=0.30))

    # Head drop shadow + base
    s.append(C((cx+fR*0.025, cy+fR*0.06-fR*0.025), fR*0.535, "#000000", opacity=0.20))
    s.append(C((cx, cy+fR*0.06), fR*0.525, skin))
    s.append(C((cx+fR*0.14, cy+fR*0.06), fR*0.44, skin_shadow, opacity=0.36))
    s.append(C((cx-fR*0.18, cy+fR*0.18), fR*0.32, skin_hi, opacity=0.26))

    # Short hair — just a cap on top (no side blobs → masculine short cut)
    s.append(C((cx, cy+fR*0.48), fR*0.54, hair))           # hair dome
    s.append(R_((cx, cy+fR*0.14), fR*1.05, fR*0.55, skin)) # clip back to face
    s.append(C((cx+fR*0.14, cy+fR*0.06), fR*0.44, skin_shadow, opacity=0.22))
    s.append(C((cx-fR*0.12, cy+fR*0.42), fR*0.16, hair_hi, opacity=0.40))

    # Ears
    for ex in (-fR*0.51, fR*0.51):
        s.append(C((cx+ex, cy+fR*0.06), fR*0.095, skin))
        s.append(C((cx+ex, cy+fR*0.06), fR*0.055, skin_shadow, opacity=0.50))

    # Eyebrows — slightly heavier/flatter for male
    for ex, angle in [(-fR*0.20, 3), (fR*0.20, -3)]:
        s.append(R_((cx+ex, cy+fR*0.22), fR*0.22, fR*0.055, hair, ori=angle))

    # Eyes — brown iris
    for ex in (-fR*0.20, fR*0.20):
        s.append(C((cx+ex, cy+fR*0.11), fR*0.115, skin_shadow, opacity=0.40))
        s.append(C((cx+ex, cy+fR*0.12), fR*0.095, "#F5F0EB"))
        s.append(C((cx+ex, cy+fR*0.11), fR*0.065, "#5A3820"))  # brown iris
        s.append(C((cx+ex, cy+fR*0.11), fR*0.036, "#080604"))
        s.append(C((cx+ex-fR*0.028, cy+fR*0.145), fR*0.024, "white", opacity=0.90))
        s.append(C((cx+ex+fR*0.040, cy+fR*0.098), fR*0.012, "white", opacity=0.50))
        s.append(R_((cx+ex, cy+fR*0.065), fR*0.175, fR*0.018, skin_shadow, opacity=0.28))

    # Nose (slightly wider)
    s.append(R_((cx, cy+fR*0.01), fR*0.065, fR*0.14, skin_shadow, opacity=0.26))
    s.append(C((cx, cy-fR*0.055), fR*0.075, skin_shadow, opacity=0.30))
    for nx in (-fR*0.065, fR*0.065):
        s.append(C((cx+nx, cy-fR*0.068), fR*0.035, skin_shadow, opacity=0.48))

    # Lips (thinner/less full → male)
    s.append(R_((cx, cy-fR*0.145), fR*0.200, fR*0.042, "#B06850"))
    s.append(R_((cx, cy-fR*0.195), fR*0.210, fR*0.048, "#C07860"))
    s.append(R_((cx, cy-fR*0.168), fR*0.175, fR*0.016, "#7A3820", opacity=0.50))

    # Chin shadow (squarer hint)
    s.append(R_((cx, cy-fR*0.32), fR*0.50, fR*0.18, skin_shadow, opacity=0.14))

    # Subtle stubble dots row (5 o'clock shadow)
    import random
    rng = random.Random(42)
    for _ in range(18):
        sx = cx + rng.uniform(-fR*0.28, fR*0.28)
        sy = cy + rng.uniform(-fR*0.36, -fR*0.16)
        s.append(C((sx, sy), fR*0.018, skin_shadow, opacity=0.28))

    # Mask ring
    s.append(C((cx, cy), R*1.30, None, lineColor=BG_IDLE, lineWidth=int(R*0.62)))
    return s


# ─────────────────────────────────────────────────────────────
# 6c. FEMALE USER AVATAR STIMS
# ─────────────────────────────────────────────────────────────

def _make_user_female_stims(win, cx, cy, R):
    """
    Female user avatar: longer wavy hair, slightly fuller lips,
    teal shirt — identical skin tone to male for fairness.
    Reuses the same base as original _make_user_stims but with
    longer hair side-blobs and teal top.
    """
    s = []

    def C(pos, radius, fillColor, lineColor=None, lineWidth=1, opacity=1.0):
        radius = max(float(radius), 1.0)  # guard: PsychoPy crashes on radius<=0
        return visual.Circle(win, radius=radius, pos=pos,
                             fillColor=fillColor, lineColor=lineColor,
                             lineWidth=lineWidth, opacity=opacity)
    def R_(pos, width, height, fillColor, lineColor=None, lineWidth=1, opacity=1.0, ori=0):
        width = max(float(width), 1.0); height = max(float(height), 1.0)  # guard
        return visual.Rect(win, width=width, height=height, pos=pos,
                           fillColor=fillColor, lineColor=lineColor,
                           lineWidth=lineWidth, opacity=opacity, ori=ori)

    fR = R * 0.78
    skin = "#E8A878"; skin_shadow = "#C07848"; skin_hi = "#F8C898"
    hair = "#3C2010"; hair_hi = "#6A3C1C"; shirt = "#1A3A3A"  # teal (original)

    # Drop shadows + bg disc
    for sh_r, sh_op in [(R*1.15, 0.08), (R*1.08, 0.13), (R*1.03, 0.17)]:
        s.append(C((cx+3, cy-3), sh_r, "#000000", opacity=sh_op))
    s.append(C((cx, cy), R, "#111827"))

    # Shirt (slightly narrower shoulders)
    s.append(C((cx, cy - fR*0.78), fR*0.78, shirt))
    s.append(C((cx, cy - fR*0.62), fR*0.42, "#FFFFFF", opacity=0.08))

    # Neck
    s.append(R_((cx, cy - fR*0.30), fR*0.28, fR*0.36, skin_shadow))
    s.append(R_((cx-fR*0.04, cy-fR*0.28), fR*0.12, fR*0.30, skin_hi, opacity=0.35))

    # Head
    s.append(C((cx+fR*0.025, cy+fR*0.06-fR*0.025), fR*0.535, "#000000", opacity=0.22))
    s.append(C((cx, cy+fR*0.06), fR*0.525, skin))
    s.append(C((cx+fR*0.14, cy+fR*0.06), fR*0.44, skin_shadow, opacity=0.38))
    s.append(C((cx-fR*0.18, cy+fR*0.18), fR*0.32, skin_hi, opacity=0.30))
    s.append(C((cx-fR*0.24, cy+fR*0.34), fR*0.10, "white", opacity=0.14))

    # Long wavy hair — back layer goes lower to simulate length
    s.append(C((cx, cy+fR*0.10), fR*0.96, hair))          # bigger dome = long hair
    s.append(C((cx, cy+fR*0.06), fR*0.525, hair))
    s.append(C((cx-fR*0.70, cy-fR*0.30), fR*0.55, hair))  # left side locks
    s.append(C((cx-fR*0.72, cy-fR*0.70), fR*0.40, hair))  # lower left
    s.append(C((cx+fR*0.64, cy-fR*0.28), fR*0.45, hair))  # right side
    s.append(C((cx+fR*0.66, cy-fR*0.66), fR*0.32, hair))  # lower right
    # Clip hair back to show face
    s.append(R_((cx, cy-fR*0.16), fR*1.10, fR*0.60, skin))
    s.append(C((cx+fR*0.14, cy+fR*0.06), fR*0.44, skin_shadow, opacity=0.28))
    s.append(C((cx-fR*0.14, cy+fR*0.46), fR*0.20, hair_hi, opacity=0.50))

    # Ears
    for ex in (-fR*0.51, fR*0.51):
        s.append(C((cx+ex, cy+fR*0.06), fR*0.095, skin))
        s.append(C((cx+ex, cy+fR*0.06), fR*0.055, skin_shadow, opacity=0.55))

    # Eyebrows (slightly arched for feminine look)
    for ex, angle in [(-fR*0.20, 8), (fR*0.20, -8)]:
        s.append(R_((cx+ex, cy+fR*0.22), fR*0.18, fR*0.040, hair, ori=angle))

    # Eyes — blue-grey iris (same as original user avatar)
    for ex in (-fR*0.20, fR*0.20):
        s.append(C((cx+ex, cy+fR*0.11), fR*0.115, skin_shadow, opacity=0.45))
        s.append(C((cx+ex, cy+fR*0.12), fR*0.095, "#F5F0EB"))
        s.append(C((cx+ex, cy+fR*0.11), fR*0.065, "#3A5A8A"))
        s.append(C((cx+ex, cy+fR*0.11), fR*0.036, "#0A0806"))
        s.append(C((cx+ex-fR*0.028, cy+fR*0.145), fR*0.024, "white", opacity=0.95))
        s.append(C((cx+ex+fR*0.040, cy+fR*0.098), fR*0.012, "white", opacity=0.55))
        s.append(R_((cx+ex, cy+fR*0.065), fR*0.175, fR*0.018, skin_shadow, opacity=0.30))

    # Nose
    s.append(R_((cx, cy+fR*0.01), fR*0.055, fR*0.14, skin_shadow, opacity=0.28))
    s.append(C((cx, cy-fR*0.055), fR*0.068, skin_shadow, opacity=0.32))
    for nx in (-fR*0.055, fR*0.055):
        s.append(C((cx+nx, cy-fR*0.068), fR*0.030, skin_shadow, opacity=0.50))

    # Lips (fuller)
    s.append(R_((cx, cy-fR*0.145), fR*0.220, fR*0.058, "#C07860"))
    s.append(R_((cx, cy-fR*0.205), fR*0.240, fR*0.072, "#D08870"))
    s.append(C((cx, cy-fR*0.196), fR*0.060, "white", opacity=0.16))
    s.append(R_((cx, cy-fR*0.168), fR*0.192, fR*0.018, "#7A3820", opacity=0.55))

    # Chin shadow
    s.append(C((cx, cy-fR*0.30), fR*0.20, skin_shadow, opacity=0.22))

    # Mask ring
    s.append(C((cx, cy), R*1.30, None, lineColor=BG_IDLE, lineWidth=int(R*0.62)))
    return s


# ─────────────────────────────────────────────────────────────
# 6d. GENDER GLOBALS
#   _AGENT_GENDER  — the chat agent's gender (set by selection screen)
#   User is always drawn as male (fixed — never changes)
# ─────────────────────────────────────────────────────────────

_AGENT_GENDER = {"choice": "female"}   # updated by show_avatar_selection()
# _USER_GENDER is not needed — user is always male

def _make_user_stims_dispatch(win, cx, cy, R):
    """User avatar is always male — fixed, never changes."""
    return _make_user_male_stims(win, cx, cy, R)


# ─────────────────────────────────────────────────────────────
# 6e. AVATAR SELECTION SCREEN
# ─────────────────────────────────────────────────────────────

def _draw_gender_symbol(win, cx, cy, gender, col, sr=14):
    """
    Draw ♂ (circle + arrow) or ♀ (circle + cross) from primitives.
    sr = symbol circle radius in pixels.
    """
    lw = 2.5
    if gender == "male":
        # Circle
        visual.Circle(win, radius=sr, pos=(cx - sr*0.55, cy),
                      fillColor=None, lineColor=col, lineWidth=lw).draw()
        # Arrow shaft (diagonal up-right)
        ax0, ay0 = cx - sr*0.55 + sr*0.70, cy + sr*0.70
        ax1, ay1 = cx + sr*0.85,            cy + sr*1.85
        shaft_cx = (ax0+ax1)/2; shaft_cy = (ay0+ay1)/2
        shaft_len = math.hypot(ax1-ax0, ay1-ay0)
        shaft_ang = -math.degrees(math.atan2(ay1-ay0, ax1-ax0))
        visual.Rect(win, width=shaft_len, height=lw,
                    pos=(shaft_cx, shaft_cy),
                    fillColor=col, lineColor=None, ori=shaft_ang).draw()
        # Arrow head (two short lines at the tip)
        for ang_off in (135, 180):
            rad = math.radians(ang_off + 45)
            ex = ax1 + math.cos(rad) * sr*0.38
            ey = ay1 + math.sin(rad) * sr*0.38
            hcx = (ax1+ex)/2; hcy = (ay1+ey)/2
            hlen = math.hypot(ex-ax1, ey-ay1)
            hang = -math.degrees(math.atan2(ey-ay1, ex-ax1))
            visual.Rect(win, width=hlen, height=lw,
                        pos=(hcx, hcy),
                        fillColor=col, lineColor=None, ori=hang).draw()
    else:
        # ♀: circle on top, vertical stem, horizontal crossbar
        # Circle
        visual.Circle(win, radius=sr, pos=(cx, cy + sr*0.55),
                      fillColor=None, lineColor=col, lineWidth=lw).draw()
        # Stem (vertical down from bottom of circle)
        visual.Rect(win, width=lw, height=sr*1.2,
                    pos=(cx, cy - sr*0.05),
                    fillColor=col, lineColor=None).draw()
        # Crossbar
        visual.Rect(win, width=sr*1.1, height=lw,
                    pos=(cx, cy - sr*0.30),
                    fillColor=col, lineColor=None).draw()


def _draw_avatar_preview(win, label, cx, cy, R, gender, highlight=False):
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
    fR_   = R * 0.32
    fcy_  = av_cy + R * 0.08
    prev_accent = col_hi if highlight else "#3A5A8A"
    if gender == "male":
        stims = _make_robot_male_stims(win, cx, av_cy, prev_accent, R, fR_, fcy_)
    else:
        stims = _make_robot_stims(win, cx, av_cy, prev_accent, R, fR_, fcy_)
    for st in stims:
        st.draw()

    # ── Name + role tag section ──
    name_y = cy - card_h // 2 + int(R * 0.72)
    # subtle separator line above name
    visual.Rect(win, width=card_w - 24, height=1,
                pos=(cx, name_y + int(R * 0.28)),
                fillColor=border_col, lineColor=None, opacity=0.35).draw()

    lbl_col = col_hi if highlight else "#8899BB"
    visual.TextStim(win, text=label,
                    pos=(cx, name_y),
                    color=lbl_col, height=22, font="Arial Bold",
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


def show_avatar_selection(win):
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
        visual.TextStim(win, text="Choose Your Chat Agent",
                        pos=(0, WIN_H // 2 - 52),
                        color="white", height=22, font="Arial Bold",
                        anchorHoriz="center", anchorVert="center").draw()

        # Subtitle
        visual.TextStim(win,
            text="Both agents share identical personality traits",
            pos=(0, WIN_H // 2 - 86),
            color="#4A6A9A", height=13, font="Arial",
            anchorHoriz="center", anchorVert="center").draw()

        # Hint — click only, no keyboard labels
        visual.TextStim(win,
            text="Click a card to choose  •  press ENTER to confirm",
            pos=(0, WIN_H // 2 - 108),
            color="#2A4060", height=12, font="Arial",
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
                        color="white", height=17, font="Arial Bold",
                        anchorHoriz="center", anchorVert="center").draw()

    while True:
        t = time.time()
        win.clearBuffer()

        _draw_bg(t)
        _draw_header()

        _draw_avatar_preview(win, "Alex", LEFT_CX,  CARD_CY, R, "male",
                             highlight=(selected == "male"))
        _draw_avatar_preview(win, "Sara", RIGHT_CX, CARD_CY, R, "female",
                             highlight=(selected == "female"))

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


def draw_robot_avatar(win, cx, cy, accent, size=1.0, anim_t=0.0):
    """Draw the CHAT AGENT avatar — gender follows the selection screen choice."""
    R      = 40 * size
    fR     = R * 0.32
    fcy    = cy + R * 0.08
    gender = _AGENT_GENDER["choice"]          # agent gender — set by selection screen
    key    = ("robot", cx, cy, accent, size, gender)
    if key not in _avatar_cache:
        if gender == "male":
            _avatar_cache[key] = _make_robot_male_stims(win, cx, cy, accent, R, fR, fcy)
        else:
            _avatar_cache[key] = _make_robot_stims(win, cx, cy, accent, R, fR, fcy)
    for stim in _avatar_cache[key]:
        stim.draw()


def draw_user_avatar(win, cx, cy, size=1.0):
    """Draw the USER avatar — always male, never changes."""
    R   = 40 * size
    key = ("user_male", cx, cy, size)         # fixed key — always male
    if key not in _avatar_cache:
        _avatar_cache[key] = _make_user_male_stims(win, cx, cy, R)
    for stim in _avatar_cache[key]:
        stim.draw()
# ─────────────────────────────────────────────────────────────
# 7. CHAT MESSAGE BOX
# ─────────────────────────────────────────────────────────────

CHAT_BOX_W   = 700
CHAT_BOX_H   = 52
AVATAR_R     = 40     # matches R=40 in draw_robot_avatar
AVATAR_GAP   = 12

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
                    height=13, font="Arial Bold",
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
        draw_robot_avatar(win, av_cx, y_pos, accent=accent_color)
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
    bar_y = WIN_H//2 - 34
    bar_h = 68

    # ── Header ──
    s["hdr_bg"]    = visual.Rect(win, width=WIN_W, height=bar_h,
                                  pos=(0, bar_y), fillColor="#080C18", lineColor=None)
    s["hdr_top"]   = visual.Rect(win, width=WIN_W, height=4,
                                  pos=(0, WIN_H//2-2), fillColor=accent, lineColor=None)
    s["hdr_shine"] = visual.Rect(win, width=WIN_W, height=bar_h//2,
                                  pos=(0, bar_y + bar_h//4),
                                  fillColor="#FFFFFF", lineColor=None, opacity=0.025)
    s["hdr_bot"]   = visual.Rect(win, width=WIN_W, height=1,
                                  pos=(0, WIN_H//2 - bar_h),
                                  fillColor=accent, lineColor=None, opacity=0.35)
    # online dot
    s["hdr_dot"]   = visual.Circle(win, radius=6,
                                    pos=(-WIN_W//2 + 24, bar_y),
                                    fillColor="#00E676", lineColor=None)
    s["hdr_dot_r"] = visual.Circle(win, radius=10,
                                    pos=(-WIN_W//2 + 24, bar_y),
                                    fillColor="#00E676", lineColor=None, opacity=0.20)

    # ── Input bar ──
    s["inp_div"]   = visual.Rect(win, width=WIN_W, height=1,
                                  pos=(0, -WIN_H//2 + INPUT_BAR_H),
                                  fillColor=accent, lineColor=None, opacity=0.30)
    s["inp_bg"]    = visual.Rect(win, width=WIN_W, height=INPUT_BAR_H,
                                  pos=(0, -WIN_H//2 + INPUT_BAR_H//2),
                                  fillColor="#07080F", lineColor=None)
    s["inp_shine"] = visual.Rect(win, width=WIN_W, height=INPUT_BAR_H//2,
                                  pos=(0, -WIN_H//2 + INPUT_BAR_H*3//4),
                                  fillColor="#FFFFFF", lineColor=None, opacity=0.018)

    _static_stims[accent] = s
    return s


def redraw_scene(win, history, profile, typed, is_typing, time_left=None, anim_t=0.0):
    win.clearBuffer()
    accent = profile["color"]
    ss     = _get_static_stims(win, accent)
    bar_y  = WIN_H//2 - 34
    bar_h  = 68

    # ── Background subtle horizontal lines ──
    for row in range(-WIN_H//2, WIN_H//2, 32):
        visual.Rect(win, width=WIN_W, height=1,
                    pos=(0, row), fillColor="#FFFFFF",
                    lineColor=None, opacity=0.012).draw()

    # ── Header ──
    ss["hdr_bg"].draw()
    ss["hdr_shine"].draw()
    ss["hdr_top"].draw()
    ss["hdr_bot"].draw()
    ss["hdr_dot_r"].draw()
    ss["hdr_dot"].draw()

    # Agent name + personality tag
    visual.TextStim(win, text=f"  {profile['name']}",
                    pos=(-WIN_W//2 + 44, bar_y + 9),
                    color="white", height=20, font="Arial Bold",
                    anchorHoriz="left", anchorVert="center").draw()
    visual.TextStim(win,
                    text=f"  {profile.get('name','Agent')} · AI Personality Agent · Active",
                    pos=(-WIN_W//2 + 44, bar_y - 12),
                    color=accent, height=11, font="Arial",
                    anchorHoriz="left", anchorVert="center", opacity=0.85).draw()

    # ── Header right side: Timer + END button ──
    # END button — far right of header
    end_w, end_h = EXIT_BTN_W, EXIT_BTN_H
    end_x, end_y = EXIT_BTN_X, EXIT_BTN_Y
    visual.Rect(win, width=end_w + 6, height=end_h + 6,
                pos=(end_x, end_y),
                fillColor="#880000", lineColor=None, opacity=0.22).draw()
    visual.Rect(win, width=end_w, height=end_h,
                pos=(end_x, end_y),
                fillColor="#3A0000", lineColor="#CC3333", lineWidth=1.5).draw()
    visual.TextStim(win, text="END",
                    pos=(end_x, end_y),
                    color="#FF5555", height=13, font="Arial Bold",
                    anchorHoriz="center", anchorVert="center").draw()

    # Timer pill — sits directly left of END button with a small gap
    if time_left is not None:
        mins = int(time_left) // 60
        secs = int(time_left) % 60
        timer_str = f"{mins}:{secs:02d}"
        t_w  = 72
        t_gap = 10
        t_x  = end_x - end_w // 2 - t_gap - t_w // 2
        t_col = "#FF4444" if time_left < 30 else ("#FFAA44" if time_left < 90 else "#C8D8F0")
        visual.Rect(win, width=t_w, height=end_h,
                    pos=(t_x, end_y),
                    fillColor="#09121E", lineColor=accent,
                    lineWidth=1.2).draw()
        visual.TextStim(win, text=timer_str,
                        pos=(t_x, end_y),
                        color=t_col, height=14, font="Arial Bold",
                        anchorHoriz="center", anchorVert="center").draw()

    # ── Chat messages ──
    visible = history[-5:]
    y = CHAT_AREA_TOP - 35
    for role, text in visible:
        h = draw_message_box(win, text, y, role,
                             accent_color=accent, profile=profile)
        y -= h + 18

    # ── Input bar ──
    ss["inp_div"].draw()
    ss["inp_bg"].draw()
    ss["inp_shine"].draw()

    bar_y2  = -WIN_H//2 + INPUT_BAR_H//2
    field_w = WIN_W - 130
    border_col  = accent  if is_typing else "#1E2E48"
    field_color = "#0D1828" if is_typing else "#090E1A"

    # Input field glow (typing state)
    if is_typing:
        visual.Rect(win, width=field_w + 10, height=48,
                    pos=(-25, bar_y2),
                    fillColor=accent, lineColor=None, opacity=0.07).draw()

    # Input field
    visual.Rect(win, width=field_w, height=42,
                pos=(-25, bar_y2),
                fillColor=field_color, lineColor=border_col, lineWidth=2.0).draw()
    # Field inner shine
    visual.Rect(win, width=field_w - 6, height=12,
                pos=(-25, bar_y2 + 12),
                fillColor="#FFFFFF", lineColor=None, opacity=0.025).draw()

    if not typed:
        visual.TextStim(win, text="Type a message and press ENTER…",
                        pos=(-WIN_W//2 + 66, bar_y2),
                        color="#2A3A58", height=16, font="Arial",
                        anchorHoriz="left", anchorVert="center").draw()
    else:
        visual.TextStim(win, text=typed + "|",
                        pos=(-WIN_W//2 + 66, bar_y2),
                        color="#D0E4FF", height=17, font="Arial",
                        anchorHoriz="left", anchorVert="center",
                        wrapWidth=field_w - 48).draw()

    # Send button (circle with arrow)
    btn_x   = WIN_W//2 - 38
    btn_col = accent if typed else "#111C2C"
    visual.Circle(win, radius=24, pos=(btn_x, bar_y2),
                  fillColor=btn_col, lineColor=None,
                  opacity=1.0 if typed else 0.55).draw()
    if typed:
        # Glow ring on active button
        visual.Circle(win, radius=28, pos=(btn_x, bar_y2),
                      fillColor=accent, lineColor=None, opacity=0.18).draw()
    visual.TextStim(win, text="→",
                    pos=(btn_x, bar_y2),
                    color="white", height=22, font="Arial Bold",
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
    """Save conversation to a CSV file in a 'data' folder next to the script."""
    # Create data folder next to the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir   = os.path.join(script_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pid       = participant_id.strip() or "unknown"
    filename  = os.path.join(data_dir, f"chat_{pid}_{agent_name}_{timestamp}.csv")

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["turn", "role", "message", "participant_id",
                         "agent", "avatar_gender", "timestamp"])
        for i, (role, text) in enumerate(chat_log):
            writer.writerow([i + 1, role, text, pid, agent_name,
                             avatar_gender, timestamp])

    return filename


# ─────────────────────────────────────────────────────────────
# 16. ENTRY POINT
# ─────────────────────────────────────────────────────────────

def main():
    info   = get_experiment_info()
    chosen = info["Personality Agent"]
    pid    = info["Participant ID"].strip() or "unknown"

    win   = make_window()

    # ── Avatar selection screen (before experiment begins) ──
    avatar_gender = show_avatar_selection(win)

    agent = ConversationalAgent(name=chosen, gender=avatar_gender)

    show_message(win,
        "Welcome!\n\nYou will now have a conversation\nwith an agent.\n\nPress any key to begin.",
        duration=0.1, color="white")
    event.waitKeys()

    chat_log = run_conversation(win, agent)

    # ── Save to CSV (includes avatar gender) ──
    saved_path = save_chat_csv(chat_log, participant_id=pid,
                               agent_name=chosen, avatar_gender=avatar_gender)
    print(f"\n✓ Chat saved → {saved_path}")
    show_message(win, "Thank you for participating!\n\nThe session has ended.",
                 duration=3.0, color="white")
    win.close()
    core.quit()


if __name__ == "__main__":
    main()
