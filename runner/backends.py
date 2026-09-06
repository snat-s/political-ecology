"""Execute the shared harness locally or on Modal and release resources."""

import os
import shutil
import subprocess
import threading

from runner.config import ROOT


def run_modal(args, run_dir, credentials):
    """Run a bounded sandbox and copy artifacts before terminating it."""
    import modal

    image = modal.Image.from_dockerfile(
        str(ROOT / "Dockerfile"), context_dir=str(ROOT), add_python="3.11"
    )
    app = modal.App.lookup("political-ecology", create_if_missing=True)
    # Each agent runs a separate Node/Pi process. Preserve the small-run
    # allocation while scaling larger fleets in groups of ten agents.
    resource_groups = max(1, (args.agents + 9) // 10)
    with modal.enable_output():
        sandbox = modal.Sandbox.create(
            "sleep",
            "infinity",
            app=app,
            image=image,
            secrets=[modal.Secret.from_dict(credentials)],
            timeout=args.timeout + 120,
            cpu=2 * resource_groups,
            memory=2048 * resource_groups,
            outbound_domain_allowlist=args.api_domain,
        )
    (run_dir / "sandbox-id.txt").write_text(sandbox.object_id)
    print(f"Sandbox: {sandbox.object_id}", flush=True)
    try:
        sandbox.filesystem.copy_from_local(
            run_dir / "config.json", "/experiment/config.json"
        )
        process = sandbox.exec(
            "timeout",
            "--signal=TERM",
            "--kill-after=5",
            str(args.timeout),
            "python3",
            "-m",
            "harness.fleet",
        )

        def drain_errors():
            with (run_dir / "stderr.log").open("w") as output:
                for line in process.stderr:
                    output.write(line)

        errors = threading.Thread(target=drain_errors)
        errors.start()
        with (run_dir / "fleet.log").open("w") as output:
            for line in process.stdout:
                output.write(line)
                output.flush()
        process.wait()
        errors.join()
        for remote_path, local_name in [
            ("/experiment/shared/shared.txt", "shared.txt"),
            ("/experiment/state/economy.sqlite", "economy.sqlite"),
        ]:
            try:
                sandbox.filesystem.copy_to_local(
                    remote_path, run_dir / local_name
                )
            except modal.exception.SandboxFilesystemNotFoundError:
                pass
        return process.returncode
    finally:
        sandbox.terminate()


def run_local(args, run_dir, credentials):
    """Run a disposable Docker/Podman container with only its output mounted."""
    engine = args.engine or shutil.which("docker") or shutil.which("podman")
    if not engine:
        raise RuntimeError(
            "Install Docker or Podman, or select --backend modal"
        )
    subprocess.run(
        [engine, "build", "-t", "political-ecology:local", str(ROOT)],
        check=True,
    )
    command = [
        engine,
        "run",
        "--rm",
        "--init",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--memory=2g",
        "--cpus=2",
        "-v",
        f"{run_dir}:/experiment:Z",
    ]
    for key in credentials:
        command.extend(["--env", key])
    command.extend(
        [
            "political-ecology:local",
            "timeout",
            "--signal=TERM",
            "--kill-after=5",
            str(args.timeout),
            "python3",
            "-m",
            "harness.fleet",
        ]
    )
    with (run_dir / "fleet.log").open("w") as output:
        return subprocess.run(
            command,
            env={**os.environ, **credentials},
            stdout=output,
            stderr=subprocess.STDOUT,
        ).returncode
