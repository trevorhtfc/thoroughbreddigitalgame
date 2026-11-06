// A race meeting, as data. The game is played at one meeting at a time; every other meeting (another course, another
// week) is another file of this shape, registered the same way. Nothing in here is Ascot-specific code: the course is
// named, and its races are looked up in that course's view file (assets/course/<course>-view.json -> races).
window.MEETINGS = window.MEETINGS || {};
window.MEETINGS["royal-ascot"] = {
  id: "royal-ascot",
  name: "Royal Ascot",
  short: "Ascot",
  course: "ascot",                       // assets/course/ascot.json, ascot-view.json, ascot-stalls.json, ascot-standards.json
  month: "June",
  year: 2026,
  days: ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
  racesPerDay: 2,
  nRaces: 10,
  minOpen: 3,                            // at least three handicaps or conditions races on every card
  minPattern: 3,                         // and at least three pattern races
  hcapMax: 110,                          // handicaps are for horses rated 110 or less
  goings: ["Softer", "Good", "Good", "Quicker", "Quicker", "Quick", "Heavy"],   // drawn for each day
  // The four rating bands of each grade (the board game's decks): the field is drawn across them, and the lowest is the
  // rating a horse needs to run at all. Prizes for 1st to 4th.
  grades: {
  "Group 1": { cls: "g1", short: "G1", bands: [120, 115, 110, 105], prizes: [300000, 150000, 75000, 40000] },
  "Group 2": { cls: "g2", short: "G2", bands: [110, 105, 100, 95], prizes: [200000, 100000, 60000, 30000] },
  "Group 3": { cls: "g3", short: "G3", bands: [105, 100, 95, 90], prizes: [150000, 75000, 40000, 20000] },
  "Listed": { cls: "gl", short: "L", bands: [105, 100, 95, 90], prizes: [100000, 50000, 30000, 15000] },
  // Handicaps and the Queen Alexandra: lower bands and smaller prizes, with bigger, more even fields
  "Handicap": { cls: "gh", short: "Hcap", bands: [100, 95, 90, 85], prizes: [60000, 30000, 15000, 8000] },
  "Conditions": { cls: "gc", short: "Cond", bands: [100, 95, 90, 85], prizes: [60000, 30000, 15000, 8000] }
},
  // Runners in each kind of race, your horse included (owner, 5 Nov): 2-year-old races 14-26; handicaps 18-26 on the
  // straight course, 18-20 round the bend; Group races 10-18 on the straight, 8-14 round the bend; Listed and
  // Conditions races 10-16. The round mile (starting in the chute) counts as round the bend.
  fieldSize: { twoYO: [14, 26], hcapStraight: [18, 26], hcapRound: [18, 20], groupStraight: [10, 18], groupRound: [8, 14], other: [10, 16] },
  straightUpTo: 8,                       // races up to a mile are run on the straight course unless marked round
  // The race in the course's view file, by furlongs ("8r": the round mile)
  viewRaces: { 5: "5f", 6: "6f", 7: "7f", 8: "mile", "8r": "roundmile", 10: "1m2f", 12: "1m4f", 14: "1m6f", 16: "long", 20: "2m4f", 22: "2m6f" },
  // ages: [min, max]; sex: F fillies only, C colts only; f: furlongs; round: run round the bend
  // Royal Ascot 2026, day by day in race order (Tue-Sat). Each card draws two races a day.
  pool: [
  { id: "queen-anne", day: 0, name: "Queen Anne Stakes", grade: "Group 1", f: 8, dist: "1m", ages: [4, 9], ageLabel: "4YO+" },
  { id: "coventry", day: 0, name: "Coventry Stakes", grade: "Group 2", f: 6, dist: "6f", ages: [2, 2], ageLabel: "2YO" },
  { id: "king-charles", day: 0, name: "King Charles III Stakes", grade: "Group 1", f: 5, dist: "5f", ages: [3, 9], ageLabel: "3YO+" },
  { id: "st-james", day: 0, name: "St James's Palace Stakes", grade: "Group 1", f: 8, dist: "1m", ages: [3, 3], ageLabel: "3YO colts", sex: "C", round: true },
  { id: "ascot-stakes", day: 0, name: "Ascot Stakes", grade: "Handicap", f: 20, dist: "2m4f", ages: [4, 9], ageLabel: "4YO+" },
  { id: "wolferton", day: 0, name: "Wolferton Stakes", grade: "Listed", f: 10, dist: "1m2f", ages: [4, 9], ageLabel: "4YO+" },
  { id: "copper-horse", day: 0, name: "Copper Horse Stakes", grade: "Handicap", f: 14, dist: "1m6f", ages: [4, 9], ageLabel: "4YO+" },
  { id: "queen-mary", day: 1, name: "Queen Mary Stakes", grade: "Group 2", f: 5, dist: "5f", ages: [2, 2], ageLabel: "2YO fillies", sex: "F" },
  { id: "queens-vase", day: 1, name: "Queen's Vase", grade: "Group 2", f: 14, dist: "1m6f", ages: [3, 3], ageLabel: "3YO" },
  { id: "duke-of-cambridge", day: 1, name: "Duke of Cambridge Stakes", grade: "Group 2", f: 8, dist: "1m", ages: [4, 9], ageLabel: "4YO+ fillies & mares", sex: "F" },
  { id: "prince-of-wales", day: 1, name: "Prince of Wales's Stakes", grade: "Group 1", f: 10, dist: "1m2f", ages: [4, 9], ageLabel: "4YO+" },
  { id: "royal-hunt-cup", day: 1, name: "Royal Hunt Cup", grade: "Handicap", f: 8, dist: "1m", ages: [3, 9], ageLabel: "3YO+" },
  { id: "kensington-palace", day: 1, name: "Kensington Palace Stakes", grade: "Handicap", f: 8, dist: "1m", ages: [4, 9], ageLabel: "4YO+ fillies & mares", sex: "F", round: true },
  { id: "windsor-castle", day: 1, name: "Windsor Castle Stakes", grade: "Listed", f: 6, dist: "6f", ages: [2, 2], ageLabel: "2YO" },
  { id: "chesham", day: 2, name: "Chesham Stakes", grade: "Listed", f: 7, dist: "7f", ages: [2, 2], ageLabel: "2YO" },
  { id: "king-george-v", day: 2, name: "King George V Stakes", grade: "Handicap", f: 12, dist: "1m4f", ages: [3, 3], ageLabel: "3YO" },
  { id: "ribblesdale", day: 2, name: "Ribblesdale Stakes", grade: "Group 2", f: 12, dist: "1m4f", ages: [3, 3], ageLabel: "3YO fillies", sex: "F" },
  { id: "gold-cup", day: 2, name: "Gold Cup", grade: "Group 1", f: 20, dist: "2m4f", ages: [4, 9], ageLabel: "4YO+" },
  { id: "britannia", day: 2, name: "Britannia Stakes", grade: "Handicap", f: 8, dist: "1m", ages: [3, 3], ageLabel: "3YO colts", sex: "C" },
  { id: "hampton-court", day: 2, name: "Hampton Court Stakes", grade: "Group 3", f: 10, dist: "1m2f", ages: [3, 3], ageLabel: "3YO" },
  { id: "buckingham-palace", day: 2, name: "Buckingham Palace Stakes", grade: "Handicap", f: 7, dist: "7f", ages: [3, 9], ageLabel: "3YO+" },
  { id: "albany", day: 3, name: "Albany Stakes", grade: "Group 3", f: 6, dist: "6f", ages: [2, 2], ageLabel: "2YO fillies", sex: "F" },
  { id: "commonwealth", day: 3, name: "Commonwealth Cup", grade: "Group 1", f: 6, dist: "6f", ages: [3, 3], ageLabel: "3YO" },
  { id: "duke-of-edinburgh", day: 3, name: "Duke of Edinburgh Stakes", grade: "Handicap", f: 12, dist: "1m4f", ages: [3, 9], ageLabel: "3YO+" },
  { id: "coronation", day: 3, name: "Coronation Stakes", grade: "Group 1", f: 8, dist: "1m", ages: [3, 3], ageLabel: "3YO fillies", sex: "F", round: true },
  { id: "sandringham", day: 3, name: "Sandringham Stakes", grade: "Handicap", f: 8, dist: "1m", ages: [3, 3], ageLabel: "3YO fillies", sex: "F", round: true },
  { id: "king-edward-vii", day: 3, name: "King Edward VII Stakes", grade: "Group 2", f: 12, dist: "1m4f", ages: [3, 3], ageLabel: "3YO colts", sex: "C" },
  { id: "holyroodhouse", day: 3, name: "Palace of Holyroodhouse Stakes", grade: "Handicap", f: 5, dist: "5f", ages: [3, 3], ageLabel: "3YO" },
  { id: "norfolk", day: 4, name: "Norfolk Stakes", grade: "Group 2", f: 5, dist: "5f", ages: [2, 2], ageLabel: "2YO" },
  { id: "hardwicke", day: 4, name: "Hardwicke Stakes", grade: "Group 2", f: 12, dist: "1m4f", ages: [4, 9], ageLabel: "4YO+" },
  { id: "qeii", day: 4, name: "Queen Elizabeth II Jubilee Stakes", grade: "Group 1", f: 6, dist: "6f", ages: [4, 9], ageLabel: "4YO+" },
  { id: "jersey", day: 4, name: "Jersey Stakes", grade: "Group 3", f: 7, dist: "7f", ages: [3, 3], ageLabel: "3YO" },
  { id: "wokingham", day: 4, name: "Wokingham Stakes", grade: "Handicap", f: 6, dist: "6f", ages: [3, 9], ageLabel: "3YO+" },
  { id: "golden-gates", day: 4, name: "Golden Gates Stakes", grade: "Handicap", f: 10, dist: "1m2f", ages: [3, 3], ageLabel: "3YO" },
  { id: "queen-alexandra", day: 4, name: "Queen Alexandra Stakes", grade: "Conditions", f: 22, dist: "2m6f", ages: [4, 9], ageLabel: "4YO+" }
],
  // The ambition: prize money earns a title
  titles: [
    { min: 1000000, name: "Royal Ascot Champion", note: "The meeting's top owner. Hardly anyone gets here.", cls: "t5" },
    { min: 750000, name: "Leading Owner", note: "A week to frame and hang in the yard.", cls: "t4" },
    { min: 500000, name: "Group Race Force", note: "Your colours were everywhere that mattered.", cls: "t3" },
    { min: 250000, name: "Royal Ascot Winner", note: "A proper week at the royal meeting.", cls: "t2" },
    { min: 0, name: "Paying Guest", note: "You enjoyed the champagne. Next year.", cls: "t1" }
  ],
  ladderTop: 1250000
};
