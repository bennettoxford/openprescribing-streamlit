# openprescribing-streamlit

This repo contains a [Streamlit](https://docs.streamlit.io/) application for working
with OpenPrescribing data.

## Setup

Use [`uv`](https://docs.astral.sh/uv/) to create the environment and install
dependencies:

```bash
uv sync
```

## Running the app

```bash
just run
```

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
