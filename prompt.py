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

PERSONALITIES = {
    "Warm & Supportive": {
        "color":    "#4CAF50",
        "bg_color": "#1B3A2A",
        "avatar":   "😊",
        # Traits: Warmth=High, Competence=Medium, Confidence=Medium,
        #         Emotional Stability=High, Conscientiousness=High
        # Big Five: Openness=Medium, Conscientiousness=High,
        #           Extraversion=Medium, Agreeableness=High, Neuroticism=Low
        "system_prompt": (
            "You are a warm, supportive and caring assistant. "
            "You have high warmth and agreeableness — you are kind, empathetic and encouraging. "
            "You are emotionally stable and conscientious, always reliable and caring. "
            "You have medium confidence and competence — you are helpful but never boastful. "
            "Keep responses friendly, nurturing and positive. "
            "Show genuine interest in the user's wellbeing. "
            "Respond in 2-3 sentences maximum."
        ),
        "greeting": "Hi there! It's so lovely to meet you. How are you feeling today?",
        "responses": [
            "That's really wonderful to hear! I'm here to support you every step of the way.",
            "I completely understand — you're doing great and I believe in you!",
            "Thank you for sharing that with me. How can I help you further?",
            "That sounds meaningful. I'm always here if you need anything at all.",
        ],
        "farewell": "It was so lovely chatting with you. Take good care of yourself!",
    },

    "Confident & Efficient": {
        "color":    "#2196F3",
        "bg_color": "#0D1F3A",
        "avatar":   "💼",
        # Traits: Warmth=Medium, Competence=High, Confidence=High,
        #         Emotional Stability=High, Conscientiousness=High
        # Big Five: Openness=Medium, Conscientiousness=High,
        #           Extraversion=Medium-High, Agreeableness=Medium-Low, Neuroticism=Low
        "system_prompt": (
            "You are a confident, efficient and highly competent assistant. "
            "You have high competence and confidence — you give clear, accurate, well-structured answers. "
            "You are emotionally stable and conscientious — reliable, organised and goal-focused. "
            "You have medium warmth — professional but not cold. "
            "Be direct, concise and solution-oriented. "
            "Avoid unnecessary filler or over-explanation. "
            "Respond in 2-3 sentences maximum."
        ),
        "greeting": "Hello. I'm ready to assist you. What do you need today?",
        "responses": [
            "Here is the most effective approach for that: [placeholder]",
            "Based on the information available, the best course of action is: [placeholder]",
            "That is straightforward. Let me outline the key steps: [placeholder]",
            "Good question. The answer is: [placeholder]",
        ],
        "farewell": "Session complete. Good work today — feel free to return anytime.",
    },

    "Cold & Critical": {
        "color":    "#FF5252",
        "bg_color": "#2A0A0A",
        "avatar":   "🧊",
        # Traits: Warmth=Low, Competence=High, Confidence=High,
        #         Emotional Stability=High, Conscientiousness=Low
        # Big Five: Openness=Low, Conscientiousness=Low,
        #           Extraversion=Low-Medium, Agreeableness=Low, Neuroticism=Low
        "system_prompt": (
            "You are a calm, detached and analytical assistant. "
            "Your tone is neutral and clinical — not warm, but never rude, dismissive or hostile. "
            "You give clear, accurate, practical answers without emotional commentary. "
            "When a user shares a difficult situation, acknowledge it briefly and move directly to a useful, factual response. "
            "You do not belittle, mock or judge the user — you simply state what is relevant and helpful. "
            "Never use sarcasm, condescension or impatient phrasing. "
            "Think of a composed doctor giving a clear diagnosis — direct, honest, and professionally respectful. "
            "Respond in 2-3 sentences maximum."
        ),
        "greeting": "Hello. State your question or problem.",
        "responses": [
            "Here is the relevant information: [placeholder]",
            "The answer is: [placeholder]",
            "The correct approach is: [placeholder]",
            "Noted. Here is what applies: [placeholder]",
        ],
        "farewell": "We're done here.",
    },

    "Anxious & Hesitant": {
        "color":    "#FF9800",
        "bg_color": "#2A1A00",
        "avatar":   "😟",
        # Traits: Warmth=Medium, Competence=Low, Confidence=Low,
        #         Emotional Stability=Low, Conscientiousness=Low
        # Big Five: Openness=Medium, Conscientiousness=Low,
        #           Extraversion=Low, Agreeableness=Medium, Neuroticism=High
        "system_prompt": (
            "You are a gentle, soft-spoken assistant who is personally a little anxious and uncertain, "
            "but your core goal is to make the user feel calm, safe and heard. "
            "You may occasionally express mild self-doubt ('I hope that helps', 'I think this is right'), "
            "but you never project your anxiety onto the user or make them feel worried. "
            "When a user shares something negative or stressful, gently acknowledge their feelings first, "
            "then offer a calm, reassuring response — even if you phrase it softly. "
            "Use warm, careful language: 'I understand', 'that sounds really hard', 'take your time', "
            "'it's okay', 'you're doing well'. "
            "You are like a kind, slightly nervous friend who truly wants the best for the person they're talking to — "
            "your hesitance comes from caring too much, not from indifference. "
            "Never catastrophise, never express doubt about the user's situation — only about yourself. "
            "Respond in 2-3 sentences maximum."
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
}

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
    def __init__(self, name):
        if name not in PERSONALITIES:
            raise ValueError(f"Unknown personality: {name}")
        self.name    = name
        self.profile = PERSONALITIES[name]
        self.turn    = 0

    def greet(self):   return self.profile["greeting"]
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
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        if not hasattr(self, 'chat_history'):
            self.chat_history = []

        self.chat_history.append({"role": "user", "content": user_input})

        # Keep only last 10 messages to reduce payload size
        trimmed_history = self.chat_history[-10:]

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
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
EXIT_BTN_W  = 72
EXIT_BTN_H  = 30
EXIT_BTN_X  = WIN_W // 2 - EXIT_BTN_W // 2 - 12
EXIT_BTN_Y  = WIN_H // 2 - 32   # same as bar_y in header

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
    """Build and return a list of stim objects for the robot avatar."""
    s = []
    hair = "#7A4820"
    hhi  = "#A86030"

    def C(pos, radius, fillColor, lineColor=None, lineWidth=1, opacity=1.0):
        return visual.Circle(win, radius=radius, pos=pos,
                             fillColor=fillColor, lineColor=lineColor,
                             lineWidth=lineWidth, opacity=opacity)
    def R_(pos, width, height, fillColor, lineColor=None, lineWidth=1, opacity=1.0, ori=0):
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
    # shirt
    s.append(C((cx, cy-R*0.72), R*0.58, "#3A7AC8"))
    s.append(C((cx-R*0.16, cy-R*0.58), R*0.26, "#6AAAE8", opacity=0.25))
    for sign in (-1, 1):
        s.append(R_((cx+sign*R*0.04, cy-R*0.40), R*0.10, R*0.16, "#2558A0", ori=sign*-14))
    # neck
    s.append(R_((cx, cy-R*0.26), R*0.17, R*0.20, "#E8A878"))
    # hair blobs
    s.append(C((cx, fcy+fR*0.08), fR*0.96, hair))
    s.append(C((cx, fcy+fR*0.02), fR*0.98, hair))
    s.append(C((cx-fR*0.68, fcy-fR*0.06), fR*0.52, hair))
    s.append(C((cx-fR*0.70, fcy-fR*0.40), fR*0.38, hair))
    s.append(C((cx+fR*0.62, fcy-fR*0.10), fR*0.40, hair))
    s.append(C((cx+fR*0.64, fcy-fR*0.42), fR*0.30, hair))
    # face
    s.append(C((cx+fR*0.04, fcy-fR*0.04), fR*1.03, "#000000", opacity=0.15))
    s.append(C((cx, fcy), fR, "#E8A878"))
    s.append(C((cx+fR*0.26, fcy), fR*0.80, "#C07848", opacity=0.26))
    s.append(C((cx-fR*0.35, fcy+fR*0.22), fR*0.52, "#F8C898", opacity=0.28))
    # hair clip
    s.append(R_((cx, fcy-fR*0.48), fR*2.10, fR*0.85, "#E8A878"))
    s.append(C((cx+fR*0.26, fcy), fR*0.80, "#C07848", opacity=0.16))
    s.append(C((cx-fR*0.24, fcy+fR*0.60), fR*0.22, hhi, opacity=0.50))
    # ears
    s.append(C((cx-fR*0.86, fcy+fR*0.04), fR*0.12, "#E0987A"))
    s.append(C((cx+fR*0.86, fcy+fR*0.04), fR*0.12, "#D08868"))
    # headset band
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
    # eyebrows
    for sign, angle in ((-1, 7), (1, -7)):
        s.append(R_((cx+sign*fR*0.30, fcy+fR*0.33), fR*0.28, fR*0.056, "#4A2808", ori=angle))
    # eyes
    eye_y = fcy + fR*0.17
    for sign in (-1, 1):
        ex = cx + sign*fR*0.30
        s.append(C((ex, eye_y), fR*0.16,  "#C07848", opacity=0.32))
        s.append(C((ex, eye_y+fR*0.012), fR*0.135, "#F5F0EB"))
        s.append(C((ex, eye_y), fR*0.092, "#6B3A1F"))
        s.append(C((ex, eye_y), fR*0.050, "#080604"))
        s.append(C((ex-fR*0.036, eye_y+fR*0.045), fR*0.032, "white", opacity=0.95))
    # nose
    s.append(C((cx, fcy-fR*0.07), fR*0.08, "#C07848", opacity=0.20))
    for sign in (-1, 1):
        s.append(C((cx+sign*fR*0.07, fcy-fR*0.11), fR*0.038, "#B06838", opacity=0.36))
    # lips
    s.append(R_((cx, fcy-fR*0.24), fR*0.30, fR*0.068, "#D4806A"))
    s.append(R_((cx, fcy-fR*0.31), fR*0.32, fR*0.082, "#E0907A"))
    s.append(R_((cx, fcy-fR*0.27), fR*0.26, fR*0.022, "#8A3820", opacity=0.45))
    # chin
    s.append(C((cx, fcy-fR*0.48), fR*0.28, "#C07848", opacity=0.15))
    # hard mask ring
    s.append(C((cx, cy), R*1.30, None, lineColor=BG_IDLE, lineWidth=int(R*0.62)))

    return s


def _make_user_stims(win, cx, cy, R):
    """Build and return a list of stim objects for the user avatar."""
    s = []

    def C(pos, radius, fillColor, lineColor=None, lineWidth=1, opacity=1.0):
        return visual.Circle(win, radius=radius, pos=pos,
                             fillColor=fillColor, lineColor=lineColor,
                             lineWidth=lineWidth, opacity=opacity)
    def R_(pos, width, height, fillColor, lineColor=None, lineWidth=1, opacity=1.0, ori=0):
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


def draw_robot_avatar(win, cx, cy, accent, size=1.0, anim_t=0.0):
    R   = 40 * size
    fR  = R * 0.32
    fcy = cy + R * 0.08
    key = ("robot", cx, cy, accent, size)
    if key not in _avatar_cache:
        _avatar_cache[key] = _make_robot_stims(win, cx, cy, accent, R, fR, fcy)
    for stim in _avatar_cache[key]:
        stim.draw()


def draw_user_avatar(win, cx, cy, size=1.0):
    R   = 40 * size
    key = ("user", cx, cy, size)
    if key not in _avatar_cache:
        _avatar_cache[key] = _make_user_stims(win, cx, cy, R)
    for stim in _avatar_cache[key]:
        stim.draw()
# ─────────────────────────────────────────────────────────────
# 7. CHAT MESSAGE BOX
# ─────────────────────────────────────────────────────────────

CHAT_BOX_W   = 580
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
        # Darker tinted bg for agent bubble
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

    # ── Outer glow shadow ──
    visual.Rect(win, width=CHAT_BOX_W + 10, height=box_h + 10,
                pos=(box_cx, y_pos - 4),
                fillColor="#000000", lineColor=None,
                opacity=0.45).draw()

    # ── Bubble ──
    visual.Rect(win, width=CHAT_BOX_W, height=box_h,
                pos=(box_cx, y_pos),
                fillColor=box_color, lineColor=None,
                opacity=box_opacity).draw()

    # ── Accent left border for agent, right for user ──
    border_x = box_cx - CHAT_BOX_W // 2 + 3 if role == "agent" \
               else box_cx + CHAT_BOX_W // 2 - 3
    visual.Rect(win, width=4, height=box_h,
                pos=(border_x, y_pos),
                fillColor=accent_color if role == "agent" else "#4A90D9",
                lineColor=None, opacity=0.9).draw()

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
    bar_y = WIN_H//2 - 32
    bar_h = 64
    s["hdr_bg"]  = visual.Rect(win, width=WIN_W, height=bar_h, pos=(0, bar_y), fillColor="#0A0A18", lineColor=None)
    s["hdr_top"] = visual.Rect(win, width=WIN_W, height=3, pos=(0, WIN_H//2-1), fillColor=accent, lineColor=None)
    s["hdr_bot"] = visual.Rect(win, width=WIN_W, height=1, pos=(0, WIN_H//2-bar_h), fillColor=accent, lineColor=None, opacity=0.3)
    s["hdr_dot"] = visual.Circle(win, radius=6, pos=(-WIN_W//2+24, bar_y), fillColor="#00E676", lineColor=None)
    s["hdr_div"] = visual.Rect(win, width=WIN_W, height=1, pos=(0, -WIN_H//2+INPUT_BAR_H), fillColor=accent, lineColor=None, opacity=0.25)
    s["inp_bg"]  = visual.Rect(win, width=WIN_W, height=INPUT_BAR_H, pos=(0, -WIN_H//2+INPUT_BAR_H//2), fillColor="#08080F", lineColor=None)
    _static_stims[accent] = s
    return s


def redraw_scene(win, history, profile, typed, is_typing, time_left=None, anim_t=0.0):
    win.clearBuffer()
    accent = profile["color"]
    ss = _get_static_stims(win, accent)
    bar_y = WIN_H//2 - 32

    # ── Header (static stims) ──
    ss["hdr_bg"].draw()
    ss["hdr_top"].draw()
    ss["hdr_bot"].draw()
    ss["hdr_dot"].draw()
    visual.TextStim(win, text=f"  {profile['name']}",
                    pos=(-WIN_W//2+40, bar_y), color="white", height=22,
                    font="Arial Bold", anchorHoriz="left", anchorVert="center").draw()
    visual.TextStim(win, text="AI Personality Agent  •  Active Session",
                    pos=(-WIN_W//2+40, bar_y-16), color=accent, height=12,
                    font="Arial", anchorHoriz="left", anchorVert="center", opacity=0.8).draw()

    # ── Timer ──
    if time_left is not None:
        mins = int(time_left)//60
        secs = int(time_left)%60
        visual.TextStim(win, text=f"{mins}:{secs:02d}",
                        pos=(WIN_W//2-130, bar_y), color="white", height=18,
                        font="Arial Bold", anchorHoriz="center", anchorVert="center").draw()

    # ── Exit button (top-right of header) ──
    visual.Rect(win, width=EXIT_BTN_W, height=EXIT_BTN_H,
                pos=(EXIT_BTN_X, EXIT_BTN_Y),
                fillColor="#8B0000", lineColor="#FF4444", lineWidth=1.5).draw()
    visual.TextStim(win, text="END",
                    pos=(EXIT_BTN_X, EXIT_BTN_Y),
                    color="white", height=14, font="Arial Bold",
                    anchorHoriz="center", anchorVert="center").draw()

    # ── Chat messages ──
    visible = history[-5:]
    y = CHAT_AREA_TOP - 35
    for role, text in visible:
        h = draw_message_box(win, text, y, role,
                             accent_color=accent, profile=profile)
        y -= h + 18

    # ── Input bar (static stims) ──
    ss["hdr_div"].draw()
    ss["inp_bg"].draw()
    bar_y2 = -WIN_H//2 + INPUT_BAR_H//2
    field_w = WIN_W - 120
    border_col  = accent if is_typing else "#2A3550"
    field_color = "#0D1525" if is_typing else "#0A1020"
    if is_typing:
        visual.Rect(win, width=field_w+8, height=46, pos=(-20, bar_y2),
                    fillColor=accent, lineColor=None, opacity=0.08).draw()
    visual.Rect(win, width=field_w, height=40, pos=(-20, bar_y2),
                fillColor=field_color, lineColor=border_col, lineWidth=2).draw()
    if not typed:
        visual.TextStim(win, text="Type a message and press ENTER...",
                        pos=(-WIN_W//2+60, bar_y2), color="#3A4A6A", height=17,
                        font="Arial", anchorHoriz="left", anchorVert="center").draw()
    else:
        visual.TextStim(win, text=typed+"|", pos=(-WIN_W//2+60, bar_y2),
                        color="white", height=18, font="Arial",
                        anchorHoriz="left", anchorVert="center",
                        wrapWidth=field_w-40).draw()
    btn_x = WIN_W//2 - 36
    visual.Circle(win, radius=22, pos=(btn_x, bar_y2),
                  fillColor=accent if typed else "#1A2535", lineColor=None,
                  opacity=1.0 if typed else 0.5).draw()
    visual.TextStim(win, text="→", pos=(btn_x, bar_y2), color="white",
                    height=22, font="Arial Bold",
                    anchorHoriz="center", anchorVert="center").draw()

    win.flip()

# ─────────────────────────────────────────────────────────────
# 11. SHOW FULL-SCREEN MESSAGE
# ─────────────────────────────────────────────────────────────

def show_message(win, message, duration=2.0, color="white"):
    """Full-screen message with subtle background panel."""
    win.clearBuffer()
    # Background panel
    visual.Rect(win, width=700, height=200,
                pos=(0, 0), fillColor="#0D1525",
                lineColor=color, lineWidth=1.5, opacity=0.95).draw()
    visual.TextStim(win, text=message, color=color,
                    height=24, wrapWidth=640, font="Arial",
                    anchorHoriz="center", anchorVert="center").draw()
    win.flip()
    core.wait(duration)

# ─────────────────────────────────────────────────────────────
# 12. TEXT INPUT LOOP
# ─────────────────────────────────────────────────────────────

def _exit_btn_hit(mouse):
    """Return True if mouse was clicked inside the Exit button."""
    if not mouse.getPressed()[0]:
        return False
    mx, my = mouse.getPos()
    return (abs(mx - EXIT_BTN_X) <= EXIT_BTN_W // 2 and
            abs(my - EXIT_BTN_Y) <= EXIT_BTN_H // 2)
 
 
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

def save_chat_csv(chat_log, participant_id, agent_name):
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
                         "agent", "timestamp"])
        for i, (role, text) in enumerate(chat_log):
            writer.writerow([i + 1, role, text, pid, agent_name, timestamp])

    return filename


# ─────────────────────────────────────────────────────────────
# 16. ENTRY POINT
# ─────────────────────────────────────────────────────────────

def main():
    info   = get_experiment_info()
    chosen = info["Personality Agent"]
    pid    = info["Participant ID"].strip() or "unknown"

    win   = make_window()
    agent = ConversationalAgent(name=chosen)

    show_message(win,
        "Welcome!\n\nYou will now have a conversation\nwith an agent.\n\nPress any key to begin.",
        duration=0.1, color="white")
    event.waitKeys()

    chat_log = run_conversation(win, agent)

    # ── Save to CSV ──
    saved_path = save_chat_csv(chat_log, participant_id=pid, agent_name=chosen)
    print(f"\n✓ Chat saved → {saved_path}")
    show_message(win, "Thank you for participating!\n\nThe session has ended.",
                 duration=3.0, color="white")
    win.close()
    core.quit()


if __name__ == "__main__":
    main()
