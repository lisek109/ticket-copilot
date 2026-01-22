# Incident Response (KB)

**Goal:** provide a consistent, fast first response for production incidents reported via tickets/email.

## Severity / Priority mapping
- **P1 (Critical):** major outage, many users impacted, core systems unavailable
- **P2 (High):** significant degradation, limited workaround
- **P3 (Medium):** single-user issue or non-critical feature
- **P4 (Low):** request, question, informational

## First-response checklist (0–15 minutes)
1. **Acknowledge** receipt to the reporter (confirm you are investigating).
2. **Collect essentials:**
   - what system/service?
   - what is broken (symptoms)?
   - when did it start?
   - how many users impacted?
   - any error messages / logs / screenshots?
3. **Check status sources:**
   - internal status page / monitoring dashboards
   - recent deployments / changes
4. **Confirm scope:**
   - single user vs multi-user
   - specific region/team vs global
5. **Open or link an incident** if multiple users are affected.

## Triage workflow
- If **multi-user impact** suspected → treat as **P1/P2** and escalate immediately.
- If **single-user** and clear category (e.g., access) → follow the relevant procedure (VPN, password reset, etc.).
- If unclear → request clarifying details, do not guess.

## Escalation criteria
Escalate to on-call / L2 when:
- service appears down or error rate spikes
- multiple tickets report the same symptom
- no mitigation within 15–30 minutes
- data loss/security concerns are mentioned

## Communication template
**Subject:** Incident update — <service> — <status>

Hi team,  
We are investigating reports of **<symptom>** affecting **<scope>** since **<time>**.  
Current status: **<investigating/mitigated/resolved>**.  
Next update in **<time>**.  
Reference: **<request_id/incident_id>**.

## Post-incident
After resolution:
- add a short summary (what/why/fix)
- list follow-ups (monitoring, runbooks, tests)
- update KB if new steps were discovered
