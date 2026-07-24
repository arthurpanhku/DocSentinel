# Checkout Service — Design Review Demo

## Internet edge and identity

The customer-facing single-page application sends HTTPS requests to a public API
Gateway. The gateway validates the signature, issuer, audience, and expiry of each
OIDC access token before forwarding an authenticated subject identifier to the
Checkout API.

The Checkout API accepts an `account_id` path parameter. It verifies that the
authenticated subject owns the requested account before reading an order.

## Payment webhook

The Payment Webhook is reachable from the public internet and accepts JSON event
payloads from the payment provider. HMAC signature validation is planned for the
next release but is not implemented in the current design.

Accepted webhook events are written directly to the order state machine. Duplicate
event detection is implemented using the provider event ID, but payload integrity
is not otherwise verified.

## Administrative access

The internal Admin Console calls the Checkout API through a private network route.
Administrators authenticate with individual SSO accounts and phishing-resistant
MFA. Every privileged action records the administrator subject, action, target,
timestamp, and result in an append-only audit stream.

The report-export worker uses one shared service token with the `order-admin` role.
The token is stored in the deployment secret store and currently has no automatic
rotation schedule.

## Data flows

All service-to-service connections use TLS 1.3. The order database uses managed
encryption at rest. Payment card numbers are never stored; the system stores only
the payment provider token and the last four digits for display.

## Availability

The public API Gateway enforces 100 requests per minute per authenticated subject.
The Payment Webhook has no per-sender rate limit because provider IP ranges have not
yet been integrated into the gateway policy.
