import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const apiKey = process.env.ELEVENLABS_API_KEY;

if (!apiKey) {
  throw new Error("ELEVENLABS_API_KEY is missing.");
}

const outputDir = resolve(
  "asset-library",
  "music",
  "signature-lab",
  "v3-brand-tracks",
);

const sharedNegativeStyles = [
  "vocals",
  "spoken words",
  "lo-fi vinyl noise",
  "corporate background music",
  "generic technology music",
  "trap hi-hat rolls",
  "phonk",
  "EDM drop",
  "festival build",
  "epic trailer",
  "huge cinematic drums",
  "sentimental piano",
  "long ambient wash",
  "fade-out",
];

const tracks = [
  {
    id: "01-obsidian-swing-main",
    title: "Obsidian Swing Main",
    seed: 2701,
    chunks: [
      {
        text: "[Opening Hook]",
        duration_ms: 10_000,
        positive_styles: [
          "instrumental",
          "94 BPM",
          "premium minimal broken beat",
          "immediate memorable two-note muted pluck hook",
          "dry punchy drums",
          "warm controlled sub-bass",
          "brushed steel percussion",
          "subtle rhythmic swing",
          "speech-friendly arrangement",
          "high-end modern production",
        ],
        negative_styles: sharedNegativeStyles,
        context_adherence: "high",
      },
      {
        text: "[Pocket Development]",
        duration_ms: 10_000,
        positive_styles: [
          "same two-note hook with a small rhythmic variation",
          "confident syncopated groove",
          "one restrained glass accent",
          "slightly stronger bass movement",
          "new dry percussion detail",
          "ample space in the midrange for narration",
        ],
        negative_styles: sharedNegativeStyles,
        context_adherence: "high",
      },
      {
        text: "[Tension Reset]",
        duration_ms: 10_000,
        positive_styles: [
          "brief subtraction at the start of the section",
          "hook reduced to bass and muted pluck",
          "controlled tension",
          "rhythmic return halfway through",
          "clean tactile percussion",
        ],
        negative_styles: sharedNegativeStyles,
        context_adherence: "high",
      },
      {
        text: "[Confident Payoff]",
        duration_ms: 10_000,
        positive_styles: [
          "fullest version of the restrained groove",
          "recognizable opening hook",
          "stronger pocket without a drop",
          "precise premium finish",
          "clean final signature hit",
          "no fade",
        ],
        negative_styles: sharedNegativeStyles,
        context_adherence: "high",
      },
    ],
  },
  {
    id: "02-afro-mineral",
    title: "Afro Mineral",
    seed: 2702,
    chunks: [
      {
        text: "[Rhythmic Identity]",
        duration_ms: 10_000,
        positive_styles: [
          "instrumental",
          "100 BPM",
          "subtle Afro-diasporic rhythmic pocket",
          "immediate interlocking percussion hook",
          "dry hand percussion",
          "soft shaker movement",
          "muted guitar harmonics",
          "round controlled bassline",
          "brushed metal punctuation",
          "elegant premium production",
        ],
        negative_styles: [
          ...sharedNegativeStyles,
          "amapiano log drum",
          "tropical pop",
          "party track",
          "afrobeats type-beat imitation",
        ],
        context_adherence: "high",
      },
      {
        text: "[Warm Forward Motion]",
        duration_ms: 10_000,
        positive_styles: [
          "same interlocking rhythm with a guitar answer",
          "charismatic bass pocket",
          "organic human groove",
          "one new tuned percussion detail",
          "sparse melody",
          "clear room for speech",
        ],
        negative_styles: [
          ...sharedNegativeStyles,
          "amapiano log drum",
          "tropical pop",
          "party track",
        ],
        context_adherence: "high",
      },
      {
        text: "[Breath And Re-entry]",
        duration_ms: 10_000,
        positive_styles: [
          "short percussion-only reset",
          "muted guitar hook returns",
          "bass rejoins gradually",
          "subtle call and response",
          "grounded confident energy",
        ],
        negative_styles: [
          ...sharedNegativeStyles,
          "amapiano log drum",
          "tropical pop",
          "party track",
        ],
        context_adherence: "high",
      },
      {
        text: "[Mineral Payoff]",
        duration_ms: 10_000,
        positive_styles: [
          "full interlocking pocket",
          "warm guitar harmonics",
          "precise steel accents",
          "memorable opening rhythm",
          "confident clean resolution",
          "no fade",
        ],
        negative_styles: [
          ...sharedNegativeStyles,
          "amapiano log drum",
          "tropical pop",
          "party track",
        ],
        context_adherence: "high",
      },
    ],
  },
  {
    id: "03-controlled-rise",
    title: "Controlled Rise",
    seed: 2703,
    chunks: [
      {
        text: "[Immediate Momentum]",
        duration_ms: 10_000,
        positive_styles: [
          "instrumental",
          "96 BPM",
          "controlled motivational energy",
          "memorable three-note plucked hook",
          "compact low pulse",
          "dry modern drums",
          "restrained harmonic movement",
          "tactile organic percussion",
          "premium speech-friendly mix",
        ],
        negative_styles: [
          ...sharedNegativeStyles,
          "orchestra",
          "heroic strings",
          "brass",
          "gym motivation music",
        ],
        context_adherence: "high",
      },
      {
        text: "[First Lift]",
        duration_ms: 10_000,
        positive_styles: [
          "same three-note hook",
          "slightly wider harmony",
          "firmer but restrained drums",
          "forward bass pulse",
          "subtle sense of progress",
          "no climax",
        ],
        negative_styles: [
          ...sharedNegativeStyles,
          "orchestra",
          "heroic strings",
          "brass",
          "gym motivation music",
        ],
        context_adherence: "high",
      },
      {
        text: "[Controlled Tension]",
        duration_ms: 10_000,
        positive_styles: [
          "reduced drums at the opening",
          "low pulse and plucked hook remain",
          "gradual rhythmic return",
          "small harmonic lift",
          "focused anticipation",
        ],
        negative_styles: [
          ...sharedNegativeStyles,
          "orchestra",
          "heroic strings",
          "brass",
          "gym motivation music",
        ],
        context_adherence: "high",
      },
      {
        text: "[Earned Resolution]",
        duration_ms: 10_000,
        positive_styles: [
          "strongest version of the compact groove",
          "clear three-note identity",
          "confident harmonic resolution",
          "energy without grandeur",
          "clean final signature hit",
          "no fade",
        ],
        negative_styles: [
          ...sharedNegativeStyles,
          "orchestra",
          "heroic strings",
          "brass",
          "gym motivation music",
        ],
        context_adherence: "high",
      },
    ],
  },
  {
    id: "04-noir-pocket",
    title: "Noir Pocket",
    seed: 2704,
    chunks: [
      {
        text: "[Noir Hook]",
        duration_ms: 10_000,
        positive_styles: [
          "instrumental",
          "98 BPM",
          "addictive restrained neo-soul broken-beat pocket",
          "immediate rubbery bass pickup",
          "clipped wooden-key response",
          "dry drums",
          "off-grid ghost percussion",
          "minimal two-chord color",
          "nocturnal premium confidence",
          "high-end modern production",
        ],
        negative_styles: [
          ...sharedNegativeStyles,
          "jazz solo",
          "funk pastiche",
          "sleepy beat",
          "glossy pop chorus",
        ],
        context_adherence: "high",
      },
      {
        text: "[Deep Pocket]",
        duration_ms: 10_000,
        positive_styles: [
          "same bass pickup and wooden-key answer",
          "stronger ghost-note groove",
          "tight rhythmic reward",
          "sparse harmonic movement",
          "room for spoken voice",
        ],
        negative_styles: [
          ...sharedNegativeStyles,
          "jazz solo",
          "funk pastiche",
          "sleepy beat",
        ],
        context_adherence: "high",
      },
      {
        text: "[Stop And Return]",
        duration_ms: 10_000,
        positive_styles: [
          "brief stop after the opening beat",
          "bass hook exposed",
          "drums return with a new syncopation",
          "controlled nocturnal tension",
          "short wooden-key punctuation",
        ],
        negative_styles: [
          ...sharedNegativeStyles,
          "jazz solo",
          "funk pastiche",
          "sleepy beat",
        ],
        context_adherence: "high",
      },
      {
        text: "[Pocket Payoff]",
        duration_ms: 10_000,
        positive_styles: [
          "full dry broken-beat groove",
          "recognizable rubbery bass pickup",
          "confident wooden-key answer",
          "rhythmically satisfying close",
          "clean final hit",
          "no fade",
        ],
        negative_styles: [
          ...sharedNegativeStyles,
          "jazz solo",
          "funk pastiche",
          "sleepy beat",
        ],
        context_adherence: "high",
      },
    ],
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
      composition_plan: {
        chunks: track.chunks,
      },
      model_id: "music_v2",
      seed: track.seed,
    }),
  });

  if (!response.ok) {
    const details = await response.text();
    throw new Error(`${track.title} failed (${response.status}): ${details}`);
  }

  const audio = Buffer.from(await response.arrayBuffer());
  const audioPath = resolve(outputDir, `${track.id}.mp3`);

  await writeFile(audioPath, audio);
  console.log(`Generated ${track.title}: ${audioPath}`);
}

await writeFile(
  resolve(outputDir, "manifest.json"),
  `${JSON.stringify(tracks, null, 2)}\n`,
);

console.log(`Generated ${tracks.length} reusable brand tracks.`);
