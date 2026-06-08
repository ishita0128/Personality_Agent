"""
Personality-Based Conversational Agents — PsychoPy Placeholder
================================================================
A scaffold for running a multi-agent conversational experiment in PsychoPy.
Swap the placeholder response logic with your actual NLP/LLM backend.

Personalities implemented:
  1. Friendly      – warm, supportive, encouraging
  2. Analytical    – logical, precise, data-driven
  3. Empathetic    – emotionally attuned, reflective
  4. Humorous      – playful, light-hearted, witty
  5. Authoritative – confident, direct, instructive

Requirements:
    pip install psychopy
"""

from psychopy import visual, core, event, gui
import random

# ─────────────────────────────────────────────
# 1. PERSONALITY DEFINITIONS
# ─────────────────────────────────────────────

PERSONALITIES = {
    "Friendly": {
        "color": "#4CAF50",
        "avatar": "😊",
        "greeting": "Hey there! So great to meet you! How can I help today?",
        "responses": [
            "That's a wonderful thought! Tell me more.",
            "I love that you brought this up — it's so important!",
            "You're doing amazing. Let's explore this together!",
            "Great question! Here's what I think… [placeholder]",
        ],
        "farewell": "It was so nice chatting with you. Take care! 😊",
    },
    "Analytical": {
        "color": "#2196F3",
        "avatar": "🔍",
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
        "color": "#E91E63",
        "avatar": "💗",
        "greeting": "Hello. I'm here with you. How are you feeling today?",
        "responses": [
            "I hear you. That sounds really meaningful.",
            "It makes sense that you feel that way. Let's sit with that a moment.",
            "Thank you for sharing — that took courage.",
            "I want to understand more. Can you tell me how that felt? [placeholder]",
        ],
        "farewell": "Thank you for being open with me. I'm always here. 💗",
    },
    "Humorous": {
        "color": "#FF9800",
        "avatar": "😄",
        "greeting": "Well, well, well… look who showed up! Ready to have some fun?",
        "responses": [
            "Ha! Great point — almost as good as mine. [placeholder]",
            "I'd explain it, but then we'd both be confused. [placeholder]",
            "Why did the researcher cross the road? For better data! Anyway… [placeholder]",
            "Oh, that's a big topic. Good thing I brought snacks. [placeholder]",
        ],
        "farewell": "Bye! Try not to miss me too much. 😄",
    },
    "Authoritative": {
        "color": "#9C27B0",
        "avatar": "📢",
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

# ─────────────────────────────────────────────
# 2. EXPERIMENT SETTINGS (via GUI dialog)
# ─────────────────────────────────────────────

def get_experiment_info():
    """Show a dialog to collect participant info and choose personality."""
    dlg_info = {
        "Participant ID": "",
        "Age": "",
        "Personality Agent": list(PERSONALITIES.keys()),
        "Condition": ["single_agent", "counterbalanced", "random"],
    }
    dlg = gui.DlgFromDict(
        dictionary=dlg_info,
        title="Personality Agent Experiment",
        order=["Participant ID", "Age", "Personality Agent", "Condition"],
    )
    if dlg.OK:
        return dlg_info
    else:
        core.quit()

# ─────────────────────────────────────────────
# 3. AGENT CLASS
# ─────────────────────────────────────────────

class ConversationalAgent:
    """Encapsulates a single personality agent."""

    def __init__(self, name: str):
        if name not in PERSONALITIES:
            raise ValueError(f"Unknown personality: {name}")
        self.name = name
        self.profile = PERSONALITIES[name]
        self.turn = 0

    def greet(self) -> str:
        return self.profile["greeting"]

    def respond(self, user_input: str = "") -> str:
        """
        Placeholder response logic.
        Replace with API call or NLP model output as needed.
        """
        # ── TODO: plug in your LLM / response generation here ──
        # e.g.: return call_openai(user_input, system_prompt=self.profile["system_prompt"])
        self.turn += 1
        responses = self.profile["responses"]
        return responses[self.turn % len(responses)]

    def farewell(self) -> str:
        return self.profile["farewell"]


# ─────────────────────────────────────────────
# 4. PSYCHOPY DISPLAY HELPERS
# ─────────────────────────────────────────────

def make_window():
    return visual.Window(
        size=(900, 650),
        color="#1A1A2E",
        units="pix",
        fullscr=False,
        title="Personality Agent Chat",
    )


def draw_chat_bubble(win, text, y_pos, role="agent", agent_color="#FFFFFF"):
    """Draw a simple chat bubble for agent or user."""
    bg_color = agent_color if role == "agent" else "#334155"
    x_offset = -180 if role == "agent" else 180

    bubble = visual.Rect(
        win, width=520, height=70, pos=(x_offset, y_pos),
        fillColor=bg_color, lineColor=None, opacity=0.85
    )
    label = visual.TextStim(
        win, text=text, pos=(x_offset, y_pos),
        color="white", height=18, wrapWidth=490,
        font="Courier New"
    )
    bubble.draw()
    label.draw()


def show_message(win, message, duration=2.0, color="white"):
    """Display a centred message for a fixed duration."""
    stim = visual.TextStim(
        win, text=message, color=color,
        height=22, wrapWidth=700, font="Courier New"
    )
    stim.draw()
    win.flip()
    core.wait(duration)


def get_text_input(win, prompt="You: "):
    """Simple keyboard text input loop."""
    typed = ""
    prompt_stim = visual.TextStim(
        win, text=prompt + "_", pos=(0, -240),
        color="#A0AEC0", height=20, font="Courier New"
    )
    while True:
        keys = event.getKeys(keyList=None)
        for key in keys:
            if key == "return":
                return typed.strip()
            elif key == "escape":
                return None
            elif key == "backspace":
                typed = typed[:-1]
            elif len(key) == 1:
                typed += key
        prompt_stim.text = prompt + typed + "_"
        prompt_stim.draw()
        win.flip()


# ─────────────────────────────────────────────
# 5. MAIN EXPERIMENT LOOP
# ─────────────────────────────────────────────

def run_conversation(win, agent: ConversationalAgent, n_turns: int = 5):
    """Run a multi-turn conversation with the agent."""
    history = []  # list of (role, text) tuples
    profile = agent.profile

    # Greeting
    greeting = agent.greet()
    history.append(("agent", f"{profile['avatar']} {greeting}"))

    for _ in range(n_turns):
        # ── Render chat history ──
        win.clearBuffer()
        y_start = 200
        for role, text in history[-6:]:          # show last 6 turns
            draw_chat_bubble(win, text, y_start, role=role,
                             agent_color=profile["color"])
            y_start -= 90

        instruction = visual.TextStim(
            win,
            text="Type your message and press ENTER  |  ESC to end",
            pos=(0, -290), color="#64748B", height=16, font="Courier New"
        )
        instruction.draw()
        win.flip()

        # ── Get user input ──
        user_text = get_text_input(win, prompt="You: ")
        if user_text is None or user_text.lower() in ("quit", "exit", "bye"):
            break
        if not user_text:
            continue

        history.append(("user", f"You: {user_text}"))

        # ── Agent responds ──
        agent_reply = agent.respond(user_text)
        history.append(("agent", f"{profile['avatar']} {agent_reply}"))

    # Farewell
    farewell_text = agent.farewell()
    show_message(win, farewell_text, duration=3.0, color=profile["color"])
    return history


# ─────────────────────────────────────────────
# 6. ENTRY POINT
# ─────────────────────────────────────────────

def main():
    # 6a. Collect experiment info
    info = get_experiment_info()
    participant_id = info["Participant ID"]
    condition = info["Condition"]
    chosen_personality = info["Personality Agent"]

    # 6b. Resolve agent order based on condition
    if condition == "random":
        chosen_personality = random.choice(list(PERSONALITIES.keys()))
    elif condition == "counterbalanced":
        # TODO: implement Latin-square counterbalancing per participant
        pass  # placeholder: falls back to chosen_personality from dialog

    # 6c. Create window and agent
    win = make_window()
    agent = ConversationalAgent(name=chosen_personality)

    # 6d. Welcome screen
    show_message(
        win,
        f"Welcome, Participant {participant_id}!\n\n"
        f"You will now chat with the  «{chosen_personality}»  agent.\n\n"
        "Press any key to begin.",
        duration=0.1,
        color="white",
    )
    event.waitKeys()

    # 6e. Run the conversation
    chat_log = run_conversation(win, agent, n_turns=6)

    # 6f. Save log (placeholder — replace with proper data handler)
    print("\n─── Chat Log ───")
    for role, text in chat_log:
        print(f"[{role.upper()}]  {text}")

    # 6g. End screen
    show_message(
        win,
        "Thank you for participating!\n\nThe session has ended.",
        duration=3.0,
        color="white",
    )
    win.close()
    core.quit()


if __name__ == "__main__":
    main()
