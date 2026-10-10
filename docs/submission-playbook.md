# LeakLoop submission playbook — Build It path

This is the local, no-AWS-account submission route. It uses AWS SAM CLI and
AWS Lambda Powertools, both open-source AWS tools. Do not claim the project is
deployed, uses DynamoDB, Cognito, S3 or SNS unless you have actually completed
the optional deployment.

## Three-minute demo

1. **Problem (0:00–0:25).** Show a running tap or a simple leak photo you have
   permission to use. Explain how reports disappear in chats and nobody sees
   who owns the repair.
2. **Report (0:25–1:00).** Pin the actual test location, enter a landmark and
   short description, then submit. Show it immediately in the queue and map.
3. **Maintenance workflow (1:00–1:50).** Open the local maintenance queue,
   acknowledge it, then mark the repair after entering the flow value recorded
   during a repair check. Show the timeline and dashboard update.
4. **Impact integrity (1:50–2:20).** Explain the distinction between a
   reporter's estimate and flow recorded at repair. Do not call this cumulative
   water saved.
5. **AWS open source (2:20–3:00).** Show `sam validate` and `sam build` in a
   terminal, then open `infra/template.yaml` and the Powertools logger in
   `backend/app/main.py`. Explain that SAM packages the local serverless
   application and Powertools provides production-style structured logging.
   Say clearly that this is the permitted **Build It** path, not a cloud
   deployment.

## Grounding

- Get permission before showing an actual location or facility report.
- If using a test incident, call it a test in the video and app.
- Use one real facilities-person observation only if it was collected during
  the hackathon; do not invent validation.
- State that local maintenance actions are demo-only. The optional Ship It
  template adds Cognito, S3 and SNS when a deployment is available.

## Optional Ship It deployment

```bash
sam build --template-file infra/template.yaml
sam deploy --guided
```

The official rules require the public repository, a YouTube demo under three
minutes, and a short writeup. The video must show AWS use. Check the
[official rules](https://www.wemakedevs.org/aws/rules) and
[judging criteria](https://www.wemakedevs.org/aws/env) before submitting.
