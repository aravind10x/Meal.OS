import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeAll, afterAll } from "vitest";
import { server } from "./mocks/handlers";

// Start MSW server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));

// Reset any request handlers between tests
afterEach(() => {
  cleanup();
  server.resetHandlers();
});

// Clean up after all tests
afterAll(() => server.close());
