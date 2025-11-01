# backend/prompts.py

# ===== Shared banlist and style kernels =====
BANLIST = [
    "ethical concerns", "ethical precarity", "moral imperative", "moonshot",
    "snake oil", "technological overreach", "chasing unicorns", "balance in research",
    "science isn’t settled", "science is not settled", "frontier of hope", "seeds of hope"
]

SPEECH_SYSTEM = """
You are a Congressional Debate finalist. Given a bill, write two complete, ready-to-deliver speeches:
one Affirmation and one Negation.

Constraints:
- Nationals-final tone: brisk signposting, vivid but tasteful imagery, clean transitions, tight warrants.
- Include: Hook (1–2 sentences), Roadmap (1 sentence), 3 flowing contentions (Claim → Mechanism (2–3 steps) → Impact → "what this means"),
  weighing (probability • timeframe • irreversibility/distribution), crystallization, and a memorable closing line.
- Natural paragraphs (no bullet points), ~140–160 wpm pacing. Aim for ~{minutes} minutes each.
- Do NOT fabricate statistics; when suggesting evidence, phrase as "According to [credible source category] ...".
- Vary rhetoric: one analogy or framing device; one "what this means" bridge per contention; one crystallization.
- Before writing, brainstorm 5 analogy candidates per side; pick the best one to use in each speech.
  After both speeches, print an "Analogy Bank" (Aff 5, Neg 5).
- Avoid any of these phrases: {banlist}.
"""

NOVELTY_TAXONOMY = """
When asked for creative arguments, generate candidates across these buckets:
- Implementation failure modes (procurement, right-of-way, cost overrun mechanics)
- Second-order effects (lock-in, path dependence, rebound, crowd-out of better alternatives)
- Supply chain ethics & geopolitics (materials, labor, ESG, sanctions exposure)
- Systems risk & security (cyber-physical, fail-safes, critical dependencies)
- Legal/federalism/administrative law (preemption, APA, state matches, litigation risk)
- Equity & spatial distribution (who benefits vs who pays; rural/urban; corridors vs periphery)
- Environmental side-effects (construction-phase emissions, biodiversity, water, mining)
- Labor & capacity constraints (specialized workforce bottlenecks, training lag)
- Data/privacy/AI governance (telemetry, tracking, vendor lock)
- International commitments (treaties, standards misalignment)
"""

BIOMED_TAXONOMY = """
For biomedical/regenerative topics also explore:
- GMP/CMC manufacturing scale-up (cleanrooms, sterility assurance, batch failure rates)
- Autologous vs allogeneic pipelines (throughput, QC burden, cost per patient)
- Reimbursement pathways (CMS/VA coverage, CPT/HCPCS codes, DRG fit/misfit)
- IP thickets & freedom-to-operate (gene-editing, iPSC methods, growth factors)
- Biobank consent drift & reidentification risk (HIPAA/GDPR, broad consent mismatch)
- Xeno-free reagent supply chains & ethical sourcing (growth media, scaffolds)
- Tumorigenicity/off-target risks & FDA clinical holds (risk perception, trust shocks)
- Surgical workforce/training bottlenecks for implantation & rehab
- Data governance for cell provenance & chain-of-custody (auditability)
- Dual-use & militarization (performance enhancement vs therapy optics)
"""

def _style_extra(style_lc: str, novelty: str):
    extras = {
        "creative": " Lean into vivid, debate-appropriate imagery; keep one memorable image per speech.",
        "technical": " Prioritize precise policy mechanisms and brisk, evidence-friendly prose; limit imagery.",
        "novice-friendly": " Use simpler sentences, define jargon in-line, and add brief concrete examples.",
        "razor": " Cut filler. Short, punchy, high-density lines; crisp signposting; strong crystallization.",
        "nationals": ""
    }
    extra = extras.get(style_lc, "")
    if style_lc == "creative" or (novelty or "standard").lower() in {"high", "wild"}:
        extra += "\nFavor non-obvious but defensible mechanisms. Avoid top-10 common talking points."
    extra += "\nPrefer 10–22 words per sentence on average, varied cadence. Use 'First, Second, Third' in roadmap and as paragraph openers."
    return extra

# ===== Full speeches =====
def build_speech_prompt(bill: str, minutes: int = 2, style: str = "nationals", novelty: str = "standard", custom_instructions: str | None = None):
    style_lc = (style or "nationals").lower().strip()
    system_prompt = SPEECH_SYSTEM.format(minutes=minutes, banlist=", ".join(BANLIST)) + _style_extra(style_lc, novelty)

    user_prompt = f"""
Bill:
{bill}

Write TWO speeches to read aloud:

[Affirmation Speech]
- Hook
- Roadmap
- Three integrated contentions (Claim → Mechanism (2–3 steps) → Impact → "what this means")
- Weighing (probability • timeframe • irreversibility/distribution)
- Crystallization
- Closing line

[Negation Speech]
(same structure)

Target length: ~{minutes} minutes each. Style: {style_lc}.
Return the two speeches with section headings and clean paragraphs (no bullets).
At the end, include:
ANALOGY BANK
- AFF (5 one-liners)
- NEG (5 one-liners)

Replace any banned phrases with fresher wording.
""".strip()

    if custom_instructions:
        user_prompt += f"\n\nADDITIONAL INSTRUCTIONS:\n{custom_instructions.strip()}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

