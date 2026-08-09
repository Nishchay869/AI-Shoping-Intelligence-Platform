import { withPage, parsePriceToMinor } from "./browser";
import type { ScrapedProduct } from "./types";

/** Scrapes one Amazon product page for its title, current price, stock, and image.
 *
 * Unlike Flipkart, Amazon's core product-page ids (#productTitle, #availability, #landingImage) and the
 * .a-price component's classes have stayed stable for years, so semantic ids are used directly here -
 * verified against a live page. */
export async function scrapeAmazonProduct(url: string): Promise<ScrapedProduct> {
  return withPage(async (page) => {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30_000 });
    await page.waitForSelector("#productTitle, #captchacharacters", { timeout: 15_000 }).catch(() => {});

    const data = await page.evaluate(() => {
      const captcha = document.querySelector("#captchacharacters") !== null;
      const title = document.querySelector("#productTitle")?.textContent?.trim() ?? null;
      const priceText = document.querySelector(".a-price .a-offscreen")?.textContent?.trim() ?? null;
      const availabilityText = document.querySelector("#availability span")?.textContent?.trim() ?? "";
      const imageUrl = document.querySelector<HTMLImageElement>("#landingImage, #imgBlkFront")?.src ?? null;
      return { captcha, title, priceText, availabilityText, imageUrl };
    });

    if (data.captcha) {
      throw new Error(`Amazon served a CAPTCHA/bot-check page for ${url} instead of the product page - try again later or from a different IP`);
    }

    const priceMinor = data.priceText ? parsePriceToMinor(data.priceText) : null;
    if (!data.title || priceMinor === null) {
      throw new Error(`Could not extract product data from ${url} - Amazon's page layout may have changed since this scraper was written`);
    }

    return {
      title: data.title,
      priceMinor,
      currency: "INR",
      available: !/currently unavailable|out of stock/i.test(data.availabilityText),
      imageUrl: data.imageUrl,
      sourceUrl: url,
    };
  });
}
