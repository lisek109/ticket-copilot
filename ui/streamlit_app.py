import requests
import streamlit as st

# Base URL of the deployed API
# Change this if running locally
API_BASE = "https://ticketcopilotprojectacr.agreeablecliff-25cf21b5.westeurope.azurecontainerapps.io"


st.set_page_config(page_title="TicketCopilot", page_icon="🤖", layout="wide")

st.title("TicketCopilot")
st.markdown("AI assistant for support ticket classification and response generation.")

# Text input simulating an incoming support email
email_subject = st.text_input("Email subject")

email_body = st.text_area(
    "Email content",
    height=200,
    placeholder="Example: I cannot login to the VPN since this morning...",
)

if st.button("Analyze ticket"):

    if not email_body:
        st.warning("Please enter email content.")
        st.stop()

    # Create ticket via API
    ticket_payload = {
        "channel": "email",
        "subject": email_subject,
        "body": email_body,
    }

    ticket_resp = requests.post(f"{API_BASE}/tickets", json=ticket_payload)

    if ticket_resp.status_code != 200:
        st.error("Failed to create ticket.")
        st.stop()

    ticket = ticket_resp.json()
    ticket_id = ticket["id"]

    st.success(f"Ticket created: {ticket_id}")

    # Run classification
    cls_resp = requests.post(f"{API_BASE}/tickets/{ticket_id}/classify")

    if cls_resp.status_code == 200:
        cls = cls_resp.json()

        st.subheader("Classification")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Category", cls["category"])

        with col2:
            st.metric("Priority", cls["priority"])

    # Generate answer suggestion
    ans_resp = requests.post(f"{API_BASE}/tickets/{ticket_id}/answer")

    if ans_resp.status_code == 200:
        ans = ans_resp.json()

        st.subheader("Suggested Response")

        st.write(ans["suggested_answer"])

        st.subheader("Sources")

        for src in ans["sources"]:
            st.markdown(f"**{src['source']}**")
            st.caption(src["snippet"])