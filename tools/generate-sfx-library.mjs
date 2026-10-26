/**
 * Generateur de bibliotheque SFX - Hyperframes
 *
 * Lecon apprise le 2026-09-10 : l'ancien generateur (generate-0726-v2-sfx.mjs)
 * demandait "liquid-chrome shimmer", "glass highlight", "brushed-steel click".
 * C'est le vocabulaire de l'identite VISUELLE de la marque (metal, chrome, acier).
 * Transpose en prompt sonore, il produit litteralement du chrome : centroide mesure
 * 8 000 a 10 700 Hz, 91 a 98 % de l'energie au-dessus de 3 kHz.
 * La reference qui performe est a 84-225 Hz, 0 % au-dessus de 3 kHz.
 *
 * => L'identite visuelle est metal. L'identite SONORE est sub-grave.
 *    Vocabulaire autorise : sub, low, deep, chest, thud, rumble, muffled, felt.
 *    Vocabulaire interdit : chrome, glass, shimmer, sparkle, metallic, crystal, bright.
 *    Chaque prompt porte sa liste de negatifs.
 *
 * Chaque son genere passe ensuite par tools/sfx_bench.py. Ce qui sort du spec est
 * jete, pas reecoute.
 *
 * Usage : node tools/generate-sfx-library.mjs <vague> [--only role1,role2] [--dry]
 */
import { mkdir, writeFile, access } from "node:fs/promises";
import { resolve, join } from "node:path";

const apiKey = process.env.ELEVENLABS_API_KEY;
if (!apiKey) throw new Error("ELEVENLABS_API_KEY manquante dans l'environnement.");

const NEG_SUB = "no high frequencies, no metallic ring, no glass, no shimmer, no sparkle, no cymbal, no hiss, no reverb wash, no music, no voice";
const NEG_UI = "no music, no voice, no reverb, no cartoon, no arcade, no melody";

