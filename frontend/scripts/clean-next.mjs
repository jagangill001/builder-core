import { existsSync } from "node:fs";
import { rm } from "node:fs/promises";
import { resolve } from "node:path";

const buildDir = resolve(process.cwd(), ".next");

async function sleep(ms) {
  await new Promise((resolveSleep) => setTimeout(resolveSleep, ms));
}

for (let attempt = 1; attempt <= 5; attempt += 1) {
  if (!existsSync(buildDir)) {
    process.exit(0);
  }

  try {
    await rm(buildDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 250 });
    process.exit(0);
  } catch (error) {
    if (attempt === 5) {
      console.error(`Could not clear ${buildDir}: ${error instanceof Error ? error.message : String(error)}`);
      process.exit(1);
    }
    await sleep(300);
  }
}
