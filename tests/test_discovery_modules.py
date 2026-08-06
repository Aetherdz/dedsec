import unittest
from unittest.mock import patch

from dedsec.modules import content_discovery, dirlisting_check


class FakeResponse:
    def __init__(self, status_code=200, headers=None, text="", content=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text
        self.content = content if content is not None else text.encode()


class ContentDiscoveryTests(unittest.TestCase):
    @patch("dedsec.modules.content_discovery.get_soft404_profile", return_value={})
    @patch("dedsec.modules.content_discovery.safe_request")
    def test_finds_real_paths_and_rejects_placeholders(self, mock_safe_request, _mock_soft404):
        def fake_request(url, timeout=10, allow_redirects=True):
            if url.endswith("/admin/") or url.endswith("/api/"):
                return FakeResponse(status_code=200, text="<html>admin panel dashboard</html>")
            if url.endswith("/login"):
                return FakeResponse(status_code=403, text="forbidden")
            if url.endswith("/docs/"):
                return FakeResponse(status_code=301, headers={"Location": "/docs/index.html"})
            if url.endswith("/placeholder"):
                return FakeResponse(status_code=200, text="<html></html>")
            return FakeResponse(status_code=404, text="not found")

        mock_safe_request.side_effect = fake_request

        result = content_discovery.run("https://example.com", "example.com")

        found_urls = [item["url"] for item in result["found"]]
        self.assertTrue(any(url.endswith("/admin/") for url in found_urls))
        self.assertTrue(any(url.endswith("/api/") for url in found_urls))
        # 403 → restricted, never "found"
        self.assertFalse(any(url.endswith("/login") for url in found_urls))
        self.assertTrue(
            any(item["status"] == 403 for item in result["restricted"])
        )
        # 301 → redirects bucket
        self.assertTrue(any("/docs/" in item["url"] for item in result["redirects"]))
        # Everything else either rejected or not in found; placeholder rejected
        self.assertGreaterEqual(result["tested"], len(content_discovery.DISCOVERY_PATHS) - 1)

    @patch("dedsec.modules.content_discovery.get_soft404_profile")
    @patch("dedsec.modules.content_discovery.safe_request")
    def test_soft404_filtering(self, mock_safe_request, mock_soft404):
        # Baseline profile says 404-ish pages average ~360 bytes.
        mock_soft404.return_value = {"status_code": 200, "avg_length": 360, "sample_text": "nothing here" * 30}
        mock_safe_request.return_value = FakeResponse(status_code=200, text="nothing here" * 30)

        result = content_discovery.run("https://example.com", "example.com")
        self.assertEqual(result["found"], [])
        self.assertGreaterEqual(result["soft_404s"], 1)

    @patch("dedsec.modules.content_discovery.get_soft404_profile", return_value={})
    @patch("dedsec.modules.content_discovery.safe_request")
    def test_transport_failure_never_confirmed(self, mock_safe_request, _mock_soft404):
        mock_safe_request.return_value = None
        result = content_discovery.run("https://example.com", "example.com")
        self.assertEqual(result["found"], [])
        self.assertEqual(result["transport_failures"], result["tested"])


class DirListingTests(unittest.TestCase):
    @patch("dedsec.modules.dirlisting_check.safe_request")
    def test_confirm_listing_with_signature_and_links(self, mock_safe_request):
        def fake_request(url, timeout=10, allow_redirects=True):
            if url.endswith("/wp-content/uploads/"):
                body = (
                    "<html><title>Index of /wp-content/uploads/</title>"
                    "<a href='a.txt'>a.txt</a><a href='b.txt'>b.txt</a>"
                    "<a href='c.txt'>c.txt</a></html>"
                )
                return FakeResponse(status_code=200, text=body)
            return FakeResponse(status_code=404, text="not found")

        mock_safe_request.side_effect = fake_request

        result = dirlisting_check.run("https://example.com", "example.com")
        uploads = [c for c in result["confirmed"] if c["url"].endswith("/uploads/")]
        self.assertGreaterEqual(len(uploads), 1)
        self.assertTrue(
            all(c["classification"] == "verified-directory-listing" for c in uploads)
        )
        self.assertEqual(result["confirmed"][0]["classification"], "verified-directory-listing")
        self.assertTrue(result["confirmed"][0]["url"].endswith("/uploads/"))

    @patch("dedsec.modules.dirlisting_check.safe_request")
    def test_signature_without_enough_links_is_rejected(self, mock_safe_request):
        # "Index of" appears but there is only one link → conservative reject.
        body = "<html><title>Index of /files/</title><a href='a.txt'>a.txt</a></html>"
        mock_safe_request.return_value = FakeResponse(status_code=200, text=body)

        result = dirlisting_check.run("https://example.com", "example.com")
        self.assertEqual(result["confirmed"], [])
        self.assertTrue(
            any(item["classification"] == "rejected-listing-candidate" for item in result["observations"])
        )

    @patch("dedsec.modules.dirlisting_check.safe_request")
    def test_transport_failure_is_inconclusive(self, mock_safe_request):
        mock_safe_request.return_value = None
        result = dirlisting_check.run("https://example.com", "example.com")
        self.assertEqual(result["confirmed"], [])
        self.assertEqual(result["transport_failures"], result["tested"])


if __name__ == "__main__":
    unittest.main()
