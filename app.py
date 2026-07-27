import streamlit as st
from openai import OpenAI

# Page configuration
st.set_page_config(page_title="ALEX - Universe Narrator", page_icon="✨")

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

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "feedback" in message:
            fb = message["feedback"]
            icon = "👍 Thumbs Up" if fb == 1 else "👎 Thumbs Down"
            st.caption(f"Creator Feedback Recorded: {icon}")

# User input
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

                # Safe execution block
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
                else:
                    st.error("Received an empty response from the model.")
                
            except Exception as e:
                st.error(f"Featherless API Error: {e}")

# Add Feedback widget to the latest assistant message
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    last_idx = len(st.session_state.messages) - 1
    
    if "feedback" not in st.session_state.messages[last_idx]:
        feedback_key = f"feedback_{last_idx}"
        
        def save_feedback():
            val = st.session_state.get(feedback_key)
            if val is not None:
                st.session_state.messages[last_idx]["feedback"] = val

        st.feedback("thumbs", key=feedback_key, on_change=save_feedback)