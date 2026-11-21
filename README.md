[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/Rhcuan69/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/Rhcuan69/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

# The World Today — 21 November 2026

Entry for make.fun bounty **news-image-20261121**: sum up 21 November 2026's
world news in one image — https://make.fun/bounty/news-image-20261121

`main.py` copies the pre-rendered front page `news-21-nov-2026.png`
(1024×1024, 21 KB) to `/output/entry.png`. Deterministic, no network,
Python stdlib only. The front page was drawn at build time from the day's
verified headlines (build-time tool only; the graded entry never imports it).
The renderer is pure stdlib too — its own PNG encoder and bitmap font, no
Pillow, no numpy.

## The seven stories

1. **Poland seeks more NATO air defences** — Warsaw asks for more support
   after two Russian missiles and a drone came down; NATO calls it a grave
   violation. (WW6RAG / OneTurn)
2. **Nasdaq plunges 5.3% as Nvidia tumbles on SEC probe report** — S&P 500
   falls 3.7% in its seventh straight loss; Nvidia down about 14% after a
   Reuters report. (WW6RAG)
3. **Mexico captures "El Chapo Isidro" cartel boss** — Fausto Isidro Meza
   Flores, one of the FBI's 10 most wanted, seized in Guasave, Sinaloa.
   (Kilambi News)
4. **Magnitude 6.8 quake strikes off Timor-Leste** — tremor 103 km northeast
   of Lospalos at 09:42 UTC; no tsunami threat, low risk of damage.
   (Kilambi News)
5. **UN talks agree to draft "killer robot" rules** — 128 countries in Geneva
   agree to work toward rules for lethal autonomous weapons by 2028.
   (The Augerton Digest)
6. **BepiColombo reaches Mercury orbit after eight years** — Europe-Japan twin
   orbiters enter orbit at 18:24 UTC; only the second mission to orbit
   Mercury. (EarthSky / USA Today)
7. **Pill hailed as breakthrough for pancreatic cancer** — daraxonrasib made
   tumours undetectable in one in 12 patients; nearly all tumours stopped
   growing. (OneTurn)

All seven were first reported on Saturday 21 November 2026, worded as
reported, without hype or invented facts.

Referral: https://make.fun/r/nx2h6gdz

## How to run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png (byte-identical on every run)
```

Re-render the image (pure stdlib, no dependencies):

```sh
python3 tools/render_news.py
```

## License

MIT — see [LICENSE](LICENSE).
