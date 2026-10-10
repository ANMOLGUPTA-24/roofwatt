# Submission readiness checklist

## Eligibility and history

- [ ] Every team member is an eligible university student in India, 18+, and has
  registered for the tour.
- [ ] Every team member has an AWS Builder Center profile and has started
  university verification.
- [ ] The public repository has commits dated during Oct 8–11, 2026 and contains
  only work built in this event. Do not backdate, copy, or rewrite history.
- [ ] AI assistance is disclosed in the repository: see AI_TOOLS.md.

## Build It evidence and demo

- [ ] Run `sam validate --template-file infra/template.yaml` and `sam build
  --template-file infra/template.yaml` with the AWS SAM CLI.
- [ ] Record a report being created, acknowledged and repaired locally.
- [ ] In the video, show the SAM build output, [infra/template.yaml](../infra/template.yaml)
  and the Powertools logger in [main.py](../backend/app/main.py).
- [ ] State accurately: this is the Build It path using the open-source AWS SAM
  CLI and AWS Lambda Powertools. It is not deployed on AWS.
- [ ] Keep the YouTube video public or unlisted and under three minutes.

## Submission

- [ ] Repository is public and its README includes setup, AWS architecture,
  safety boundary and AI-tool disclosure.
- [ ] Writeup states the problem, who uses it, what is built, validation done,
  data sources and AWS services.
- [ ] Submit the public repository, working YouTube URL and short writeup before
  the deadline on the hackathon page.
- [ ] Publish an AWS Builder Center build post and link it for the blog prize.

## Claims to avoid

- Do not describe estimated flow as measured or as cumulative water saved.
- Do not invent pilot data, testimonials, deployments, user counts, AWS service
  usage, or impact metrics.
