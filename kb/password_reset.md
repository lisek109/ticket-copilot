# Password Reset Procedure (KB)

## When to use
- User forgot password
- Account locked due to failed attempts
- MFA reset requested

## Identity verification (mandatory)
Before resetting:
- confirm user identity according to company policy
- never request full passwords or secrets via email

## Reset steps
1. Check account status in IdP / AD
2. Unlock account if locked
3. Trigger password reset or send reset link
4. Ask user to log in and confirm success

## Common pitfalls
- Cached credentials on device
- Old VPN / email client storing previous password
- MFA device out of sync

## Escalation
Escalate to IAM if:
- repeated lockouts occur
- user cannot complete MFA
- security incident suspected

## Audit note
Do not store passwords. Log only request_id and action taken.
