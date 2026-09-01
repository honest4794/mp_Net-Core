#!/usr/bin/env python3
"""Contracts for the repository-local firmware upload helper."""

import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "PC" / "upload_firmware.py"

spec = importlib.util.spec_from_file_location("upload_firmware", MODULE_PATH)
upload_firmware = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_firmware)

REPL_UPLOADER_PATH = ROOT / "test" / "protocol" / "night_run" / "repl_upload.py"
repl_spec = importlib.util.spec_from_file_location("repl_upload", REPL_UPLOADER_PATH)
repl_upload = importlib.util.module_from_spec(repl_spec)
repl_spec.loader.exec_module(repl_upload)


class _UploadFixture(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "firmware.bin").write_bytes(b"firmware")
        (self.root / "slave").mkdir()
        (self.root / "uploader.py").write_text("# uploader\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_ini(self, extra=""):
        path = self.root / "upload_local.ini"
        path.write_text(
            "[upload]\n"
            "firmware = firmware.bin\n"
            "source = slave\n"
            "uploader = uploader.py\n"
            "chip = esp32s3\n"
            "baud = 460800\n"
            "address = 0x0\n"
            "esptool = esptool.py\n"
            "mpremote = uvx mpremote\n"
            "reconnect_seconds = 3\n"
            + extra,
            encoding="utf-8",
        )
        return path


class UploadConfigurationTests(_UploadFixture):

    def test_rejects_a_saved_usb_port(self):
        """Accepting a saved port could flash a different board after reconnect."""
        with self.assertRaisesRegex(ValueError, "must not store USB ports"):
            upload_firmware.load_config(
                self.write_ini("port = /dev/cu.usbmodem-stale\n"))

    def test_load_config_resolves_paths_relative_to_the_ini(self):
        """Resolving paths against the current shell directory breaks local configs."""
        config = upload_firmware.load_config(self.write_ini())

        self.assertEqual((self.root / "firmware.bin").resolve(), config.firmware)
        self.assertEqual((self.root / "slave").resolve(), config.source)
        self.assertEqual((self.root / "uploader.py").resolve(), config.uploader)
        self.assertEqual(("esptool.py",), config.esptool)
        self.assertEqual(("uvx", "mpremote"), config.mpremote)

    def test_maps_application_tree_to_root_and_skips_python_cache(self):
        """Uploading bytecode/cache artifacts can deploy stale host-side code."""
        source = self.root / "slave"
        (source / "app.py").write_text("app = 1\n", encoding="utf-8")
        (source / "lib").mkdir()
        (source / "lib" / "sys.py").write_text("system = 1\n", encoding="utf-8")
        (source / "lib" / "stale.pyc").write_bytes(b"stale")
        (source / "__pycache__").mkdir()
        (source / "__pycache__" / "app.pyc").write_bytes(b"stale")

        mappings = upload_firmware.collect_upload_files(source)

        self.assertEqual(
            [
                (source / "app.py", "/app.py"),
                (source / "lib" / "sys.py", "/lib/sys.py"),
            ],
            mappings,
        )

    def test_flash_command_contains_only_the_explicit_current_port(self):
        """Dropping the CLI port would let esptool auto-select the wrong board."""
        config = upload_firmware.load_config(self.write_ini())

        command = upload_firmware.build_flash_command(
            config, "/dev/cu.usbmodem-current")

        self.assertEqual(
            [
                "esptool.py", "--chip", "esp32s3",
                "--port", "/dev/cu.usbmodem-current",
                "--baud", "460800", "write-flash", "-z", "0x0",
                os.fspath((self.root / "firmware.bin").resolve()),
            ],
            command,
        )

    def test_file_upload_command_passes_port_and_python_no_bytecode_flag(self):
        """Omitting -B violates repository hygiene and can leave cache files."""
        config = upload_firmware.load_config(self.write_ini())
        local_path = self.root / "slave" / "app.py"

        command = upload_firmware.build_upload_command(
            config, "/dev/cu.usbmodem-current", local_path, "/app.py")

        self.assertEqual("-B", command[1])
        self.assertEqual(os.fspath(config.uploader), command[2])
        self.assertEqual("/dev/cu.usbmodem-current", command[3])
        self.assertEqual(os.fspath(local_path), command[4])
        self.assertEqual("/app.py", command[5])

    def test_erase_requires_exact_port_confirmation(self):
        """A generic yes prompt is too weak for destructive full-flash erase."""
        port = "/dev/cu.usbmodem-current"

        self.assertFalse(upload_firmware.confirm_erase(
            port, lambda _prompt: "yes"))
        self.assertTrue(upload_firmware.confirm_erase(
            port, lambda _prompt: "ERASE " + port))


class UploadWorkflowTests(_UploadFixture):
    def setUp(self):
        super().setUp()
        (self.root / "slave" / "app.py").write_text("app = 1\n", encoding="utf-8")
        self.config = upload_firmware.load_config(self.write_ini())
        self.port = "/dev/cu.usbmodem-initial"

    def test_flash_erase_runs_nothing_when_exact_confirmation_is_missing(self):
        """A cancelled erase must not fall through into writing firmware."""
        commands = []

        result = upload_firmware.flash_firmware(
            self.config,
            self.port,
            erase=True,
            input_fn=lambda _prompt: "yes",
            runner=lambda command, **_kwargs: commands.append(command),
        )

        self.assertFalse(result)
        self.assertEqual([], commands)

    def test_flash_with_erase_uses_the_explicit_port_for_both_commands(self):
        """The destructive command and write command must target the same verified board."""
        commands = []

        result = upload_firmware.flash_firmware(
            self.config,
            self.port,
            erase=True,
            input_fn=lambda _prompt: "ERASE " + self.port,
            runner=lambda command, **_kwargs: commands.append(command),
        )

        self.assertTrue(result)
        self.assertEqual(2, len(commands))
        self.assertIn(self.port, commands[0])
        self.assertIn("erase-flash", commands[0])
        self.assertIn(self.port, commands[1])
        self.assertIn("write-flash", commands[1])

    def test_file_failure_stops_before_reset_and_later_files(self):
        """Resetting after a partial deploy can boot an inconsistent application tree."""
        (self.root / "slave" / "later.py").write_text("later = 1\n", encoding="utf-8")
        commands = []

        def failing_runner(command, **_kwargs):
            commands.append(command)
            raise subprocess.CalledProcessError(1, command)

        with self.assertRaises(subprocess.CalledProcessError):
            upload_firmware.deploy_files(
                self.config, self.port, runner=failing_runner)

        self.assertEqual(1, len(commands))
        self.assertNotIn("reset", commands[0])

    def test_dry_run_prints_workflow_without_calling_hardware_runner(self):
        """Dry-run that opens serial hardware is not a safe preview."""
        commands = []

        count = upload_firmware.deploy_files(
            self.config,
            self.port,
            dry_run=True,
            runner=lambda command, **_kwargs: commands.append(command),
        )

        self.assertEqual(1, count)
        self.assertEqual([], commands)

    def test_all_reconfirms_port_before_deploying_application_files(self):
        """Silently reusing the pre-flash port can deploy to a re-enumerated board."""
        files_port = "/dev/cu.usbmodem-after-flash"
        commands = []

        result = upload_firmware.run_all(
            self.config,
            self.port,
            input_fn=lambda _prompt: files_port,
            runner=lambda command, **_kwargs: commands.append(command),
            sleep_fn=lambda _seconds: None,
        )

        self.assertTrue(result)
        self.assertIn(self.port, commands[0])
        upload_commands = [command for command in commands if os.fspath(self.config.uploader) in command]
        self.assertEqual(1, len(upload_commands))
        self.assertIn(files_port, upload_commands[0])
        self.assertNotIn(self.port, upload_commands[0])

    def test_all_with_erase_refuses_before_flash_without_a_device_profile(self):
        """Erasing without restoring /config.json leaves hardware identity undefined."""
        commands = []

        with self.assertRaisesRegex(ValueError, "device_config"):
            upload_firmware.run_all(
                self.config,
                self.port,
                erase=True,
                input_fn=lambda _prompt: "ERASE " + self.port,
                runner=lambda command, **_kwargs: commands.append(command),
                sleep_fn=lambda _seconds: None,
            )

        self.assertEqual([], commands)

    def test_configured_device_profile_uploads_to_config_json_first(self):
        """Restoring the profile after app files could briefly boot unsafe defaults."""
        (self.root / "profile.json").write_text('{"System": {}}\n', encoding="utf-8")
        config = upload_firmware.load_config(
            self.write_ini("device_config = profile.json\n"))
        commands = []

        count = upload_firmware.deploy_files(
            config,
            self.port,
            runner=lambda command, **_kwargs: commands.append(command),
        )

        self.assertEqual(2, count)
        self.assertEqual("/config.json", commands[0][-1])
        self.assertEqual("/app.py", commands[1][-1])
        self.assertIn("reset", commands[2])

    def test_remote_directory_commands_create_parents_in_order(self):
        """Writing a nested file before its directories exist fails on fresh firmware."""
        self.assertEqual(
            [
                "os.mkdir('/lib') if 'lib' not in os.listdir('/') else None",
                "os.mkdir('/lib/sys') if 'sys' not in os.listdir('/lib') else None",
            ],
            repl_upload._mkdir_commands("/lib/sys/module.py"),
        )


class RepositoryConfigurationTests(unittest.TestCase):
    def test_repository_example_supports_files_dry_run(self):
        """A stale template would make the documented first command fail."""
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            result = upload_firmware.main([
                "--config", os.fspath(ROOT / "upload_local.example.ini"),
                "--dry-run",
                "files",
                "--port", "/dev/cu.usbmodem-example",
            ])

        self.assertEqual(0, result, output.getvalue())
        self.assertIn("/dev/cu.usbmodem-example", output.getvalue())
        self.assertIn("/app.py", output.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
