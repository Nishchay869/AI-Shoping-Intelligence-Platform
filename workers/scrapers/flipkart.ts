import { withPage, parsePriceToMinor } from "./browser";
import type { ScrapedProduct } from "./types";

/** Scrapes one Flipkart product page for its title, current price, stock, and image.
 *
 * Flipkart's CSS classes are build-hashed (e.g. "_1psv1zeb9") and change on every deploy, so this
 * deliberately avoids matching on class names. Title comes from the page's single <h1>. Price comes from
 * the first leaf element whose text is exactly a rupee amount (e.g. "₹30,999") - the current selling price
 * renders before the struck-through MRP in document order, verified against a live page. */
export async function scrapeFlipkartProduct(url: string): Promise<ScrapedProduct> {
  return withPage(async (page) => {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30_000 });
    await page.waitForSelector("h1", { timeout: 15_000 }).catch(() => {});

    const data = await page.evaluate(() => {
      const title = document.querySelector("h1")?.textContent?.trim() ?? null;
      const priceEl = Array.from(document.querySelectorAll("div, span")).find(
        (el) => el.children.length === 0 && /^₹[\d,]+$/.test(el.textContent?.trim() ?? "")
      );
      const image = document.querySelector<HTMLImageElement>("img[src*='rukminim']");
      const soldOut = /sold out/i.test(document.body.innerText);
      return {
        title,
        priceText: priceEl?.textContent?.trim() ?? null,
        imageUrl: image?.src ?? null,
        soldOut,
      };
    });

    const priceMinor = data.priceText ? parsePriceToMinor(data.priceText) : null;
    if (!data.title || priceMinor === null) {
      throw new Error(
        `Could not extract product data from ${url} - Flipkart's page layout may have changed since this scraper was written, or this request hit a bot-check/CAPTCHA page instead of the real product page`
      );
    }

    return {
      title: data.title,
      priceMinor,
      currency: "INR",
      available: !data.soldOut,
      imageUrl: data.imageUrl,
      sourceUrl: url,
    };
  });
}
