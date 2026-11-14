/* How to play (owner, 14 Nov 2026: take the steps off the cover, "and move that to the next page as more of an
   instructions piece integrating the team cards etc as well").
   One page that walks through the season place by place, each step with its window onto the board (or the racecourse),
   the team cards shown where they come into play, and how you win. It opens by itself the first time a player starts
   a game (before making their colours), and any time from the cover's "How to play" button or Palace House.
   Its numbers come from the rules (START_BUDGET, OFFER_SIZE, TEAM_POINTS, JOCKEY_RIDES, TITLES), so it stays true. */
let HT = null;
const HT_SEEN = "tb-howto-seen";
const howToSeen = () => { try { return !!localStorage.getItem(HT_SEEN); } catch (e) { return true; } };
// Asked before a game starts: true if the page had to be shown first (it calls `again` when the player carries on)
function needHowTo(again) { if (howToSeen() || HT) return false; openHowTo({ then: again }); return true; }

function htSteps() {
  const teamOn = typeof TEAM_POINTS !== "undefined", rides = typeof JOCKEY_RIDES !== "undefined" ? JOCKEY_RIDES : [0, 3, 4, 5];
  const pts = teamOn ? TEAM_POINTS : 6, two = OFFER_SIZE === 2 ? "two" : OFFER_SIZE === 3 ? "three" : OFFER_SIZE;
  const cards = (role) => teamOn ? `<p class="ht-team ${ROLE_CLS[role]}"><img src="img/team/${role[0]}3.webp" alt=""><span><b>Your ${role.toLowerCase()}${role === "Jockey" ? "s" : ""}</b> ${HT_TEAM[role]}</span></p>` : "";
  return [
    { place: "jockey", when: CHAPTERS.draw.season, title: "The draw",
      text: `The Jockey Club draws your ten races for ${W.whereLong}: a mix of Group races, handicaps and races for 2-year-olds, different every season. This is what you are building a stable to win.` },
    teamOn && { place: "jockey", when: CHAPTERS.team.season, title: "Draft your team", team: true,
      text: `Before the stud opens, draw the people behind your stable from the Bronze, Silver and Gold decks. You have <b>${pts} points</b>: Gold costs 3, Silver 2 and Bronze 1, and you need at least one owner, one trainer and one jockey. Tap a deck and its top card is yours.` },
    { place: "stud", when: CHAPTERS.breed.season, title: "Breed at the National Stud",
      text: `You start with <b>${money(START_BUDGET)}</b>. Buy mares from the piles (${two} are turned over each time and you keep one), then send each to a stallion. A mare can be at most one star above her stallion; an outcross breeds best, the same family worst, and an unproven stallion may be a star better or worse than he looks.`,
      after: cards("Owner") },
    { place: "tatts", when: CHAPTERS.sales.season, title: "Buy at Tattersalls",
      text: `The yearlings out of the mares nobody bred are sold in three Books. Bid against five rival buyers: you see the pedigree, not the yearling, until it's yours. Once you leave the stud there's no going back.` },
    { place: "warren", when: CHAPTERS.gallops.season, title: "Train on Warren Hill",
      text: `Your string are 2-year-olds now. Your trainer's jobs get them ready: a step longer or shorter in trip, settling a keen horse, handling another going, a tune-up for a big race. Bring on any horse who needs it to 3 or 4.`,
      after: cards("Trainer") },
    { place: "jockey", when: CHAPTERS.entries.season, title: "Make your entries",
      text: `${W.entryRule}. Each step away from a horse's best trip costs 5 from its rating, and the going counts ${W.goingCounts}: up to +5 on ground it likes, down to −10 three steps off. Book your jockeys for the rides that suit them.`,
      after: cards("Jockey") },
    { place: "races", when: W.when, title: MEETING.id === "newmarket" ? "Race through the season" : "Race at Royal Ascot",
      text: `${MEETING.id === "newmarket" ? "Two races at each of five meetings on the Rowley Mile and the July Course" : "Ten races over five days, two a day"}. Watch each one in 3D or sim it. Rating, trip, going and pace decide a race, and a horse's running style meets the pace: front-runners suit a slow race, hold-up horses a fast one.` },
    { place: "palace", when: "Home", title: "Count the prize money",
      text: `Prize money is its own pot: what you spent doesn't count against it. It climbs a ladder of titles, from ${TITLES[TITLES.length - 1].name} to <b>${TITLES[0].name}</b> at ${money(TITLES[0].min)}, and your titles, best ${W.bestWord}s and winners hang in Palace House.` },
  ].filter(Boolean);
}
const HT_TEAM = {
  Owner: "helps at the stud and the sales: more money, more mares to choose from, a stallion of your own, an eye for a pedigree or a yearling.",
  Trainer: "does the jobs on Warren Hill. Some are specialists: a trip, 2-year-olds, late developers or a sire line.",
  Jockey: "ride the races you book them for: the Champion anywhere, the others at their trips, their style of race, big races or soft ground.",
};

