# Compatibility and page performance (local)

Target `http://localhost:8000` · host Darwin 24.5.0 (arm64) · run 2026-10-31 12:46 EAT

Browsers: chromium 156.0.8078.4, firefox 157.0, webkit 27.2

| Engine | Size | Profile | Pages OK | Median ready (ms) | Slowest (ms) | JS errors | Sideways overflow |
|---|---|---|---|---|---|---|---|
| chromium | phone | normal | 8/8 | 70 | 140 | 0 | 0 |
| chromium | tablet | normal | 8/8 | 66 | 80 | 0 | 0 |
| chromium | desktop | normal | 8/8 | 61 | 76 | 0 | 0 |
| firefox | phone | normal | 8/8 | 111 | 187 | 0 | 0 |
| firefox | tablet | normal | 8/8 | 111 | 176 | 0 | 0 |
| firefox | desktop | normal | 8/8 | 110 | 168 | 0 | 0 |
| webkit | phone | normal | 8/8 | 73 | 142 | 0 | 0 |
| webkit | tablet | normal | 8/8 | 74 | 89 | 0 | 0 |
| webkit | desktop | normal | 8/8 | 72 | 86 | 0 | 0 |
| chromium | phone | low-end (4x CPU, slow 3G) | 8/8 | 720 | 3786 | 0 | 0 |

Problems found: 0
