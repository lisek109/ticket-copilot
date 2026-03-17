import requests
import streamlit as st

# Base URL of the deployed API
# Change this to http://localhost:8000 when testing against a local backend
API_BASE = "https://ticketcopilotprojectacr.agreeablecliff-25cf21b5.westeurope.azurecontainerapps.io"

st.set_page_config(
    page_title="TicketCopilot",
    page_icon="🤖",
    layout="wide",
)

# Initialize session state
if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "current_user_email" not in st.session_state:
    st.session_state.current_user_email = None

if "ticket_history" not in st.session_state:
    st.session_state.ticket_history = []


def get_auth_headers() -> dict | None:
    """
    Return Authorization headers if a JWT token is available.
    """
    token = st.session_state.access_token
    if not token:
        return None

    return {"Authorization": f"Bearer {token}"}


def register_user(email: str, password: str, full_name: str) -> bool:
    """
    Register a new user through the backend API.
    """
    payload = {
        "email": email,
        "password": password,
        "full_name": full_name,
    }

    response = requests.post(f"{API_BASE}/auth/register", json=payload, timeout=30)

    if response.status_code == 200:
        return True

    st.error(f"Registration failed: {response.text}")
    return False


def login_user(email: str, password: str) -> bool:
    """
    Authenticate the user and store the JWT token in session state.
    """
    payload = {
        "email": email,
        "password": password,
    }

    response = requests.post(f"{API_BASE}/auth/login", json=payload, timeout=30)

    if response.status_code == 200:
        token_data = response.json()
        st.session_state.access_token = token_data["access_token"]
        st.session_state.current_user_email = email
        return True

    st.error(f"Login failed: {response.text}")
    return False


def logout_user() -> None:
    """
    Clear the current session authentication state.
    """
    st.session_state.access_token = None
    st.session_state.current_user_email = None
    st.session_state.ticket_history = []


st.title("TicketCopilot")
st.markdown("AI assistant for support ticket classification and grounded support replies.")

# Sidebar authentication panel
with st.sidebar:
    st.header("Authentication")

    if st.session_state.access_token:
        st.success(f"Logged in as {st.session_state.current_user_email}")

        if st.button("Logout", use_container_width=True):
            logout_user()
            st.rerun()

    else:
        auth_tab_login, auth_tab_register = st.tabs(["Login", "Register"])

        with auth_tab_login:
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")

            if st.button("Login", use_container_width=True):
                if not login_email or not login_password:
                    st.warning("Please provide both email and password.")
                else:
                    if login_user(login_email, login_password):
                        st.success("Logged in successfully.")
                        st.rerun()

        with auth_tab_register:
            register_full_name = st.text_input("Full name", key="register_full_name")
            register_email = st.text_input("Email", key="register_email")
            register_password = st.text_input("Password", type="password", key="register_password")

            if st.button("Register", use_container_width=True):
                if not register_full_name or not register_email or not register_password:
                    st.warning("Please fill in all registration fields.")
                else:
                    if register_user(register_email, register_password, register_full_name):
                        st.success("Registration successful. You can now log in.")

    st.divider()

    st.header("Mailbox Settings")
    st.caption("Planned product feature. This section will later store mailbox integration settings.")

    mailbox_email = st.text_input("Mailbox email", disabled=True, placeholder="support@example.com")
    mailbox_host = st.text_input("IMAP host", disabled=True, placeholder="imap.gmail.com")
    mailbox_password = st.text_input("App password / token", disabled=True, type="password")
    st.button("Save mailbox settings", disabled=True, use_container_width=True)
    st.button("Test mailbox connection", disabled=True, use_container_width=True)


# Block ticket demo until the user is logged in
if not st.session_state.access_token:
    st.info("Please register or log in to use the ticket analysis demo.")
    st.stop()


left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("Ticket Demo")

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
        ticket_resp = requests.post(
            f"{API_BASE}/tickets",
            json=ticket_payload,
            headers=headers,
            timeout=30,
        )

    if ticket_resp.status_code != 200:
        st.error(f"Failed to create ticket: {ticket_resp.text}")
        st.stop()

    ticket = ticket_resp.json()
    ticket_id = ticket["id"]

    # Step 2: Run classification
    with st.spinner("Running classification..."):
        cls_resp = requests.post(
            f"{API_BASE}/tickets/{ticket_id}/classify",
            headers=headers,
            timeout=30,
        )

    if cls_resp.status_code != 200:
        st.error(f"Failed to classify ticket: {cls_resp.text}")
        st.stop()

    cls = cls_resp.json()

    # Step 3: Generate grounded answer
    with st.spinner("Generating grounded response..."):
        ans_resp = requests.post(
            f"{API_BASE}/tickets/{ticket_id}/answer",
            headers=headers,
            timeout=60,
        )

    if ans_resp.status_code != 200:
        st.error(f"Failed to generate suggested response: {ans_resp.text}")
        st.stop()

    ans = ans_resp.json()

    # Save ticket summary in session history
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