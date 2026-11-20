# One image of the world's news — Friday 20 November 2026

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/xoman222-max/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/xoman222-max/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

Entry for make.fun's `news-image-20261120` bounty: sum up 20 November's
world news in one image. 50 stories, 7 regions, every one verified to have
happened or been first reported on Friday 20 November 2026.

## The image

`entry.png` (1024×1024, ~200 KB) is a front page drawn by code:

- Giant date header: **FRIDAY 20 NOVEMBER 2026 — 50 STORIES · 7 REGIONS**
- A UTC timeline of the day's six key moments
- 16 featured stories, each with a flat vector pictogram, a 1–2 sentence
  summary, a region/topic tag and a source label
- A world map with numbered pins for all 16 featured stories
- **ALSO ON FRIDAY 20 NOVEMBER**: the other 34 stories, one line each
- **DATE CHECK**: the tempting wrong-date stories deliberately left out
  (the Shenzhen trilateral summit, the ICJ Myanmar verdict, the Anthropic
  debut, the Pete Rose pardon, the Somalia expulsion, the COP31 draft and
  more — all 19 November), plus two items not yet happened
- Footer: date-fidelity statement and sources

All pictograms are original drawings made by the renderer. No photographs.

## Date verification

Every story was checked against its first-report date in live news
searches on 20 November 2026. This mattered: most of the day's
headline-grabbing items — the Trump–Xi–Putin summit, the ICJ genocide
verdict, Anthropic's stock debut, the Pete Rose pardon, the Somalia
expulsion, Meta's net-zero rethink, the deep-sea mining auction, the
California Nvidia probe — happened on Thursday 19 November, so they
were excluded from the 50 and named in the DATE CHECK bar instead.

## Reproduce

```sh
python3 renderer.py stories.json entry.png   # needs Pillow, locally only
python3 renderer.py stories.json /tmp/check.png
sha256sum entry.png /tmp/check.png           # identical: deterministic
```

`main.py` is pure standard library: it only copies `entry.png` to
`/output/entry.png`, so it runs in the judging container with no
dependencies.

## Sources

AFP, AP, BBC, Reuters, UN News, Japan Times, Bangkok Post, The Times,
Save the Children, Scoop.

## Licence

MIT — see `LICENSE`.
