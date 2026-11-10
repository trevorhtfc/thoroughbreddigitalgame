// DRAFT (8 Nov 2026), not loaded by the game yet: a Newmarket season, the owner's "key moments of the full season".
// The same shape as royal-ascot.js, with one difference: instead of one week drawn at random, five meetings from April to
// October, every race on a fixed list, and the same horse may run at more than one meeting as long as it qualifies
// (owner, 8 Nov). Open questions for the owner are marked QUESTION.
//
// Each race: id; meeting (index into 'meetings'); name; grade; f (furlongs) and dist; ages [min, max] (9 = and older);
// ageLabel; sex (F fillies/mares only, C colts only; none = open); course ("rowley" or "july"). Grades as Royal Ascot's;
// the two heritage handicaps and the Cesarewitch are 'Handicap' with heritage: true.
window.MEETINGS = window.MEETINGS || {};
window.MEETINGS["newmarket-season"] = {
  id: "newmarket-season",
  name: "The Newmarket Season",
  short: "Newmarket",
  year: 2026,
  status: "DRAFT",
  // Two courses (owner, 8 Nov: "add the July course", much leafier): each meeting is at one of them. Course files:
  // courses/<file>-draft.json, <file>-stalls.json, <file>-standards.json.
  courses: {
    rowley: { name: "Rowley Mile", file: "newmarket", straightUpTo: 10,
              starts: { 5: "5f", 6: "6f", 7: "7f", 8: "1m", 9: "1m1f", 10: "1m2f", 12: "1m4f", 14: "1m6f", 16: "2m", 18: "2m2f", 20: "2m4f" } },
    july: { name: "July Course", file: "newmarket-july", straightUpTo: 8,
            starts: { 5: "5f", 6: "6f", 7: "7f", 8: "1m", 10: "1m2f", 12: "1m4f", 13: "1m5f", 14: "1m6f", 16: "2m" } },
  },
  meetings: [
    { id: "craven", name: "The Craven Meeting", month: "April", course: "rowley", days: 3 },
    { id: "guineas", name: "The Guineas Festival", month: "May", course: "rowley", days: 3 },
    { id: "july", name: "The July Festival", month: "July", course: "july", days: 3 },
    { id: "cambridgeshire", name: "The Cambridgeshire Meeting", month: "September", course: "rowley", days: 3 },
    { id: "future-champions", name: "The Future Champions Festival", month: "October", course: "rowley", days: 2 },
  ],
  // QUESTION 2: how often may a horse run? Proposed: once per meeting, at as many meetings as it qualifies for (up to
  // five runs a season), so a good horse can go Craven → Guineas → July → autumn, as the real ones do.
  runsPerMeeting: 1,
  hcapMax: 110,
  // A horse's age is fixed for the whole season (all horses have their birthday on 1 January): a two-year-old runs in
  // the two-year-old races all season. So the string needs a mix: 14 of the 36 races are for two-year-olds.
  goings: ["Softer", "Good", "Good", "Quicker", "Quicker", "Quick", "Heavy"],
  grades: {
    "Group 1": { cls: "g1", short: "G1", bands: [120, 115, 110, 105], prizes: [300000, 150000, 75000, 40000] },
    "Group 2": { cls: "g2", short: "G2", bands: [110, 105, 100, 95], prizes: [200000, 100000, 60000, 30000] },
    "Group 3": { cls: "g3", short: "G3", bands: [105, 100, 95, 90], prizes: [150000, 75000, 40000, 20000] },
    "Listed": { cls: "gl", short: "L", bands: [105, 100, 95, 90], prizes: [100000, 50000, 30000, 15000] },
    "Handicap": { cls: "gh", short: "Hcap", bands: [100, 95, 90, 85], prizes: [60000, 30000, 15000, 8000] },
  },
  // Runners, your horse included: as Royal Ascot, but the Rowley Mile takes up to 30 (the July Course 28), so the big
  // handicaps (the Bunbury Cup, the Cambridgeshire, the Cesarewitch) get the big fields they have in real life.
  fieldSize: { twoYO: [12, 22], hcapStraight: [20, 28], hcapRound: [20, 28], groupStraight: [8, 16], groupRound: [8, 14], other: [10, 16] },
  pool: [
    // 1. The Craven Meeting (April), Rowley Mile: the Classic trials
    { id: "craven", meeting: 0, name: "Craven Stakes", grade: "Group 3", f: 8, dist: "1m", ages: [3, 3], ageLabel: "3YO colts", sex: "C", course: "rowley" },
    { id: "nell-gwyn", meeting: 0, name: "Nell Gwyn Stakes", grade: "Group 3", f: 7, dist: "7f", ages: [3, 3], ageLabel: "3YO fillies", sex: "F", course: "rowley" },
    { id: "abernant", meeting: 0, name: "Abernant Stakes", grade: "Group 3", f: 6, dist: "6f", ages: [3, 9], ageLabel: "3YO+", course: "rowley" },
    { id: "earl-of-sefton", meeting: 0, name: "Earl of Sefton Stakes", grade: "Group 3", f: 9, dist: "1m1f", ages: [4, 9], ageLabel: "4YO+", course: "rowley" },
    { id: "feilden", meeting: 0, name: "Feilden Stakes", grade: "Listed", f: 9, dist: "1m1f", ages: [3, 3], ageLabel: "3YO", course: "rowley" },
    // 2. The Guineas Festival (May), Rowley Mile
    { id: "2000-guineas", meeting: 1, name: "2000 Guineas Stakes", grade: "Group 1", f: 8, dist: "1m", ages: [3, 3], ageLabel: "3YO colts & fillies", course: "rowley", classic: true },
    { id: "1000-guineas", meeting: 1, name: "1000 Guineas Stakes", grade: "Group 1", f: 8, dist: "1m", ages: [3, 3], ageLabel: "3YO fillies", sex: "F", course: "rowley", classic: true },
    { id: "jockey-club", meeting: 1, name: "Jockey Club Stakes", grade: "Group 2", f: 12, dist: "1m4f", ages: [4, 9], ageLabel: "4YO+", course: "rowley" },
    { id: "palace-house", meeting: 1, name: "Palace House Stakes", grade: "Group 3", f: 5, dist: "5f", ages: [3, 9], ageLabel: "3YO+", course: "rowley" },
    // the owner's list has the Dahlia as Group 3; the real race has been a Group 2 since 2015 (kept as listed: say if not)
    { id: "dahlia", meeting: 1, name: "Dahlia Stakes", grade: "Group 3", f: 9, dist: "1m1f", ages: [4, 9], ageLabel: "4YO+ fillies & mares", sex: "F", course: "rowley" },
    { id: "king-charles-ii", meeting: 1, name: "King Charles II Stakes", grade: "Listed", f: 7, dist: "7f", ages: [3, 3], ageLabel: "3YO", course: "rowley" },
    // 3. The July Festival (July), July Course
    { id: "july-cup", meeting: 2, name: "The July Cup", grade: "Group 1", f: 6, dist: "6f", ages: [3, 9], ageLabel: "3YO+", course: "july" },
    { id: "falmouth", meeting: 2, name: "Falmouth Stakes", grade: "Group 1", f: 8, dist: "1m", ages: [3, 9], ageLabel: "3YO+ fillies & mares", sex: "F", course: "july" },
    { id: "princess-of-wales", meeting: 2, name: "Princess of Wales's Stakes", grade: "Group 2", f: 12, dist: "1m4f", ages: [3, 9], ageLabel: "3YO+", course: "july" },
    { id: "duchess-of-cambridge", meeting: 2, name: "Duchess of Cambridge Stakes", grade: "Group 2", f: 6, dist: "6f", ages: [2, 2], ageLabel: "2YO fillies", sex: "F", course: "july" },
    { id: "july-stakes", meeting: 2, name: "July Stakes", grade: "Group 2", f: 6, dist: "6f", ages: [2, 2], ageLabel: "2YO colts", sex: "C", course: "july" },
    { id: "superlative", meeting: 2, name: "Superlative Stakes", grade: "Group 2", f: 7, dist: "7f", ages: [2, 2], ageLabel: "2YO", course: "july" },
    { id: "bahrain-trophy", meeting: 2, name: "Bahrain Trophy", grade: "Group 3", f: 13, dist: "1m5f", ages: [3, 3], ageLabel: "3YO", course: "july" },
    { id: "sir-henry-cecil", meeting: 2, name: "Sir Henry Cecil Stakes", grade: "Listed", f: 8, dist: "1m", ages: [3, 3], ageLabel: "3YO", course: "july" },
    { id: "bunbury-cup", meeting: 2, name: "Bunbury Cup", grade: "Handicap", heritage: true, f: 7, dist: "7f", ages: [3, 9], ageLabel: "3YO+", course: "july" },
    // 4. The Cambridgeshire Meeting (September), Rowley Mile
    { id: "sun-chariot", meeting: 3, name: "Sun Chariot Stakes", grade: "Group 1", f: 8, dist: "1m", ages: [3, 9], ageLabel: "3YO+ fillies & mares", sex: "F", course: "rowley" },
    { id: "cheveley-park", meeting: 3, name: "Cheveley Park Stakes", grade: "Group 1", f: 6, dist: "6f", ages: [2, 2], ageLabel: "2YO fillies", sex: "F", course: "rowley" },
    { id: "middle-park", meeting: 3, name: "Middle Park Stakes", grade: "Group 1", f: 6, dist: "6f", ages: [2, 2], ageLabel: "2YO colts", sex: "C", course: "rowley" },
    { id: "royal-lodge", meeting: 3, name: "Royal Lodge Stakes", grade: "Group 2", f: 8, dist: "1m", ages: [2, 2], ageLabel: "2YO colts", sex: "C", course: "rowley" },
    { id: "rockfel", meeting: 3, name: "Rockfel Stakes", grade: "Group 2", f: 7, dist: "7f", ages: [2, 2], ageLabel: "2YO fillies", sex: "F", course: "rowley" },
    { id: "somerville-tattersall", meeting: 3, name: "Somerville Tattersall Stakes", grade: "Group 3", f: 7, dist: "7f", ages: [2, 2], ageLabel: "2YO colts", sex: "C", course: "rowley" },
    { id: "rose-bowl", meeting: 3, name: "Rose Bowl Stakes", grade: "Listed", f: 6, dist: "6f", ages: [2, 2], ageLabel: "2YO", course: "rowley" },
    { id: "cambridgeshire", meeting: 3, name: "The Cambridgeshire", grade: "Handicap", heritage: true, f: 9, dist: "1m1f", ages: [3, 9], ageLabel: "3YO+", course: "rowley" },
    // 5. The Future Champions Festival (October), Rowley Mile
    { id: "dewhurst", meeting: 4, name: "The Dewhurst Stakes", grade: "Group 1", f: 7, dist: "7f", ages: [2, 2], ageLabel: "2YO colts & fillies", course: "rowley" },
    { id: "fillies-mile", meeting: 4, name: "Fillies' Mile", grade: "Group 1", f: 8, dist: "1m", ages: [2, 2], ageLabel: "2YO fillies", sex: "F", course: "rowley" },
    { id: "challenge", meeting: 4, name: "Challenge Stakes", grade: "Group 2", f: 7, dist: "7f", ages: [3, 9], ageLabel: "3YO+", course: "rowley" },
    { id: "oh-so-sharp", meeting: 4, name: "Oh So Sharp Stakes", grade: "Group 3", f: 7, dist: "7f", ages: [2, 2], ageLabel: "2YO fillies", sex: "F", course: "rowley" },
    { id: "autumn", meeting: 4, name: "Autumn Stakes", grade: "Group 3", f: 8, dist: "1m", ages: [2, 2], ageLabel: "2YO", course: "rowley" },
    { id: "zetland", meeting: 4, name: "Zetland Stakes", grade: "Group 3", f: 10, dist: "1m2f", ages: [2, 2], ageLabel: "2YO", course: "rowley" },
    { id: "pride", meeting: 4, name: "Pride Stakes", grade: "Group 3", f: 10, dist: "1m2f", ages: [3, 9], ageLabel: "3YO+ fillies & mares", sex: "F", course: "rowley" },
    { id: "cesarewitch", meeting: 4, name: "The Cesarewitch", grade: "Handicap", heritage: true, f: 18, dist: "2m2f", ages: [3, 9], ageLabel: "3YO+", course: "rowley" },
  ],
  // QUESTION 3: the titles and the prize ladder for a whole season (Royal Ascot's top title starts at £1m for a week).
  titles: [],
};
