#!/usr/bin/env python3
"""OpenReview Docker Compose development tool.

Manages the full test/development stack: API servers, web frontend,
infrastructure services (MongoDB, Redis, Elasticsearch).

Modes:
  test (default)  Run pytest then tear down all services
  serve           Start services for browser testing, keep running
  shell           Interactive shell in a container
  setup-only      Start infrastructure, no tests
"""

import argparse
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
COMPOSE_FILE = SCRIPT_DIR / "docker-compose.yml"
COMPOSE_SERVE_FILE = SCRIPT_DIR / "docker-compose.serve.yml"
CONFIG_FILE = SCRIPT_DIR / "config.json"
CONFIG_EXAMPLE = SCRIPT_DIR / "config.example.json"

VALID_SHELL_TARGETS = {"test", "api-v1", "api-v2", "web"}

DEFAULTS = {
    "api_v1": {"path": "../../openreview-api-v1", "branch": ""},
    "api_v2": {"path": "../../openreview-api", "branch": ""},
    "web": {"path": "../../openreview-web", "branch": ""},
    "mode": "test",
    "auto_checkout": True,
    "keep_infra": False,
}

# Ports exposed to the host in serve mode
SERVE_PORTS = [3000, 3001, 3030]


def load_config():
    """Load config.json, erroring if it doesn't exist."""
    if not CONFIG_FILE.exists():
        print("Error: config.json not found.", file=sys.stderr)
        print(f"Copy the example config and edit it for your setup:", file=sys.stderr)
        print(f"  cp {CONFIG_EXAMPLE.name} {CONFIG_FILE.name}", file=sys.stderr)
        sys.exit(1)

    config = dict(DEFAULTS)
    with open(CONFIG_FILE) as f:
        user_config = json.load(f)
    for key in ("api_v1", "api_v2", "web"):
        if key in user_config:
            config[key] = {**DEFAULTS[key], **user_config[key]}
    if "mode" in user_config:
        config["mode"] = user_config["mode"]
    if "auto_checkout" in user_config:
        config["auto_checkout"] = user_config["auto_checkout"]
    if "keep_infra" in user_config:
        config["keep_infra"] = user_config["keep_infra"]
    return config


def resolve_path(path_str):
    """Resolve a path relative to the docker/ directory, or absolute."""
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (SCRIPT_DIR / p).resolve()


def check_dirty(repo_path, name):
    """Check if a git repo has uncommitted changes. Returns True if dirty."""
    result = subprocess.run(
        ["git", "-C", str(repo_path), "diff", "--quiet"],
        capture_output=True,
    )
    if result.returncode != 0:
        return True
    result = subprocess.run(
        ["git", "-C", str(repo_path), "diff", "--cached", "--quiet"],
        capture_output=True,
    )
    return result.returncode != 0


def checkout_branch(repo_path, branch, name):
    """Checkout a branch in a sibling repo."""
    if not branch:
        return
    if not repo_path.exists():
        print(f"Error: {name} repo not found at {repo_path}", file=sys.stderr)
        sys.exit(1)
    if check_dirty(repo_path, name):
        print(
            f"Error: {name} has uncommitted changes at {repo_path}. "
            f"Commit or stash before auto-checkout.",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"Checking out '{branch}' in {name} ({repo_path})...")
    result = subprocess.run(
        ["git", "-C", str(repo_path), "checkout", branch],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error: git checkout failed in {name}:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)


def check_port_conflicts(ports):
    """Check if any ports are already in use on the host. Exit with guidance if so."""
    import socket
    conflicts = []
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) == 0:
                conflicts.append(port)
    if conflicts:
        print("Error: The following ports are already in use:", file=sys.stderr)
        for port in conflicts:
            print(f"  - Port {port}", file=sys.stderr)
        print(file=sys.stderr)
        print("This may be from a previous run or another process.", file=sys.stderr)
        print("To fix, either:", file=sys.stderr)
        print("  1. Stop the process using the port: lsof -ti:<port> | xargs kill", file=sys.stderr)
        print("  2. Tear down a previous Docker run: cd docker && docker compose down", file=sys.stderr)
        sys.exit(1)


def compose_cmd(serve_mode=False):
    """Build the base docker compose command list."""
    cmd = ["docker", "compose", "-f", str(COMPOSE_FILE)]
    if serve_mode:
        cmd.extend(["-f", str(COMPOSE_SERVE_FILE)])
    return cmd


def run(cmd, check=True, **kwargs):
    """Run a subprocess command, exiting on failure if check=True."""
    result = subprocess.run(cmd, **kwargs)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result


