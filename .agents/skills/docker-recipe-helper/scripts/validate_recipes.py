#!/usr/bin/env python3
import os
import sys
import yaml

# ANSI Color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_err(msg):
    print(f"{RED}{BOLD}ERROR:{RESET} {msg}")

def print_warn(msg):
    print(f"{YELLOW}{BOLD}WARN:{RESET} {msg}")

def print_info(msg):
    print(f"{BLUE}INFO:{RESET} {msg}")

def validate_recipe(recipe_dir, compose_file):
    recipe_name = os.path.basename(recipe_dir)
    errors = 0
    warnings = 0

    try:
        with open(compose_file, 'r') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print_err(f"[{recipe_name}] Failed to parse YAML in {os.path.basename(compose_file)}: {e}")
        return 1, 0

    if not data or not isinstance(data, dict):
        print_err(f"[{recipe_name}] Invalid compose format in {os.path.basename(compose_file)}")
        return 1, 0

    services = data.get('services', {})
    if not isinstance(services, dict):
        print_err(f"[{recipe_name}] 'services' section must be a dictionary")
        return 1, 0

    for service_name, service_config in services.items():
        if not service_config or not isinstance(service_config, dict):
            continue

        # 1. Validate Traefik labels
        labels = service_config.get('labels', [])
        label_pairs = {}
        if isinstance(labels, list):
            for label in labels:
                if isinstance(label, str) and '=' in label:
                    k, v = label.split('=', 1)
                    label_pairs[k.strip()] = v.strip()
        elif isinstance(labels, dict):
            label_pairs = labels

        for k, v in label_pairs.items():
            if k.startswith('traefik.http.routers.'):
                parts = k.split('.')
                if len(parts) >= 4:
                    router_name = parts[3]
                    # Check if router_name is inconsistent
                    # Ignore standard wildcard or matching patterns
                    normalized_recipe = recipe_name.replace('-', '').lower()
                    normalized_service = service_name.replace('-', '').lower()
                    normalized_router = router_name.replace('-', '').lower()

                    if normalized_router != normalized_recipe and normalized_router != normalized_service:
                        # Extra check: is it duplicati? Or just a general mismatch?
                        if normalized_router == 'duplicati' and normalized_recipe != 'duplicati':
                            print_err(f"[{recipe_name}] Service '{service_name}' uses copy-pasted Traefik router name '{router_name}' in label '{k}'")
                            errors += 1
                        else:
                            print_warn(f"[{recipe_name}] Service '{service_name}' uses router name '{router_name}' in label '{k}' which does not match recipe folder or service name")
                            warnings += 1

        # 2. Validate volumes
        volumes = service_config.get('volumes', [])
        if isinstance(volumes, list):
            for volume in volumes:
                if isinstance(volume, str):
                    parts = volume.split(':')
                    host_path = parts[0]
                    # Check if it's a host path
                    if host_path.startswith('/'):
                        # Allowed system files
                        if host_path in ['/var/run/docker.sock', '/var/run/docker.sock:ro']:
                            continue
                        if not host_path.startswith('CHANGE_TO_COMPOSE_DATA_PATH'):
                            print_warn(f"[{recipe_name}] Service '{service_name}' uses hardcoded host path '{host_path}' instead of placeholder 'CHANGE_TO_COMPOSE_DATA_PATH'")
                            warnings += 1

    return errors, warnings

def main():
    # Detect workspace dir automatically
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
    if not os.path.exists(os.path.join(workspace_dir, "LICENSE")):
        workspace_dir = os.getcwd()

    print_info(f"Scanning workspace: {workspace_dir}")

    exclude_dirs = {'.git', '.agents', '.gemini', 'node_modules', 'artifacts'}
    
    total_errors = 0
    total_warnings = 0
    recipe_count = 0

    for item in sorted(os.listdir(workspace_dir)):
        item_path = os.path.join(workspace_dir, item)
        if not os.path.isdir(item_path) or item in exclude_dirs or item.startswith('.'):
            continue

        recipe_count += 1
        compose_file = None
        for name in ['docker-compose.yml', 'compose.yaml']:
            path = os.path.join(item_path, name)
            if os.path.exists(path):
                compose_file = path
                break

        if not compose_file:
            print_warn(f"[{item}] No docker-compose.yml or compose.yaml found in recipe folder")
            total_warnings += 1
            continue

        err, warn = validate_recipe(item_path, compose_file)
        total_errors += err
        total_warnings += warn

    print("\n" + "="*40)
    print(f"Validation Summary:")
    print(f"  Recipes checked: {recipe_count}")
    print(f"  Total errors:    {RED if total_errors else GREEN}{total_errors}{RESET}")
    print(f"  Total warnings:  {YELLOW if total_warnings else GREEN}{total_warnings}{RESET}")
    print("="*40)

    if total_errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
