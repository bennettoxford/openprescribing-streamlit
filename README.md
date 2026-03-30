# openprescribing-streamlit

This repo contains a [Streamlit](https://docs.streamlit.io/) application for working
with OpenPrescribing data.

It is deployed at [streamlit.openprescribing.net](https://streamlit.openprescribing.net/).

## Setup

Use [`uv`](https://docs.astral.sh/uv/) to create the environment and install
dependencies:

```bash
uv sync
```

Copy `.env.sample` to `.env`, and replace the value of `DUCKDB_PATH` with the path to a
local copy of the prescribing database.

## Running the app

```bash
uv run streamlit run app.py
```

(or `just run`)

## Docker

Build the image and run a smoke test with:

```bash
just docker-build
just docker-smoke
```

Run the app from Docker with:

```bash
just docker-run
```

## Deployment

Deploys are handled by GitHub Actions via [deploy.yml](./.github/workflows/deploy.yml).
Pushing to `main` builds the Docker image, pushes it to GitHub Container Registry,
and asks Dokku to deploy that image on `dokku5.ebmdatalab.net`.

### Cloudflare setup

There is an A record for streamlit.openprescribing.net pointing to 139.59.173.124, dokku5's IP address.

### GitHub setup

To deploy, the repository needs access to the `DOKKU5_DEPLOY_SSH_KEY` organisation secret.

### Dokku setup

The following commands were run to set up the app on `dokku5`:

```bash
dokku apps:create openprescribing-streamlit
dokku domains:add openprescribing-streamlit streamlit.openprescribing.net
dokku letsencrypt:enable openprescribing-streamlit
dokku ports:set openprescribing-streamlit http:80:8501 https:443:8501
dokku storage:mount openprescribing-streamlit /var/lib/dokku/data/storage/openprescribing:/storage
dokku config:set openprescribing-streamlit DUCKDB_PATH=/storage/prescribing.duckdb
```
