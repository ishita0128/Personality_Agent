"""
Personality-Based Conversational Agents — PsychoPy
====================================================
Proper chat-app UI: robot avatars drawn with shapes, rounded message
boxes, header bar, input field. Swap respond() with your LLM backend.

Requirements:  pip install psychopy
"""

from psychopy import visual, core, event, gui
import math
import csv
import os
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# 1. PERSONALITY DEFINITIONS
# ─────────────────────────────────────────────────────────────

PERSONALITIES = {
    "Friendly": {
        "color":    "#4CAF50",
        "bg_color": "#1B3A2A",
        "avatar":   "😊",
        "greeting": "Hey there! So great to meet you! How can I help today?",
        "responses": [
            "That's a wonderful thought! Tell me more.",
            "I love that you brought this up — it's so important!",
            "You're doing amazing. Let's explore this together!",
            "Great question! Here's what I think… [placeholder]",
        ],
        "farewell": "It was so nice chatting with you. Take care!",
    },
    "Analytical": {
        "color":    "#2196F3",
        "bg_color": "#0D1F3A",
        "avatar":   "🔍",
        "greeting": "Hello. I am ready to process your query. Please proceed.",
        "responses": [
            "Based on available data, the most probable answer is… [placeholder]",
            "Let me break this down systematically: [placeholder]",
            "There are three key factors to consider here: [placeholder]",
            "The evidence suggests… [placeholder]",
        ],
        "farewell": "Session complete. Data recorded. Goodbye.",
    },
    "Empathetic": {
        "color":    "#E91E63",
        "bg_color": "#3A0D1F",
        "avatar":   "💗",
        "greeting": "Hello. I'm here with you. How are you feeling today?",
        "responses": [
            "I hear you. That sounds really meaningful.",
            "It makes sense that you feel that way.",
            "Thank you for sharing — that took courage.",
            "I want to understand more. Can you tell me how that felt?",
        ],
        "farewell": "Thank you for being open with me. I'm always here.",
    },
    "Humorous": {
        "color":    "#FF9800",
        "bg_color": "#3A2400",
        "avatar":   "😄",
        "greeting": "Well, well, well… look who showed up! Ready to have some fun?",
        "responses": [
            "Ha! Great point — almost as good as mine. [placeholder]",
            "I'd explain it, but then we'd both be confused. [placeholder]",
            "Why did the researcher cross the road? For better data! [placeholder]",
            "Oh, that's a big topic. Good thing I brought snacks. [placeholder]",
        ],
        "farewell": "Bye! Try not to miss me too much.",
    },
    "Authoritative": {
        "color":    "#9C27B0",
        "bg_color": "#1E0A2E",
        "avatar":   "📢",
        "greeting": "Welcome. I will guide you through this session. Pay attention.",
        "responses": [
            "The answer is clear: [placeholder]",
            "You should focus on the following: [placeholder]",
            "This is the most effective approach: [placeholder]",
            "Do not overlook this critical point: [placeholder]",
        ],
        "farewell": "Session concluded. Apply what you have learned.",
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
        from groq import Groq

        system_prompts = {
        "Friendly":      "You are warm, supportive and encouraging. Keep responses short.",
        "Analytical":    "You are logical, precise and data-driven. Be systematic and concise.",
        "Empathetic":    "You are emotionally attuned and reflective. Respond with care.",
        "Humorous":      "You are playful, witty and light-hearted. Keep it fun.",
        "Authoritative": "You are confident, direct and instructive. Be clear and commanding.",
    }

        client = Groq(api_key="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")

        if not hasattr(self, 'chat_history'):
          self.chat_history = []

        self.chat_history.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompts[self.name]},
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

BG_IDLE   = hex_to_norm("#1A1A2E")
BG_TYPING = hex_to_norm("#1E2A3A")
BG_FLASH  = hex_to_norm("#2E4060")

# ─────────────────────────────────────────────────────────────
# 5. WINDOW
# ─────────────────────────────────────────────────────────────

WIN_W, WIN_H = 920, 680

def make_window():
    return visual.Window(
        size=(WIN_W, WIN_H), color=BG_IDLE,
        units="pix", fullscr=False,
        title="Personality Agent Chat",
    )

# ─────────────────────────────────────────────────────────────
# 6. ROBOT AVATAR  (drawn entirely from PsychoPy primitives)
# ─────────────────────────────────────────────────────────────

def draw_robot_avatar(win, cx, cy, accent, size=1.0):
    """
    Draw a friendly robot face centred at (cx, cy).
    accent  = hex colour string for the head circle & highlights.
    size    = scale factor (1.0 = standard ~36 px radius).
    """
    R  = 36 * size          # outer circle radius
    ac = accent             # accent hex
    dk = "#0D1520"          # dark shade

    # ── Outer circle (teal/accent) ──
    visual.Circle(win, radius=R, pos=(cx, cy),
                  fillColor=ac, lineColor=None).draw()

    # ── White face panel ──
    visual.Rect(win, width=R*1.1, height=R*0.85,
                pos=(cx, cy - R*0.05),
                fillColor="white", lineColor=None,
                ori=0).draw()

    # ── Rounded top of face (white arc illusion via circle) ──
    visual.Circle(win, radius=R*0.56, pos=(cx, cy + R*0.23),
                  fillColor="white", lineColor=None).draw()

    # ── Eyes (dark circles with cyan pupils) ──
    for ex in (-R*0.28, R*0.28):
        visual.Circle(win, radius=R*0.18, pos=(cx+ex, cy+R*0.12),
                      fillColor=dk, lineColor=None).draw()
        visual.Circle(win, radius=R*0.09, pos=(cx+ex, cy+R*0.12),
                      fillColor="#00BFFF", lineColor=None).draw()
        # eye glint
        visual.Circle(win, radius=R*0.04, pos=(cx+ex+R*0.06, cy+R*0.18),
                      fillColor="white", lineColor=None).draw()

    # ── Smile (arc approximated by small circles) ──
    for ang in range(-50, 55, 12):
        rad = math.radians(ang)
        sx  = cx + R*0.30 * math.sin(rad)
        sy  = cy - R*0.08 - R*0.13 * math.cos(rad)
        visual.Circle(win, radius=R*0.035, pos=(sx, sy),
                      fillColor=dk, lineColor=None).draw()

    # ── Antenna ──
    visual.Rect(win, width=R*0.07, height=R*0.35,
                pos=(cx, cy + R*0.92),
                fillColor=dk, lineColor=None).draw()
    visual.Circle(win, radius=R*0.12, pos=(cx, cy + R*1.12),
                  fillColor=ac, lineColor=dk, lineWidth=1.5).draw()

    # ── Ears / side panels ──
    for ex in (-R*0.88, R*0.88):
        visual.Rect(win, width=R*0.22, height=R*0.38,
                    pos=(cx+ex, cy - R*0.05),
                    fillColor=dk, lineColor=None).draw()

    # ── Body stub ──
    visual.Rect(win, width=R*0.7, height=R*0.28,
                pos=(cx, cy - R*0.72),
                fillColor="white", lineColor=dk, lineWidth=1).draw()
    # body dots
    for bx in (-R*0.18, 0, R*0.18):
        visual.Circle(win, radius=R*0.06, pos=(cx+bx, cy - R*0.72),
                      fillColor=dk, lineColor=None).draw()


def draw_user_avatar(win, cx, cy, size=1.0):
    """Simple person silhouette avatar for the user."""
    R  = 36 * size
    bg = "#2D4A6A"

    # Background circle
    visual.Circle(win, radius=R, pos=(cx, cy),
                  fillColor=bg, lineColor=None).draw()
    # Head
    visual.Circle(win, radius=R*0.32, pos=(cx, cy + R*0.22),
                  fillColor="#A0C4E8", lineColor=None).draw()
    # Shoulders
    visual.Circle(win, radius=R*0.55, pos=(cx, cy - R*0.55),
                  fillColor="#A0C4E8", lineColor=None).draw()
    # Clip overflow with background ring
    visual.Circle(win, radius=R, pos=(cx, cy),
                  fillColor=None, lineColor=BG_IDLE, lineWidth=3).draw()

# ─────────────────────────────────────────────────────────────
# 7. CHAT MESSAGE BOX
# ─────────────────────────────────────────────────────────────

CHAT_BOX_W   = 560    # max bubble width
CHAT_BOX_H   = 52     # default single-line height (grows with text)
AVATAR_R     = 36     # avatar radius (matches draw_robot_avatar R)
AVATAR_GAP   = 10     # gap between avatar edge and bubble

def draw_message_box(win, text, y_pos, role, accent_color, profile):
    """
    Draw a proper rounded-rect chat bubble with avatar beside it.
    role = "agent" → left-aligned robot avatar + coloured bubble
    role = "user"  → right-aligned person avatar + grey bubble
    """
    AV_CX_AGENT = -WIN_W//2 + AVATAR_R + 14
    AV_CX_USER  =  WIN_W//2 - AVATAR_R - 14

    # ── Estimate text height to size the box ──
    # rough: each ~55 chars wraps to a new line at our font size
    chars_per_line = 52
    lines = max(1, math.ceil(len(text) / chars_per_line))
    box_h = 38 + lines * 22

    if role == "agent":
        av_cx      = AV_CX_AGENT
        box_left   = av_cx + AVATAR_R + AVATAR_GAP
        box_cx     = box_left + CHAT_BOX_W // 2
        box_color  = accent_color
        txt_color  = "#FFFFFF"
        txt_anchor = "left"
        txt_x      = box_left + 14
    else:
        av_cx      = AV_CX_USER
        box_right  = av_cx - AVATAR_R - AVATAR_GAP
        box_cx     = box_right - CHAT_BOX_W // 2
        box_color  = "#2D3748"
        txt_color  = "#E2E8F0"
        txt_anchor = "left"
        txt_x      = box_cx - CHAT_BOX_W // 2 + 14

    # ── Shadow layer ──
    visual.Rect(win, width=CHAT_BOX_W + 6, height=box_h + 6,
                pos=(box_cx, y_pos - 3),
                fillColor="#000000", lineColor=None,
                opacity=0.35).draw()

    # ── Bubble background ──
    visual.Rect(win, width=CHAT_BOX_W, height=box_h,
                pos=(box_cx, y_pos),
                fillColor=box_color, lineColor=None,
                opacity=1.0).draw()

    # ── Message text ──
    visual.TextStim(win, text=text,
                    pos=(txt_x, y_pos),
                    color=txt_color, height=18,
                    wrapWidth=CHAT_BOX_W - 28,
                    font="Arial",
                    anchorHoriz="left",
                    anchorVert="center").draw()

    # ── Avatar ──
    if role == "agent":
        draw_robot_avatar(win, av_cx, y_pos, accent=accent_color)
    else:
        draw_user_avatar(win, av_cx, y_pos)

    return box_h   # return actual height used

# ─────────────────────────────────────────────────────────────
# 8. HEADER BAR
# ─────────────────────────────────────────────────────────────

def draw_header(win, agent_name, accent):
    """Top bar showing agent name."""
    bar_y = WIN_H // 2 - 30
    visual.Rect(win, width=WIN_W, height=60,
                pos=(0, bar_y),
                fillColor=accent, lineColor=None, opacity=0.9).draw()
    visual.TextStim(win, text=f"  🤖  {agent_name} Agent",
                    pos=(-WIN_W//2 + 20, bar_y),
                    color="white", height=22, font="Arial Bold",
                    anchorHoriz="left", anchorVert="center").draw()

# ─────────────────────────────────────────────────────────────
# 9. INPUT BAR
# ─────────────────────────────────────────────────────────────

INPUT_Y      = -WIN_H // 2 + 38
INPUT_BAR_H  = 56

def draw_input_bar(win, typed, accent, is_typing):
    """Bottom input bar with rounded field."""
    bar_y = -WIN_H // 2 + INPUT_BAR_H // 2

    # Background strip
    visual.Rect(win, width=WIN_W, height=INPUT_BAR_H,
                pos=(0, bar_y),
                fillColor="#12121F", lineColor=None).draw()

    # Input field box
    field_color = accent if is_typing else "#2D3748"
    border_col  = accent if is_typing else "#4A5568"
    visual.Rect(win, width=WIN_W - 80, height=36,
                pos=(0, bar_y),
                fillColor=field_color if is_typing else "#1E2535",
                lineColor=border_col, lineWidth=2).draw()

    # Typed text + blinking cursor
    display = typed + "|"
    visual.TextStim(win, text=display,
                    pos=(-WIN_W//2 + 56, bar_y),
                    color="white" if typed else "#718096",
                    height=18, font="Arial",
                    anchorHoriz="left", anchorVert="center",
                    wrapWidth=WIN_W - 120).draw()

    # Hint text when empty
    if not typed:
        visual.TextStim(win, text="Type a message and press ENTER...",
                        pos=(-WIN_W//2 + 56, bar_y),
                        color="#4A5568", height=17, font="Arial",
                        anchorHoriz="left", anchorVert="center").draw()

# ─────────────────────────────────────────────────────────────
# 10. FULL SCENE REDRAW
# ─────────────────────────────────────────────────────────────

CHAT_AREA_TOP = WIN_H // 2 - 70    # below header
CHAT_AREA_BOT = -WIN_H // 2 + 70   # above input bar

def redraw_scene(win, history, profile, typed, is_typing):
    win.clearBuffer()

    # Header
    draw_header(win, profile["name"], profile["color"])

    # Chat messages — lay out from top, newest last
    visible = history[-5:]
    y = CHAT_AREA_TOP - 30
    for role, text in visible:
        h = draw_message_box(win, text, y, role,
                             accent_color=profile["color"],
                             profile=profile)
        y -= h + 20   # spacing between bubbles

    # Input bar
    draw_input_bar(win, typed, profile["color"], is_typing)

    win.flip()

# ─────────────────────────────────────────────────────────────
# 11. SHOW FULL-SCREEN MESSAGE
# ─────────────────────────────────────────────────────────────

def show_message(win, message, duration=2.0, color="white"):
    win.clearBuffer()
    visual.TextStim(win, text=message, color=color,
                    height=24, wrapWidth=700, font="Arial").draw()
    win.flip()
    core.wait(duration)

# ─────────────────────────────────────────────────────────────
# 12. TEXT INPUT LOOP
# ─────────────────────────────────────────────────────────────

def get_text_input(win, history, profile):
    typed     = ""
    is_typing = False

    while True:
        keys = event.getKeys(keyList=None)
        for key in keys:
            if key == "return":
                # Flash on send
                win.color = BG_FLASH
                redraw_scene(win, history, profile, typed, True)
                core.wait(0.10)
                win.color = BG_IDLE
                return typed.strip()
            elif key == "escape":
                win.color = BG_IDLE
                return None
            elif key == "backspace":
                typed = typed[:-1]
            elif key == "space":
                typed += " "
            elif len(key) == 1:
                typed += key

        new_typing = len(typed) > 0
        if new_typing != is_typing:
            win.color = BG_TYPING if new_typing else BG_IDLE
            is_typing = new_typing

        redraw_scene(win, history, profile, typed, is_typing)

# ─────────────────────────────────────────────────────────────
# 13. CONVERSATION LOOP
# ─────────────────────────────────────────────────────────────

def run_conversation(win, agent, n_turns=6):
    history = []
    profile = {**agent.profile, "name": agent.name}

    history.append(("agent", agent.greet()))

    for _ in range(n_turns):
        user_text = get_text_input(win, history, profile)
        if user_text is None or user_text.lower() in ("quit", "exit", "bye"):
            break
        if not user_text:
            continue

        history.append(("user", user_text))

        reply = agent.respond(user_text)
        history.append(("agent", reply))

    win.color = BG_IDLE
    show_message(win, agent.farewell(), duration=3.0,
                 color=agent.profile["color"])
    return history

# ─────────────────────────────────────────────────────────────
# 14. SAVE CHAT TO CSV
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
# 15. ENTRY POINT
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
