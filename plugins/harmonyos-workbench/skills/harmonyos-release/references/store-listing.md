# AppGallery store listing gate

Load this reference when preparing an AppGallery candidate, a listing revision, or a store asset. It is a preflight contract, not authority to upload or submit.

## Listing record

Keep the source copy in a project-approved private/release directory; do not commit real test credentials, personal data, or unreviewed legal text. The audit only records field-presence facts, not the text or URLs.

```json
{
  "locales": {
    "zh-CN": {
      "appName": "…",
      "oneLineIntroduction": "…",
      "introduction": "…",
      "privacyStatementUrl": "https://example.com/privacy",
      "privacyStatementVersion": "2026-08-12",
      "privacyStatementReviewedAt": "2026-08-12",
      "screenshots": ["store/zh-CN/01.png"]
    }
  }
}
```

Every locale must state the product truthfully, match the released feature set and permission/data behavior, and point to a public, reviewed HTTPS privacy statement. Write the one-line introduction around the primary user value and use the full introduction for actual features and material limits; do not add roadmap promises or unsupported capability claims. A URL-shaped string is only configuration evidence; validate live availability and legal/product review separately at handoff. Generated privacy copy is a `needs_review` draft, never a legal conclusion.

## Icon baseline

For the current Workbench AppGallery baseline, provide one source icon that is exactly **1024×1024**, PNG, no larger than **3 MiB**, with neither an alpha channel nor transparency chunk. Do not bake the destination's rounded mask into the source icon. The audit can prove PNG structure and absence of alpha; a reviewer still checks that the visual has no pre-rounded/squircle treatment, is legible at small size, matches the in-app identity, and has the necessary rights.

If an icon is generated, treat it as a draft: retain creation provenance and rights basis, inspect it visually, export the final opaque PNG, then run the audit. Do not use a generated asset as proof of trademark or copyright ownership.

## Candidate command

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py listing-audit \
  --project /path/to/project \
  --icon /private/store/app-icon.png \
  --listing docs/release/store-listing.json \
  --evidence artifacts/harmonyos-workbench/release/listing.json
```

Re-check the exact AGC console requirements for the target region and app form immediately before submission. The console and review policies, not this baseline, are the final authority.
