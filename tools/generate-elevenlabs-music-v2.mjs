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
  "v2-candidates",
);

const candidates = [
  {
    id: "01-obsidian-swing",
    title: "Obsidian Swing",
    prompt: [
      "Create a 12-second instrumental micro-score for a premium French business talking-head Reel.",
      "Open instantly with a memorable two-note hook on a dry muted pluck, then establish a confident syncopated broken-beat groove at 94 BPM.",
      "Use tight punchy drums, controlled warm sub-bass, brushed steel percussion, and one subtle glass accent.",
      "The feeling is calm authority with forward motion: modern, tasteful, understated, and rhythmically addictive.",
      "The hook must be identifiable within the first second and return once with a small variation before the ending.",
      "End cleanly, not with a fade.",
      "Instrumental only. No vocals, no lo-fi hiss, no corporate music, no trap hi-hat rolls, no phonk, no EDM drop, no epic trailer, no cyberpunk arpeggio, no dominant pads.",
    ].join(" "),
  },
  {
    id: "02-ivory-step",
    title: "Ivory Step",
    prompt: [
      "Create a 12-second instrumental micro-score for a premium personal-brand talking-head Reel.",
      "Start immediately with a catchy three-note motif played by warm muted electric guitar harmonics, supported by dry organic hand percussion and a restrained round bass groove at 88 BPM.",
      "Add one tactile metallic click as punctuation, but keep the overall sound human, intimate, expensive, and confident rather than sentimental.",
      "Introduce a satisfying rhythmic answer around second six and finish with a crisp resolved hit.",
      "The melody must be simple enough to remember after one listen without competing with speech.",
      "Instrumental only. No vocals, no acoustic lifestyle cliché, no lo-fi beat, no corporate uplift, no jazz solo, no cinematic swell, no trap drums, no glossy pop chorus.",
    ].join(" "),
  },
  {
    id: "03-proof-pressure",
    title: "Proof Pressure",
    prompt: [
      "Create a 12-second instrumental micro-score for a high-retention business proof or case-study Reel.",
      "Begin on frame one with a sharp low-mid percussion hook: three syncopated hits with a distinctive final metallic resonance.",
      "Build a precise 106 BPM groove from dry kick, rim, muted tom, short bass pulse, and sparse chromatic mallet notes.",
      "Make it feel analytical, controlled, modern, and quietly tense, with a micro-break near second seven followed by a stronger return.",
      "It should sound like evidence arriving, not like science fiction.",
      "End with one concise signature reveal hit.",
      "Instrumental only. No vocals, no HUD beeps, no techno, no EDM drop, no trailer braam, no phonk, no corporate soundtrack, no long reverb, no generic AI ambience.",
    ].join(" "),
  },
  {
    id: "04-noir-pocket",
    title: "Noir Pocket",
    prompt: [
      "Create a 12-second instrumental micro-score with an irresistible but restrained pocket for a calm, charismatic talking-head Reel.",
      "Start instantly with a distinctive rubbery bass pickup and a clipped wooden-key response.",
      "Use a sparse neo-soul-informed groove at 97 BPM with dry drums, off-grid ghost percussion, deep controlled bass, and a minimal two-chord harmonic color.",
      "The result must feel premium, nocturnal, self-assured, and naturally cool without imitating any artist.",
      "Add a brief stop-and-return before second eight to refresh attention, then close decisively.",
      "Instrumental only. No vocals, no lo-fi vinyl noise, no sleepy beat, no trap rolls, no sentimental Rhodes solo, no funk pastiche, no glossy commercial jingle.",
    ].join(" "),
  },
  {
    id: "05-cut-signal",
    title: "Cut Signal",
    prompt: [
      "Create a 12-second instrumental micro-score designed for fast but premium social-video editing.",
      "Launch immediately with a catchy percussive motif made from a tuned metal tap, a short breathy texture, and a low kick response.",
      "Drive it with a minimal polyrhythmic groove at 110 BPM, dry transient-rich percussion, a compact bassline, and one warm tonal layer.",
      "Every two seconds should contain a subtle new detail that supports cuts without sounding busy.",
      "The mood is precise, innovative, human, and confidently different from generic technology content.",
      "Finish with the opening motif transformed into a clean final punctuation.",
      "Instrumental only. No vocals, no house drop, no cyber arpeggio, no glitch overload, no trailer sound, no corporate bed, no phonk, no ambient wash.",
    ].join(" "),
  },
];

await mkdir(outputDir, { recursive: true });

for (const candidate of candidates) {
  const response = await fetch("https://api.elevenlabs.io/v1/music", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "xi-api-key": apiKey,
    },
    body: JSON.stringify({
      prompt: candidate.prompt,
      music_length_ms: 12_000,
      model_id: "music_v2",
      force_instrumental: true,
    }),
  });

  if (!response.ok) {
    const details = await response.text();
    throw new Error(
      `${candidate.title} failed (${response.status}): ${details}`,
    );
  }

  const audio = Buffer.from(await response.arrayBuffer());
  const audioPath = resolve(outputDir, `${candidate.id}.mp3`);

  await writeFile(audioPath, audio);
  console.log(`Generated ${candidate.title}: ${audioPath}`);
}

await writeFile(
  resolve(outputDir, "manifest.json"),
  `${JSON.stringify(candidates, null, 2)}\n`,
);

console.log(`Generated ${candidates.length} candidates.`);
