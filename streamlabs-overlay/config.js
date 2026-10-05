/*
 * Live Betting Overlay — configuration
 * Edit the values below, save, then right-click the Browser Source in
 * Streamlabs and choose "Refresh" to apply changes.
 */
window.OVERLAY_CONFIG = {
  channel: {
    name: "FUTON BETS",
    handle: "@thefutonbets69",
    initials: "FB",
  },

  // Brand colors
  theme: {
    accent: "#00E676",   // primary (wins, highlights)
    accent2: "#FFC400",  // secondary (odds, pending)
    danger: "#FF3D57",   // losses, LIVE badge
  },

  // Scoreboard (set show: false to hide)
  game: {
    show: true,
    league: "NFL",
    away: { name: "KC", score: 17 },
    home: { name: "BUF", score: 14 },
    status: "Q3 · 8:42",
  },

  // Bets — status: "pending" | "won" | "lost" | "push"
  // odds are American (e.g. -110, +150). stake in units.
  bets: [
    { pick: "Chiefs -2.5",       market: "Spread",     odds: -110, stake: 2,   status: "pending" },
    { pick: "Over 47.5",         market: "Total",      odds: -105, stake: 1.5, status: "pending" },
    { pick: "Kelce Anytime TD",  market: "Player Prop", odds: +120, stake: 1,  status: "won" },
    { pick: "Bills ML",          market: "1st Half",   odds: +105, stake: 1,   status: "lost" },
  ],

  bankroll: {
    unitSize: 25,        // $ per unit
    startingUnits: 100,
    currency: "$",
  },

  // Scrolling odds ticker
  ticker: [
    "NFL · KC -2.5 (-110) @ BUF · O/U 47.5",
    "NFL · PHI -6 (-112) vs NYG · O/U 42.5",
    "NBA · BOS -4.5 (-110) @ MIL · O/U 226",
    "NHL · EDM ML -135 vs VAN",
    "MLB · LAD -1.5 (+120) @ SD",
  ],

  // Like / Subscribe / Share call-to-action
  cta: {
    showEverySeconds: 90,   // how often the CTA banner appears
    visibleSeconds: 12,     // how long it stays on screen
  },

  disclaimer: "21+ · Entertainment only, not financial advice · Gamble responsibly · 1-800-GAMBLER",
};
