import { defineConfig } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const frontend = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(frontend, "..");

export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  expect: { timeout: 8_000 },
  fullyParallel: false,
  reporter: "list",
  use: { baseURL: "http://127.0.0.1:3011", trace: "retain-on-failure" },
  webServer: [
    {
      command: "python -m uvicorn main:app --host 127.0.0.1 --port 8011",
      cwd: path.join(root, "backend"),
      url: "http://127.0.0.1:8011/health",
      env: { DATABASE_URL: "sqlite:///./playwright-e2e.db", CORS_ORIGINS: "http://127.0.0.1:3011" },
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: "npm run build && npm run start -- --hostname 127.0.0.1 --port 3011",
      cwd: frontend,
      url: "http://127.0.0.1:3011",
      env: { NEXT_PUBLIC_API_URL: "http://127.0.0.1:8011/api" },
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});
