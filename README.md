# The World Today — 21 November 2026

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/Rhcuan69/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/Rhcuan69/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

A one-page newspaper front page for Saturday 21 November 2026, drawn
entirely in code: seven stories that were first reported that day, set
as a broadsheet-style page with a big masthead, a black date band, a
lead story, and six more stories in a two-by-three grid. Every letter,
rule, and little pictogram is plotted pixel by pixel — no photos, no
fonts, no image files are involved.

Bounty: https://make.fun/bounty/news-image-20261121

## The seven stories

1. **Poland seeks more NATO air defences** — Warsaw asks for more
   support after two Russian missiles and a drone came down; NATO calls
   it a grave violation.
2. **Nasdaq plunges 5.3% as Nvidia tumbles on SEC probe report** —
   S and P 500 falls 3.7% in seventh straight loss; Nvidia down about
   14% after Reuters report.
3. **Mexico captures 'El Chapo Isidro' cartel boss** — Fausto Isidro
   Meza Flores, one of the FBI's 10 most wanted, seized in Guasave,
   Sinaloa.
4. **Magnitude 6.8 quake strikes off Timor-Leste** — tremor 103 km
   northeast of Lospalos at 09:42 UTC; no tsunami threat, low risk of
   damage.
5. **UN talks agree to draft 'killer robot' rules** — 128 countries in
   Geneva agree to work toward rules for lethal autonomous weapons by
   2028.
6. **BepiColombo reaches Mercury orbit after eight years** —
   Europe-Japan twin orbiters enter orbit 18:24 UTC; only the second
   mission to orbit Mercury.
7. **Pill hailed as breakthrough for pancreatic cancer** —
   Daraxonrasib made tumours undetectable in one in 12 patients;
   nearly all tumours stopped growing.

## How it is made

`tools/render_news.py` is pure Python standard library. It keeps a
pixel buffer, draws the page with a hand-made 5-by-7 blocky letter set,
adds a small pictogram for each story (a shield, a falling chart, a
badge, a seismograph, a robot, a ringed planet, a capsule), and writes
the PNG itself with `zlib` — so the output is deterministic: run it
twice and you get identical bytes.

```sh
python3 tools/render_news.py   # writes news-21-nov-2026.png (1024x1024)
python3 main.py                # checks the PNG, copies it to entry.png
```

`main.py` validates the rendered file first (PNG magic bytes, IHDR
1024x1024, IEND trailer, size at most 1 MiB) and then copies it to
`$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output`).

## Referral

https://make.fun/r/nx2h6gdz
