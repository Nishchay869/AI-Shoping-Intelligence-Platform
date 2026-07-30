import { serve } from "inngest/next";
import { inngest } from "@workers/client";
import { priceCheck } from "@workers/price-check";

export const { GET, POST, PUT } = serve({ client: inngest, functions: [priceCheck] });
