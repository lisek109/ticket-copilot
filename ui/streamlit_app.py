import requests
import streamlit as st

# Base URL of the deployed API
# Change this to localhost when testing a local backend
API_BASE = "https://ticketcopilotprojectacr.agreeablecliff-25cf21b5.westeurope.azurecontainerapps.io"


def get_auth_headers():
    token = st.session_state.access_token
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


st.set_page_config(
    page_title="TicketCopilot",
    page_icon="🤖",
    layout="wide",
)

# Session state keeps a simple in-memory history for the current UI session
if "ticket_history" not in st.session_state:
    st.session_state.ticket_history = []

st.title("TicketCopilot")
st.markdown("AI assistant for support ticket classification and grounded support replies.")

st.subheader("Login")

login_email = st.text_input("Email")
login_password = st.text_input("Password", type="password")

if st.button("Login"):
    login_payload = {
        "email": login_email,
        "password": login_password,
    }

    resp = requests.post(f"{API_BASE}/auth/login", json=login_payload, timeout=30)

    if resp.status_code == 200:
        token_data = resp.json()
        st.session_state.access_token = token_data["access_token"]
        st.success("Logged in successfully.")
    else:
        st.error("Login failed.")

left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("New Support Email")

    email_subject = st.text_input("Email subject")
    email_body = st.text_area(
        "Email content",
        height=220,
        placeholder="Example: I cannot login to the VPN since this morning...",
    )

    analyze = st.button("Analyze ticket", use_container_width=True)

with right_col:
    st.subheader("Session History")

    if st.session_state.ticket_history:
        for item in reversed(st.session_state.ticket_history[-5:]):
            st.markdown(f"**{item['subject'] or 'No subject'}**")
            st.caption(f"Ticket ID: {item['ticket_id']}")
            st.caption(f"Category: {item['category']} | Priority: {item['priority']}")
            st.divider()
    else:
        st.caption("No analyzed tickets yet.")

if analyze:
    if not email_body.strip():
        st.warning("Please enter email content.")
        st.stop()
        
    headers = get_auth_headers()
    if not headers:
        st.error("You must be logged in.")
        st.stop()

    # Step 1: Create ticket
    ticket_payload = {
        "channel": "email",
        "subject": email_subject,
        "body": email_body,
    }

    with st.spinner("Creating ticket..."):
        ticket_resp = requests.post(f"{API_BASE}/tickets", json=ticket_payload, timeout=30)

    if ticket_resp.status_code != 200:
        st.error("Failed to create ticket.")
        st.stop()

    ticket = ticket_resp.json()
    ticket_id = ticket["id"]

    # Step 2: Run classification
    with st.spinner("Running classification..."):
        cls_resp = requests.post(f"{API_BASE}/tickets/{ticket_id}/classify", timeout=30)

    if cls_resp.status_code != 200:
        st.error("Failed to classify ticket.")
        st.stop()

    cls = cls_resp.json()

    # Step 3: Generate answer suggestion
    with st.spinner("Generating grounded response..."):
        ans_resp = requests.post(f"{API_BASE}/tickets/{ticket_id}/answer", timeout=60)

    if ans_resp.status_code != 200:
        st.error("Failed to generate suggested response.")
        st.stop()

    ans = ans_resp.json()

    # Save simple local UI history
    st.session_state.ticket_history.append(
        {
            "ticket_id": ticket_id,
            "subject": email_subject,
            "category": cls["category"],
            "priority": cls["priority"],
        }
    )

    st.success("Ticket analyzed successfully.")

    st.subheader("Ticket Details")
    st.code(ticket_id, language=None)

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Category", cls["category"])
    metric_col2.metric("Priority", cls["priority"])
    metric_col3.metric("Answer Mode", ans.get("answer_mode", "unknown"))

    st.subheader("Suggested Response")
    st.write(ans["suggested_answer"])

    st.subheader("Knowledge Sources")
    for idx, src in enumerate(ans["sources"], start=1):
        with st.expander(f"Source {idx}: {src['source']}"):
            st.write(src["snippet"])