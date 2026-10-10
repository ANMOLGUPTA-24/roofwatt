# LeakLoop — product brief

## The specific problem

In a campus or apartment community, a resident can spot a running tap, pipe
leak, or overflowing tank, but the report often stops in a message thread.
Maintenance has no shared queue, residents cannot see whether someone took
ownership, and nobody records what the repair changed.

LeakLoop closes that loop for one local community. It is intentionally about
water loss people can point to and maintenance can fix, not a broad water
dashboard.

## One complete user flow

| Person | Action | What the next person can see |
| --- | --- | --- |
| Resident / student | Pin location, describe leak, add an optional loss estimate | A timestamped, mappable report |
| Maintenance | Acknowledge when work is accepted | Status changes to in progress with a note |
| Maintenance | Acknowledge with a handoff note; record repair with a flow-check value and note | Repair update appears in the timeline and impact summary |
| Community | Review the shared board | Open reports and user-entered repair-check values are visible |

## Why this has a stronger demo shape

The official First Commit winners showed patterns worth learning from:

- **Suraksha** connected the caregiver operating the app with the older parent
  receiving care. Its product problem was a multi-person relationship.
- **Beacon Night Shift** gathered evidence, proposed an action, waited for a
  human approval, then checked whether the system recovered.
- **CampusEvac** made two roles cooperate in an interactive drill.

The common thread is a visible workflow with a clear user and an outcome. The
official recap describes all three and reports 1,180 submissions at that event:
[First Commit recap and winners](https://www.wemakedevs.org/blogs/first-commit-hackathon-recap-and-whats-next).

LeakLoop applies that workflow discipline to a concrete Heat and Water problem:
report → acknowledge → repair → record the flow value entered during a check. It avoids adding
an AI chatbot where deterministic status tracking is clearer and safer.

This does not establish that LeakLoop will win. The edge depends on a working
deployment, a clean demo, and one real community observation during the event.

## What the current MVP does

- Mobile-friendly leak report with map pin and browser geolocation.
- Community board with map markers, filters and status timeline.
- Explicit state transitions: reported → acknowledged → repaired.
- Requires a flow-check value and repair note to close a repair.
- Uses Cognito group membership to limit deployed maintenance updates.
- Supports an optional after-repair evidence photo stored privately in S3.
- Publishes new-report and status-change alerts to an SNS maintenance topic.
- Separates reporter-supplied estimates from user-entered repair-check values.
- Stores reports in memory locally and in DynamoDB when deployed.
- Emits structured AWS Lambda Powertools logs for report and repair events.

## Impact claims

The tool records litres per day, not lifetime savings. A reporter's number is
labelled estimated; the repair counter only includes a value entered during
repair. Neither value is independently verified by the app. It makes no claim
about water saved over time until a follow-up measurement is collected.

## Pilot

During the event, ask one campus facilities or apartment maintenance contact
to walk through a report they have permission to share. Measure:

1. Can a resident submit it in under one minute?
2. Can maintenance understand the location and take ownership?
3. What evidence would they trust before marking it repaired?

Use anonymised notes in [pilot-notes.md](pilot-notes.md). Never invent a
real-world leak, quote, or savings number.

## Current limitations

The deployed prototype has Cognito maintenance-role protection, optional S3
photo evidence and SNS alerts. It still has no duplicate detection, reporter
identity, rate limiting, or repair verification by a second person. Photos and
flow values are user-entered evidence, not independent proof. The map uses
OpenStreetMap tiles; project reports are user-entered. A production rollout
would add abuse protection before inviting an unrestricted public audience.
