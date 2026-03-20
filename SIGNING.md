# Signed Commits & Vigilant Mode

This repository requires signed commits. All commits should show a **Verified** badge on GitHub.

## Setup (SSH Signing — Recommended)

### 1. Enable Vigilant Mode on GitHub

Go to [github.com/settings/ssh](https://github.com/settings/ssh), scroll to
**Vigilant mode**, and toggle it **on**. This flags unsigned commits as
*Unverified*.

### 2. Add a Signing Key on GitHub

1. Go to **Settings → SSH and GPG keys → New SSH key**
2. Set **Key type** to **Signing Key** (not Authentication)
3. Paste your public key (e.g. `~/.ssh/id_ed25519.pub`)

> The same physical key can serve as both Authentication and Signing —
> just add it twice under the two different types.

### 3. Configure Git Locally

```bash
# Use SSH for signing
git config --global gpg.format ssh

# Point to your private key
git config --global user.signingkey ~/.ssh/id_ed25519

# Sign all commits automatically
git config --global commit.gpgsign true
```

### 4. Verify

```bash
# Check the last commit's signature
git log --show-signature -1
```

After pushing, the commit should display a green **Verified** badge on GitHub.
