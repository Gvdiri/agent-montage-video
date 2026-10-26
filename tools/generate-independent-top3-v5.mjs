import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const apiKey = process.env.ELEVENLABS_API_KEY;

if (!apiKey) {
  throw new Error("ELEVENLABS_API_KEY is missing.");
}

const outputDir = resolve(
  "asset-library",
  "music",
  "top3-independent-v5",
);

const tracks = [
  {
    id: "01-magnetic-tension",
    title: "Magnetic Tension",
    prompt: [
      "Create a 20-second instrumental with an instantly addictive dark motivational pulse.",
      "Use 112 BPM, a powerful half-time pocket, clean distorted low bass, dry punchy drums,",
      "a tense three-note plucked hook, and small rhythmic rewards every four bars.",
      "It must feel disciplined, ambitious, magnetic, modern, and expensive rather than heroic.",
      "Build genuine momentum and deliver a satisfying final eight seconds.",
      "No vocals. Prioritize a memorable musical identity and strong production over behaving like quiet background music.",
    ].join(" "),
  },
  {
    id: "02-human-engine",
    title: "Human Engine",
    prompt: [
      "Create a 20-second instrumental built around a sophisticated Afro-diasporic broken groove at 102 BPM.",
      "Open immediately with an interlocking percussion and bass hook, then add a warm plucked-string answer,",
      "deep rounded low end, tactile hand percussion, and a restrained metallic counter-rhythm.",
      "Make it charismatic, physical, soulful, premium, and forward-moving without becoming a party track.",
      "The rhythm must be memorable after one listen and evolve clearly in the second half.",
      "No vocals. Let the groove have real personality.",
    ].join(" "),
  },
  {
    id: "03-silent-build",
    title: "Silent Build",
    prompt: [
      "Create a 20-second music-led instrumental for a cinematic deep-work montage with bold text on screen.",
      "Use 120 BPM, a compelling four-note analog-synth motif, tight modern percussion,",
      "a driving bass pulse, textured organic clicks, and a clear emotional rise.",
      "Start with the hook on frame one, create a brief suspension near the midpoint,",
      "then return with a powerful but tasteful final section.",
      "It should make repetitive work feel meaningful, focused, and inevitable.",
      "No vocals. This track is allowed to command attention.",
    ].join(" "),
  },
];

await mkdir(outputDir, { recursive: true });

for (const track of tracks) {
  const response = await fetch("https://api.elevenlabs.io/v1/music", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "xi-api-key": apiKey,
    },
    body: JSON.stringify({
      prompt: track.prompt,
      music_length_ms: 20_000,
      model_id: "music_v2",
      force_instrumental: true,
    }),
  });

  if (!response.ok) {
    const details = await response.text();
    throw new Error(`${track.title} failed (${response.status}): ${details}`);
  }

  const audio = Buffer.from(await response.arrayBuffer());
  await writeFile(resolve(outputDir, `${track.id}.mp3`), audio);
  console.log(`Generated ${track.title}`);
}

await writeFile(
  resolve(outputDir, "README.md"),
  [
    "# Independent Top 3 - Exploration Only",
    "",
    "> STATUS: NOT APPROVED",
    ">",
    "> Three independent creative directions. None is a standing rule or a",
    "> selected brand signature.",
    "",
    ...tracks.map((track) => `- \`${track.id}.mp3\`: ${track.title}`),
    "",
  ].join("\n"),
);

console.log("Independent top 3 generation complete.");
