import { defineConfig } from "vitest/config";
import path from "node:path";

export default defineConfig({
  // Next.js requires "jsx": "preserve" in tsconfig; vite 8 (rolldown/oxc)
  // refuses to transform preserved JSX, so compile TSX for tests with the
  // automatic runtime explicitly.
  oxc: { jsx: { runtime: "automatic" } },
  test: {
    environment: "node",
    include: ["lib/**/*.test.ts", "__tests__/**/*.test.ts", "__tests__/**/*.test.tsx"],
  },
  resolve: {
    alias: { "@": path.resolve(__dirname, ".") },
  },
});
