# Compatibility and page performance (local)

Target `http://localhost:8000` · host Darwin 24.5.0 (arm64) · run 2026-10-30 15:19 EAT

Browsers: chromium 156.0.8078.4, firefox 157.0, webkit 27.2

| Engine | Size | Profile | Pages OK | Median ready (ms) | Slowest (ms) | JS errors | Sideways overflow |
|---|---|---|---|---|---|---|---|
| chromium | phone | normal | 8/8 | 62 | 157 | 0 | 0 |
| chromium | tablet | normal | 8/8 | 55 | 75 | 0 | 0 |
| chromium | desktop | normal | 8/8 | 54 | 74 | 0 | 0 |
| firefox | phone | normal | 8/8 | 108 | 230 | 0 | 0 |
| firefox | tablet | normal | 8/8 | 105 | 208 | 0 | 0 |
| firefox | desktop | normal | 8/8 | 106 | 198 | 0 | 0 |
| webkit | phone | normal | 8/8 | 62 | 202 | 0 | 0 |
| webkit | tablet | normal | 8/8 | 58 | 124 | 0 | 0 |
| webkit | desktop | normal | 8/8 | 58 | 97 | 0 | 0 |
| chromium | phone | low-end (4x CPU, slow 3G) | 8/8 | 555 | 2667 | 0 | 0 |

Problems found: 0
