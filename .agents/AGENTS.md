# Workspace Guidelines: Docker Recipes

This repository contains personal Docker and Docker Compose configurations, organized as a monorepo where each subdirectory is a standalone recipe. We enforce a **Security & Isolation First** philosophy.

## 1. Directory Structure & File Naming
* Each subdirectory represents one recipe.
* Inside each subdirectory, the Docker Compose file must be named exactly `compose.yaml`. The legacy `docker-compose.yml` is forbidden.
* Do not specify the obsolete `version` header.
* Environment file `.env` can be placed in the same folder if needed.

## 2. Rootless, Permissions & Filesystems
We prioritize strict container lockdown:
* **User Directive**: Every service must explicitly declare `user: "${PUID}:${PGID}"` (unless using a scratch/rootless specific image that breaks otherwise, but by default it is required).
* **Capabilities**: Every service must drop all capabilities using `cap_drop: - ALL`.
* **Read-Only Root**: Every service must declare `read_only: true` for its root filesystem.
* **Transient State**: Because the root filesystem is read-only, services must use `tmpfs` mounts for `/tmp`, `/var/run`, or `/run` to function.

## 3. Persistent Volumes
* **Local Paths**: For lightweight configs, use relative paths (`./config` or `./data`).
* **Persistent Paths**: For heavy data, use `${DATA_PATH}/<recipe-name>/...`.
* **System Mounts**: Host paths like `/proc` or `/sys` are strictly whitelisted only for monitoring tools.

## 4. Isolated Proxy Networks & Traefik
We avoid a globally shared network for exposed services.
* **Isolated Networks**: Each exposed service must use its own dedicated proxy bridge network. The network must be named exactly `<recipe_name>_proxy`.
* **Enable Label**: `"traefik.enable=true"`.
* **Router Names**: Router name prefix (`traefik.http.routers.<router-name>`) must match the recipe or service name.
* **Domain Name**: Use `<subdomain>.srv.kllnr.de`.
* **SSL Resolvers**: Use `dns_certresolver` and entrypoint `websecure`.