# ===== Argument package =====
SYSTEM_COACH = """
You are a Congressional Debate coach.
Task: Given a bill, produce unique Affirmation and Negation packages: arguments (with warrants), evidence prompts, creative rhetoric (hooks/analogies), and weighing/crystallization lines.
Constraints:
- Clean structure; tight warrants; explicit impacts; "what this means" bridges; crisp crystallization.
- Each contention must follow: Claim → Mechanism (2–3 concrete steps) → Impact → "what this means".
- Always include Weighing using: probability • timeframe • irreversibility/distribution.
- Avoid cliché phrasing; use domain-grounded analogies; vary sentence length (10–22 words).
Output schema:
[BILL SUMMARY – 1–2 lines]

AFFIRMATION
• Contentions (3): [claim] — [mechanism] — [impact] — [what this means]
• Rhetoric: Hook | Analogy | Crystallization line
• Evidence Prompts: (3–5, by source type/topic + what to pull)
• Weighing: probability • timeframe • irreversibility/distribution

NEGATION
• Contentions (3): [claim] — [mechanism] — [impact] — [what this means]
• Rhetoric: Hook | Analogy | Crystallization line
• Evidence Prompts: (3–5)
• Weighing: probability • timeframe • irreversibility/distribution

QUICK QX PACK
• 5 cross-questions targeting key mechanisms/links/impacts

ANALOGY VARIATIONS
• AFF (5): one-line options tied to chosen angles
• NEG (5): one-line options tied to chosen angles
"""

FEW_SHOT_EXAMPLE = """
Example Bill (summary): Prohibit public-school "Gifted & Talented" (GT) programs; redirect funds to universal enrichment.

AFFIRMATION
• Contentions:
  1) Equity of Access — selective screening replicates bias → closes opportunity gaps.
  2) Peer Effects For All — enrichment raises floor + ceiling via cooperative learning → system-wide gains.
  3) Admin Overhead → Instruction — redirect GT admin to teachers → more instructional minutes.
• Rhetoric: Hook: "Gifted isn't a classroom—it's a chance." | Analogy: "Water the whole garden." | Crystallization: "Equity that scales beats excellence that isolates."
• Evidence Prompts: mis-ID rates by income/race; enrichment RCTs; GT admin costs; cooperative learning meta-analyses.
• Weighing: scope • sustainability • probability

NEGATION
• Contentions:
  1) Tailored Acceleration — high-ability pacing needs → avoid disengagement/flight.
  2) Spillover from Advanced Tracks — prestige/grants help everyone → don't torch the halo.
  3) Implementation Risk — universal enrichment unfunded → mediocrity for all.
• Rhetoric: Hook: "Excellence isn't elitism; it's oxygen." | Analogy: "Sprinters shouldn't walk." | Crystallization: "Fix the filter, don't smash the beaker."
• Evidence Prompts: attrition/engagement data; magnet/advanced program outcomes; PD costs.
• Weighing: probability of rollout failure • distributional harms • retention.
"""

FEW_SHOT_BIOMED = """
Example Bill (summary): Appropriate $2B annually for limb-regeneration stem-cell research under NIH/DoD, funding basic science through trials.

AFFIRMATION
• Contentions:
  1) Whole-Function Recovery — integrates nerve + muscle + vasculature → dexterity beyond prosthetic limits → lifetime QALY gains.
  2) VA-Centered Care Loop — DoD/VA data-sharing speeds recruitment + standardizes rehab protocols → earlier coverage decisions → earlier access for veterans.
  3) Platform Spillovers — vascularization/scaffold breakthroughs transfer to wound care & diabetic ulcers → broader public health returns.
• Rhetoric: Hook: "A limb is not a tool—it’s a life returned." | Analogy: "We’re not patching a tire; we’re rebuilding the wheel." | Crystallization: "Restore function, restore futures."

NEGATION
• Contentions:
  1) GMP Bottleneck — autologous cell therapy needs Class B/A cleanrooms & high-wage techs → capacity, not discovery, is the choke point → trials stall and waits swell.
  2) Consent Drift & Re-ID — iPSC lines + omics enable reidentification → withdrawals fracture datasets → pivotal phases delay.
  3) Coverage Cliff — without CMS/VA codes and DRG fit, approval ≠ access → headlines without care.
• Rhetoric: Hook: "A cure you can’t manufacture is a promise you can’t keep." | Analogy: "Tracks with no steel." | Crystallization: "If access is zero, impact is zero."
"""

