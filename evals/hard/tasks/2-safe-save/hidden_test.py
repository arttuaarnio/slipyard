"""Hidden tests: a crash in the middle of writing must leave the old file intact.
The crash is real: the process is limited in how many bytes it may write, so the
write fails part-way, whatever the implementation looks like."""
import json
import os
import resource
import signal

from tests.helpers import CliCase


def limit_writes(max_bytes):
    def apply():
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_FSIZE, (max_bytes, max_bytes))
    return apply


class SafeSaveTest(CliCase):
    def fill(self, n=40):
        for i in range(n):
            self.add("2024-03-01", f"-{i}.25", "food", "--note", "x" * 40)

    def test_crash_mid_write_keeps_old_file(self):
        self.fill()
        with open(self.file, encoding="utf-8") as f:
            before = f.read()
        # Writing a complete new ledger needs more bytes than this, so the save dies part-way.
        result = self.cli("add", "2024-03-02", "-1.00", "food", preexec_fn=limit_writes(len(before) // 2))
        with open(self.file, encoding="utf-8") as f:
            after = f.read()
        self.assertEqual(after, before, "the ledger file was damaged by a failed save")
        json.loads(after)
        self.assertEqual(self.cli("list").returncode, 0)

    def test_crash_on_first_save_leaves_no_broken_file(self):
        self.cli("add", "2024-03-02", "-1.00", "food", "--note", "y" * 200, preexec_fn=limit_writes(50))
        if os.path.exists(self.file):
            with open(self.file, encoding="utf-8") as f:
                json.loads(f.read())

    def test_normal_saves_still_work_and_leave_no_temp_files(self):
        self.fill(3)
        self.assertEqual(len(self.cli("list").stdout.splitlines()), 3)
        self.assertEqual(sorted(os.listdir(self.dir.name)), ["ledger.json"])

    def test_failed_save_reports_an_error(self):
        self.fill()
        size = os.path.getsize(self.file)
        result = self.cli("add", "2024-03-02", "-1.00", "food", preexec_fn=limit_writes(size // 2))
        self.assertNotEqual(result.returncode, 0, "a failed save must not look like success")
