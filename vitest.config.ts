import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["**/__tests__/**/*.test.ts", "**/*.test.ts"],
    exclude: ["node_modules/**", "dist/**", "coverage/**", "tmp/**", "generated/**"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json-summary", "html"],
      include: ["tools/**/*.ts", "generator/**/*.ts"],
      exclude: ["**/__tests__/**", "**/__fixtures__/**", "**/*.test.ts"],
      thresholds: {
        lines: 90,
        functions: 90,
        branches: 85,
        statements: 90,
      },
    },
    clearMocks: true,
    restoreMocks: true,
  },
});
