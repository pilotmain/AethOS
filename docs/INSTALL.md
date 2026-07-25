# Install AethOS

AethOS has native, resumable installers for macOS, Linux, and Windows. They
install into the current AethOS checkout when run locally, or clone the public
repository into `~/aethos` when streamed from the web.

## One-command setup

macOS or Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/pilotmain/AethOS/main/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/pilotmain/AethOS/main/install.ps1 | iex
```

Windows using the built-in `curl.exe`:

```powershell
curl.exe -fsSL https://raw.githubusercontent.com/pilotmain/AethOS/main/install.ps1 | powershell.exe -NoProfile -ExecutionPolicy Bypass -Command -
```

For higher assurance, clone a tagged release, inspect the installer, and run it
locally instead of piping a network response into a shell.

## What the installer does

1. Checks the operating system, Git, Python 3.11+, Node.js 20+, npm, and disk.
2. Uses the current checkout or clones the selected branch/tag.
3. Creates an isolated Python virtual environment and installs AethOS, cloud
   adapters, and secure-vault support.
4. Creates `.env` from `.env.example` only when no `.env` exists.
5. Installs the locked Mission Control graph with `npm ci` and preserves any
   existing `web/.env.local`.
6. Imports the API, exercises the CLI, and type-checks Mission Control.

It does not invoke `sudo`, install global packages, start a background service,
write credentials, enable provider mutations, or enable host shell execution.

## Start and verify

macOS or Linux:

```bash
cd ~/aethos
./run.sh
```

Windows:

```powershell
cd ~/aethos
.\run.ps1
```

Then open http://localhost:3000 and complete the first-run wizard. In another
terminal, run `.venv/bin/aethos doctor` on macOS/Linux or
`.\.venv\Scripts\aethos.exe doctor` on Windows.

## Resume and inspect progress

Each successful stage writes a versioned marker. A failed run preserves those
markers, shows the last command output, and prints a recovery command.

| Action | macOS / Linux | Windows |
|---|---|---|
| Continue | `./install.sh --resume` | `.\install.ps1 -Resume` |
| Show status | `./install.sh --status` | `.\install.ps1 -Status` |
| Explain a stage | `./install.sh --help-step verify` | `.\install.ps1 -HelpStep verify` |
| Re-run from a stage | `./install.sh --from frontend` | `.\install.ps1 -From frontend` |
| Full command help | `./install.sh --help` | `.\install.ps1 -Help` |

Stages are `preflight`, `source`, `backend`, `frontend`, and `verify`.
Installer state and its detailed log live under `.aethos-installer/` in a local
checkout, or next to the target directory until the remote clone exists. The
state contains no credentials.

If a streamed run stops before the repository is cloned, there is no local
installer file yet. The error output therefore prints a stream-safe continuation
command. Its equivalent is:

```bash
curl -fsSL https://raw.githubusercontent.com/pilotmain/AethOS/main/install.sh | bash -s -- --resume
```

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/pilotmain/AethOS/main/install.ps1))) -Resume
```

## Common options

- Custom install directory: `--install-dir PATH` / `-InstallDir PATH`
- Install a release tag: `--branch v0.2.0` / `-Branch v0.2.0`
- API/CLI only: `--skip-web` / `-SkipWeb`
- Full dependency output: `--detailed` / `-Detailed`
- Custom ports: `--api-port`, `--web-port` / `-ApiPort`, `-WebPort`

When streaming the installer, set `AETHOS_INSTALL_DIR`, `AETHOS_BRANCH`, or
the port environment variables before the command. Run a local copy when you
need to pass multiple command-line options.

## Upgrade

Re-run the installer. A clean Git checkout is fast-forwarded, dependencies are
reconciled from the project and lock files, and configuration is preserved. If
the checkout has local changes, the source update is skipped rather than
overwriting them. Update or stash those changes yourself, then resume.

## Uninstall

AethOS deliberately has no destructive uninstall command. Stop `run.sh` or
`run.ps1`, back up `.env` and any required local data, and remove the explicit
installation and installer-state directories yourself.
