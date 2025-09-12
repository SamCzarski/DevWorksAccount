
# Google IDP Setup

## Navigate to the project

Go to [Google Cloud Console](https://console.cloud.google.com/) page

Create a Project or select an existing one.

*view [Google IDP Clients](https://console.cloud.google.com/auth/clients?project=sam-devworks)*

## Enable APIs

* Go to `APIs & Services` -> `Library`
* Search for `Google+ API` (for older login) or just `Google Identity Services / People API` (recommended).
* Click `Enable`

## Configure OAuth Consent Screen

* Go to `APIs & Services` -> `OAuth consent screen`.
* Choose `External` (if users are not internal to your organization) or `Internal`.
Fill in:
  * App name, ie: "DevWorks Cloud"
  * User support email: "your_name@example.com"
  * Developer contact email: "your_name@example.com"

## Create OAuth 2.0 Credentials

* Go to `APIs & Services` -> `Credentials` -> `Create Credentials` -> `OAuth Client ID`
* Select Web Application
* Add Authorized JavaScript origins, ie: `https://localhost:8000`
* Add Authorized redirect URIs, ie: `https://localhost:8000/login/idp/complete/google-oauth2/`
* Click `Create`

## Copy Key and Secret
After creating, Google will show:
  * `Client ID` -> this is your `IDP_GOOGLE_KEY`
  * `Client Secret` → this is your `IDP_GOOGLE_SECRET`

*Store them securely (e.g., environment variables, Docker secrets, or a secrets manager).*











