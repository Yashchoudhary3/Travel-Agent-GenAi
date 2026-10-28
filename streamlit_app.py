import streamlit as st

from app.services.chat_service import handle_chat_stream, reset_session

st.set_page_config(page_title="AI Travel Planner", page_icon="✈️")
st.title("AI Travel Planner")
st.caption("A multi-agent planner: requirements, research, cost estimation, then itinerary.")

with st.sidebar:
    st.subheader("Agents")
    st.markdown(
        """
1. **Requirement Agent** extracts the trip details  
2. **Research Agent** looks up places, weather, and costs  
3. **Cost Estimation Agent** builds the budget  
4. **Planning Agent** writes the itinerary  
        """
    )
    st.caption("Each agent retries failed tools and falls back instead of crashing the trip.")

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []


def reset_chat() -> None:
    if st.session_state.session_id:
        reset_session(st.session_state.session_id)

    st.session_state.session_id = None
    st.session_state.messages = []


col1, col2 = st.columns([1, 5])
with col1:
    if st.button("New trip"):
        reset_chat()
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Plan a trip to Japan for 7 days...")

if prompt:
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            data = None

            with st.status("Working on your trip...", expanded=True) as status:
                for event in handle_chat_stream(
                    prompt,
                    st.session_state.session_id,
                    history=st.session_state.messages,
                ):
                    if event["type"] == "status":
                        st.write(event["message"])
                    elif event["type"] == "complete":
                        data = event
                        if event["status"] == "complete":
                            status.update(
                                label="Your travel plan is ready!",
                                state="complete",
                            )
                        else:
                            status.update(
                                label="Need a few more details",
                                state="complete",
                            )
                    elif event["type"] == "error":
                        status.update(label="Something went wrong", state="error")
                        st.error(event["message"])

            if data is None:
                st.error("No response received. Please try again.")
                st.stop()

            st.session_state.session_id = data["session_id"]
            st.markdown(data["reply"])
            st.session_state.messages.append(
                {"role": "assistant", "content": data["reply"]}
            )

        except Exception as error:
            st.error(f"Something went wrong while planning your trip.\n\n{error}")
            st.stop()