def start_infrastructure(serve_mode=False):
    """Start infrastructure services (mongo, redis, ES, web)."""
    print("=== Starting infrastructure ===")
    cmd = compose_cmd(serve_mode) + ["up", "-d", "--wait", "mongo", "redis", "elasticsearch", "web"]
    run(cmd)


def restart_apis(serve_mode=False):
    """Force recreate API servers for clean database, then start web."""
    print("=== Restarting API servers (clean database) ===")
    base = compose_cmd(serve_mode)
    run(base + ["rm", "-sf", "api-v1", "api-v2"])
    run(base + ["up", "-d", "--wait", "api-v2"])


def start_apis_no_clean(serve_mode=False):
    """Start API servers without cleanStart (preserves existing DB)."""
    print("=== Starting API servers (preserving database) ===")
    os.environ["CLEAN_START"] = "false"
    base = compose_cmd(serve_mode)
    run(base + ["rm", "-sf", "api-v1", "api-v2"])
    run(base + ["up", "-d", "--wait", "api-v1", "api-v2"])


def teardown_apis(serve_mode=False):
    """Stop only API servers and test container, keep infra running."""
    print("=== Stopping API servers ===")
    base = compose_cmd(serve_mode)
    run(base + ["rm", "-sf", "api-v1", "api-v2"], check=False)


def teardown(serve_mode=False):
    """Tear down all services."""
    print("=== Tearing down all services ===")
    cmd = compose_cmd(serve_mode) + ["down"]
    run(cmd, check=False)


def mode_test(pytest_args, no_clean=False, keep_infra=False):
    """Run tests then tear down."""
    try:
        if no_clean:
            start_infrastructure()
            start_apis_no_clean()
        else:
            start_infrastructure()
            restart_apis()

        print("=== Running tests ===")
        cmd = compose_cmd() + ["run", "--rm", "test"] + pytest_args
        result = run(cmd, check=False)
        return result.returncode
    finally:
        if keep_infra:
            teardown_apis()
            print()
            print("Infrastructure (mongo, redis, elasticsearch, web) still running.")
            print("Next run with --no-clean to reuse, or tear down with: docker compose down")
        else:
            teardown()


def mode_serve(pytest_args, no_clean=False, keep_infra=False, shell_target=None):
    """Start services for browser testing, optionally populate with tests."""
    check_port_conflicts(SERVE_PORTS)

    if no_clean:
        start_infrastructure(serve_mode=True)
        start_apis_no_clean(serve_mode=True)
    else:
        start_infrastructure(serve_mode=True)
        restart_apis(serve_mode=True)

    # Run population tests if provided
    if pytest_args:
        print("=== Running tests to populate database ===")
        cmd = compose_cmd(serve_mode=True) + ["run", "--rm", "test"] + pytest_args
        result = run(cmd, check=False)
        if result.returncode != 0:
            print(
                f"\nWarning: Tests exited with code {result.returncode}. "
                "Services are still running.",
                file=sys.stderr,
            )

    print()
    print("Services are running:")
    print("  Web:    http://localhost:3030")
    print("  API v1: http://localhost:3000")
    print("  API v2: http://localhost:3001")
    print()
    print("View logs per service in separate terminals:")
    print("  docker compose logs -f api-v1")
    print("  docker compose logs -f api-v2")
    print("  docker compose logs -f web")
    print("  docker compose logs -f mongo")
    print()

    if shell_target:
        # Drop into a shell; teardown when the shell exits
        print(f"Dropping into {shell_target} shell. Services stay up until you exit.")
        print()
        if shell_target == "test":
            cmd = compose_cmd(serve_mode=True) + ["run", "--rm", "--entrypoint",
                                                   "bash /docker/scripts/test-shell-entrypoint.sh", "test"]
        else:
            cmd = compose_cmd(serve_mode=True) + ["exec", shell_target, "bash"]
        subprocess.run(cmd)
    else:
        # No shell — wait for Ctrl+C
        if keep_infra:
            print("Ctrl+C will stop API servers but keep infrastructure running.")
        else:
            print("Ctrl+C will stop all services.")
        print("Or run 'docker compose down' from another terminal.")
        print()
        try:
            import threading
            threading.Event().wait()
        except KeyboardInterrupt:
            pass

    # Teardown
    if keep_infra:
        teardown_apis(serve_mode=True)
        print("Infrastructure still running. Tear down with: docker compose down")
    else:
        print("\nShutting down...")
        teardown(serve_mode=True)


