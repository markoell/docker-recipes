# Workspace Guidelines: Docker Recipes

This repository contains personal Docker and Docker Compose configurations, organized as a monorepo where each subdirectory is a standalone recipe.

## 1. Directory Structure
* Each subdirectory represents one recipe (e.g., `traefik`, `pi-hole`, `duplicati`).
* Inside each subdirectory, there must be a Docker Compose file named `compose.yaml`.
* Optional environment file `.env` can be placed in the same folder if needed.

## 2. Environment Variables & Placeholders
* **PUID / PGID**: Use `${PUID}` and `${PGID}` instead of hardcoded UID/GID.
* **Time Zone**: Use `${TZ}`.
* **Volume Paths**: Use the placeholder `CHANGE_TO_COMPOSE_DATA_PATH/<recipe-name>/...` for mounting persistent directories on the host, where `<recipe-name>` matches the directory name of the recipe.
* **Local Paths**: For lightweight configs, relative paths within the recipe directory (e.g. `./config`) can be used if they don't hold heavy persistent data.

## 3. Traefik Routing Conventions
When exposing a service via Traefik:
* Enable Traefik with the label `"traefik.enable=true"`.
* **Router Names**: Always ensure that the router name prefix in the labels (e.g., `traefik.http.routers.<router-name>`) matches the recipe subdirectory name or service name. Avoid copy-pasting labels (e.g., using `duplicati` labels in other recipes).
* **Domain Name**: Use host pattern `<subdomain>.srv.kllnr.de` (e.g., `"traefik.http.routers.pihole.rule=Host(\`pihole.srv.kllnr.de\`)"`).
* **SSL Resolvers**: By default, use `dns_certresolver` and entrypoint `websecure`.
