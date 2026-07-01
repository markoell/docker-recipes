---
name: docker-recipe-helper
description: Helper skill to validate, analyze, and manage Docker recipes with strict security checks (read-only, capability drops, isolated networks).
---

# Docker Recipe Helper Skill

This skill helps validate and enforce strict security standards for Docker recipes in this repository.

## Commands

### Validation Script
You can validate the repository recipes using the Python validation script located at `.agents/skills/docker-recipe-helper/scripts/validate_recipes.py`.

Run it from the root of the workspace:
```bash
python3 .agents/skills/docker-recipe-helper/scripts/validate_recipes.py
```

### What It Validates
1. **Compose Name**: Enforces `compose.yaml` (forbids `docker-compose.yml` and `version` headers).
2. **Strict Security & Isolation**:
   - Ensures `user: "${PUID}:${PGID}"` is defined.
   - Ensures `cap_drop: - ALL` is defined for all services.
   - Ensures `read_only: true` is defined.
   - Ensures `tmpfs` mounts are present for transient state.
3. **Network Isolation**: Ensures exposed services use isolated proxy networks named `<recipe_name>_proxy`, instead of a shared global network. It flags any service still using the shared `proxy` network.
4. **Volume Mounts**: Warns about absolute host paths. Restricts persistent mounts to relative paths or `${DATA_PATH}`.
5. **Traefik Labels**: Validates router names, `dns_certresolver`, and the `.srv.kllnr.de` domain.