def mode_shell(target, no_clean=False):
    """Drop into an interactive shell in a container."""
    if no_clean:
        start_infrastructure()
        start_apis_no_clean()
    else:
        start_infrastructure()
        restart_apis()

    if target == "test":
        # Create a new ephemeral test container with the shell entrypoint
        # (sets up venv and deps, then drops into bash)
        cmd = compose_cmd() + ["run", "--rm", "--entrypoint",
                                "bash /docker/scripts/test-shell-entrypoint.sh", "test"]
    else:
        # Exec into an already-running service container
        cmd = compose_cmd() + ["exec", target, "bash"]

    print(f"=== Opening shell in {target} ===")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)



def parse_args():
    parser = argparse.ArgumentParser(
        description="OpenReview Docker Compose development tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s tests/test_client.py              Run a test file, then tear down
  %(prog)s tests/test_client.py -v           Run with verbose pytest output
  %(prog)s --serve                           Start services for browser testing
  %(prog)s --serve tests/test_icml_conf.py   Populate DB, then keep serving
  %(prog)s --serve --shell                   Serve with interactive shell access
  %(prog)s --shell                           Interactive shell in test container
  %(prog)s --shell api-v2                    Shell into the API v2 container
  %(prog)s --branch-api-v2 feat/x -- tests/test_client.py
                                             Checkout branch, run tests
""",
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--test", action="store_const", const="test", dest="mode",
        help="Run tests then tear down (default)",
    )
    mode_group.add_argument(
        "--serve", action="store_const", const="serve", dest="mode",
        help="Start services for browser testing, keep running",
    )

    parser.add_argument(
        "--shell", nargs="?", const="test", metavar="SERVICE",
        choices=sorted(VALID_SHELL_TARGETS),
        help="Interactive shell (default: test, options: api-v1, api-v2, web). Can combine with --serve.",
    )

    parser.add_argument(
        "--branch-api-v1", metavar="BRANCH",
        help="Checkout this branch in the api-v1 repo",
    )
    parser.add_argument(
        "--branch-api-v2", metavar="BRANCH",
        help="Checkout this branch in the api-v2 repo",
    )
    parser.add_argument(
        "--branch-web", metavar="BRANCH",
        help="Checkout this branch in the web repo",
    )
    parser.add_argument(
        "--no-checkout", action="store_true",
        help="Skip auto-checkout even if config enables it",
    )
    parser.add_argument(
        "--no-clean", action="store_true",
        help="Preserve existing DB (skip API server restart/cleanStart)",
    )
    parser.add_argument(
        "--keep-infra", action="store_true", default=None,
        help="Keep infrastructure (mongo, redis, ES, web) running after tests",
    )
    parser.add_argument(
        "pytest_args", nargs="*", metavar="PYTEST_ARG",
        help="Arguments passed through to pytest",
    )

    args = parser.parse_args()

    # Determine mode
    args.shell_target = args.shell  # None if not specified
    if args.shell is not None and not args.mode:
        # --shell alone (no --serve, --test, etc.)
        args.resolved_mode = "shell"
    elif args.mode:
        args.resolved_mode = args.mode
    else:
        args.resolved_mode = None  # will be resolved from config

    return args


def main():
    args = parse_args()
    config = load_config()

    # Resolve mode: CLI > config > default
    mode = args.resolved_mode or config.get("mode", "test")

    # Resolve paths
    api_v1_path = resolve_path(config["api_v1"]["path"])
    api_v2_path = resolve_path(config["api_v2"]["path"])
    web_path = resolve_path(config["web"]["path"])

    # Resolve branches: CLI overrides > config
    api_v1_branch = args.branch_api_v1 or config["api_v1"]["branch"]
    api_v2_branch = args.branch_api_v2 or config["api_v2"]["branch"]
    web_branch = args.branch_web or config["web"]["branch"]

    # Auto-checkout branches
    auto_checkout = config.get("auto_checkout", True) and not args.no_checkout
    if auto_checkout:
        checkout_branch(api_v1_path, api_v1_branch, "api-v1")
        checkout_branch(api_v2_path, api_v2_branch, "api-v2")
        checkout_branch(web_path, web_branch, "web")

    # Resolve keep_infra: CLI > config > default
    keep_infra = args.keep_infra if args.keep_infra is not None else config.get("keep_infra", False)

    # Export paths as environment variables for docker compose
    os.environ["API_V1_PATH"] = str(api_v1_path)
    os.environ["API_V2_PATH"] = str(api_v2_path)
    os.environ["WEB_PATH"] = str(web_path)

    if mode == "test":
        rc = mode_test(args.pytest_args, no_clean=args.no_clean, keep_infra=keep_infra)
        sys.exit(rc)
    elif mode == "serve":
        mode_serve(args.pytest_args, no_clean=args.no_clean, keep_infra=keep_infra,
                   shell_target=args.shell_target)
    elif mode == "shell":
        mode_shell(args.shell_target, no_clean=args.no_clean)
    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
