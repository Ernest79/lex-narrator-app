import streamlit as st
from openai import OpenAI
import json
import os
import datetime

# --- SECURE LORE IMPORT & FALLBACK ---
try:
    from lore import DEFAULT_PERSONA, DEFAULT_LORE
except ImportError:
    DEFAULT_PERSONA = st.secrets.get("DEFAULT_PERSONA", "Default persona fallback...")
    DEFAULT_LORE = st.secrets.get("DEFAULT_LORE", "Default lore fallback...")

# Page configuration
st.set_page_config(page_title="ALEX - Universe Narrator", page_icon="✨", layout="wide")

# --- CUSTOM CSS & THEME STYLING ---
st.markdown("""
<style>
    /* Main Background & Theme Colors */
    .stApp {
        background: linear-gradient(180deg, #3B4D66 0%, #0D121A 50%, #000000 95%);
        color: #FAFAFA;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0D121A;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Matte Card Fills & Glass Overlays */
    div.stExpander, .stChatMessage, div.stForm {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
    }
    
    /* Profile Tag Buttons Container */
    .tag-container {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

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
            del st.session_state["password"]
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

# --- INITIALIZE OPENAI CLIENT ---
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

# --- MAIN APP HEADER & IMAGE SECTION ---
st.title("ALEX: Universe Narrator ✨")

# Image posting / upload section below title
with st.expander("🖼️ Universe Image Banner / Upload", expanded=False):
    uploaded_image = st.file_uploader("Upload profile or universe reference image", type=["png", "jpg", "jpeg"])
    if uploaded_image is not None:
        st.image(uploaded_image, use_container_width=True, caption="Active Universe Reference")
    else:
        st.caption("Upload an image to anchor the current scene or persona vibe.")

# --- INITIALIZE SESSION STATES ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR CONFIGURATION (DROPDOWNS & FEEDBACK ON LEFT) ---
st.sidebar.title("🎛️ Creator Dashboard")

# Dropdown 1: Model & Generation Settings
with st.sidebar.expander("⚙️ Model Settings", expanded=False):
    model_name = st.text_input("Model ID", value="Qwen/Qwen2.5-7B-Instruct")
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    max_tokens = st.slider("Max Tokens", min_value=50, max_value=2048, value=500, step=50)

# Dropdown 2: Narrative Modes
with st.sidebar.expander("🎭 Narrative Energy Modes", expanded=False):
    alex_mode = st.selectbox(
        "Choose Mode",
        [
            "Standard (Default)", 
            "Mode 1: Take Charge (In Control)", 
            "Mode 2: Come Over And Chill (Relaxed/Stoned)", 
            "Mode 3: Playtime (Teasing/Bratty)", 
            "Mode 4: Tell Me Everything (Storyteller/Intimate)"
        ]
    )

# Dropdown 3: Live Lore & Persona Editor
with st.sidebar.expander("📝 Live Persona & Lore Editor", expanded=False):
    edited_persona = st.text_area("Base Persona", value=DEFAULT_PERSONA, height=100)
    edited_lore = st.text_area("Universe Lore", value=DEFAULT_LORE, height=150)

# Dropdown 4: Session Utilities & Export
with st.sidebar.expander("💾 Session Tools", expanded=False):
    if st.session_state.messages:
        chat_export = json.dumps(st.session_state.messages, indent=4)
        st.download_button(
            label="📥 Download Chat (.json)",
            data=chat_export,
            file_name=f"alex_session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

# --- MASTER FEEDBACK REVIEW PANEL (KEPT ON THE LEFT SIDEBAR) ---
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


# --- PROFILE-STYLE TAG BUTTONS AT THE TOP ---
st.markdown("##### ⚡ Quick Memory Tags")
tag_col1, tag_col2, tag_col3 = st.columns(3)

with tag_col1:
    if st.button("🛍️ Barney's Afternoon", use_container_width=True):
        st.session_state.messages.append({"role": "system", "content": "[System Note: ALEX is currently thinking about a recent afternoon wandering around Barney's in Manhattan looking at architecture and design books.]"})
        st.success("Injected Barney's memory!")
        st.rerun()

with tag_col2:
    if st.button("🌿 Tuesday Chill", use_container_width=True):
        st.session_state.messages.append({"role": "system", "content": "[System Note: ALEX is completely unhurried on a Tuesday night, smoking weed, nowhere to be, sharing a casual moment.]"})
        st.success("Injected Chill memory!")
        st.rerun()

with tag_col3:
    if st.button("✈️ Travel Mode", use_container_width=True):
        st.session_state.messages.append({"role": "system", "content": "[System Note: ALEX is currently away on a corporate work travel trip, texting from a hotel room.]"})
        st.success("Injected Travel memory!")
        st.rerun()

st.markdown("---")

# --- DISPLAY CHAT HISTORY ---
current_assistant_num = 0
for message in st.session_state.messages:
    if message["role"] == "system":
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