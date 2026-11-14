// =====================================================================================================================
// Thoroughbred: your accounts (owner, 11 Nov: "track how your money is being spent more in the game ... make it feel
// like there are thresholds"). Every payment and refund is booked here by kind; the money pill in the top bar opens the
// accounts. The thresholds are the prices that decide what you can still do: the stud fees and mares at the stud, and
// the cheapest lot in each Book at Tattersalls. Spend below one and the game says so as it happens.
// The budget and the prize money stay separate pots (owner, 11 Nov): money left over isn't scored.
// =====================================================================================================================
const LEDGER_KINDS = [
  { k: "mares", name: "Mares" },
  { k: "fees", name: "Stud fees" },
  { k: "yearlings", name: "Yearlings" },
];
// what each price lets you do (cheapest of its kind); "sales" ones matter all the way to the end of the sale
const THRESHOLDS = () => [
  { at: FEE_BY_STARS[5], what: "a 5★ nomination", place: "stud" },
  { at: FEE_BY_STARS[4], what: "a 4★ nomination", place: "stud" },
  { at: RESERVES[BOOKS[0].min], what: "a Book 1 yearling", place: "sales" },
  { at: PILES[0].price, what: "a Blue-blooded mare", place: "stud" },
  { at: FEE_BY_STARS[3], what: "a 3★ nomination", place: "stud" },
  { at: RESERVES[BOOKS[1].min], what: "a Book 2 yearling", place: "sales" },
  { at: PILES[1].price, what: "a Useful mare", place: "stud" },
  { at: RESERVES[BOOKS[2].min], what: "a Book 3 yearling", place: "sales" },
].sort((a, b) => b.at - a.at);
const ledgerOf = () => (S.ledger = S.ledger || { mares: 0, fees: 0, yearlings: 0, refunds: 0 });
// book a payment (amt > 0) or a refund (amt < 0) made just now; S.budget has already changed
function ledger(kind, amt) {
  if (!amt) return;
  const L = ledgerOf();
  if (amt < 0) L.refunds += -amt; else L[kind] = (L[kind] || 0) + amt;
  const before = S.budget + amt, now = S.budget;
  // the thresholds this payment took you under (those that still matter where you are now), the cheapest first
  const crossed = THRESHOLDS().filter(t => before >= t.at && now < t.at && (t.place === "sales" || S.step < 2)).reverse().slice(0, 3).map(t => t.what);
  const list = crossed.length > 1 ? crossed.slice(0, -1).join(", ") + " and " + crossed[crossed.length - 1] : crossed[0];
  if (crossed.length) setTimeout(() => toast(`Down to ${money(now)}: ${list} ${crossed.length > 1 ? "are" : "is"} out of reach now`), 2500);
}
function accountsHTML() {
  const L = ledgerOf(), pw = typeof held === "function" && held("powerhouse") ? POWERHOUSE[held("powerhouse").tier] : 0;
  const start = START_BUDGET + pw, spent = LEDGER_KINDS.reduce((a, x) => a + (L[x.k] || 0), 0) - (L.refunds || 0);
  const pct = v => Math.max(0, v / start * 100).toFixed(2) + "%";
  const bar = LEDGER_KINDS.map(x => L[x.k] ? `<i class="ac-${x.k}" style="width:${pct(L[x.k])}" title="${x.name} ${money(L[x.k])}"></i>` : "").join("")
    + `<i class="ac-left" style="width:${pct(S.budget)}" title="Left ${money(S.budget)}"></i>`;
  const row = (name, v, cls) => `<li class="${cls || ""}"><span>${name}</span><b>${v}</b></li>`;
  const can = THRESHOLDS().map(t => `<li class="${S.budget >= t.at ? "ok" : "no"}"><span>${S.budget >= t.at ? "✓" : "✕"} ${t.what.replace(/^an? /, "").replace(/^./, c => c.toUpperCase())}</span><b>${money(t.at)}</b></li>`).join("");
  return `<div class="ac-h"><b>YOUR ACCOUNTS</b><button class="tb-square" data-accounts="close" aria-label="Close">✕</button></div>
    <div class="ac-bar" aria-hidden="true">${bar}</div>
    <ul class="ac-rows">${row("Starting budget", money(START_BUDGET))}${pw ? row("Powerhouse", "+" + money(pw), "in") : ""}
      ${LEDGER_KINDS.map(x => row(x.name, L[x.k] ? "−" + money(L[x.k]) : "–", "k-" + x.k)).join("")}
      ${L.refunds ? row("Sent back", "+" + money(L.refunds), "in") : ""}
      ${row("Left to spend", money(S.budget), "tot")}</ul>
    <p class="ac-sub">What it still buys</p><ul class="ac-can">${can}</ul>
    <p class="ac-note">Money left at the end isn't prize money: the two are separate pots. ${spent > 0 ? `You've spent ${Math.round(spent / start * 100)}% so far.` : ""}</p>`;
}
function toggleAccounts(force) {
  let el = document.getElementById("acct");
  if (el && force !== true) { el.remove(); return; }
  if (!el) { el = document.createElement("div"); el.id = "acct"; el.className = "acct"; el.setAttribute("role", "dialog"); el.setAttribute("aria-label", "Your accounts"); document.body.appendChild(el); }
  el.innerHTML = accountsHTML();
}
// keep an open account up to date, and close it with a tap elsewhere
const refreshAccounts = () => { if (document.getElementById("acct")) toggleAccounts(true); };
document.addEventListener("click", e => { const el = document.getElementById("acct"); if (el && !el.contains(e.target) && !e.target.closest("[data-accounts]")) el.remove(); }, true);
