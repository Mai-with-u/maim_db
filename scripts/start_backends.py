#!/usr/bin/env python3
"""Utility launcher for MaiMBot reply backend and MaimConfig config backend.

Run this script from anywhere to start both services from the shared mono-repo.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAIMBOT_DIR = (REPO_ROOT / ".." / "MaiMBot").resolve()
DEFAULT_MAIMCONFIG_DIR = (REPO_ROOT / ".." / "MaimConfig").resolve()
DEFAULT_LOG_DIR = REPO_ROOT / "logs" / "backends"


@dataclass
class ServiceCommand:
    name: str
    cmd: List[str]
    cwd: Path
    env: Dict[str, str]
    log_path: Path
    process: Optional[subprocess.Popen] = None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start MaiMBot reply backend and MaimConfig config backend from one place.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """Examples:
            ------------
            # Start both services with defaults
            python scripts/start_backends.py

            # Use custom ports and disable MaiMBot
            python scripts/start_backends.py --skip-maimbot --maimconfig-port 18080
            """
        ),
    )
    parser.add_argument("--python", default=sys.executable, help="Python interpreter used for both services.")
    parser.add_argument("--maimbot-dir", default=DEFAULT_MAIMBOT_DIR, type=Path, help="Path to MaiMBot repository root.")
    parser.add_argument(
        "--maimbot-entry",
        default="src/main.py",
        help="Entry script relative to the MaiMBot directory.",
    )
    parser.add_argument(
        "--maimbot-env",
        default=None,
        type=Path,
        help="Optional .env file to source before starting MaiMBot.",
    )
    parser.add_argument(
        "--maimbot-extra",
        nargs=argparse.REMAINDER,
        default=None,
        help="Extra arguments appended to the MaiMBot command (use '--' to separate).",
    )
    parser.add_argument("--maimconfig-dir", default=DEFAULT_MAIMCONFIG_DIR, type=Path, help="Path to MaimConfig repository root.")
    parser.add_argument("--maimconfig-host", default="0.0.0.0", help="Host for the MaimConfig uvicorn server.")
    parser.add_argument("--maimconfig-port", default=8000, type=int, help="Port for the MaimConfig uvicorn server.")
    parser.add_argument(
        "--maimconfig-log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Log level for uvicorn.",
    )
    parser.add_argument(
        "--maimconfig-reload",
        action="store_true",
        help="Enable uvicorn --reload for hot reloading.",
    )
    parser.add_argument(
        "--log-dir",
        default=DEFAULT_LOG_DIR,
        type=Path,
        help="Directory to store aggregated service logs.",
    )
    parser.add_argument("--grace-period", type=float, default=10.0, help="Seconds to wait before force-killing services on exit.")
    parser.add_argument("--skip-maimbot", action="store_true", help="Skip launching the MaiMBot reply backend.")
    parser.add_argument("--skip-maimconfig", action="store_true", help="Skip launching the MaimConfig backend.")
    return parser.parse_args()


def _load_env_file(path: Optional[Path]) -> Dict[str, str]:
    env_updates: Dict[str, str] = {}
    if not path:
        return env_updates
    if not path.exists():
        raise FileNotFoundError(f"Env file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            env_updates[key.strip()] = value.strip()
    return env_updates


def _build_services(args: argparse.Namespace, timestamp: str) -> List[ServiceCommand]:
    services: List[ServiceCommand] = []
    env_template = os.environ.copy()

    if not args.skip_maimconfig:
        maimconfig_dir = args.maimconfig_dir.expanduser().resolve()
        if not (maimconfig_dir / "main.py").exists():
            raise FileNotFoundError(f"Cannot locate main.py in {maimconfig_dir}")
        cmd = [
            args.python,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            args.maimconfig_host,
            "--port",
            str(args.maimconfig_port),
            "--log-level",
            args.maimconfig_log_level,
        ]
        if args.maimconfig_reload:
            cmd.append("--reload")
        services.append(
            ServiceCommand(
                name="maimconfig",
                cmd=cmd,
                cwd=maimconfig_dir,
                env=dict(env_template),
                log_path=args.log_dir / f"{timestamp}_maimconfig.log",
            )
        )

    if not args.skip_maimbot:
        maimbot_dir = args.maimbot_dir.expanduser().resolve()
        entry = maimbot_dir / args.maimbot_entry
        if not entry.exists():
            raise FileNotFoundError(f"Cannot locate {args.maimbot_entry} in {maimbot_dir}")
        env = dict(env_template)
        env.update(_load_env_file(args.maimbot_env))
        cmd = [args.python, args.maimbot_entry]
        if args.maimbot_extra:
            cmd.extend(args.maimbot_extra)
        services.append(
            ServiceCommand(
                name="maimbot",
                cmd=cmd,
                cwd=maimbot_dir,
                env=env,
                log_path=args.log_dir / f"{timestamp}_maimbot.log",
            )
        )

    return services


def _launch_service(service: ServiceCommand) -> None:
    service.log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = service.log_path.open("a", encoding="utf-8")
    log_file.write(f"[{_dt.datetime.now().isoformat()}] Starting {service.name}: {' '.join(service.cmd)}\n")
    log_file.flush()
    service.process = subprocess.Popen(
        service.cmd,
        cwd=str(service.cwd),
        env=service.env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )
    log_file.close()


def _stop_service(service: ServiceCommand, grace_period: float) -> None:
    proc = service.process
    if not proc or proc.poll() is not None:
        return
    print(f"Stopping {service.name}...", flush=True)
    proc.terminate()
    try:
        proc.wait(timeout=grace_period)
    except subprocess.TimeoutExpired:
        print(f"{service.name} did not stop in {grace_period}s, killing...", flush=True)
        proc.kill()


def _monitor(services: List[ServiceCommand], grace_period: float) -> int:
    active = [svc for svc in services if svc.process]
    exit_code = 0
    try:
        while active:
            for svc in list(active):
                proc = svc.process
                if proc is None:
                    active.remove(svc)
                    continue
                ret = proc.poll()
                if ret is None:
                    continue
                print(f"✅ {svc.name} exited with code {ret}")
                exit_code = exit_code or ret
                active.remove(svc)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCtrl+C received, shutting down services...", flush=True)
    finally:
        for svc in services:
            _stop_service(svc, grace_period)
    return exit_code


def main() -> int:
    args = _parse_args()
    args.log_dir = args.log_dir.expanduser().resolve()
    args.log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    services = _build_services(args, timestamp)

    if not services:
        print("No services requested. Use --skip-* flags to control selection.")
        return 0

    for svc in services:
        print(f"Launching {svc.name} (logs -> {svc.log_path})")
        _launch_service(svc)

    print("All requested services launched. Press Ctrl+C to stop.")
    exit_code = _monitor(services, args.grace_period)
    print("Done.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
