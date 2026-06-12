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
3. Create Apps Script project.
4. Upload manifest, Code, and Index.
5. Create version.
6. Create deployment with `manifestFileName: "appsscript"`.
7. Return the deployment URL.

Each deployment returns a new URL.
