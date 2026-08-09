/** Manual demo/test entry point - not wired into the app.
 * Usage: npx tsx workers/scrape-cli.ts <product-url> */
import { scrapeAmazonProduct } from "./scrapers/amazon";
import { scrapeFlipkartProduct } from "./scrapers/flipkart";

async function main() {
  const url = process.argv[2];
  if (!url) {
    console.error("Usage: npx tsx workers/scrape-cli.ts <product-url>");
    process.exit(1);
  }

  const host = new URL(url).hostname;
  const scrape = host.includes("amazon") ? scrapeAmazonProduct : host.includes("flipkart") ? scrapeFlipkartProduct : null;
  if (!scrape) {
    console.error(`No scraper for host "${host}" - only amazon.* and flipkart.* are supported`);
    process.exit(1);
  }

  const product = await scrape(url);
  console.log(JSON.stringify(product, null, 2));
}

main().catch((error) => {
  console.error("Scrape failed:", error.message);
  process.exit(1);
});
