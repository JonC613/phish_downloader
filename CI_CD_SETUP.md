# CI/CD Setup Guide

## GitHub Actions Workflow

The `.github/workflows/ci-cd.yml` workflow automatically:

1. **Runs tests** on every push/PR
2. **Builds Docker images** (Streamlit + DB Loader)
3. **Pushes images** to GitHub Container Registry (`ghcr.io`)
4. **Tags images** with branch name, SHA, and `latest`

## Required Setup

### 1. Enable GitHub Packages

The workflow uses `GITHUB_TOKEN` (automatically available) to push images to `ghcr.io`.

No additional secrets needed for image pushing!

### 2. Make Images Public (Optional)

After first push, go to:
- `https://github.com/users/<USERNAME>/packages/container/<REPO>-streamlit/settings`
- Change visibility to "Public" if you want public access

### 3. Pull Images Anywhere

```bash
# Login (only if private)
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Pull images
docker pull ghcr.io/<USERNAME>/<REPO>-streamlit:latest
docker pull ghcr.io/<USERNAME>/<REPO>-loader:latest
```

### 4. Update docker-compose.yml for Production

Replace `build:` sections with `image:` in your docker-compose.yml:

```yaml
services:
  streamlit:
    image: ghcr.io/<USERNAME>/<REPO>-streamlit:latest
    # Remove build: section
    ...
  
  db_loader:
    image: ghcr.io/<USERNAME>/<REPO>-loader:latest
    # Remove build: section
    ...
```

### 5. Deploy Automatically (Optional)

Uncomment the `deploy` job in the workflow and add these secrets:

- `DEPLOY_HOST` - Your server IP/hostname
- `DEPLOY_USER` - SSH username
- `DEPLOY_SSH_KEY` - Private SSH key for authentication

Update the script path to match your server's directory.

## Deployment Options

### Option A: Manual Deploy (Simplest)

On your server:
```bash
git pull
docker-compose pull
docker-compose up -d
```

### Option B: Automated Deploy

The workflow's `deploy` job (when enabled) will:
1. SSH into your server
2. Pull latest code + images
3. Restart containers
4. Clean up old images

### Option C: Cloud Platform

Deploy to platforms that support Docker Compose:
- **Fly.io** - `fly launch` + `fly deploy`
- **Render** - Connect repo, auto-deploy on push
- **Railway** - Import Docker Compose, auto-deploy
- **DigitalOcean App Platform** - Upload compose file

## Workflow Triggers

- **Push to `main`/`develop`** → Build, test, push images, deploy (if enabled)
- **Pull Request** → Build and test only
- **Manual trigger** → Run from Actions tab

## View Build Status

Add badge to README.md:
```markdown
![CI/CD](https://github.com/<USERNAME>/<REPO>/actions/workflows/ci-cd.yml/badge.svg)
```

## Viewing the App

After deployment, access:
- Streamlit UI: `http://<your-server>:8501`
- PostgreSQL: Internal only (port 5434 on host if needed)

## Troubleshooting

**Images not pushing?**
- Check Actions logs for errors
- Verify repo has "Packages" permission enabled

**Deploy fails?**
- Verify SSH credentials in Secrets
- Check server has Docker + Docker Compose installed
- Ensure server can pull from ghcr.io

**Tests failing?**
- Run locally: `python -m pytest tests/ -v`
- Check all dependencies in requirements.txt
