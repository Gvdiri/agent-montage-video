import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const apiKey = process.env.ELEVENLABS_API_KEY;
if (!apiKey) {
  throw new Error("ELEVENLABS_API_KEY is missing.");
}

const outputDir = resolve(
  "ma-video",
  "asset-library",
  "sfx",
  "custom-0726-v2",
);

const effects = [
  {
    id: "google-reveal",
    duration_seconds: 1.5,
    prompt_influence: 0.72,
    text: "Restrained premium technology reveal, a short low metallic inhale followed by a clean liquid-chrome shimmer and one precise glass highlight, cinematic but minimal, no trailer boom, no EDM, no voice",
  },
  {
    id: "product-takeover",
    duration_seconds: 0.8,
    prompt_influence: 0.78,
    text: "Fast premium interface takeover transition, tight liquid-metal displacement with a dry low-mid impact and a very short polished digital tail, distinctive and modern, not a generic whoosh, no voice",
  },
  {
    id: "process-tick",
    duration_seconds: 0.55,
    prompt_influence: 0.82,
    text: "Precise luxury UI confirmation sound, tiny brushed-steel click fused with a muted glass ping, short tactile transient, clean and satisfying, no arcade sound, no voice",
  },
  {
    id: "face-return",
    duration_seconds: 0.65,
    prompt_influence: 0.74,
    text: "Subtle editorial return transition, soft reverse air movement ending in a warm dry tactile click, understated premium social video sound, no boom, no voice",
  },
  {
    id: "keyword-send",
    duration_seconds: 0.9,
    prompt_influence: 0.8,
    text: "Premium message send confirmation, restrained upward tonal pulse with a small chrome sparkle and a soft confident landing, memorable but not cute, no voice",
  },
];

await mkdir(outputDir, { recursive: true });

for (const effect of effects) {
  const response = await fetch(
    "https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_128",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "xi-api-key": apiKey,
      },
      body: JSON.stringify({
        text: effect.text,
        duration_seconds: effect.duration_seconds,
        prompt_influence: effect.prompt_influence,
        model_id: "eleven_text_to_sound_v2",
        loop: false,
      }),
    },
  );

  if (!response.ok) {
    const details = await response.text();
    throw new Error(`${effect.id} failed (${response.status}): ${details}`);
  }

  const audio = Buffer.from(await response.arrayBuffer());
  await writeFile(resolve(outputDir, `${effect.id}.mp3`), audio);
  console.log(`Generated ${effect.id}`);
}

await writeFile(
  resolve(outputDir, "manifest.json"),
  `${JSON.stringify(effects, null, 2)}\n`,
);

console.log("0726 V2 sound effects complete.");
