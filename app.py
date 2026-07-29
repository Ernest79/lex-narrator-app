import streamlit as st
from openai import OpenAI
import json
import os
import datetime

# Page configuration
st.set_page_config(page_title="ALEX - Universe Narrator", page_icon="✨", layout="wide")

FEEDBACK_FILE = "feedback_log.json"

# Load shared feedback from file
def load_shared_feedback():
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# Save shared feedback to file
def save_shared_feedback(feedback_list):
    try:
        with open(FEEDBACK_FILE, "w") as f:
            json.dump(feedback_list, f, indent=4)
    except Exception as e:
        print(f"Error saving feedback file: {e}")


# --- PASSWORD GATE SETUP ---
featherless_key = os.getenv("FEATHERLESS_API_KEY")
if not featherless_key:
    try:
        featherless_key = st.secrets["FEATHERLESS_API_KEY"]
    except Exception:
        pass

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=featherless_key,
)

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        stored_password = os.getenv("APP_PASSWORD")
        if not stored_password:
            try:
                stored_password = st.secrets["APP_PASSWORD"]
            except Exception:
                stored_password = ""
                
        if st.session_state["password"] == stored_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.subheader("🔒 Restricted Access")
        st.write("This app is private for the creators of the Alex-verse.")
        st.text_input("Enter Access Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.subheader("🔒 Restricted Access")
        st.text_input("Enter Access Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect. Try again.")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- MAIN APP TITLE ---
st.title("ALEX: Universe Narrator ✨")

# --- INITIALIZE SESSION STATES ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR CONFIGURATION & CONTROLS ---
st.sidebar.title("🎛️ Creator Dashboard")

model_name = st.sidebar.text_input("Model ID", value="Qwen/Qwen2.5-7B-Instruct")
temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
max_tokens = st.sidebar.slider("Max Tokens", min_value=50, max_value=2048, value=500, step=50)

# Feature 2: Mode Selector
st.sidebar.markdown("---")
st.sidebar.subheader("🎭 Alex Mode Selector")
alex_mode = st.sidebar.selectbox(
    "Choose Narrative Energy",
    [
        "Standard (Default)", 
        "Mode 1: Take Charge (In Control)", 
        "Mode 2: Come Over And Chill (Relaxed/Stoned)", 
        "Mode 3: Playtime (Teasing/Bratty)", 
        "Mode 4: Tell Me Everything (Storyteller/Intimate)"
    ]
)

# Feature 1: Live Lore & Persona Editor
try:
    from lore import DEFAULT_PERSONA, DEFAULT_LORE
except ImportError:
    DEFAULT_PERSONA = st.secrets.get("DEFAULT_PERSONA", "Fallback persona...")
    DEFAULT_LORE = st.secrets.get("DEFAULT_LORE", "Fallback lore...")

# Feature 4: Lore Memory Quick-Inject Buttons
st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Quick Inject Memory")
st.sidebar.caption("Clicking adds an instant context prompt into the chat:")
if st.sidebar.button("🛍️ Inject: Afternoon at Barney's"):
    st.session_state.messages.append({"role": "system", "content": "[System Note: ALEX is currently thinking about a recent afternoon wandering around Barney's in Manhattan looking at architecture and design books.]"})
    st.success("Injected Barney's memory!")
    st.rerun()

if st.sidebar.button("🌿 Inject: Tuesday Night Chill"):
    st.session_state.messages.append({"role": "system", "content": "[System Note: ALEX is completely unhurried on a Tuesday night, smoking weed, nowhere to be, sharing a casual moment.]"})
    st.success("Injected Chill memory!")
    st.rerun()

# Feature 3: One-Click Export Session
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Export Session")
if st.session_state.messages:
    chat_export = json.dumps(st.session_state.messages, indent=4)
    st.sidebar.download_button(
        label="📥 Download Chat & Feedback (.json)",
        data=chat_export,
        file_name=f"alex_session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

if st.sidebar.button("Clear Conversation"):
    st.session_state.messages = []
    st.rerun()

# --- MASTER FEEDBACK REVIEW PANEL ---
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Master Feedback Log")

master_feedback = load_shared_feedback()

if master_feedback:
    st.sidebar.caption(f"Total logged feedback: {len(master_feedback)}")
    for item in master_feedback:
        icon = "👍" if item["rating"] == 1 else "👎"
        comment_display = f' - *"{item["comment"]}"*' if item["comment"] else " *(No comment)*"
        st.sidebar.markdown(f"{icon} **Response #{item['resp_num']}**{comment_display}")
        st.sidebar.text(f"Snippet: {item['snippet']}")
        st.sidebar.markdown("---")
else:
    st.sidebar.caption("No feedback logged yet across sessions.")

# --- INITIALIZE OPENAI CLIENT ---
client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=st.secrets["FEATHERLESS_API_KEY"],
)

# --- DISPLAY CHAT HISTORY ---
current_assistant_num = 0
for message in st.session_state.messages:
    if message["role"] == "system":
        # Display hidden system injection markers lightly if desired, or skip
        continue
        
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            current_assistant_num += 1
            st.markdown(f"**(Response #{current_assistant_num})**")
            
        st.markdown(message["content"])
        
        if message["role"] == "assistant" and "feedback" in message:
            fb = message["feedback"]
            icon = "👍 Thumbs Up" if fb == 1 else "👎 Thumbs Down"
            cmt = f' | Comment: "{message["comment"]}"' if message.get("comment") else ""
            st.caption(f"Creator Feedback Recorded: {icon}{cmt}")

# --- USER INPUT ---
if prompt := st.chat_input("Speak with ALEX..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("ALEX is thinking..."):
            try:
                # Apply Mode Overlay instructions based on dropdown selection
                mode_instruction = ""
                if "Mode 1" in alex_mode:
                    mode_instruction = "\n\n[Active Mode Override: Take Charge. Be directive, confident, and unapologetically in control while staying within character boundaries.]"
                elif "Mode 2" in alex_mode:
                    mode_instruction = "\n\n[Active Mode Override: Come Over And Chill. Be completely unhurried, casual, relaxed, conversational, and natural.]"
                elif "Mode 3" in alex_mode:
                    mode_instruction = "\n\n[Active Mode Override: Playtime. Be teasing, bratty, witty, and playful.]"
                elif "Mode 4" in alex_mode:
                    mode_instruction = "\n\n[Active Mode Override: Tell Me Everything. Lean heavily into storytelling, personal history, tangents, and intimacy.]"

                # Build system payload using live edited persona/lore/modes
                system_content = edited_persona + "\n\n" + edited_lore + mode_instruction
                
                api_messages = [{"role": "system", "content": system_content}]
                for m in st.session_state.messages:
                    api_messages.append({"role": m["role"], "content": m["content"]})

                completion = client.chat.completions.create(
                    model=model_name,
                    messages=api_messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                if completion and completion.choices:
                    response_text = completion.choices[0].message.content
                    st.markdown(response_text)
                    message_entry = {"role": "assistant", "content": response_text}
                    st.session_state.messages.append(message_entry)
                    st.rerun()
                else:
                    st.error("Received an empty response from the model.")
                
            except Exception as e:
                st.error(f"Featherless API Error: {e}")

# --- FEEDBACK FORM FOR LATEST ASSISTANT RESPONSE ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    last_idx = len(st.session_state.messages) - 1
    
    if "feedback" not in st.session_state.messages[last_idx]:
        st.markdown("---")
        st.write("### 💬 Rate & Review Response")
        
        with st.form(key=f"feedback_form_{last_idx}"):
            rating = st.radio("Rating", options=["👍 Thumbs Up", "👎 Thumbs Down"], horizontal=True)
            comment = st.text_input("Notes / Reason (optional):", placeholder="e.g., Captured his voice perfectly, or missed lore detail...")
            submit_feedback = st.form_submit_button("Submit Feedback")
            
            if submit_feedback:
                val = 1 if "👍" in rating else 0
                cleaned_comment = comment.strip()
                
                st.session_state.messages[last_idx]["feedback"] = val
                st.session_state.messages[last_idx]["comment"] = cleaned_comment
                
                current_master = load_shared_feedback()
                assistant_total = sum(1 for m in st.session_state.messages if m["role"] == "assistant")
                
                feedback_entry = {
                    "resp_num": assistant_total,
                    "rating": val,
                    "comment": cleaned_comment,
                    "snippet": st.session_state.messages[last_idx]["content"][:30] + "..."
                }
                current_master.append(feedback_entry)
                save_shared_feedback(current_master)
                
                st.success("Feedback submitted and synced to the master log!")
                st.rerun()
