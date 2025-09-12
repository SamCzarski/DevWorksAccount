

# Setup gcloud CLI

gcloud auth login
gcloud config set account sam.czarski@gmail.com
gcloud auth list


# Create a Project

gcloud projects create <PROJECT_ID> --name="<PROJECT_NAME>"
```bash
gcloud projects create sam-devworks --name="DevWorks Project"
```
gcloud beta billing accounts list
gcloud beta billing projects link <PROJECT_ID>
```bash
gcloud beta billing projects link sam-devworks
```
gcloud projects list

**Check current project**
gcloud config list --format 'value(core.project)'
*if output is not the project you created (sam-devworks) change it*

## Set the project
gcloud config set project <PROJECT_ID>
```bash
gcloud config set project sam-devworks
```

gcloud services enable cloudkms.googleapis.com

gcloud kms keyrings create <KEYRING_ID> --location global
*this must have billing enabled*
```bash
gcloud kms keyrings create devworks-keyring --location global
```

## Create the key
gcloud kms keys create <KEY_ID> \
  --location global \
  --keyring <KEYRING_ID> \
  --purpose encryption
```bash
gcloud kms keys create devworks-key \
  --location global \
  --keyring devworks-keyring \
  --purpose encryption
```

## Verify the key

```bash
gcloud kms keyrings list --location global
gcloud kms keys list --location global --keyring <KEYRING_ID>
gcloud kms keys describe <KEY_ID> --location global --keyring <KEYRING_ID>
```

devworks key: `projects/sam-devworks/locations/global/keyRings/devworks-keyring/cryptoKeys/devworks-key`

# gcloud billing

## Enable billing

**link project to billing**
`gcloud beta billing projects link <PROJECT_ID> --billing-account=<BILLING_ACCOUNT_ID>`

## Disable billing

`gcloud beta billing projects unlink <PROJECT_ID>`


## Verify billing is enabled
gcloud beta billing projects describe <PROJECT_ID>





