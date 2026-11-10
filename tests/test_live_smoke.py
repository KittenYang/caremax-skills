"""Optional read-only smoke. Skipped unless CAREMAX_LIVE_SMOKE=1.

This test never sends a token and never writes. It only GETs a public manifest.
"""

from __future__ import annotations

import os
import unittest
import urllib.request


@unittest.skipUnless(os.environ.get("CAREMAX_LIVE_SMOKE") == "1", "opt-in live smoke; skipped by default")
class LiveSmokeTest(unittest.TestCase):
    def test_public_manifest_is_readable(self):
        base = os.environ.get("CAREMAX_LIVE_BASE", "https://api.caremax.ai").rstrip("/")
        request = urllib.request.Request(f"{base}/skill.json", method="GET")
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read(200)
            self.assertEqual(response.status, 200)
            self.assertTrue(body.startswith(b"{") or b"skill" in body.lower())


if __name__ == "__main__":
    unittest.main()
