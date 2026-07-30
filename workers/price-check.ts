import { inngest } from "./client";

/** Schedules retailer price checks; adapter execution is introduced after provider credentials are approved. */
export const priceCheck = inngest.createFunction(
  { id: "price-check", retries: 3 },
  { cron: "0 */6 * * *" },
  async ({ step }) => step.run("queue-enabled-retailers", async () => ({ queued: true }))
);
