import { Inngest } from "inngest";

/** Typed event client shared by web routes and durable background functions. */
export const inngest = new Inngest({ id: "pricewise" });
