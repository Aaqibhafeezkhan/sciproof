# Signing a manifest

A manifest records hashes. Hashes detect a changed file; they do not stop someone who can rewrite
both the manifest and the files from producing consistent, false evidence. A **signature** adds
who vouches for the manifest and makes any later edit of the manifest detectable.

SciProof implements no cryptography. It calls OpenSSH (`ssh-keygen -Y`), which has to be installed
(it is on most developer machines), and it never decides whom to trust.

## Sign

```bash
ssh-keygen -t ed25519 -f ~/.ssh/sciproof_ed25519 -C alice@example.org   # once
sciproof sign baseline.sciproof.json --key ~/.ssh/sciproof_ed25519
```

This writes `baseline.sciproof.json.sig` next to the manifest (a detached signature in the
`sciproof-manifest@hayagrivai-labs` namespace, so it cannot be replayed as another kind of
signature). The manifest is validated first, and `ssh-keygen` asks for the key's passphrase itself.
Signing again replaces the old signature.

## Check

You say whom you trust, in an OpenSSH *allowed signers* file: one `principal public-key` per line.

```bash
echo "alice@example.org $(cut -d' ' -f1,2 ~/.ssh/sciproof_ed25519.pub)" > allowed_signers
sciproof verify baseline.sciproof.json --allowed-signers allowed_signers
```

The report gets one more check, `manifest signature`:

| Result | Meaning |
| --- | --- |
| `PASS` | `baseline.sciproof.json.sig` was made by a key in your file, for exactly these bytes. The signer and the key fingerprint are in the message and in the JSON evidence. |
| `FAIL` | The signature is not from a key in your file, is damaged, was made for another purpose (namespace), or the manifest was changed after signing. |
| `INCONCLUSIVE` | There is no `.sig` file, or `ssh-keygen` is not installed. A missing signature is never a pass. |

A manifest cannot name its own trust root: only the file you pass on the command line is read.
A good signature also changes the report's "not checked" list: it no longer says the manifest is
unsigned, and says instead that the experiment's honesty is still not established.

`--allowed-signers` can be combined with `--rerun`; the signature check does not execute anything.
`sciproof list` shows which manifests have a `.sig` file next to them (it does not check it).

## What a good signature does not show

* That the experiment was run as described, or that the result is correct: only that the holder of
  an allowed key vouches for these bytes.
* When it was signed. Without a trusted timestamp, a signer can sign an old manifest later.
* That the key was not stolen. Revocation lists are supported by `ssh-keygen` but not by SciProof.
* That the `allowed_signers` file is yours: it is the trust root, protect it like one.

If the manifest lives in Git, mark it as binary so that `core.autocrlf` cannot change its bytes:
`*.sciproof.json -text` in `.gitattributes`. SciProof writes manifests with LF line endings on
every system.

## Python

```python
import sciproof

sciproof.sign_manifest("baseline.sciproof.json", "~/.ssh/sciproof_ed25519")
report = sciproof.verify_manifest("baseline.sciproof.json", allowed_signers="allowed_signers")
print(report.signature)  # {'status': 'good', 'principal': 'alice@example.org', ...}
```
