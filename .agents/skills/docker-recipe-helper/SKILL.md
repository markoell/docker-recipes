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
1. **Compose Configuration Presence**: Checks if each subfolder contains `docker-compose.yml` or `compose.yaml`.
2. **YAML Parsing**: Ensures all compose files are syntactically valid YAML.
3. **Traefik Router Consistency**: Validates that any Traefik labels (e.g. `traefik.http.routers.<router-name>`) use router names that match either the service name or the folder name. It flags copy-paste errors (like using `duplicati` as a router name in `pi-hole`).
4. **Volume Path Placeholders**: Detects absolute paths on the host and suggests using the standard `CHANGE_TO_COMPOSE_DATA_PATH/<recipe-name>/...` placeholder.
