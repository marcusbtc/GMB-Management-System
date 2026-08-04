# Production deployment contract

This application contains private Google Business Profile data. Run it behind authenticated private ingress only; `docker-compose.prod.yml` intentionally publishes no host ports.

Configure the Google OAuth values in the deployment control plane. `GEMINI_API_KEY` is optional. Never commit or log credential values. The OAuth redirect URI must match the private deployment URL registered with Google.

## Persistence and backup

Persistence: stateless. OAuth credentials and fetched profile data remain in Streamlit session memory, and generated reports use temporary storage. The service has no application database or durable volume.

Backup: not applicable to application data. Back up deployment configuration through the control plane without exporting secret values. A restart ends active sessions and requires users to authenticate again.

## Deployment and rollback

Deploy an immutable image only after CI passes. Verify `/_stcore/health` from the private network before routing users. There are no schema migrations.

Rollback by activating the previous immutable image, keeping the same control-plane secrets, and rechecking `/_stcore/health`. No data restore step exists because the application is stateless.
