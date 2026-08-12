# Visual identity and icon roles

Load this reference when designing an app icon, settings icon, feature icon, or visual-identity asset. Name the destination first; do not transfer export constraints from one role to another.

| Asset role | Owner / contract | Export rule |
| --- | --- | --- |
| System-facing app icon (store, launcher or platform identity) | `harmonyos-release` plus current platform rules | Keep a dedicated opaque source/export when the platform requires it; current AppGallery baseline is 1024×1024 PNG, ≤3 MiB, no alpha/transparency and no pre-rounded mask. |
| In-app settings or feature icon | `harmonyos-design` | May use transparent/vector assets or remove a background when that improves hierarchy, contrast and legibility. It must not inherit the store PNG rule by default. |
| Brand/VI illustration | `harmonyos-design` | Choose the format, background and crop for the actual surface; retain source/rights information and accessibility contrast. |

System-facing and in-app assets can share a glyph, palette and token family without sharing a file. Keep the master asset and named exports distinct. Verify the in-app icon at its actual size, dark/light surface, disabled/focus state and screen density. Do not add a white square merely because the store export is opaque, and do not pass a transparent UI export to a system-facing icon slot that forbids it.

For user-facing settings rows, pair an icon with a text label; never rely on color or a decorative glyph alone to convey a setting's state or action.
