# Local Firmware Upload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe one-command workflow for flashing MicroPython firmware, deploying the repository's `slave/` application, or doing both.

**Architecture:** A host-side Python CLI reads stable settings from an ignored INI file and always receives the current USB port on the command line. It composes explicit-port `esptool`, normal-REPL upload, and `mpremote reset` operations; the existing normal-REPL uploader gains remote-directory creation so a fresh filesystem can receive the whole application tree.

**Tech Stack:** Python 3 standard library (`argparse`, `configparser`, `pathlib`, `subprocess`, `unittest`), esptool, pyserial, mpremote

**Spec:** `docs/superpowers/specs/2026-09-01-local-firmware-upload-design.md`

## Global Constraints

- Run every Python command with `-B` and create no `__pycache__` or `*.pyc` files.
- Never save an upload or monitor port in configuration.
- Pass the verified port explicitly to every flash, upload, and reset subprocess.
- Never erase flash unless `--erase` is present and the operator confirms `ERASE <port>`.
- Stop immediately when any hardware subprocess fails.
- Do not stage the user's existing untracked `outputs/` directory.

---

### Task 1: Configuration and safe command construction

**Files:**
- Create: `tools/PC/upload_firmware.py`
- Create: `test/protocol/test_upload_firmware.py`

**Interfaces:**
- Produces: `UploadConfig`, `load_config(path)`, `collect_upload_files(source)`, `build_flash_command(config, port)`, `build_upload_command(config, port, local_path, remote_path)`, and `confirm_erase(port, input_fn=input)`.
- `collect_upload_files` returns stable `(local_path, remote_path)` pairs and excludes `__pycache__` directories and `*.py[cod]` files.

- [ ] **Step 1: Write failing configuration, mapping, command, and confirmation tests**

```python
class UploadConfigurationTests(unittest.TestCase):
    def test_rejects_any_saved_port(self):
        with self.assertRaisesRegex(ValueError, "must not store USB ports"):
            upload_firmware.load_config(self.write_ini("port=/dev/cu.bad"))

    def test_maps_application_tree_to_root_and_skips_bytecode(self):
        self.assertEqual(
            [(source / "app.py", "/app.py"),
             (source / "lib" / "sys.py", "/lib/sys.py")],
            upload_firmware.collect_upload_files(source),
        )

    def test_flash_command_contains_the_explicit_port(self):
        command = upload_firmware.build_flash_command(config, "/dev/cu.current")
        self.assertIn("/dev/cu.current", command)

    def test_erase_requires_exact_port_confirmation(self):
        self.assertFalse(upload_firmware.confirm_erase(
            "/dev/cu.current", lambda _prompt: "yes"))
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python -B -m unittest test.protocol.test_upload_firmware -v`

Expected: FAIL because `tools/PC/upload_firmware.py` does not exist.

- [ ] **Step 3: Implement minimal pure configuration and command helpers**

Implement an immutable configuration containing resolved `firmware`, `source`, and `uploader` paths plus tokenized `esptool` and `mpremote` commands. Reject INI option names `port`, `upload_port`, and `monitor_port` before resolving paths. Build commands as argument lists, never shell strings.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python -B -m unittest test.protocol.test_upload_firmware -v`

Expected: all Task 1 tests PASS.

- [ ] **Step 5: Commit Task 1**

```bash
git add tools/PC/upload_firmware.py test/protocol/test_upload_firmware.py
git commit -m "feat: add safe upload configuration core"
```

### Task 2: Flash, files, and combined workflow

**Files:**
- Modify: `tools/PC/upload_firmware.py`
- Modify: `test/protocol/test_upload_firmware.py`
- Modify: `test/protocol/night_run/repl_upload.py`

**Interfaces:**
- Consumes: Task 1's configuration, file mapping, command builders, and erase confirmation.
- Produces: `flash_firmware`, `deploy_files`, `run_all`, `run_command`, `_mkdir_commands`, and `main`.

- [ ] **Step 1: Write failing workflow tests**

```python
def test_flash_erase_runs_only_after_confirmation(self):
    result = upload_firmware.flash_firmware(
        config, port, erase=True, input_fn=lambda _prompt: "wrong",
        runner=recording_runner)
    self.assertFalse(result)
    self.assertEqual([], commands)

def test_all_reconfirms_port_before_deploying_files(self):
    upload_firmware.run_all(
        config, initial_port, input_fn=lambda _prompt: files_port,
        runner=recording_runner, sleep_fn=lambda _seconds: None)
    self.assertIn(initial_port, commands[0])
    self.assertTrue(any(files_port in command for command in commands[1:]))
