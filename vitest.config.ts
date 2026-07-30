import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  // tsconfig.json sets jsx:"preserve" (Next's own SWC compiler does the real transform at build time) -
  // Vitest runs outside that pipeline, so esbuild needs its own JSX instruction for .tsx test/component files.
  esbuild: { jsx: "automatic" },
  test: {
    // Default stays "node" so existing fast, DOM-free tests (pure logic, API route handlers) are unaffected.
    // Component tests opt into jsdom per-file via a `// @vitest-environment jsdom` docblock comment.
    environment: "node",
    // src/shared/config/env.ts requires these at import time; every route/component test that transitively
    // imports it would otherwise throw a ZodError. Placeholder values are fine here - no real Supabase call
    // happens during `npm test`.
    env: {
      NEXT_PUBLIC_SUPABASE_URL: "https://placeholder.supabase.co",
      NEXT_PUBLIC_SUPABASE_ANON_KEY: "placeholder-anon-key",
    },
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.ts", "tests/**/*.test.tsx"]
  }
});
