# Apps Script Deployment Contract

## OAuth Scopes

The local OAuth authorized-user JSON must include:

```text
https://www.googleapis.com/auth/spreadsheets
https://www.googleapis.com/auth/script.projects
https://www.googleapis.com/auth/script.deployments
```

Fail before data pull if script scopes are missing.

## Files

Upload exactly these Apps Script files:

- `appsscript` as type `JSON`
- `Code` as type `SERVER_JS`
- `Index` as type `HTML`

`appsscript` must be present. Apps Script API deployment fails without an explicit manifest.

## Manifest

Use:

```json
{
  "timeZone": "Asia/Singapore",
  "runtimeVersion": "V8",
  "oauthScopes": ["https://www.googleapis.com/auth/spreadsheets"],
  "webapp": {
    "executeAs": "USER_DEPLOYING",
    "access": "DOMAIN"
  }
}
```

Shopee domain policy blocks `ANYONE`; use `DOMAIN`.

## Deployment Sequence

1. Create or reuse Google Sheet.
2. Render `Code.gs` with final `SHEET_ID`.
3. Create Apps Script project, unless an existing `script_id` is supplied for stable-link updates.
4. Upload manifest, Code, and Index.
5. Create version.
6. Create deployment with `manifestFileName: "appsscript"`, unless an existing `deployment_id` is supplied; in that case update the deployment to the new version.
7. Return the deployment URL.

## Stable Link Updates

If a user asks to update the current link, reuse the existing Apps Script project and deployment:

```text
projects.updateContent(scriptId)
projects.versions.create(scriptId)
projects.deployments.update(scriptId, deploymentId, deploymentConfig.versionNumber = new version)
```

The Web App URL is tied to `deploymentId`, so updating the same deployment keeps the same URL. Creating a fresh deployment returns a new URL.
