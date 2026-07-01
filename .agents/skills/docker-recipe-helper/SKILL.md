---
name: docker-recipe-helper
description: Helper skill to validate, analyze, and manage Docker recipes, including checking for copy-paste label errors, invalid volumes, or compose syntax errors.
---

# Docker Recipe Helper Skill

This skill helps validate and manage Docker recipes in this repository.

## Commands

### Validation Script
You can validate the repository recipes using the Python validation script located at `.agents/skills/docker-recipe-helper/scripts/validate_recipes.py`.

Run it from the root of the workspace:
```bash
python3 .agents/skills/docker-recipe-helper/scripts/validate_recipes.py
```

### What It Validates
1. **Compose Configuration Presence**: Checks if each subfolder contains `compose.yaml`. The legacy name `docker-compose.yml` is flagged.
2. **YAML Parsing**: Ensures all compose files are syntactically valid YAML.
3. **Deprecated Syntax**: Ensures the obsolete `version` header is removed.
4. **Traefik Router Consistency**: Validates that any Traefik labels (e.g. `traefik.http.routers.<router-name>`) use router names matching either the service name or the folder name. It checks for the correct certresolver (`dns_certresolver`) and domain (`.srv.kllnr.de`).
5. **Volume Path Standards**: Detects hardcoded host paths and warns if they do not use the standard `${DATA_PATH}` environment variable or are not relative (`./data`, `./config`). It allows whitelisted system paths (`/proc`, `/sys`, etc.) for monitoring services.
6. **Network Routing**: Checks that Traefik-exposed services are attached to the `proxy` network.

