"""Exercise the real offline report in Chromium; run separately in browser CI."""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

page_path = Path(sys.argv[1]).resolve()
with sync_playwright() as browser_tool:
    browser = browser_tool.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto(page_path.as_uri())
    assert page.title().startswith("FluTrees")
    page.get_by_role("link", name="Explore simplified tree").click()
    branch = page.locator("h2#pruned + details")
    assert branch.get_attribute("open") is not None
    branch.locator(":scope > summary").click()
    assert branch.get_attribute("open") is None
    branch.locator(":scope > summary").click()
    members = branch.locator(":scope > details").first
    members.locator(":scope > summary").click()
    assert members.locator("tbody tr").count() == 48
    assert members.locator("tbody tr").first.is_visible()
    assert page.locator("img").evaluate("(img) => img.complete && img.naturalWidth > 0")
    for anchor in page.locator("a[href]").all():
        href = anchor.get_attribute("href")
        if not href.startswith("#"):
            assert (page_path.parent / href).is_file(), href
    page.screenshot(path=str(page_path.parent / "report-browser.png"), full_page=True)
    browser.close()
