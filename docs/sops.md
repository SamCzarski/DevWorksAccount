

```bash
sudo apt install age
age-keygen -o ~/.config/sops/age/keys.txt
```


`~/.config/sops/age/keys.txt`:
```text
# created: 2025-09-08T02:34:00Z
# public key: age1qxxxx...
AGE-SECRET-KEY-XXXX...
```

`~/.sops.yaml`:
```yaml
creation_rules:
  - path_regex: \.(yaml|p12|pem|crt|csr|srl|ext|key)$
    age: age1qxxxx...   # 👈 your public key
  - path_regex: \.enc$
    age: age1qxxxx...   # 👈 your public key
```

Encrypt:
sops -e test.yaml > test.enc.yaml

Decrypt:
sops -d test.enc.yaml > test.dec.yaml


# use gcloud keyring to encrypt/decrypt
## Encrypt
```bash
sops --gcp-kms projects/sam-devworks/locations/global/keyRings/devworks-keyring/cryptoKeys/devworks-key \
    --encrypt dec.yaml > enc.yaml
```

## Decrypt
```bash
sops --gcp-kms projects/sam-devworks/locations/global/keyRings/devworks-keyring/cryptoKeys/devworks-key \
    --decrypt enc.yaml > dec.yaml
```


# Batch encrypt/decrypt

**cd** into the directory with the files to encrypt

## Encrypt
create a directory called `encrypted` to hold the encrypted files
run the command:
```bash
find ./ -type f \( -name "*.p12" -o -name "*.pem" -o -name "*.crt" -o -name "*.csr" -o -name "*.srl" -o -name "*.ext" -o -name "*.key" -o -name "*.yaml" \) -print0 | \
xargs -0 -I{} sops --encrypt --output encrypted/{}.enc {} --gcp-kms projects/sam-devworks/locations/global/keyRings/devworks-keyring/cryptoKeys/devworks-key
```
or
```bash
find ./ -type f \( -name "*.p12" -o -name "*.pem" -o -name "*.crt" -o -name "*.csr" -o -name "*.srl" -o -name "*.ext" -o -name "*.key" -o -name "*.yaml" \) -print0 | \
xargs -0 -I{} sops --encrypt --output encrypted/{}.enc {}
```

## Decrypt
**cd** into the `encrypted` directory with the encrypted files
create a directory called `decrypted` to hold the decrypted files

```bash
find ./ -type f -name "*.enc" -print0 | xargs -0 -I{} sh -c 'sops --decrypt "$1" > "$(basename "$1" .enc)"' _ {}
```
clean up the `.enc` files
```bash
rm *.enc
```

# Development

**Note:** for early development use `~/.config/sops/age/keys.txt`, later user gcloud KMS




