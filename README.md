# LeakLoop

**A water leak should not disappear into a complaint form.** LeakLoop helps a
campus or housing society move a report from a resident to maintenance, then
records a repair update and the flow value entered during its check.

Built for Environmental Hacks (WeMakeDevs × AWS), Heat and Water track.

## Hackathon path: Build It, locally

LeakLoop is eligible as a **Build It** project: it uses the open-source AWS SAM
CLI to build the serverless package and AWS Lambda Powertools for structured
application logging. This path needs no AWS account, card, credentials or
deployment. The optional AWS deployment template remains in the repository for
a later Ship It version, but is not required for the submission.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

Open http://127.0.0.1:8000. Tap the map to set a report location, fill in the
landmark and description, and submit. The report appears in the community
board. Switch to **Maintenance queue**, add a real handoff note, then enter the
flow value, repair note and optional evidence when recording completion. The
summary separates reporter-supplied estimates from flow values recorded during
repair checks. Local mode permits maintenance actions for a quick demo; the AWS
deployment requires a Cognito maintenance account.

Local reports are held in memory and reset when the server stops. AWS
deployment stores reports in DynamoDB.

## Workflow

```text
Resident reports leak → Maintenance acknowledges → Repair and flow check → Community sees recorded outcome
```

## AWS

AWS SAM deploys FastAPI on Lambda through Mangum, with DynamoDB for reports
and repair history, private S3 evidence, Cognito maintenance roles, and SNS
maintenance alerts. AWS Lambda Powertools writes structured logs for report
and repair events. See [infra/template.yaml](infra/template.yaml).

```bash
sam build --template-file infra/template.yaml
sam deploy --guided
```

During guided deploy, optionally enter a team email for `NotificationEmail`,
then confirm the email subscription. Create one maintenance user and add it to
the Cognito `maintenance` group before recording the demo. Detailed steps are
in [AWS setup](docs/aws-setup.md).

For the no-account hackathon route, demonstrate the local build instead:

```bash
source .sam-venv/bin/activate
sam validate --template-file infra/template.yaml
sam build --template-file infra/template.yaml
```

Then run the app with `uvicorn` as shown above. See
[Build It evidence](docs/build-it-evidence.md) for exactly what to show judges.

## Impact and limits

- Reported litres/day is an estimate supplied by the reporter.
- Estimates and repair-check values are self-reported. The app does not
  independently verify a repair or claim cumulative savings.
- Resident reports are deliberately low-friction. After AWS deployment,
  Cognito protects acknowledge and repair actions with the `maintenance`
  group. Do not put personally identifying or sensitive images in reports.
- Maintenance repair photos are private S3 objects, viewed with short-lived
  links and deleted by lifecycle policy after 90 days. They are evidence, not
  independent proof.
- No reports are seeded. Demonstrate the workflow with a clearly labelled
  example report or a real report shared with permission.

## Hackathon materials

- [Product brief and winner benchmark](docs/product-brief.md)
- [Three-minute demo plan](docs/submission-playbook.md)
- [Submission checklist](docs/submission-checklist.md)
- [AI tools used](AI_TOOLS.md)
