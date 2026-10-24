import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "libexec/mango-performance-mode.sudoers.template"
INSTALLER = ROOT / "install-system.sh"


class SudoersTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("visudo"), "visudo not installed")
    def test_rendered_template_is_valid_sudoers(self):
        rendered = TEMPLATE.read_text().replace("%INSTALL_USER%", "alice")
        with tempfile.NamedTemporaryFile("w", suffix=".sudoers") as file:
            file.write(rendered)
            file.flush()
            result = subprocess.run(["visudo", "-cf", file.name], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rule_allows_only_the_three_modes(self):
        rule = [line for line in TEMPLATE.read_text().splitlines() if "NOPASSWD" in line][0]
        commands = [c.strip() for c in rule.split("NOPASSWD:", 1)[1].split(",")]
        self.assertEqual(
            commands,
            [f"/usr/local/libexec/performance-mode-apply {m}" for m in ("eco", "balanced", "max")],
        )

    def test_installer_validates_before_touching_sudoers_d(self):
        # A broken file in /etc/sudoers.d makes sudo unusable, so the check
        # must run on a temporary copy before anything is installed there.
        lines = INSTALLER.read_text().splitlines()
        check = next(i for i, line in enumerate(lines) if "visudo -cf" in line)
        code = [(i, line) for i, line in enumerate(lines) if not line.lstrip().startswith("#")]
        writes = [i for i, line in code if "/etc/sudoers.d/" in line]
        self.assertTrue(writes)
        self.assertTrue(all(check < i for i in writes), "sudoers.d written before validation")
        self.assertIn('"$SUDOERS_TMP"', lines[check])


if __name__ == "__main__":
    unittest.main()
