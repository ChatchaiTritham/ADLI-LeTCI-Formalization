# Pre-registration — scorebook band-rule extension (P1)

Written: 2026-10-11T13:35Z (UTC), BEFORE any new scorebook was searched for, downloaded, or transcribed.
Known prior data at this time: 2008 Novel Connect (18 items, S10). These 18 items are the
*exploratory* set; all hypotheses below are confirmatory only on items from OTHER cases/teams.

## Unit, coding
- Unit = one Baldrige item scored by one team (consensus stage preferred; independent stage analysed
  separately if found) whose scorebook marks one scoring range per evaluation factor
  (A, D, L, I or Le, T, C, I) AND gives an item consensus percentage.
- Bands: 0..5 = 0-5%, 10-25%, 30-45%, 50-65%, 70-85%, 90-100% (same as S10; consensus band = band(pct)).
- No imputation. An item with any unreadable factor range or percentage is excluded and listed.

## Rules (predictions of the consensus band from the 4 factor bands, sorted b1<=b2<=b3<=b4)
gate = b1; lower median = b2; upper median = b3; any-median hit = b2<=c<=b3;
rounded mean = floor(mean+0.5); midrange = floor((b1+b4)/2+0.5); mode (ties -> lower; reported only).

## Hypotheses (confirmatory set = new items, excluding Novel Connect 2008)
- H1: any-median hit rate > rounded-mean exact hit rate. Primary test: on the DISCRIMINATING subset
  D = items where rounded mean is NOT in [b2,b3], count items where consensus is in [b2,b3] vs equals
  rounded mean; exact two-sided binomial (p0=0.5) on the discordant pairs (McNemar exact). alpha=0.05.
- H2: gate exact hit rate < any-median hit rate (McNemar exact on all items).
- H3 (descriptive): consensus band exceeds gate in a majority of items with a lone weakest factor.
- Uncertainty: Wilson 95% CIs per rule; cluster bootstrap (resample cases, 10,000 reps, seed 20261011)
  for the any-median minus rounded-mean difference.
- Note: since rounded mean of 4 integers always lies in [b1,b4] and very often in [b2,b3], D is
  expected to be small; if |D| < 10 the H1 test is declared underpowered and reported descriptively.

## Stopping
Use every eligible public scorebook found in one search session; no item selection by outcome.
