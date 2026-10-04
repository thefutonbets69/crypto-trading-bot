# Streamlabs YouTube Stream Template — Setup

## Files
| File | Scene name in Streamlabs | What it shows |
|---|---|---|
| overlay-starting.html | Starting Soon | Full-screen title + countdown |
| overlay-live.html | Live | Transparent overlay: LIVE badge, clock, webcam frame, name bar, scrolling ticker |
| overlay-brb.html | Be Right Back | Full-screen BRB screen |
| overlay-ending.html | Ending | Full-screen "Thanks for watching" |
| overlay-mlb-gamecast.html | (add to Live scene) | **MLB gamecast**: score, inning, count, outs, runners, batter vs pitcher and plays. Preset for Braves vs Dodgers |
| overlay-playbyplay.html | (add to Live scene) | Live written play-by-play + score, updates automatically |

## 1. Personalize (2 min)
Open each `.html` file in Notepad (or any text editor) and edit the `CONFIG` block at the top:
channel name, title, socials, ticker text, colors, and countdown length. Keep the same values in all four files.
To preview, double-click a file to open it in your browser.

## 2. Build the scenes in Streamlabs Desktop
Keep the four files in one folder that won't move, such as `Documents/StreamOverlay`.

For each scene:
1. In the **Scenes** panel click **+**, then name the scene (for example "Starting Soon").
2. In the **Sources** panel click **+**, choose **Browser Source**, and name it.
3. Tick **Local file**, then browse to the matching `overlay-*.html`.
4. Set **Width 1920** and **Height 1080**, then click **Done**.

For the **Live** scene, add these extra sources and order them so the overlay stays on top:
- **Overlay (Browser Source)**: top of the list
- **Video Capture Device**: your webcam. Resize it to sit inside the cyan "WEBCAM" frame (bottom right).
- **Display Capture** or **Game Capture**: your screen or game, at the bottom of the list
- Optional: Streamlabs **Alert Box** and **Chat Box** widgets, from Sources **+**, then Widgets

Also add your microphone under **Settings → Audio** if it isn't already there.

## 3. MLB gamecast for Braves vs Dodgers (Live scene)
This uses MLB's official free live data, the same feed behind MLB Gameday. It's already set to follow the Braves vs the Dodgers.
It finds today's game by itself and updates every 10 seconds.

1. In your **Live** scene, click Sources **+**, choose **Browser Source**, tick **Local file**, and pick `overlay-mlb-gamecast.html`.
   Set **Width 480** and **Height 640**.
2. Drag it into the empty top-right area, under the clock and above the webcam frame. Keep it above your game or screen capture in the Sources list.
3. **Test it now:** double-click the file to open it in Chrome.
   - Before the game it shows "First pitch [time]". During the game it shows the live score, count, outs, runners and plays.
   - If it says "No game today", open the game on mlb.com/gameday. Copy the long number at the end of that URL into `gamePk: ""` in the file.
4. To position the box without a game on, set `demo: true` (shows a fake game), then set it back to `false`.

To follow a different team later, change `teamId` (Braves 144, Dodgers 119). Set `opponentId: 0` for any opponent.

### Backup: show the Oddspedia (or ESPN / MLB.com) gamecast page itself
1. Open the game's page on oddspedia.com in your browser and copy the URL.
2. In the Live scene, add a **Browser Source**. Leave **Local file** unticked and paste the URL. Set Width 1280 and Height 900.
3. Right-click the source, choose **Interact**, and close any cookie or ad pop-ups.
4. Hold **Alt** and drag the box edges to crop down to just the gamecast part.

Downsides: pop-ups and ads can reappear, and the page layout can change. Some sites don't allow rebroadcasting their content, so check their terms.
The `overlay-mlb-gamecast.html` box avoids all of these.

## 4. Live play-by-play feed for other sports (Live scene)
The feed reads live game data from ESPN's public scoreboard, which also powers espn.com. It updates every 10 seconds without you touching anything.

1. Open `overlay-playbyplay.html` in Notepad and set:
   - `league`: for example `football/nfl`, `basketball/nba`, `baseball/mlb` or `hockey/nhl`. The full list is in the file.
   - `team`: the abbreviation of the team to follow, like `KC`, `LAL` or `NYY`. The feed finds that team's game for today on its own.
     Leave it as `""` to follow the first live game.
   - `eventId` (optional): if it picks the wrong game, paste the game's number from its espn.com URL.
2. In your **Live** scene, click Sources **+**, choose **Browser Source**, tick **Local file**, and pick `overlay-playbyplay.html`.
   Set **Width 480** and **Height 560**.
3. Drag it into the empty top-right area, under the clock and above the webcam frame. Keep it above your game capture in the Sources list.
4. **Test before you go live:** open the file in Chrome during a game and check that plays appear.
   To position the box when no game is on, set `demo: true` (shows fake plays), then set it back to `false`.

Notes:
- Scoring plays are highlighted in pink. New plays slide in at the top. If the connection drops,
  the last plays stay on screen and a small "Reconnecting…" line appears.
- ESPN's feed is free but unofficial. It runs a few seconds behind TV and could change without notice.
- If the box stays on "Loading game…" during a live game, the feed can't reach ESPN from your PC. Let me know and I'll switch the data source.

## 5. Connect YouTube and go live
1. **One-time step:** live streaming must be enabled on your YouTube channel. Go to YouTube Studio → **Create → Go live**.
   The first time can take up to 24 hours to activate.
2. In Streamlabs, log in with YouTube, or go to **Settings → Stream** and connect your YouTube account.
3. Check **Settings → Output/Video**: 1920×1080, 30 or 60 fps. Around 6000 kbps works on most connections.
4. Click **Go Live** at the bottom right. Set the title, description, and visibility (try **Unlisted** for a test), then confirm.
5. Switch scenes during the stream: Starting Soon → Live → BRB (when needed) → Ending.
