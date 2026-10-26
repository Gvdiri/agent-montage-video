import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const apiKey = process.env.ELEVENLABS_API_KEY;

if (!apiKey) {
  throw new Error("ELEVENLABS_API_KEY is missing.");
}

const musicDir = resolve(
  "asset-library",
  "music",
  "signature-lab",
  "v4-format-expansion",
);
const sfxDir = resolve("asset-library", "sfx", "signature-kit-v1");

const sharedMusicNegatives = [
  "vocals",
  "spoken words",
  "corporate background music",
  "lo-fi vinyl noise",
  "phonk",
  "trap hi-hat rolls",
  "EDM drop",
  "festival build",
  "epic trailer",
  "huge cinematic drums",
  "sentimental piano",
  "fade-out",
];

const musicTracks = [
  {
    id: "05-deep-work-signal",
    title: "Deep Work Signal",
    seed: 2805,
    chunks: [
      {
        text: "[Immediate Focus Hook]",
        duration_ms: 10_000,
        positive_styles: [
          "instrumental",
          "108 BPM",
          "music-led deep work montage",
          "immediate tuned percussion hook",
          "tight dry kick",
          "compact bass pulse",
          "precise syncopated clicks",
          "restrained harmonic tension",
          "modern high-end production",
          "strong enough to carry text-only video",
        ],
        negative_styles: [
          ...sharedMusicNegatives,
          "synthwave",
          "cyberpunk arpeggio",
          "gaming soundtrack",
          "typing sound gimmick",
        ],
        context_adherence: "high",
      },
      {
        text: "[Work Flow]",
        duration_ms: 10_000,
        positive_styles: [
          "same tuned percussion hook",
          "stronger bass pocket",
          "layered dry polyrhythm",
          "subtle warm chord color",
          "continuous forward momentum",
          "one satisfying micro-stop",
        ],
        negative_styles: [
          ...sharedMusicNegatives,
          "synthwave",
          "cyberpunk arpeggio",
          "gaming soundtrack",
        ],
        context_adherence: "high",
      },
      {
        text: "[Locked In]",
        duration_ms: 10_000,
        positive_styles: [
          "brief low-density reset",
          "bass pulse exposed",
          "hook returns with a sharper rhythmic answer",
          "focused tension",
          "new metallic percussion detail",
          "no large climax",
        ],
        negative_styles: [
          ...sharedMusicNegatives,
          "synthwave",
          "cyberpunk arpeggio",
          "gaming soundtrack",
        ],
        context_adherence: "high",
      },
      {
        text: "[Work Completed]",
        duration_ms: 10_000,
        positive_styles: [
          "fullest precise groove",
          "recognizable focus hook",
          "confident harmonic resolution",
          "energetic but controlled",
          "clean decisive ending",
          "no fade",
        ],
        negative_styles: [
          ...sharedMusicNegatives,
          "synthwave",
          "cyberpunk arpeggio",
          "gaming soundtrack",
        ],
        context_adherence: "high",
      },
    ],
  },
  {
    id: "06-ivory-motion",
    title: "Ivory Motion",
    seed: 2806,
    chunks: [
      {
        text: "[Human Opening]",
        duration_ms: 10_000,
        positive_styles: [
          "instrumental",
          "86 BPM",
          "warm premium personal-story score",
          "immediate memorable muted guitar-harmonic motif",
          "soft tactile hand percussion",
          "round restrained bass",
          "subtle analog key texture",
          "intimate confident mood",
          "natural high-end production",
          "speech-friendly arrangement",
        ],
        negative_styles: [
          ...sharedMusicNegatives,
          "sad ballad",
          "acoustic lifestyle advertisement",
          "romantic soundtrack",
          "jazz solo",
        ],
        context_adherence: "high",
      },
      {
        text: "[Quiet Progress]",
        duration_ms: 10_000,
        positive_styles: [
          "same guitar-harmonic motif",
          "slightly stronger organic pocket",
          "gentle bass movement",
          "one warm tonal answer",
          "optimistic without uplift cliché",
          "ample room for narration",
        ],
        negative_styles: [
          ...sharedMusicNegatives,
          "sad ballad",
          "acoustic lifestyle advertisement",
          "romantic soundtrack",
          "jazz solo",
        ],
        context_adherence: "high",
      },
      {
        text: "[Reflection]",
        duration_ms: 10_000,
        positive_styles: [
          "percussion briefly reduced",
          "guitar motif exposed",
          "warm restrained harmony",
          "small emotional turn",
          "human and grounded",
          "no melodrama",
        ],
        negative_styles: [
          ...sharedMusicNegatives,
          "sad ballad",
          "acoustic lifestyle advertisement",
          "romantic soundtrack",
          "jazz solo",
        ],
        context_adherence: "high",
      },
      {
        text: "[Earned Warmth]",
        duration_ms: 10_000,
        positive_styles: [
          "full organic pocket returns",
          "recognizable guitar motif",
          "warm confident resolution",
          "subtle sense of personal progress",
          "clean intimate final hit",
          "no fade",
        ],
        negative_styles: [
          ...sharedMusicNegatives,
          "sad ballad",
          "acoustic lifestyle advertisement",
          "romantic soundtrack",
          "jazz solo",
        ],
        context_adherence: "high",
      },
    ],
  },
];

