// The Newmarket season (owner, 10 Nov 2026): the second way to play. Ten races, two at each of five meetings through the
// season, on the Rowley Mile and the July Course. The same shape as royal-ascot.js, with three differences:
//  - the five "days" are the five meetings (Craven in April to the Future Champions in October), each with its own going;
//  - each race names its course ("rowley" or "july"), and courses[] says which course files it races on;
//  - a horse may run more than once in the season, once per meeting (runsPerMeeting), as long as it qualifies.
// The 36 races are the 8 Nov draft (game/js/meetings/newmarket-season.js, kept for reference), with "meeting" as "day".
window.MEETINGS = window.MEETINGS || {};
window.MEETINGS["newmarket"] = {
  id: "newmarket",
  name: "The Newmarket Season",
  short: "Newmarket",
  month: "April to October",
  year: 2026,
  // the five meetings, in season order: the game's race days
  days: ["The Craven Meeting", "The Guineas Festival", "The July Festival", "The Cambridgeshire Meeting", "The Future Champions Festival"],
  dayShort: ["Craven", "Guineas", "July", "Cambridgeshire", "Future Champions"],
  dayMonth: ["April", "May", "July", "September", "October"],
  dayTag: ["Apr", "May", "Jul", "Sep", "Oct"],
  racesPerDay: 2,
  nRaces: 10,
  minOpen: 1,                            // at least one of the heritage handicaps (the Bunbury Cup, the Cambridgeshire, the Cesarewitch)
  minPattern: 6,
  hcapMax: 110,
  runsPerMeeting: 1,                     // a horse may run at every meeting it qualifies for, once at each
  goings: ["Softer", "Good", "Good", "Quicker", "Quicker", "Quick", "Heavy"],   // drawn for each meeting
  // Each race's course: its files are assets/course/<file>.json, -view.json, -stalls.json, -standards.json.
  // straightUpTo: races up to this many furlongs are run on the straight; views: the race in the view file, by furlongs.
  courses: {
    rowley: { name: "Rowley Mile", file: "newmarket", straightUpTo: 10,
              views: { 5: "5f", 6: "6f", 7: "7f", 8: "1m", 9: "1m1f", 10: "1m2f", 12: "1m4f", 14: "1m6f", 16: "2m", 18: "2m2f", 20: "2m4f" } },
    july: { name: "July Course", file: "newmarket-july", straightUpTo: 8,
            views: { 5: "5f", 6: "6f", 7: "7f", 8: "1m", 10: "1m2f", 12: "1m4f", 13: "1m5f", 14: "1m6f", 16: "2m" } },
  },
  grades: {
    "Group 1": { cls: "g1", short: "G1", bands: [120, 115, 110, 105], prizes: [300000, 150000, 75000, 40000] },
    "Group 2": { cls: "g2", short: "G2", bands: [110, 105, 100, 95], prizes: [200000, 100000, 60000, 30000] },
    "Group 3": { cls: "g3", short: "G3", bands: [105, 100, 95, 90], prizes: [150000, 75000, 40000, 20000] },
    "Listed": { cls: "gl", short: "L", bands: [105, 100, 95, 90], prizes: [100000, 50000, 30000, 15000] },
    "Handicap": { cls: "gh", short: "Hcap", bands: [100, 95, 90, 85], prizes: [60000, 30000, 15000, 8000] },
  },
  // Runners, your horse included. The draft's bigger handicap fields are held to the 26 the starting stalls take.
  fieldSize: { twoYO: [12, 22], hcapStraight: [20, 26], hcapRound: [20, 26], groupStraight: [8, 16], groupRound: [8, 14], other: [10, 16] },
  pool: [
    // 1. The Craven Meeting (April), Rowley Mile: the Classic trials
    { id: "craven", day: 0, name: "Craven Stakes", grade: "Group 3", f: 8, dist: "1m", ages: [3, 3], ageLabel: "3YO colts", sex: "C", course: "rowley" },
    { id: "nell-gwyn", day: 0, name: "Nell Gwyn Stakes", grade: "Group 3", f: 7, dist: "7f", ages: [3, 3], ageLabel: "3YO fillies", sex: "F", course: "rowley" },
    { id: "abernant", day: 0, name: "Abernant Stakes", grade: "Group 3", f: 6, dist: "6f", ages: [3, 9], ageLabel: "3YO+", course: "rowley" },
    { id: "earl-of-sefton", day: 0, name: "Earl of Sefton Stakes", grade: "Group 3", f: 9, dist: "1m1f", ages: [4, 9], ageLabel: "4YO+", course: "rowley" },
    { id: "feilden", day: 0, name: "Feilden Stakes", grade: "Listed", f: 9, dist: "1m1f", ages: [3, 3], ageLabel: "3YO", course: "rowley" },
    // 2. The Guineas Festival (May), Rowley Mile
    { id: "2000-guineas", day: 1, name: "2000 Guineas Stakes", grade: "Group 1", f: 8, dist: "1m", ages: [3, 3], ageLabel: "3YO colts & fillies", course: "rowley", classic: true },
    { id: "1000-guineas", day: 1, name: "1000 Guineas Stakes", grade: "Group 1", f: 8, dist: "1m", ages: [3, 3], ageLabel: "3YO fillies", sex: "F", course: "rowley", classic: true },
    { id: "jockey-club", day: 1, name: "Jockey Club Stakes", grade: "Group 2", f: 12, dist: "1m4f", ages: [4, 9], ageLabel: "4YO+", course: "rowley" },
    { id: "palace-house", day: 1, name: "Palace House Stakes", grade: "Group 3", f: 5, dist: "5f", ages: [3, 9], ageLabel: "3YO+", course: "rowley" },
    // the owner's list has the Dahlia as Group 3; the real race has been a Group 2 since 2015 (kept as listed: say if not)
    { id: "dahlia", day: 1, name: "Dahlia Stakes", grade: "Group 3", f: 9, dist: "1m1f", ages: [4, 9], ageLabel: "4YO+ fillies & mares", sex: "F", course: "rowley" },
    { id: "king-charles-ii", day: 1, name: "King Charles II Stakes", grade: "Listed", f: 7, dist: "7f", ages: [3, 3], ageLabel: "3YO", course: "rowley" },
    // 3. The July Festival (July), July Course
    { id: "july-cup", day: 2, name: "The July Cup", grade: "Group 1", f: 6, dist: "6f", ages: [3, 9], ageLabel: "3YO+", course: "july" },
    { id: "falmouth", day: 2, name: "Falmouth Stakes", grade: "Group 1", f: 8, dist: "1m", ages: [3, 9], ageLabel: "3YO+ fillies & mares", sex: "F", course: "july" },
    { id: "princess-of-wales", day: 2, name: "Princess of Wales's Stakes", grade: "Group 2", f: 12, dist: "1m4f", ages: [3, 9], ageLabel: "3YO+", course: "july" },
    { id: "duchess-of-cambridge", day: 2, name: "Duchess of Cambridge Stakes", grade: "Group 2", f: 6, dist: "6f", ages: [2, 2], ageLabel: "2YO fillies", sex: "F", course: "july" },
    { id: "july-stakes", day: 2, name: "July Stakes", grade: "Group 2", f: 6, dist: "6f", ages: [2, 2], ageLabel: "2YO colts", sex: "C", course: "july" },
    { id: "superlative", day: 2, name: "Superlative Stakes", grade: "Group 2", f: 7, dist: "7f", ages: [2, 2], ageLabel: "2YO", course: "july" },
    { id: "bahrain-trophy", day: 2, name: "Bahrain Trophy", grade: "Group 3", f: 13, dist: "1m5f", ages: [3, 3], ageLabel: "3YO", course: "july" },
    { id: "sir-henry-cecil", day: 2, name: "Sir Henry Cecil Stakes", grade: "Listed", f: 8, dist: "1m", ages: [3, 3], ageLabel: "3YO", course: "july" },
    { id: "bunbury-cup", day: 2, name: "Bunbury Cup", grade: "Handicap", heritage: true, f: 7, dist: "7f", ages: [3, 9], ageLabel: "3YO+", course: "july" },
    // 4. The Cambridgeshire Meeting (September), Rowley Mile
    { id: "sun-chariot", day: 3, name: "Sun Chariot Stakes", grade: "Group 1", f: 8, dist: "1m", ages: [3, 9], ageLabel: "3YO+ fillies & mares", sex: "F", course: "rowley" },
    { id: "cheveley-park", day: 3, name: "Cheveley Park Stakes", grade: "Group 1", f: 6, dist: "6f", ages: [2, 2], ageLabel: "2YO fillies", sex: "F", course: "rowley" },
    { id: "middle-park", day: 3, name: "Middle Park Stakes", grade: "Group 1", f: 6, dist: "6f", ages: [2, 2], ageLabel: "2YO colts", sex: "C", course: "rowley" },
    { id: "royal-lodge", day: 3, name: "Royal Lodge Stakes", grade: "Group 2", f: 8, dist: "1m", ages: [2, 2], ageLabel: "2YO colts", sex: "C", course: "rowley" },
    { id: "rockfel", day: 3, name: "Rockfel Stakes", grade: "Group 2", f: 7, dist: "7f", ages: [2, 2], ageLabel: "2YO fillies", sex: "F", course: "rowley" },
    { id: "somerville-tattersall", day: 3, name: "Somerville Tattersall Stakes", grade: "Group 3", f: 7, dist: "7f", ages: [2, 2], ageLabel: "2YO colts", sex: "C", course: "rowley" },
    { id: "rose-bowl", day: 3, name: "Rose Bowl Stakes", grade: "Listed", f: 6, dist: "6f", ages: [2, 2], ageLabel: "2YO", course: "rowley" },
    { id: "cambridgeshire", day: 3, name: "The Cambridgeshire", grade: "Handicap", heritage: true, f: 9, dist: "1m1f", ages: [3, 9], ageLabel: "3YO+", course: "rowley" },
    // 5. The Future Champions Festival (October), Rowley Mile
    { id: "dewhurst", day: 4, name: "The Dewhurst Stakes", grade: "Group 1", f: 7, dist: "7f", ages: [2, 2], ageLabel: "2YO colts & fillies", course: "rowley" },
    { id: "fillies-mile", day: 4, name: "Fillies' Mile", grade: "Group 1", f: 8, dist: "1m", ages: [2, 2], ageLabel: "2YO fillies", sex: "F", course: "rowley" },
    { id: "challenge", day: 4, name: "Challenge Stakes", grade: "Group 2", f: 7, dist: "7f", ages: [3, 9], ageLabel: "3YO+", course: "rowley" },
    { id: "oh-so-sharp", day: 4, name: "Oh So Sharp Stakes", grade: "Group 3", f: 7, dist: "7f", ages: [2, 2], ageLabel: "2YO fillies", sex: "F", course: "rowley" },
    { id: "autumn", day: 4, name: "Autumn Stakes", grade: "Group 3", f: 8, dist: "1m", ages: [2, 2], ageLabel: "2YO", course: "rowley" },
    { id: "zetland", day: 4, name: "Zetland Stakes", grade: "Group 3", f: 10, dist: "1m2f", ages: [2, 2], ageLabel: "2YO", course: "rowley" },
    { id: "pride", day: 4, name: "Pride Stakes", grade: "Group 3", f: 10, dist: "1m2f", ages: [3, 9], ageLabel: "3YO+ fillies & mares", sex: "F", course: "rowley" },
    { id: "cesarewitch", day: 4, name: "The Cesarewitch", grade: "Handicap", heritage: true, f: 18, dist: "2m2f", ages: [3, 9], ageLabel: "3YO+", course: "rowley" },
  ],
  titles: [
    { min: 1000000, name: "Newmarket Champion", note: "Headquarters belongs to your colours. Hardly anyone gets here.", cls: "t5" },
    { min: 750000, name: "Leading Owner", note: "A season to frame and hang in the yard.", cls: "t4" },
    { min: 500000, name: "Classic Force", note: "Your colours were in every big finish on the Heath.", cls: "t3" },
    { min: 250000, name: "Newmarket Winner", note: "A proper season at Headquarters.", cls: "t2" },
    { min: 0, name: "Heath Walker", note: "Dawn on the gallops was lovely. Next year.", cls: "t1" }
  ],
  ladderTop: 1250000,
  // How the screens name things in this season
  words: {
    where: "Newmarket", whereLong: "the Newmarket season", venue: "the racecourse", gameTitle: "Newmarket",
    when: "April to October", whenRaces: "The season",
    programme: "The Newmarket programme",
    drawLine: "The Jockey Club has drawn your ten races for the Newmarket season. Go and see what you're aiming at.",
    drawText: "The programme for the Newmarket season is out: ten races at five meetings, two at each, drawn fresh for this season.",
    entriesLine: "Enter your horses at the Jockey Club. A horse can run at every meeting it qualifies for, once at each.",
    weekLine: "Five meetings, ten races, on the Rowley Mile and the July Course.",
    lockedStatus: "The racing starts in April, once your string is in training",
    lockedText: "Five meetings, ten races, on the Rowley Mile and the July Course, watched in 3D.",
    go: "Go to the races", back: "Back to the races", over: "The Newmarket season is over for this year",
    weekTitle: "The Newmarket season", weekRunning: "The season is under way",
    standingsAt: "The final standings for the season",
    titleFrom: "Your title from the Newmarket season", playedNoun: "Newmarket season", playedPlural: "YOUR NEWMARKET SEASONS",
    lede: "Your ten races in the Newmarket season, two at each of five meetings from April to October, on the Rowley Mile and the July Course: Classics, Group races, Listed races and the big heritage handicaps.",
    watchHere: "Watch a race to see it run on the Rowley Mile or the July Course in 3D",
    weekWord: "the racing", weekDone: "the season is run", weekHead: "THE RACING", bestWord: "season",
    goingWhen: "The going for each meeting is declared when you go to the races, after your entries are in.", goingCounts: "on the day", backToRacing: "Back to the races",
    coverPicture: "img/newmarket-cover.jpg",          // the cover shows the Rowley Mile, not the Ascot film
    cardBack: "NEWMARKET", dayWord: "meeting",
    entryRule: "One horse per race, and a horse can run at every meeting it qualifies for, once at each",
    film: null, still: "img/newmarket-still.jpg",
    filmCaption: "",
    coverKicker: "Newmarket · five meetings · one season",
    coverLede: "Build a stable in Newmarket, breed and buy your string, then race them through the Newmarket season, from the Craven in April to the Future Champions in October. Win enough and you're crowned <b>Newmarket Champion</b>.",
    coverRaces: ["The Newmarket season", "Ten races at five meetings, watched in 3D. A good horse can run at every meeting. Prize money is its own pot."],
    howRaces: "<b>The Newmarket season</b>: two races at each of five meetings on the Rowley Mile and the July Course. Watch each race in 3D or sim it.",
  },
};