```

Add tests that a subprocess failure stops subsequent files, dry-run invokes no
hardware process, and `repl_upload._mkdir_commands('/lib/sys/a.py')` creates
`/lib` before `/lib/sys`.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -B -m unittest test.protocol.test_upload_firmware -v`

Expected: FAIL because workflow functions and remote-directory creation are missing.

- [ ] **Step 3: Implement the workflow and CLI**

`flash` optionally executes explicit-port `erase-flash`, then explicit-port
`write-flash -z 0x0 IMAGE`. `files` uploads every mapped file with
`python -B test/protocol/night_run/repl_upload.py PORT LOCAL REMOTE`, then runs
`mpremote connect PORT reset`. `all` performs flash, waits, lists serial ports,
requires the operator to type the newly verified files port, then deploys.

Modify `repl_upload.upload` to issue idempotent normal-REPL `os.mkdir` commands
for every remote parent before opening the destination. Keep its existing byte
count verification and failure exit status.

- [ ] **Step 4: Run focused and existing uploader tests**

Run: `python -B -m unittest test.protocol.test_upload_firmware -v`

Expected: PASS with no hardware access.

- [ ] **Step 5: Commit Task 2**

```bash
git add tools/PC/upload_firmware.py test/protocol/test_upload_firmware.py test/protocol/night_run/repl_upload.py
git commit -m "feat: add firmware and project upload workflows"
```

### Task 3: Local template, real local configuration, and operator documentation

**Files:**
- Create: `upload_local.example.ini`
- Create locally (ignored): `upload_local.ini`
- Modify: `.gitignore`
- Create: `doc/02_guides/13_local_firmware_upload.md`
- Modify: `test/protocol/test_upload_firmware.py`

**Interfaces:**
- Consumes: the Task 2 CLI.
- Produces: a ready-to-run local configuration and concise operator commands.

- [ ] **Step 1: Add a failing example-config CLI test**

```python
def test_repository_example_supports_dry_run(self):
    result = upload_firmware.main([
        "--config", "upload_local.example.ini", "--dry-run",
        "files", "--port", "/dev/cu.example",
    ])
    self.assertEqual(0, result)
```

- [ ] **Step 2: Run test and verify RED**

Run: `python -B -m unittest test.protocol.test_upload_firmware -v`

Expected: FAIL because the example configuration does not exist.

- [ ] **Step 3: Add configuration and documentation**

The example and ignored local file contain the fixed image
`ext_mod/ESP32_GENERIC_S3_2026_08_21_06_01_18.bin`, source `slave`, optional
`device_config`, chip `esp32s3`, baud `460800`, uploader path, and command
tokens. Neither file contains a USB port. Document `list`, `flash`, `files`,
`all`, `--dry-run`, the destructive `--erase` confirmation, and the rule that
`all --erase` requires a device profile to restore `/config.json`.

- [ ] **Step 4: Run tests and CLI dry-runs**

```bash
python -B -m unittest test.protocol.test_upload_firmware -v
python -B tools/PC/upload_firmware.py --config upload_local.ini --dry-run flash --port /dev/cu.example
python -B tools/PC/upload_firmware.py --config upload_local.ini --dry-run files --port /dev/cu.example
python -B tools/PC/upload_firmware.py --config upload_local.ini --dry-run all --port /dev/cu.example
```

Expected: tests PASS; dry-runs print explicit ports and perform no hardware I/O.

- [ ] **Step 5: Commit tracked Task 3 files**

```bash
git add .gitignore upload_local.example.ini doc/02_guides/13_local_firmware_upload.md test/protocol/test_upload_firmware.py
git commit -m "docs: add local upload setup"
```

### Task 4: Final verification

**Files:**
- Verify only; no planned source edits.

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: evidence that the CLI is safe, tested, and free of Python cache artifacts.

- [ ] **Step 1: Run the focused test suite**

Run: `python -B -m unittest test.protocol.test_upload_firmware -v`

Expected: PASS.

- [ ] **Step 2: Check CLI help and local configuration**

```bash
python -B tools/PC/upload_firmware.py --help
python -B tools/PC/upload_firmware.py --config upload_local.ini list
```

Expected: help documents all modes; `list` is read-only and enumerates current ports.

- [ ] **Step 3: Verify repository hygiene and narrow diff**

```bash
find . -type d -name __pycache__ -o -type f -name '*.pyc'
git status --short
git diff HEAD~3 --check
```

Expected: no cache artifacts; only the user's pre-existing `outputs/` remains untracked; diff check has no whitespace errors.
