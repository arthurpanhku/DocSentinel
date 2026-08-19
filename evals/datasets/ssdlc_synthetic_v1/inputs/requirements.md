# Requirements Review: ExampleCo Support Portal

[REQ-01] The portal stores customer names, email addresses, and support-ticket
text. The product is intended for customers in several regions.

[REQ-02] Administrators authenticate with a password. Multi-factor
authentication is explicitly out of scope for the first release.

[REQ-03] Ticket records and access logs are retained indefinitely. The
requirements do not define a deletion request workflow or retention schedule.

[REQ-04] Ordinary customers can view only tickets belonging to their own
account, and every access-control decision is logged.
