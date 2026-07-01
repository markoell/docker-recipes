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

# Whitelisted system paths that monitoring or special daemon services are allowed to bind-mount.
WHITELISTED_SYSTEM_PATHS = [
    '/',
    '/var/run',
    '/var/run/docker.sock',
    '/proc',
    '/sys',
    '/dev',
    '/etc/machine-id',
    '/var/lib/docker'
]

def is_system_path_whitelisted(path):
    # Strip any volume mount options like :ro, :rw, :z, etc.
    clean_path = path.split(':')[0]
    if clean_path != '/':
        clean_path = clean_path.rstrip('/')
    for whitelisted in WHITELISTED_SYSTEM_PATHS:
        if clean_path == whitelisted or clean_path.startswith(whitelisted + '/'):
            return True
    return False

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

    # 1. Check for deprecated 'version' header
    if 'version' in data:
        print_err(f"[{recipe_name}] Deprecated 'version' header is present in {os.path.basename(compose_file)}")
        errors += 1

    services = data.get('services', {})
    if not isinstance(services, dict):
        print_err(f"[{recipe_name}] 'services' section must be a dictionary")
        return 1, 0

    for service_name, service_config in services.items():
        if not service_config or not isinstance(service_config, dict):
            continue

        # 2. Check host network mode vs ports
        net_mode = service_config.get('network_mode')
        ports = service_config.get('ports', [])
        if net_mode == 'host' and ports:
            print_err(f"[{recipe_name}] Service '{service_name}' specifies network_mode: 'host' but also defines 'ports', which is ignored and syntactically invalid")
            errors += 1

        # 3. Security Checks (user, read_only, cap_drop)
        # Check user
        user = service_config.get('user')
        if user != "${PUID}:${PGID}":
            print_err(f"[{recipe_name}] Service '{service_name}' must explicitly set user: \"${{PUID}}:${{PGID}}\" for strict rootless security")
            errors += 1
            
        # Check read_only
        if service_config.get('read_only') is not True:
            print_err(f"[{recipe_name}] Service '{service_name}' must set read_only: true")
            errors += 1
            
        # Check cap_drop
        cap_drop = service_config.get('cap_drop', [])
        if 'ALL' not in cap_drop:
            print_err(f"[{recipe_name}] Service '{service_name}' must explicitly drop all capabilities (cap_drop: - ALL)")
            errors += 1

        # Check tmpfs if read_only is true
        if service_config.get('read_only') is True:
            tmpfs = service_config.get('tmpfs', [])
            has_tmp_mount = False
            if tmpfs:
                has_tmp_mount = True
            else:
                volumes = service_config.get('volumes', [])
                if isinstance(volumes, list):
                    for v in volumes:
                        if isinstance(v, str):
                            parts = v.split(':')
                            if len(parts) >= 2 and (parts[1] == '/tmp' or parts[1] == '/run' or parts[1] == '/var/run'):
                                has_tmp_mount = True
                
            if not has_tmp_mount:
                print_err(f"[{recipe_name}] Service '{service_name}' is read_only but provides no tmpfs or volume mounts for transient directories like /tmp or /run")
                errors += 1

        # 4. Validate Traefik labels & Proxy network requirement
        labels = service_config.get('labels', [])
        label_pairs = {}
        if isinstance(labels, list):
            for label in labels:
                if isinstance(label, str) and '=' in label:
                    k, v = label.split('=', 1)
                    label_pairs[k.strip()] = v.strip()
        elif isinstance(labels, dict):
            label_pairs = labels

        is_traefik_enabled = False
        for k, v in label_pairs.items():
            if k == 'traefik.enable' and v == 'true':
                is_traefik_enabled = True

            if k.startswith('traefik.http.routers.'):
                parts = k.split('.')
                if len(parts) >= 4:
                    router_name = parts[3]
                    
                    # Validate router name consistency
                    normalized_recipe = recipe_name.replace('-', '').lower()
                    normalized_service = service_name.replace('-', '').lower()
                    normalized_router = router_name.replace('-', '').lower()

                    if normalized_router != normalized_recipe and normalized_router != normalized_service:
                        print_err(f"[{recipe_name}] Service '{service_name}' uses mismatched/copy-pasted Traefik router name '{router_name}' in label '{k}'")
                        errors += 1

                    # Validate domain (.srv.kllnr.de)
                    if parts[-1] == 'rule':
                        # Check Host rule value
                        if 'Host(' in v:
                            if '.srv.kllnr.de' not in v:
                                print_err(f"[{recipe_name}] Service '{service_name}' uses wrong routing domain in label '{k}={v}'. Must use '<subdomain>.srv.kllnr.de'")
                                errors += 1

                    # Validate certresolver
                    if parts[-1] == 'certresolver':
                        if v != 'dns_certresolver':
                            print_err(f"[{recipe_name}] Service '{service_name}' uses wrong certresolver '{v}' in label '{k}'. Must use 'dns_certresolver'")
                            errors += 1

        # 5. Check network isolation when Traefik is enabled
        service_networks = service_config.get('networks', [])
        service_network_list = []
        if isinstance(service_networks, list):
            service_network_list = service_networks
        elif isinstance(service_networks, dict):
            service_network_list = list(service_networks.keys())

        if 'proxy' in service_network_list:
            print_err(f"[{recipe_name}] Service '{service_name}' uses the legacy shared 'proxy' network. Must use an isolated network named '{recipe_name}_proxy'")
            errors += 1

        if is_traefik_enabled and recipe_name != 'traefik':
            expected_network = f"{recipe_name}_proxy"
            if expected_network not in service_network_list:
                print_err(f"[{recipe_name}] Service '{service_name}' is enabled for Traefik but is not connected to its isolated network '{expected_network}'")
                errors += 1

        # 6. Validate volumes
        volumes = service_config.get('volumes', [])
        if isinstance(volumes, list):
            for volume in volumes:
                if isinstance(volume, str):
                    parts = volume.split(':')
                    host_path = parts[0]

                    # Warn about old placeholder
                    if 'CHANGE_TO_COMPOSE_DATA_PATH' in host_path:
                        print_err(f"[{recipe_name}] Service '{service_name}' uses outdated placeholder 'CHANGE_TO_COMPOSE_DATA_PATH' in volume mount '{volume}'")
                        errors += 1
                        continue

                    # Check absolute host path
                    if host_path.startswith('/'):
                        if not is_system_path_whitelisted(host_path):
                            print_warn(f"[{recipe_name}] Service '{service_name}' uses hardcoded host path '{host_path}' instead of environment variable '${{DATA_PATH}}' or a relative path")
                            warnings += 1
                    # Check if it starts with home dir shortcut
                    elif host_path.startswith('~'):
                        print_warn(f"[{recipe_name}] Service '{service_name}' uses home directory path '{host_path}' instead of environment variable '${{DATA_PATH}}' or a relative path")
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
        
        # Check for compose.yaml files. Warn if using docker-compose.yml
        compose_file = None
        has_legacy = os.path.exists(os.path.join(item_path, 'docker-compose.yml'))
        has_modern = os.path.exists(os.path.join(item_path, 'compose.yaml'))

        if has_modern:
            compose_file = os.path.join(item_path, 'compose.yaml')
            if has_legacy:
                print_err(f"[{item}] Contains BOTH compose.yaml and legacy docker-compose.yml. Remove docker-compose.yml")
                total_errors += 1
        elif has_legacy:
            print_err(f"[{item}] Contains legacy 'docker-compose.yml' instead of 'compose.yaml'. Rename it")
            total_errors += 1
            compose_file = os.path.join(item_path, 'docker-compose.yml')
        
        if not compose_file:
            # Only warn if it's not a known directory that doesn't need compose files (like opencloud if it's not a recipe)
            if item != 'opencloud':
                print_warn(f"[{item}] No compose.yaml found in recipe folder")
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
