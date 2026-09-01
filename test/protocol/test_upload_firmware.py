#!/usr/bin/env python3
"""Contracts for the repository-local firmware upload helper."""

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "PC" / "upload_firmware.py"

spec = importlib.util.spec_from_file_location("upload_firmware", MODULE_PATH)
upload_firmware = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_firmware)


class UploadConfigurationTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