/** vague 1 - large, exploratoire. On mesure ensuite et on recalibre. */
const VAGUE_1 = [
  // ---------------------------------------------------------------- IMPACT
  // Role : le coup. Hook, chiffre qui claque, revelation seche, negatif rouge.
  // Cible : centroide < 450 Hz, < 6 % d'aigus, > 35 % sous 200 Hz, attaque < 60 ms.
  { id: "impact-01-chest", role: "impact", d: 2.0, p: 0.75,
    t: `Deep sub bass impact, single dry chest thump at 60 hertz, instant attack, short controlled decay, felt in the body rather than heard, cinematic low end only, ${NEG_SUB}` },
  { id: "impact-02-slam-sec", role: "impact", d: 1.5, p: 0.8,
    t: `Dry low frequency slam, one heavy muffled thud, tight and immediate, no tail, like a heavy door closing in a padded room, pure low end, ${NEG_SUB}` },
  { id: "impact-03-808", role: "impact", d: 2.0, p: 0.72,
    t: `Short 808 sub drop, deep round bass hit with a fast pitch fall, clean and dry, trap style low end, no distortion, ${NEG_SUB}` },
  { id: "impact-04-hook", role: "impact", d: 1.8, p: 0.78,
    t: `Cinematic sub bass hit for a video opening, deep rumble that arrives instantly and fades in one second, heavy and confident, low frequency only, ${NEG_SUB}` },
  { id: "impact-05-negatif", role: "impact", d: 1.6, p: 0.78,
    t: `Dark ominous low impact, muffled bass thud with a slightly detuned unsettling low tone, feels like bad news, oppressive and heavy, ${NEG_SUB}` },
  { id: "impact-06-chiffre", role: "impact", d: 1.2, p: 0.8,
    t: `Very short deep bass punch for a number appearing on screen, one dry low hit, punchy attack, almost no decay, ${NEG_SUB}` },
  { id: "impact-07-rumble", role: "impact", d: 2.2, p: 0.7,
    t: `Low rumbling impact, deep earth movement, dense sub bass with a slow rolling decay, powerful and restrained, ${NEG_SUB}` },
  { id: "impact-08-double", role: "impact", d: 2.0, p: 0.75,
    t: `Two deep sub bass hits in quick succession, dry and tight, heartbeat like, pure low end, ${NEG_SUB}` },
  { id: "impact-09-mat", role: "impact", d: 1.4, p: 0.8,
    t: `Muffled heavy low thud, like a fist hitting a thick mattress, dull and deep, absolutely no brightness, ${NEG_SUB}` },
  { id: "impact-10-coupure", role: "impact", d: 1.0, p: 0.82,
    t: `Abrupt deep bass stop, one low hit that cuts dead instantly with total silence after, dry and brutal, ${NEG_SUB}` },

  // ---------------------------------------------------------------- REVEAL
  // Role : la carte de preuve qui apparait, le logo qui entre.
  // Cible : centroide < 700 Hz, < 12 % d'aigus, > 20 % sous 200 Hz.
  { id: "reveal-01-swell", role: "reveal", d: 2.5, p: 0.75,
    t: `Deep sub bass swell rising into a soft low bloom, slow build over one second then settles, warm and enveloping, low frequency only, ${NEG_SUB}` },
  { id: "reveal-02-bloom", role: "reveal", d: 2.0, p: 0.72,
    t: `Low frequency bloom, a deep round bass note that opens up and breathes, cinematic reveal, warm and dark, ${NEG_SUB}` },
  { id: "reveal-03-inhale", role: "reveal", d: 2.2, p: 0.75,
    t: `Muffled reverse air movement leading into a deep low landing, like an inhale before a statement, dark and restrained, ${NEG_SUB}` },
  { id: "reveal-04-sous-carte", role: "reveal", d: 1.8, p: 0.78,
    t: `Soft deep bass push for a panel sliding into frame, low pressure wave, subtle and premium, no transient click, ${NEG_SUB}` },
  { id: "reveal-05-logo", role: "reveal", d: 2.0, p: 0.74,
    t: `Deep low tonal reveal for a brand logo landing, sub bass note with a short warm resonance, confident and clean, ${NEG_SUB}` },
  { id: "reveal-06-lent", role: "reveal", d: 3.0, p: 0.7,
    t: `Slow deep sub bass rise and settle, three seconds, dark cinematic atmosphere opening, no impact, pure low end movement, ${NEG_SUB}` },
  { id: "reveal-07-chaud", role: "reveal", d: 2.2, p: 0.72,
    t: `Warm analog low frequency swell, round and organic, like a large speaker cone moving, no digital edge, ${NEG_SUB}` },
  { id: "reveal-08-pression", role: "reveal", d: 1.6, p: 0.78,
    t: `Sudden low pressure change, deep muffled whump like air displaced in a closed room, short and physical, ${NEG_SUB}` },

  // ------------------------------------------------------------ TRANSITION
  // Role : le liant entre deux plans. Cadence 1,5 s => il en faut BEAUCOUP.
  // Cible : centroide < 900 Hz, < 20 % d'aigus, > 12 % sous 200 Hz.
  { id: "trans-01-sub-whoosh", role: "transition", d: 1.2, p: 0.78,
    t: `Low muffled whoosh, dark air movement passing quickly, no high frequency content at all, heavily filtered, ${NEG_SUB}` },
  { id: "trans-02-balayage", role: "transition", d: 1.0, p: 0.8,
    t: `Short dark sweep, muffled low frequency movement from left to right, dull and filtered, ${NEG_SUB}` },
  { id: "trans-03-panneau", role: "transition", d: 0.9, p: 0.8,
    t: `Quick low displacement sound for a panel changing on screen, dry muffled movement with a soft low landing, ${NEG_SUB}` },
  { id: "trans-04-inverse", role: "transition", d: 1.1, p: 0.76,
    t: `Reverse low frequency swell that stops abruptly, dark muffled rise cut short, no bright tail, ${NEG_SUB}` },
  { id: "trans-05-coupe", role: "transition", d: 0.7, p: 0.82,
    t: `Very short muffled low transition, one dull soft movement, understated, almost subliminal, ${NEG_SUB}` },
  { id: "trans-06-glisse", role: "transition", d: 1.0, p: 0.78,
    t: `Low filtered slide, deep muffled friction, like a heavy object sliding on a soft surface, ${NEG_SUB}` },
  { id: "trans-07-air", role: "transition", d: 1.3, p: 0.74,
    t: `Dark filtered air movement, low pass filtered wind gust, short and controlled, no hiss, ${NEG_SUB}` },
  { id: "trans-08-retour", role: "transition", d: 0.8, p: 0.8,
    t: `Soft low return transition, muffled reverse movement ending in a warm dull tap, understated, ${NEG_SUB}` },
  { id: "trans-09-basculement", role: "transition", d: 1.0, p: 0.78,
    t: `Low frequency flip, dark muffled tumble with a soft low resolve, dry and quick, ${NEG_SUB}` },
  { id: "trans-10-sec", role: "transition", d: 0.6, p: 0.84,
    t: `Extremely short dry low transition tick, one dull muffled movement, no tail whatsoever, ${NEG_SUB}` },

  // ----------------------------------------------------------------- RISER
  // Role : la tension qui monte vers la revelation ou vers le CTA.
  // Cible : centroide < 1400 Hz, < 30 % d'aigus.
  { id: "riser-01-tension", role: "riser", d: 2.5, p: 0.75,
    t: `Dark low frequency tension riser, deep rumble slowly building in intensity, filtered and dull, ends without a crash, ${NEG_SUB}` },
  { id: "riser-02-court", role: "riser", d: 1.5, p: 0.78,
    t: `Short low build up, deep filtered rise over one second, restrained and cinematic, no impact at the end, ${NEG_SUB}` },
  { id: "riser-03-cta", role: "riser", d: 2.0, p: 0.74,
    t: `Warm low frequency lift, deep tone rising gently and confidently, positive and grounded, ${NEG_SUB}` },
  { id: "riser-04-sourd", role: "riser", d: 3.0, p: 0.72,
    t: `Muffled deep drone building slowly over three seconds, oppressive low pressure increase, heavily low pass filtered, ${NEG_SUB}` },
  { id: "riser-05-pulse", role: "riser", d: 2.5, p: 0.74,
    t: `Low pulsing build, deep sub bass pulses accelerating, dark and rhythmic, ${NEG_SUB}` },
  { id: "riser-06-souffle", role: "riser", d: 2.0, p: 0.72,
    t: `Dark filtered air building up, low rumbling approach, dull and heavy, no bright whoosh, ${NEG_SUB}` },

  // ---------------------------------------------------------- CONFIRMATION
  // Role : ca a marche. Le positif, la resolution, la coche.
  // Cible : centroide < 1200 Hz, < 25 % d'aigus, > 10 % sous 200 Hz.
  { id: "conf-01-resolve", role: "confirmation", d: 1.2, p: 0.78,
    t: `Warm low confirmation tone, deep round note that resolves upward slightly, satisfying and grounded, dark timbre, ${NEG_SUB}` },
  { id: "conf-02-coche", role: "confirmation", d: 0.9, p: 0.8,
    t: `Short warm low confirmation, muffled soft tap followed by a brief deep tone, positive and understated, ${NEG_SUB}` },
  { id: "conf-03-valide", role: "confirmation", d: 1.0, p: 0.78,
    t: `Deep positive resolve, low frequency note landing warmly, feels like something locking into place, ${NEG_SUB}` },
  { id: "conf-04-envoi", role: "confirmation", d: 1.2, p: 0.76,
    t: `Warm low send confirmation, soft deep upward pulse with a gentle landing, confident not cute, ${NEG_SUB}` },
  { id: "conf-05-chaud", role: "confirmation", d: 1.4, p: 0.74,
    t: `Warm analog low tone confirmation, round and organic, brief and reassuring, ${NEG_SUB}` },
  { id: "conf-06-final", role: "confirmation", d: 1.6, p: 0.75,
    t: `Deep closing tone, low frequency note that settles and fades, sense of completion, dark and warm, ${NEG_SUB}` },

  // -------------------------------------------------------------------- UI
  // Role : les sons d'interface reels. Ici la brillance est LEGITIME - c'est
  // ce que fait vraiment un clavier ou un clic. Spec plus permissif.
  { id: "ui-01-clic", role: "ui", d: 0.4, p: 0.85,
    t: `Single dry mouse click, mechanical, close mic, no room, ${NEG_UI}` },
  { id: "ui-02-clavier-court", role: "ui", d: 0.5, p: 0.82,
    t: `Two or three mechanical keyboard key presses, dry tactile switches, close mic, ${NEG_UI}` },
  { id: "ui-03-clavier-rafale", role: "ui", d: 2.5, p: 0.8,
    t: `Fast mechanical keyboard typing burst, someone typing a command quickly, dry tactile switches, close mic, ${NEG_UI}` },
  { id: "ui-04-entree", role: "ui", d: 0.5, p: 0.84,
    t: `Single enter key press on a mechanical keyboard, one decisive deep thock, close mic, ${NEG_UI}` },
  { id: "ui-05-notif", role: "ui", d: 0.6, p: 0.8,
    t: `Short soft notification pop, muted and modern, one gentle blip, not cheerful, ${NEG_UI}` },
  { id: "ui-06-toggle", role: "ui", d: 0.35, p: 0.85,
    t: `Small physical toggle switch flipping, dry plastic click, close mic, ${NEG_UI}` },
  { id: "ui-07-souris-double", role: "ui", d: 0.5, p: 0.85,
    t: `Double mouse click, two quick dry mechanical clicks, close mic, ${NEG_UI}` },
  { id: "ui-08-scroll", role: "ui", d: 0.8, p: 0.8,
    t: `Mouse scroll wheel turning several notches, dry mechanical detents, close mic, ${NEG_UI}` },

  // --------------------------------------------------------------- TEXTURE
  // Role : le lit sous un panneau de preuve, la tension continue.
  { id: "tex-01-drone", role: "texture", d: 6.0, p: 0.72,
    t: `Deep continuous sub bass drone, steady dark low hum, no movement, no melody, cinematic tension bed, ${NEG_SUB}` },
  { id: "tex-02-salle", role: "texture", d: 6.0, p: 0.7,
    t: `Low room tone, deep quiet mechanical hum of a large empty space, steady and dark, ${NEG_SUB}` },
  { id: "tex-03-tension", role: "texture", d: 5.0, p: 0.72,
    t: `Dark low tension bed, slowly pulsing sub bass atmosphere, unsettling and restrained, ${NEG_SUB}` },
  { id: "tex-04-serveur", role: "texture", d: 5.0, p: 0.74,
    t: `Deep server room hum, low steady machine drone, filtered dark, ${NEG_SUB}` },
  { id: "tex-05-souffle", role: "texture", d: 4.0, p: 0.7,
    t: `Very low filtered air atmosphere, deep breathing space tone, dark and calm, ${NEG_SUB}` },
];

