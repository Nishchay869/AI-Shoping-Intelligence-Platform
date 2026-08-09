import puppeteer from "puppeteer-extra";
import StealthPlugin from "puppeteer-extra-plugin-stealth";
import type { Page } from "puppeteer";

puppeteer.use(StealthPlugin());

const USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

/** Launches one headless Chrome instance, hands it a page, and always closes it - so a scraper function
 * never has to remember cleanup on its own error paths. */
export async function withPage<T>(run: (page: Page) => Promise<T>): Promise<T> {
  const browser = await puppeteer.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.setUserAgent(USER_AGENT);
    await page.setViewport({ width: 1366, height: 900 });
    return await run(page);
  } finally {
    await browser.close();
  }
}

/** "₹30,999" / "$79.99" / "85,999.00" -> price in minor units (paise/cents). Strips everything but digits
 * and the decimal point, since both sites format currency differently. */
export function parsePriceToMinor(raw: string): number | null {
  const cleaned = raw.replace(/[^\d.]/g, "");
  if (!cleaned) return null;
  const value = parseFloat(cleaned);
  return Number.isFinite(value) ? Math.round(value * 100) : null;
}
