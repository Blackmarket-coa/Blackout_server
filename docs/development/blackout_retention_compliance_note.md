# Blackout Retention Default and Compliance Note

Date: 2026-02-27  
Owners: Backend Lead + Security Architect

## Default retention decision

Default signaling retention is **48 hours** (`blackout.signal_event_ttl: "48h"`) within the policy window of 24–72 hours.

## Compliance rationale

- 48h provides enough recovery margin for intermittent peer connectivity.
- Retention remains bounded and aligned with signaling-only data minimization goals.
- Operators can shorten/extend within the policy envelope only with documented approval.

## Required controls

1. TTL-based purge job must run continuously.
2. Purged signaling events must be irretrievable via APIs.
3. Weekly review of purge lag and retained-event growth metrics.
4. Any override from 48h default must be recorded with owner + justification.