const VAGUES = { 1: VAGUE_1 };

// ---------------------------------------------------------------------------

const args = process.argv.slice(2);
const vague = args[0] || "1";
const dry = args.includes("--dry");
const onlyArg = args.find((a) => a.startsWith("--only"));
const only = onlyArg ? (onlyArg.split("=")[1] || args[args.indexOf(onlyArg) + 1] || "").split(",").filter(Boolean) : null;

let specs = VAGUES[vague];
if (!specs) throw new Error(`Vague inconnue : ${vague}`);
if (only && only.length) specs = specs.filter((s) => only.includes(s.role));

const outDir = resolve("asset-library", "sfx", `_brut-vague-${vague}`);
await mkdir(outDir, { recursive: true });

console.log(`Vague ${vague} — ${specs.length} sons à générer vers ${outDir}`);
if (dry) {
  for (const s of specs) console.log(`  [dry] ${s.id.padEnd(24)} ${s.role.padEnd(13)} ${s.d}s`);
  process.exit(0);
}

const manifest = [];
let ok = 0, ko = 0, skip = 0;

for (const [i, s] of specs.entries()) {
  const target = join(outDir, `${s.id}.mp3`);
  try {
    await access(target);
    console.log(`[${i + 1}/${specs.length}] ${s.id} — déjà là, saut`);
    manifest.push({ ...s, fichier: `${s.id}.mp3`, statut: "existant" });
    skip++;
    continue;
  } catch { /* pas encore genere */ }

  let done = false;
  for (let attempt = 1; attempt <= 3 && !done; attempt++) {
    try {
      const res = await fetch(
        "https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_128",
        {
          method: "POST",
          headers: { "Content-Type": "application/json", "xi-api-key": apiKey },
          body: JSON.stringify({
            text: s.t,
            duration_seconds: s.d,
            prompt_influence: s.p,
          }),
        },
      );
      if (!res.ok) {
        const body = await res.text();
        throw new Error(`HTTP ${res.status} — ${body.slice(0, 200)}`);
      }
      const buf = Buffer.from(await res.arrayBuffer());
      if (buf.length < 2000) throw new Error(`fichier suspect (${buf.length} o)`);
      await writeFile(target, buf);
      console.log(`[${i + 1}/${specs.length}] ${s.id.padEnd(24)} ${s.role.padEnd(13)} ${(buf.length / 1024).toFixed(0)} Ko`);
      manifest.push({ ...s, fichier: `${s.id}.mp3`, octets: buf.length, statut: "genere" });
      ok++;
      done = true;
    } catch (err) {
      if (attempt === 3) {
        console.error(`[${i + 1}/${specs.length}] ${s.id} — ÉCHEC : ${err.message}`);
        manifest.push({ ...s, statut: "echec", erreur: err.message });
        ko++;
      } else {
        await new Promise((r) => setTimeout(r, 2000 * attempt));
      }
    }
  }
}

await writeFile(
  join(outDir, "manifest.json"),
  JSON.stringify({ vague, genere_le: new Date().toISOString(), sons: manifest }, null, 2),
  "utf8",
);

console.log(`\n${ok} générés, ${skip} déjà présents, ${ko} échecs → ${outDir}`);
console.log(`Étape suivante : python tools/sfx_bench.py "${outDir}" --role <role>`);
