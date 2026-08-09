export type ScrapedProduct = {
  title: string;
  priceMinor: number;
  currency: string;
  available: boolean;
  imageUrl: string | null;
  sourceUrl: string;
};
