# Local Firmware Upload Design

## Goal

Add one repository-local command that can flash the fixed MicroPython image,
deploy the `slave/` application tree, or do both. Stable local choices live in
an ignored `upload_local.ini`; a USB port never does.

## Chosen approach

Use a small Python CLI built only on the standard library plus the repository's
existing upload dependencies. This fits the MicroPython repository directly and
does not pretend the project is built by PlatformIO.

Rejected alternatives:

- A Makefile-only wrapper cannot safely model reconnects, confirmations, and
  recursive file deployment.
- Adding a synthetic `platformio.ini` would imply PlatformIO builds this
  firmware, which is false in this repository.

## Files and interface

- `upload_local.example.ini` is the tracked template.
- `upload_local.ini` is ignored and stores the firmware image, application
  source directory, ESP chip, flash baud, and tool commands.
- `tools/PC/upload_firmware.py` provides:
  - `list`: list currently connected serial ports.
  - `flash --port PORT`: write the configured MicroPython image.
  - `files --port PORT`: recursively deploy the configured application tree.
  - `all --port PORT`: flash, wait for reconnect and explicit port
    reconfirmation, then deploy files.
- `--config`, `--dry-run`, and `--erase` are common options. `--erase` is valid
  only for `flash` and `all` and requires an additional destructive-action
  confirmation.

Every subprocess invocation receives an explicit `--port` or `connect PORT`.
No command reads a port from the INI file or a previous run.

## Upload flow

For firmware, the CLI resolves `esptool` from the configured command or PATH,
optionally erases only after confirmation, then writes the image at address
`0x0`. A nonzero exit status stops the flow.

For project files, the CLI walks the local application directory in stable
order, skips Python cache artifacts, creates required remote directories, and
uses the existing normal-REPL uploader for each file. It resets the board only
after every upload succeeds.

For `all`, the firmware step and application step are separated by a hard
reconfirmation boundary. The tool lists current ports after the board returns
and requires the operator to enter the verified application-upload port. It
does not silently reuse the pre-flash port.

## Failure handling

- Missing configuration, image, source tree, port, or external command fails
  before changing the board.
- A failed erase, flash, file upload, or reset stops immediately with a nonzero
  exit code.
- Dry-run prints the exact commands and file mappings without opening a serial
  port or changing hardware.
- The tool never deletes local files and never stores a USB port.

## Tests

Unit tests cover configuration validation, rejection of a configured USB port,
recursive local-to-remote file mapping, explicit-port command construction,
erase confirmation, and the `all` reconnect boundary. CLI dry-run tests verify
the real example configuration without touching hardware.
