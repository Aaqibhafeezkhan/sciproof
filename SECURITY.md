# Security policy

## Reporting a vulnerability

Please do **not** open a public issue for security problems. Use GitHub's private
vulnerability reporting: open the repository's **Security** tab and choose **Report a
vulnerability**. Include the SciProof version, a minimal manifest or command that shows the
problem, and the impact you expect. Maintainers will acknowledge reports as soon as they can;
this is a volunteer project, so there is no guaranteed response time.

Supported versions: the latest `0.x` release only (the project is alpha).

## Threat model

SciProof is a local command line tool run by a user who wants to check evidence of a
computation.

**Assets:** the user's files and credentials, and the trustworthiness of a verdict.

**Untrusted input:** manifests, and the files they list. A manifest you received from someone
else (a collaborator, a repository, a pull request) must be treated like a shell script from
the same source: it contains a command.

### What SciProof does about it

| Risk | Mitigation |
| --- | --- |
| A manifest makes the tool run code | `inspect` and plain `verify` never execute the recorded command or probe interpreters (tests monkeypatch `subprocess` to prove it). Re-execution needs `verify --rerun` **and** an interactive "yes" or `--yes`. Without a terminal and without `--yes` it refuses (exit status 3). |
| The user does not see what will run | The confirmation prompt prints the exact command, the working directory, and a reminder that it runs with the current user's permissions. |
| Path traversal / reading or overwriting files outside the project | Every path from a manifest must be relative, free of `..`, drive letters, backslashes and NUL; it is resolved (following symlinks) and must stay inside the manifest's directory. Violations make the manifest invalid or the check `FAIL`/`INCONCLUSIVE`; a rerun is not started if any declared path is unsafe. |
| Terminal escape sequences in manifest text | All manifest strings are escaped before printing. |
| Identifying information in a manifest | `--record-hardware` is opt-in and records only the CPU count, the processor string and the name, driver version and memory of NVIDIA GPUs: no host name, user name, serial number or GPU UUID. A `--note` is free text that you write; do not put secrets in it. |
| Leaking secrets into manifests | Only an allowlist of non-secret environment variables is recorded; Git remote URLs are not recorded; absolute directories and user names are not recorded; stdout/stderr are truncated (full stream is only hashed). The command line and the first bytes of output are stored: **review `stdout`, `stderr` and the command for secrets before sharing a manifest.** |
| Denial of service by huge or deeply nested manifests | Manifest size limit (16 MiB), size limit for numeric files (64 MiB), recursion errors handled, rerun timeout (default 1 hour). |
| Automatic installation or privilege escalation | SciProof never installs dependencies and never uses elevated privileges. |
| CI abuse | The workflow uses only `pull_request` with a read-only token and no secrets; it never runs untrusted pull-request code in a privileged context. |

### What SciProof does **not** protect against (known limitations)

* **A confirmed rerun is arbitrary code execution** with your permissions. SciProof does not
  sandbox it. Run untrusted manifests in a disposable VM or container.
* **A rerun inherits your whole environment.** The recorded command starts with a copy of
  the environment of the process that runs `sciproof verify --rerun`, including variables such as
  `AWS_SECRET_ACCESS_KEY` or `GITHUB_TOKEN`, so a manifest from someone else can read them. The
  allowlist described above only limits what is *recorded*, not what the command can *see*.
  Use `verify --rerun --clean-env` (add variables with `--pass-env NAME`) to hand the command only
  `PATH`, temp directories and the numerics-related allowlist; the report lists the *names* that
  were passed, never values. `--clean-env` does not restrict files, network or processes, so it
  reduces what an untrusted command can read from the environment and is not a sandbox. For
  untrusted manifests still use a disposable VM or container.
* **Manifests are not signed.** Hashes detect accidental or naive changes after capture; they
  do not stop someone who can rewrite both the manifest and the files from fabricating
  consistent evidence. Distribute manifests through a channel you trust (signed Git commits,
  release signing, timestamping) if that matters.
* **Time-of-check/time-of-use races** between the hash check and the rerun are not handled.
* **Declared files only.** Undeclared inputs, network access and system state are invisible.
* The interpreter probe at capture time executes the command's Python interpreter with a fixed
  snippet; it is only done for commands the user typed themselves.
* The symlink-escape tests are skipped on systems where unprivileged symlinks are unavailable
  (for example default Windows); they run on Linux in CI.