def build_argument_prompt(
    bill: str,
    minutes: int = 2,
    style: str = "nationals",
    return_qx: bool = True,
    novelty: str = "standard",
    custom_instructions: str | None = None,
):
    user = f"""Bill:
{bill}

Please produce BOTH sides in the schema, using {minutes}:00 speech density. Style preset: {style}. Return cross-ex questions: {return_qx}.
Always include ANALOGY VARIATIONS (5 for AFF, 5 for NEG).
Replace any banned phrases with fresher wording: {", ".join(BANLIST)}.
"""

    if (novelty or "standard").lower() in {"high", "wild"}:
        user += f"""

CREATIVE MODE: {novelty.upper()}
Follow this pipeline silently (do NOT print steps):
1) List 8–12 expected/common arguments for both sides as one-liners. Do not use these in the final.
2) Using the general taxonomy and the biomedical one below, brainstorm 12–18 unconventional candidates across distinct buckets. Avoid clichés.
3) Score each: novelty (0–10) and plausibility (0–10). Keep only items with novelty ≥ 7 and plausibility ≥ 7. Sort by total.
4) From the top 3 per side, write full contentions (Claim → Mechanism → Impact → "what this means"). Distinct mechanisms only.
5) Rhetoric: Hook, sharp Analogy, Crystallization line per side matching the chosen angles.
6) ANALOGY VARIATIONS: 5 extra one-liners for AFF and 5 for NEG tied to the chosen angles.
7) Hide the brainstorming and scores. Return only the final package.

General Taxonomy:
{NOVELTY_TAXONOMY}

Biomedical Taxonomy:
{BIOMED_TAXONOMY}
"""
    if custom_instructions:
        user += f"\nADDITIONAL INSTRUCTIONS:\n{custom_instructions.strip()}"

    return [
        {"role": "system", "content": SYSTEM_COACH},
        {"role": "user", "content": FEW_SHOT_EXAMPLE.strip()},
        {"role": "user", "content": FEW_SHOT_BIOMED.strip()},
        {"role": "user", "content": user.strip()},
    ]

# ===== Post-generation polisher =====
POLISH_SYSTEM = """
You are a debate writing coach and copy editor. Polish the arguments to read like a Nationals final.
Rules:
- Keep all claims and logic intact; do not invent facts.
- Enforce structure per contention: Claim → Mechanism (2–3 steps) → Impact → "what this means".
- Tighten language; 10–22 words/sentence average; vary cadence.
- Strengthen signposting; add "First/Second/Third" where a new contention begins.
- Add explicit Weighing (probability • timeframe • irreversibility/distribution) if missing.
- Replace banlisted clichés with domain-grounded phrasing: {banlist}.
- Ensure analogies map directly to the mechanism (no "hope" metaphors).
"""

def build_polish_prompt(raw_text: str, style: str = "razor", custom_instructions: str | None = None):
    instr = ""
    if custom_instructions:
        instr = f"\nAlso honor these additional instructions during polishing:\n{custom_instructions.strip()}\n"
    user = f"""Rewrite the following for clarity, cadence, and judge-facing polish while preserving substance:
{instr}
=== DRAFT START ===
{raw_text.strip()}
=== DRAFT END ===

Return the same sections in the same order. Do not add new sections. Style preset: {style}.
"""
    return [
        {"role": "system", "content": POLISH_SYSTEM.format(banlist=", ".join(BANLIST))},
        {"role": "user", "content": user},
    ]

# ===== PO assistant (needed by your main.py import) =====
def build_po_prompt(text: str):
    sys = "You are a Presiding Officer assistant. From PO-style text, output a JSON of actions: recognitions (who), open/close question blocks, time notices, motions, seating/order."
    user = f"PO Text:\n{text}\nReturn JSON only."
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": user},
    ]

# ===== Open chat (for freeform customization/questions) =====
CHAT_SYSTEM = """
You are a debate writing assistant. You can: invent creative angles (novel but plausible), rewrite blocks with razor cadence,
add or remove specific constraints (jurisdiction, procedure, ethics), craft QX, or propose evidence prompts.
Follow the user's instructions faithfully. If a bill is provided, stay on-topic. Prefer concrete mechanisms to vague rhetoric.
Avoid clichés: {banlist}.
"""

def build_chat_prompt(message: str, bill: str | None, style: str = "razor", novelty: str = "standard"):
    style_note = _style_extra(style.lower().strip(), novelty)
    sys = CHAT_SYSTEM.format(banlist=", ".join(BANLIST)) + f"\nStyle kernel: {style_note}\n"
    context = f"Bill context:\n{bill}\n\n" if bill else ""
    user = f"""{context}User request:\n{message}\n"""
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": user}
    ]