const soundEffects = [
  {
    id: "01-proof-impact",
    duration_seconds: 0.6,
    prompt_influence: 0.75,
    text: [
      "Premium restrained proof impact one-shot.",
      "A dry low-mid tactile hit with a short brushed-steel transient.",
      "Precise, modern, authoritative, no sub boom, no trailer braam, no reverb tail.",
    ].join(" "),
  },
  {
    id: "02-metal-reveal",
    duration_seconds: 0.9,
    prompt_influence: 0.7,
    text: [
      "Short premium liquid-metal reveal one-shot.",
      "A clean upward shimmer that settles into a tiny steel resonance.",
      "Elegant and restrained, no magical sparkle, no sci-fi HUD, no long tail.",
    ].join(" "),
  },
  {
    id: "03-dry-transition",
    duration_seconds: 0.5,
    prompt_influence: 0.8,
    text: [
      "Very short premium transition one-shot.",
      "Fast dry air displacement with a soft metallic edge and precise stop.",
      "No cartoon whoosh, no whistle, no cinematic boom, no reverb.",
    ].join(" "),
  },
  {
    id: "04-warm-confirmation",
    duration_seconds: 0.7,
    prompt_influence: 0.75,
    text: [
      "Warm tactile confirmation one-shot.",
      "A muted wooden click followed by a very short rounded resonant tone.",
      "Human, premium and satisfying, no app notification chime, no sparkle.",
    ].join(" "),
  },
  {
    id: "05-data-tick",
    duration_seconds: 0.5,
    prompt_influence: 0.85,
    text: [
      "Minimal premium data tick one-shot.",
      "A precise muted steel tap with a tiny low body and immediate silence.",
      "Clean, functional and modern, no beep, no clicky mouse sound, no reverb.",
    ].join(" "),
  },
];

await Promise.all([
  mkdir(musicDir, { recursive: true }),
  mkdir(sfxDir, { recursive: true }),
]);

for (const track of musicTracks) {
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
  await writeFile(resolve(musicDir, `${track.id}.mp3`), audio);
  console.log(`Generated music: ${track.title}`);
}

for (const effect of soundEffects) {
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
  await writeFile(resolve(sfxDir, `${effect.id}.mp3`), audio);
  console.log(`Generated SFX: ${effect.id}`);
}

await Promise.all([
  writeFile(
    resolve(musicDir, "manifest.json"),
    `${JSON.stringify(musicTracks, null, 2)}\n`,
  ),
  writeFile(
    resolve(sfxDir, "manifest.json"),
    `${JSON.stringify(soundEffects, null, 2)}\n`,
  ),
]);

console.log("Brand expansion generation complete.");
