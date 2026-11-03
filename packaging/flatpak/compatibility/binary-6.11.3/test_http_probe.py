"""Offline fixtures only; tests issue no HTTP requests."""

import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "p6_http_probe", Path(__file__).with_name("http_probe.py")
)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class HttpProbeTests(unittest.TestCase):
    def test_untrusted_headers_and_error_body_are_not_published(self):
        item = probe.summarize(
            "403",
            "Server: Varnish\nSet-Cookie: private\n"
            "Authorization: private\nLocation: https://secret.invalid/token\n",
            b"private body",
            0,
        )
        self.assertEqual(item["safe_headers"], {"server": "Varnish"})
        self.assertTrue(item["redirect_advertised"])
        self.assertFalse(item["expected_object_hash"])
        self.assertNotIn("private", str(item))
        self.assertNotIn("secret.invalid", str(item))

    def test_requests_are_bounded_https_and_do_not_follow_redirects_or_disable_tls(
        self,
    ):
        args = probe.command("fixture", Path("/fixture"), user_agent="libostree/2025.7")
        self.assertIn("--disable", args)  # Ignore curlrc; not TLS verification.
        self.assertEqual(args[-1], probe.URL)
        for option in ("--connect-timeout", "--max-time", "--max-filesize"):
            self.assertIn(option, args)
        for option in ("-k", "--insecure", "-L", "--location", "--retry", "--netrc"):
            self.assertNotIn(option, args)

    def test_unknown_or_incorrect_content_is_not_promoted_to_success(self):
        for code in ("200", "403", "000"):
            with self.subTest(code=code):
                item = probe.summarize(code, "", b"not the object", 0)
                self.assertFalse(item["expected_object_hash"])

    def test_fresh_diagnostic_cannot_target_the_failed_build(self):
        for path in (
            probe.ROOT / "ci-output/p6-binary-candidate-1",
            Path("/tmp/anything"),
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                probe.new_output(path)


if __name__ == "__main__":
    unittest.main()
