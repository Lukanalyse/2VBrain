from __future__ import annotations

import argparse
import json
import os
import threading
import time
from pathlib import Path

import uvicorn


def configure_data_dir(data_dir: Path) -> None:
    data_dir = data_dir.expanduser().resolve()
    config_dir = data_dir / "config"
    vault_dir = data_dir / "vault"
    library_dir = data_dir / "library"

    for directory in (data_dir, config_dir, vault_dir, library_dir):
        directory.mkdir(parents=True, exist_ok=True)

    research_config = config_dir / "research-os.yaml"
    if not research_config.exists():
        research_config.write_text(
            "vault:\n"
            f'  path: "{vault_dir}"\n\n'
            "library:\n"
            f'  path: "{library_dir}"\n\n'
            "llm:\n"
            "  provider: null\n"
            "  model: null\n\n"
            "vector_store:\n"
            "  provider: null\n"
            "  path: null\n",
            encoding="utf-8",
        )

    workspace_config = config_dir / "workspace.json"
    if not workspace_config.exists():
        workspace_config.write_text(
            json.dumps({"vault_path": str(vault_dir)}, indent=2) + "\n",
            encoding="utf-8",
        )

    database_path = data_dir / "research_os.db"
    os.environ["RESEARCH_OS_DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    os.environ["RESEARCH_OS_CONFIG_PATH"] = str(research_config)
    os.environ["RESEARCH_OS_WORKSPACE_CONFIG_PATH"] = str(workspace_config)
    os.environ["RESEARCH_OS_ASSISTANT_CONFIG_PATH"] = str(config_dir / "assistant.json")
    os.environ["RESEARCH_OS_VAULT_PATH"] = str(vault_dir)
    os.environ["RESEARCH_OS_LIBRARY_PATH"] = str(library_dir)
    os.environ["RESEARCH_OS_RUNTIME_ENVIRONMENT"] = "desktop"


def stop_when_parent_exits(parent_pid: int) -> None:
    def watch_parent() -> None:
        while True:
            try:
                os.kill(parent_pid, 0)
            except ProcessLookupError:
                os._exit(0)
            except PermissionError:
                pass
            time.sleep(0.5)

    threading.Thread(target=watch_parent, name="desktop-parent-watch", daemon=True).start()


def main() -> None:
    parser = argparse.ArgumentParser(description="Research OS desktop backend")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--parent-pid", type=int)
    args = parser.parse_args()

    configure_data_dir(args.data_dir)
    if args.parent_pid is not None:
        stop_when_parent_exits(args.parent_pid)

    from main import app

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="warning",
        access_log=False,
    )


if __name__ == "__main__":
    main()