function openHowTo(opts = {}) {
  if (HT) return;
  const steps = htSteps(), first = !!opts.then;
  HT = { then: opts.then || null };
  const box = document.createElement("div"); box.className = "ht"; box.id = "ht"; box.setAttribute("role", "dialog"); box.setAttribute("aria-modal", "true"); box.setAttribute("aria-labelledby", "htTitle");
  const teamFan = typeof TEAM_POINTS === "undefined" ? "" : `<div class="ht-fan" aria-hidden="true">${[["Owner", 3], ["Trainer", 2], ["Jockey", 1]].map(([r, t], k) =>
    `<figure class="ht-card t${t}" style="--k:${k - 1}"><img src="img/team/${r[0]}${t}.webp" alt=""><figcaption><b>${r}</b><span>${TIER_NAME[t]} · ${t} point${t === 1 ? "" : "s"}</span></figcaption></figure>`).join("")}</div>`;
  box.innerHTML = `<div class="ht-in">
      <header class="ht-head">
        <div><div class="ht-k">How to play · Thoroughbred ${esc2(W.gameTitle || "")}</div><h2 class="ht-t" id="htTitle">How the season goes</h2>
        <p class="ht-lede">One season, start to finish: draw your races, pick your team, breed and buy your string, train them and send them racing. The aim is simple: <b>win as much prize money as you can</b>.</p></div>
        ${first ? "" : `<button class="ht-x" id="htClose" type="button" aria-label="Close">&times;</button>`}
      </header>
      <ol class="ht-steps">${steps.map((s, i) => `<li class="ht-step ${s.team ? "is-team" : ""}">
          <div class="ht-pic ${s.team ? "team" : ""}" data-place="${s.place}">${s.team ? teamFan : ""}</div>
          <div class="ht-txt"><div class="ht-when"><span class="ht-n">${i + 1}</span>${esc2(SHEET_TITLE[s.place] || W.where)} · ${esc2(s.when)}</div>
            <h3>${s.title}</h3><p>${s.text}</p>${s.after || ""}</div></li>`).join("")}</ol>
      <section class="ht-two">
        <div><h3>Today's card</h3><p>The same ten races for everyone, changing at midnight. One go: your first finish goes on the leaderboard against every other stable. The mares, foals and sales are your own.</p></div>
        <div><h3>A random game</h3><p>A fresh season any time, as often as you like. Your best goes on the best-ever board.</p></div>
      </section>
      <footer class="ht-foot"><button class="tb-btn" id="htGo" type="button">${first ? (hasColours() ? "Start the season" : "On to your colours") : "Got it"} <span aria-hidden="true">›</span></button></footer>
    </div>`;
  document.body.appendChild(box); HT.box = box;
  // each step's window onto the board (the races: the racecourse still)
  requestAnimationFrame(() => box.querySelectorAll(".ht-pic:not(.team)").forEach(el => {
    const id = el.dataset.place;
    if (id === "races") { el.style.backgroundImage = `url(${W.still})`; el.style.backgroundSize = "cover"; el.style.backgroundPosition = "50% 35%"; return; }
    // a little wider than the place's own window, kept inside the board's left edge (Warren Hill sits right at it)
    const p = window.BOARD && BOARD.placeOf(id); if (!p || !p.pic) return;
    const w = p.pic[2] * 1.15; BOARD.paintPic(el, [Math.max(p.pic[0], w / 2 + 2), p.pic[1], w], 0.5);
  }));
  box.addEventListener("click", e => { const t = e.target.closest("button"); if (!t) return; if (t.id === "htGo" || t.id === "htClose") closeHowTo(t.id === "htGo"); });
  const go = box.querySelector("#htGo"); try { (box.querySelector("#htClose") || go).focus({ preventScroll: true }); } catch (e) {}
}
function closeHowTo(carryOn) {
  if (!HT) return; const then = HT.then;
  try { localStorage.setItem(HT_SEEN, String(Date.now())); } catch (e) {}
  HT.box.remove(); HT = null;
  if (carryOn && then) then();
}
addEventListener("keydown", e => { if (e.key === "Escape" && HT && !HT.then) closeHowTo(false); });
document.addEventListener("click", e => { const b = e.target.closest && e.target.closest("#menuHow, [data-howto]"); if (b) openHowTo(); });
