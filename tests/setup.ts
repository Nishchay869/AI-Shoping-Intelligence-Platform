import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";
import "@testing-library/jest-dom/vitest";

// RTL's auto-cleanup only self-registers when it detects Jest's implicit globals; this project imports
// `afterEach`/`describe`/`it` explicitly from "vitest" instead (globals: true is not set), so without this,
// each render() in a component test file would pile up in the same jsdom document instead of unmounting
// between tests - the direct cause of "found multiple elements" failures across unrelated `it` blocks.
afterEach(() => {
  cleanup();
});
