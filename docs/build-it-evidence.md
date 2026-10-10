# Build It evidence

Environmental Hacks permits projects built locally with AWS open-source tools;
the official event page lists SAM CLI under Build It and says no AWS account,
card or bill is required for that route.

## What to run

```bash
cd /home/anmol/roofwatt
source .sam-venv/bin/activate
sam validate --template-file infra/template.yaml
sam build --template-file infra/template.yaml
```

In a second terminal:

```bash
cd /home/anmol/roofwatt
source .venv/bin/activate
uvicorn backend.app.main:app --reload
```

Open `http://127.0.0.1:8000` and demonstrate report → acknowledge → repair.

## Honest wording for the video and writeup

“LeakLoop is a Build It submission. We use the open-source AWS SAM CLI to
validate and build the serverless package, and AWS Lambda Powertools for
structured application logging. We ran the product locally for this demo; the
AWS deployment template is optional and was not used in this recording.”

Do not claim that Lambda, DynamoDB, Cognito, S3 or SNS are running unless you
have actually deployed them. The template demonstrates how the project can
become a Ship It version later.
