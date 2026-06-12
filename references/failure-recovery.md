# Failure Recovery

## OAuth

Symptom: `invalid_scope`

Cause: token lacks script scopes.

Action: re-run OAuth with Sheets, `script.projects`, and `script.deployments`.

## Apps Script API

Symptom: `SERVICE_DISABLED` or "User has not enabled Apps Script API".

Action:

- enable Apps Script API in the GCP project
- enable user-level Apps Script API at `https://script.google.com/home/usersettings`

## Missing Manifest

Symptom: deployment/update content fails with missing manifest.

Action: upload `appsscript` JSON first in the file list.

## Domain Access

Symptom: `ANYONE access has been disabled`.

Action: set manifest `webapp.access` to `DOMAIN`.

## Empty Web App

Symptom: web app loads but shows no data.

Common causes:

- Sheet was not created before deploy.
- `Code.gs` has the wrong `SHEET_ID`.
- raw or section tabs are empty.
- Sheet is inaccessible to the deploying user.

Action: validate `Code.gs` sheet ID, open the Sheet URL, confirm section tabs exist, then redeploy.

## DataSuite Bridge

Symptom: raw data query fails before Sheet creation.

Common causes:

- DataSuite Studio Chrome tab is not open or authenticated.
- temp query tab creation failed.
- result limit was too low.
- SQL table partitions do not have the requested month.

Action: use `--data-mode existing-sheet` with a prepared Sheet, or rerun after opening an authenticated DataSuite Studio tab.
