# Live Betting Overlay for Streamlabs (YouTube)

A transparent 1920×1080 overlay for live betting streams. It includes:

- A brand bug with your channel name, a pulsing **LIVE** badge and a clock
- A scoreboard
- A **live bet slip** showing odds, stake, to-win amount and PENDING/WON/LOST/PUSH status
- A bankroll panel that works out P/L, record, units at risk and ROI from your bets
- A scrolling odds ticker
- A **Like / Subscribe / Share** banner that slides in on a timer, plus an always-visible Like · Subscribe · Share strip in the ticker
- A responsible-gambling disclaimer bar

## Setup in Streamlabs Desktop

1. Keep `overlay.html` and `config.js` together in the same folder.
2. In your scene, click **+** → **Browser Source** → name it "Betting Overlay".
3. Tick **Local file** and pick `overlay.html`.
4. Set **Width 1920**, **Height 1080**. Leave the Custom CSS at its default (it keeps the background transparent).
5. Put the source **above** your gameplay/webcam layers.

## Updating during the stream

Edit `config.js` (bets, scores, ticker, colors, channel name), save it, then right-click the Browser Source → **Refresh**.
You don't need to do any math: P/L, record, at-risk and ROI are calculated from the `bets` list.

## Preview in a browser

Open `overlay.html?preview=1` to see it on a dark background (Streamlabs shows it transparent).
