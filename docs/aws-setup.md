# AWS demo setup

Run the deployment from the repository root:

```bash
sam build --template-file infra/template.yaml
sam deploy --guided
```

Give the stack a short unique name. For `NotificationEmail`, use an email the
maintenance demo person can open and confirm the SNS subscription message.
Open the `LeakLoopUrl` output after deployment.

## Create the maintenance demo account

In the Cognito console, open the user pool named `leakloop-maintenance-<stack>`.
Create a user with the email address you will use in the video. Complete its
temporary-password sign-in once, then add that user to the `maintenance` group.
Only this group can acknowledge or close a report on the deployed URL.

The equivalent AWS CLI commands, after substituting the output user pool ID,
are:

```bash
aws cognito-idp admin-create-user --user-pool-id USER_POOL_ID --username you@example.com --user-attributes Name=email,Value=you@example.com
aws cognito-idp admin-add-user-to-group --user-pool-id USER_POOL_ID --username you@example.com --group-name maintenance
```

Do not include a real community's personal data in the demo. Evidence photos
are private, available through short-lived signed links, and the S3 lifecycle
deletes them after 90 days.
