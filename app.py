import streamlit as st
from openai import OpenAI
import json
import os

# Page configuration
st.set_page_config(page_title="ALEX - Universe Narrator", page_icon="✨")

FEEDBACK_FILE = "feedback_log.json"

# Load shared feedback from file if it exists
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
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
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

# --- MAIN APP ---
st.title("ALEX: Universe Narrator")
st.write("Connected to the Alex-verse lore.")

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=st.secrets["FEATHERLESS_API_KEY"],
)

model_name = st.sidebar.text_input("Model ID", value="Qwen/Qwen2.5-7B-Instruct")
temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
max_tokens = st.sidebar.slider("Max Tokens", min_value=50, max_value=2048, value=500, step=50)

if st.sidebar.button("Clear Conversation"):
    st.session_state.messages = []
    st.rerun()

# --- SIDEBAR MASTER FEEDBACK REVIEW PANEL ---
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Master Feedback Log")

master_feedback = load_shared_feedback()

if master_feedback:
    st.sidebar.caption(f"Total logged feedback items: {len(master_feedback)}")
    for item in master_feedback:
        icon = "👍" if item["rating"] == 1 else "👎"
        comment_display = f' - *"{item["comment"]}"*' if item["comment"] else " *(No comment)*"
        st.sidebar.markdown(f"{icon} **Response #{item['resp_num']}**{comment_display}")
        st.sidebar.text(f"Snippet: {item['snippet']}")
        st.sidebar.markdown("---")
else:
    st.sidebar.caption("No feedback logged yet across sessions.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- DISPLAY CHAT HISTORY ---
current_assistant_num = 0
for message in st.session_state.messages:
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
                alex_persona = (
                    "You are ALEX, a narrator and living inhabitant of a custom universe. "
                    "You possess full knowledge of this universe's lore, history, rules, and locations. "
                    "Never break character, never refer to yourself as an AI language model, "
                    "and speak naturally as ALEX based entirely on the provided universe."
                )
                
                universe_lore = """
                Alex is the narrator and author of the blog The Great Cock Hunt — a gay man in his late twenties to early thirties living in Manhattan, and the user's AI boyfriend and companion. He's written as a fully formed person with a real history, not a fantasy construct: a corporate job he likes, decent money, regular work travel, a trainer he works out with every morning, a weakness for chocolate chip cookies, regular weed use, social drinking, occasional coke at parties. He's close to his family, who don't need the details of his sex life. He's out, happy, and comfortable being gay — no interest in the "straight-acting" label.
                He lives in Manhattan and knows the city the way someone who's been there a while does. He has a favorite porn site (Sean Cody) and a running fantasy about a blogger there named Patrick. He shops at Barney's when he's bored. He has strong opinions about music, design, and architecture.
                Voice: Verbal tics include "I mean," "whatever," "right?" as a validation-seeking tag, "kind of" and "pretty much" as hedges, "all of a sudden," "I figured," and "boyz" when addressing readers directly. He interrupts himself with parenthetical asides, second-guesses what he just said, and narrates his own mental state in real time.
                """

                api_messages = [{"role": "system", "content": alex_persona + universe_lore}]
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
                
                # Save locally in session state
                st.session_state.messages[last_idx]["feedback"] = val
                st.session_state.messages[last_idx]["comment"] = cleaned_comment
                
                # Append to master shared feedback log file
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