from urllib.parse import urljoin

from dedsec.core.colors import Colors
from dedsec.core.utils import get_soft404_profile, info, is_soft_404, safe_request, section, warn

# Curated high-value discovery paths. Ordered roughly by likelihood of
# existing on a modern web target. The list is intentionally bounded so a
# full discovery pass stays inside the target HTTP request budget.
DISCOVERY_PATHS = [
    # Admin & auth surfaces
    "/admin/", "/admin", "/administrator/", "/login", "/signin", "/auth/login",
    "/wp-admin/", "/wp-login.php", "/user/login", "/account", "/dashboard",
    "/panel/", "/console", "/manage", "/management/",
    # API surfaces
    "/api/", "/api/v1/", "/api/v2/", "/v1/", "/v2/", "/graphql", "/rest/",
    "/api/swagger/", "/swagger/", "/swagger-ui/",
    # Config & sensitive files
    "/.git/config", "/.env", "/.env.local", "/config.json", "/config.php",
    "/configuration.php", "/settings", "/application.yml", "/web.config",
    "/server-status", "/server-info", "/status", "/health", "/healthz",
    "/actuator", "/actuator/env", "/metrics", "/debug", "/debug/",
    # Docs & staging
    "/docs/", "/documentation/", "/readme", "/README.md", "/CHANGELOG",
    "/test/", "/tests/", "/staging/", "/dev/", "/development/", "/qa/",
    "/demo/", "/sandbox/", "/temp/", "/tmp/", "/backup/", "/backups/",
    # Common app paths
    "/uploads/", "/files/", "/downloads/", "/assets/", "/static/",
    "/robots.txt", "/sitemap.xml", "/favicon.ico", "/crossdomain.xml",
    "/phpinfo.php", "/info.php", "/.well-known/security.txt",
]


def run(url, domain, timeout=10):
    section("Content & Path Discovery", "🧭")
    results = {
        "found": [],
        "restricted": [],
        "redirects": [],
        "rejected": [],
        "soft_404s": 0,
        "transport_failures": 0,
        "tested": 0,
    }

    soft404_prof = get_soft404_profile(url, timeout=min(timeout, 5))
    if soft404_prof:
        info(
            "Soft-404 Baseline Profile",
            f"Status {soft404_prof.get('status_code')}, Avg Len ~{soft404_prof.get('avg_length')} bytes",
        )

    seen = set()
    for path in DISCOVERY_PATHS:
        test_url = urljoin(url.rstrip("/") + "/", path.lstrip("/"))
        if test_url in seen:
            continue
        seen.add(test_url)
        results["tested"] += 1

        resp = safe_request(test_url, timeout=timeout, allow_redirects=False)
        if resp is None:
            results["transport_failures"] += 1
            continue

        if is_soft_404(resp, soft404_prof):
            results["soft_404s"] += 1
            continue

        status = resp.status_code
        if status in (401, 403):
            entry = {"url": test_url, "status": status, "classification": "restricted"}
            results["restricted"].append(entry)
            print(
                f"{Colors.YELLOW}[!]{Colors.RESET} {status} {Colors.BOLD}{path}{Colors.RESET} "
                f"{Colors.DIM}(restricted){Colors.RESET}"
            )
            continue

        if status in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location", "")
            entry = {
                "url": test_url,
                "status": status,
                "location": location,
                "classification": "redirect",
            }
            results["redirects"].append(entry)
            continue

        if status == 200:
            # A bare 200 is only a discovery signal when the body is
            # meaningfully non-empty; empty/placeholder pages are rejected.
            body = (resp.text or "").strip()
            if len(body) < 32:
                results["rejected"].append(
                    {"url": test_url, "status": status, "reason": "placeholder page"}
                )
                continue
            entry = {
                "url": test_url,
                "status": status,
                "size": len(body),
                "classification": "surface-observation",
            }
            results["found"].append(entry)
            print(
                f"{Colors.GREEN}[+]{Colors.RESET} 200 {Colors.BOLD}{path}{Colors.RESET} "
                f"{Colors.DIM}({len(body)} bytes){Colors.RESET}"
            )
            continue

        results["rejected"].append(
            {"url": test_url, "status": status, "reason": f"unexpected status {status}"}
        )

    info("Paths Found (200)", str(len(results["found"])))
    if results["restricted"]:
        info("Restricted (401/403)", str(len(results["restricted"])))
    if results["redirects"]:
        info("Redirects", str(len(results["redirects"])))
    if results["soft_404s"]:
        info("Soft-404s Filtered", str(results["soft_404s"]))
    if results["transport_failures"]:
        warn(f"{results['transport_failures']} probe(s) had transport failures; those paths are inconclusive.")
    return results
