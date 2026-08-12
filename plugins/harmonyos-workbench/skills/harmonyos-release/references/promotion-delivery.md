# Promotion delivery profile

Load this reference only when a release also needs public promotion: Xiaohongshu note/carousel, a video script, a Remotion render, launch images, QR/link material, or similar campaign content. It adds a `promotion_campaign` delivery profile to `harmonyos-release`; it does not authorize posting, paid promotion, or claiming publication.

## Truth source and boundary

Anchor every public asset to one named candidate: app name, version name/code, bundle, artifact hash, verified feature list, known limitations, public install URL, and publication state. A feature in a mock, branch, or roadmap is not a public claim. Do not generate an install QR code until the destination URL is public and verified; otherwise label it as pending rather than inventing a link.

Keep promotion copy, generated imagery, media provenance, campaign links and unpublished metrics in a project-approved private delivery directory. Durable evidence records asset hashes, reviewed claims and approval state, never raw copy, private URLs, user data, tokens or analytics.

## Xiaohongshu image-note bundle

1. Define audience, one honest hook, one concrete payoff and the intended user action.
2. Write a searchable title, body, topic set, cover caption and top-comment/FAQ response. Refresh topics and platform constraints at publication time; do not retain stale trend rankings as facts.
3. Make a cover that answers “what is this and why care” at thumbnail size, then use a carousel where each page has one job: pain point → solution → proof/boundary → how to use → public link/install path.
4. Include a usable installation command or public address when available; screenshot/test it before calling it usable.
5. Render and inspect every image on a phone-size preview. Avoid fabricated metrics, fake urgency, prohibited incentives, unverified approval claims, and misleading before/after results.

The project must supply the current Xiaohongshu output profile (dimensions, count, file size and safe-title area) rather than hard-coding a potentially stale platform setting in the Skill.

## Video script and Remotion delivery

Use approved campaign facts to produce a timed script with: segment ID, start/end time, narration, on-screen copy, visual source, caption text, claim/evidence reference, and status. Narration, captions and on-screen copy must tell the same story; a visual only is not proof.

For a Remotion project:

1. Record the entry point, composition ID, target width/height/fps, duration, output path, dependency lockfile and render command in the private delivery record.
2. Keep state-derived animation deterministic: one source of timeline truth, no drifting hard-coded durations between voice, captions and scene transitions.
3. Treat voice as the primary track. Lower BGM before mixing, inspect speech intelligibility on device speakers, and document the reviewed mix rather than assuming a numeric gain suits every track.
4. Render with the pinned dependency set; inspect first/middle/last frames, caption timing, aspect ratio, audio sync, legibility and final file metadata.
5. Preserve a source-to-render map, asset/rights provenance and the release candidate reference. A successful render does not verify the external post or platform distribution.

Use image generation only for new visual drafts. For edits, include the real source image; do not create lookalike product screenshots or imply behavior that was not demonstrated.

## Version and publication discipline

Release material must carry a version plan: `versionName` is the human-facing label; `versionCode` is the monotonic package identity. Set the expected values and last published code explicitly during preflight; the tool can verify a match/increment but cannot discover store history safely.

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py release \
  --project /path/to/project \
  --expected-version-name 1.2.0 --expected-version-code 120 \
  --previous-version-code 119
```

Only use “available now”, a store QR code, or a release announcement after the corresponding public state is verified. Preparing images/video and rendering a file are reversible local work; publication is an explicit external action.
