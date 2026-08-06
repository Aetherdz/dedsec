from urllib.parse import urljoin

from dedsec.core.colors import Colors
from dedsec.core.utils import info, safe_request, section

# Directories most likely to have directory listing enabled if the server
# autoindexes. Root is probed first, then common asset/data dirs.
LISTING_DIRS = [
    "/", "/uploads/", "/files/", "/images/", "/assets/", "/static/",
    "/media/", "/backup/", "/backups/", "/logs/", "/tmp/", "/temp/",
    "/data/", "/download/", "/downloads/", "/public/", "/css/", "/js/",
    "/img/", "/admin/files/", "/wp-content/uploads/",
]

# Content signatures that indicate a directory listing (autoindex) as
# opposed to a normal HTML page. Matched case-insensitively on the body.
LISTING_SIGNATURES = [
    "index of /",
    "directory listing for /",
    "parent directory",
    "name                    last modified",
    "<title>index of",
    "autoindex",
]

# A listing body usually contains many <a href> file links and a low
# text-to-link ratio; a single random link is not enough to call it a listing.
MIN_LINKS = 3


def run(url, domain, timeout=10):
    section("Directory Listing Check", "📂")
    results = {
        "confirmed": [],
        "observations": [],
        "tested": 0,
        "transport_failures": 0,
    }

    base = url.rstrip("/")
    for directory in LISTING_DIRS:
        test_url = urljoin(base + "/", directory.lstrip("/"))
        results["tested"] += 1
        resp = safe_request(test_url, timeout=timeout, allow_redirects=False)
        if resp is None:
            results["transport_failures"] += 1
            continue

        if resp.status_code not in (200, 301, 302, 303, 307, 308):
            continue

        # Follow the location for redirects to decide whether a listing is
        # reachable at the final destination; only a handful of probes.
        if resp.status_code in (301, 302, 303, 307, 308):
            redirect = resp.headers.get("Location")
            if not redirect:
                continue
            final = urljoin(test_url, redirect)
            if not final.lower().startswith(base.lower()):
                # Redirect outside target (e.g., CDN/S3 url) is not a listing.
                continue
            resp = safe_request(final, timeout=timeout, allow_redirects=False)
            if resp is None or resp.status_code != 200:
                continue

        body = (resp.text or "").lower()
        signed = any(sig in body for sig in LISTING_SIGNATURES)
        html_links = body.count("<a href") + body.count("<a ")
        if signed and html_links >= MIN_LINKS:
            entry = {
                "url": test_url,
                "links": html_links,
                "classification": "verified-directory-listing",
            }
            results["confirmed"].append(entry)
            print(
                f"{Colors.RED}[!]{Colors.RESET} {Colors.BOLD}Directory listing{Colors.RESET} "
                f"{Colors.CYAN}at {test_url}{Colors.RESET} ({html_links} links)"
            )
        else:
            if signed:
                # Signature matched but too few links — conservative rejection
                # to avoid a false positive on a partial snippet.
                entry = {
                    "url": test_url,
                    "links": html_links,
                    "classification": "rejected-listing-candidate",
                }
                results["observations"].append(entry)
            else:
                print(f"{Colors.DIM}[ ] {directory}: not a listing{Colors.RESET}")

    info("Confirmed Directory Listings", str(len(results["confirmed"])))
    if results["observations"]:
        info("Listing Candidates (unverified)", str(len(results["observations"])))
    if results["transport_failures"]:
        info("Transport Failures", str(results["transport_failures"]))
    return results