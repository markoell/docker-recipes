# Workspace Guidelines: Docker Recipes

This repository contains personal Docker and Docker Compose configurations, organized as a monorepo where each subdirectory is a standalone recipe.

## 1. Directory Structure & File Naming
* Each subdirectory represents one recipe (e.g., `traefik`, `pi-hole`, `duplicati`).
* Inside each subdirectory, there must be a Docker Compose file named exactly `compose.yaml`. The legacy `docker-compose.yml` name must not be used.
* Optional environment file `.env` can be placed in the same folder if needed.
* Do not specify the obsolete/deprecated `version` header in any `compose.yaml` files.

## 2. Environment Variables & Volume Mounts
* **PUID / PGID**: Use `${PUID}` and `${PGID}` instead of hardcoded UID/GID.
* **Time Zone**: Use `${TZ}`.
* **Local Paths (Lightweight)**: For lightweight configs/databases, relative paths within the recipe directory (e.g., `./config` or `./data`) must be used.
* **Persistent Paths (Heavy)**: For heavy persistent data (like media, downloads, backups), use the environment variable `${DATA_PATH}/<recipe-name>/...`.
* **System/Monitoring Mounts**: Host system paths (e.g., `/proc`, `/sys`, `/dev`, `/var/lib/docker`, `/etc/machine-id`, `/var/run/docker.sock`) are whitelisted only for system monitoring or daemon integration services (such as `cadvisor` and `node-exporter`).

## 3. Traefik Routing & Network Conventions
When exposing a service via Traefik:
* **Network Mode**: Traefik runs on a shared Docker bridge network named `proxy`. All services routed by Traefik must join this network (declared as `external: true` in their compose files).
* **Traefik Network Configuration**: Traefik must be configured with `--providers.docker.network=proxy` to ensure correct routing for multi-network containers.
* **Enable Label**: Enable Traefik with the label `"traefik.enable=true"`.
* **Router Names**: Always ensure that the router name prefix in the labels (e.g., `traefik.http.routers.<router-name>`) matches the recipe subdirectory name or service name. Avoid copy-pasting labels.
* **Domain Name**: Use host pattern `<subdomain>.srv.kllnr.de` (e.g., `"traefik.http.routers.pihole.rule=Host(\`pihole.srv.kllnr.de\`)"`).
* **SSL Resolvers**: By default, use `dns_certresolver` and entrypoint `websecure`.
