// Copies the engine into the race view (race-view/assets/engine/), as the course files are copied into
// race-view/assets/course/. Run after changing anything in race-engine/:  node race-engine/copy-to-view.mjs
import { copyFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
const here = dirname(fileURLToPath(import.meta.url)), to = join(here, "..", "race-view", "assets", "engine");
mkdirSync(to, { recursive: true });
for (const f of ["engine.js", "field.js", "settings.json"]) { copyFileSync(join(here, f), join(to, f)); console.log("copied", f); }
