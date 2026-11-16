// The York season (owner, 16 Nov 2026): the third way to play, and the first course of the full game built from the real
// track (tools/course/york). Ten races, two on each of five days: the Dante Festival in May, then the four days of the
// Ebor Festival in August. One course, so the same shape as royal-ascot.js (course, straightUpTo, viewRaces). A horse
// runs once in the season, as at Royal Ascot.
// The races are York's real programme, simplified (sponsors' names left off). The Dante is shown as one day.
window.MEETINGS = window.MEETINGS || {};
window.MEETINGS["york"] = {
  id: "york",
  name: "The York Season",
  short: "York",
  course: "york",                        // assets/course/york.json, york-view.json, york-stalls.json, york-standards.json, york-scenery.json
  month: "May and August",
  year: 2026,
  days: ["The Dante Festival", "Ebor Wednesday", "Ebor Thursday", "Ebor Friday", "Ebor Saturday"],
  dayShort: ["Dante", "Wednesday", "Thursday", "Friday", "Saturday"],
  dayMonth: ["May", "August", "August", "August", "August"],
  dayTag: ["May", "Wed", "Thu", "Fri", "Sat"],
  racesPerDay: 2,
  nRaces: 10,
  minOpen: 2,
  minPattern: 4,
  // the race mix (js/rules.js MIX): York has three Group 1s in the season (the International, the Yorkshire Oaks and the
  // Nunthorpe), so at least two of them on a card, and at least two handicaps
  mix: { group1: 2, handicaps: 2 },
  cardMix: 3,
  hcapMax: 110,
  goings: ["Softer", "Good", "Good", "Quicker", "Quicker", "Quick", "Heavy"],
  // The going for each day, drawn afresh (the Dante is three months before the Ebor): the chances of Heavy, Softer, Good,
  // Quicker, Quick. May a touch softer; the Knavesmire in August usually rides quick.
  goingOdds: [[6, 14, 32, 30, 18], [3, 10, 28, 33, 26], [3, 10, 28, 33, 26], [3, 10, 28, 33, 26], [3, 10, 28, 33, 26]],
  grades: {
    "Group 1": { cls: "g1", short: "G1", bands: [120, 115, 110, 105], prizes: [300000, 150000, 75000, 40000] },
    "Group 2": { cls: "g2", short: "G2", bands: [110, 105, 100, 95], prizes: [200000, 100000, 60000, 30000] },
    "Group 3": { cls: "g3", short: "G3", bands: [105, 100, 95, 90], prizes: [150000, 75000, 40000, 20000] },
    "Listed": { cls: "gl", short: "L", bands: [105, 100, 95, 90], prizes: [100000, 50000, 30000, 15000] },
    "Handicap": { cls: "gh", short: "Hcap", bands: [100, 95, 90, 85], prizes: [60000, 30000, 15000, 8000] },
  },
  // Runners, your horse included. York's stalls take 22.
  fieldSize: { twoYO: [12, 20], hcapStraight: [18, 22], hcapRound: [16, 20], groupStraight: [8, 16], groupRound: [8, 14], other: [10, 16] },
  straightUpTo: 6,                       // 5f and 6f are run on the straight; 7f comes in from the chute and the rest round the bend
  // The race in the course's view file, by furlongs
  viewRaces: { 5: "5f", 6: "6f", 7: "7f", 8: "1m", 9: "1m1f", 10: "1m2f", 12: "1m4f", 14: "1m6f", 16: "2m" },
  pool: [
    // The Dante Festival (May)
    { id: "dante", day: 0, name: "Dante Stakes", grade: "Group 2", f: 10, dist: "1m2f", ages: [3, 3], ageLabel: "3YO" },
    { id: "musidora", day: 0, name: "Musidora Stakes", grade: "Group 3", f: 10, dist: "1m2f", ages: [3, 3], ageLabel: "3YO fillies", sex: "F" },
    { id: "duke-of-york", day: 0, name: "Duke of York Stakes", grade: "Group 2", f: 6, dist: "6f", ages: [3, 9], ageLabel: "3YO+" },
    { id: "middleton", day: 0, name: "Middleton Stakes", grade: "Group 2", f: 10, dist: "1m2f", ages: [4, 9], ageLabel: "4YO+ fillies & mares", sex: "F" },
    { id: "yorkshire-cup", day: 0, name: "Yorkshire Cup", grade: "Group 2", f: 14, dist: "1m6f", ages: [4, 9], ageLabel: "4YO+" },
    { id: "hambleton", day: 0, name: "Hambleton Handicap", grade: "Handicap", f: 8, dist: "1m", ages: [4, 9], ageLabel: "4YO+" },
    { id: "westow", day: 0, name: "Westow Stakes", grade: "Listed", f: 5, dist: "5f", ages: [3, 3], ageLabel: "3YO" },
    // The Ebor Festival (August): Wednesday
    { id: "international", day: 1, name: "Juddmonte International", grade: "Group 1", f: 10, dist: "1m2f", ages: [3, 9], ageLabel: "3YO+" },
    { id: "great-voltigeur", day: 1, name: "Great Voltigeur Stakes", grade: "Group 2", f: 12, dist: "1m4f", ages: [3, 3], ageLabel: "3YO colts", sex: "C" },
    { id: "acomb", day: 1, name: "Acomb Stakes", grade: "Group 3", f: 7, dist: "7f", ages: [2, 2], ageLabel: "2YO" },
    { id: "stayers-hcap", day: 1, name: "Stayers' Handicap", grade: "Handicap", f: 16, dist: "2m", ages: [4, 9], ageLabel: "4YO+" },
    // Thursday
    { id: "yorkshire-oaks", day: 2, name: "Yorkshire Oaks", grade: "Group 1", f: 12, dist: "1m4f", ages: [3, 9], ageLabel: "3YO+ fillies & mares", sex: "F" },
    { id: "lowther", day: 2, name: "Lowther Stakes", grade: "Group 2", f: 6, dist: "6f", ages: [2, 2], ageLabel: "2YO fillies", sex: "F" },
    { id: "galtres", day: 2, name: "Galtres Stakes", grade: "Listed", f: 12, dist: "1m4f", ages: [3, 9], ageLabel: "3YO+ fillies & mares", sex: "F" },
    { id: "knavesmire-hcap", day: 2, name: "Knavesmire Handicap", grade: "Handicap", f: 7, dist: "7f", ages: [3, 9], ageLabel: "3YO+" },
    // Friday
    { id: "nunthorpe", day: 3, name: "Nunthorpe Stakes", grade: "Group 1", f: 5, dist: "5f", ages: [2, 9], ageLabel: "2YO+" },
    { id: "gimcrack", day: 3, name: "Gimcrack Stakes", grade: "Group 2", f: 6, dist: "6f", ages: [2, 2], ageLabel: "2YO colts", sex: "C" },
    { id: "lonsdale", day: 3, name: "Lonsdale Cup", grade: "Group 2", f: 16, dist: "2m", ages: [3, 9], ageLabel: "3YO+" },
    { id: "roses", day: 3, name: "Roses Stakes", grade: "Listed", f: 5, dist: "5f", ages: [2, 2], ageLabel: "2YO" },
    // Saturday
    { id: "ebor", day: 4, name: "The Ebor", grade: "Handicap", heritage: true, f: 14, dist: "1m6f", ages: [4, 9], ageLabel: "4YO+" },
    { id: "city-of-york", day: 4, name: "City of York Stakes", grade: "Group 2", f: 7, dist: "7f", ages: [3, 9], ageLabel: "3YO+" },
    { id: "strensall", day: 4, name: "Strensall Stakes", grade: "Group 3", f: 9, dist: "1m1f", ages: [3, 9], ageLabel: "3YO+" },
    { id: "melrose", day: 4, name: "Melrose Handicap", grade: "Handicap", f: 14, dist: "1m6f", ages: [3, 3], ageLabel: "3YO" },
  ],
  titles: [
    { min: 1000000, name: "York Champion", note: "The Knavesmire belongs to your colours. Hardly anyone gets here.", cls: "t5" },
    { min: 750000, name: "Leading Owner", note: "A season to frame and hang in the yard.", cls: "t4" },
    { min: 500000, name: "Group Race Force", note: "Your colours were in every big finish at York.", cls: "t3" },
    { min: 250000, name: "York Winner", note: "A proper season on the Knavesmire.", cls: "t2" },
    { min: 0, name: "Day Tripper", note: "The Ebor crowd was grand. Next year.", cls: "t1" }
  ],
  ladderTop: 1250000,
  // How the screens name things in this season
  words: {
    where: "York", whereLong: "the York season", venue: "the Knavesmire", gameTitle: "York",
    when: "May and August", whenRaces: "The season",
    programme: "The York programme",
    drawLine: "The Jockey Club has drawn your ten races for the York season. Go and see what you're aiming at.",
    drawText: "The programme for the York season is out: ten races over five days, two a day, at the Dante in May and the Ebor Festival in August, drawn fresh for this season.",
    entriesLine: "Enter one horse for each race at the Jockey Club, then load the horseboxes for York.",
    weekLine: "The Dante in May, then four days of the Ebor. Ten races.",
    lockedStatus: "The racing starts in May, once your string is in training",
    lockedText: "The Dante and the Ebor Festival, ten races, watched on the Knavesmire in 3D.",
    go: "Go to York", back: "Back to York", over: "The York season is over for this year",
    weekTitle: "The York season", weekRunning: "The season is under way",
    standingsAt: "The final standings at York",
    titleFrom: "Your title from the York season", playedNoun: "York season", playedPlural: "YOUR YORK SEASONS",
    lede: "Your ten races at York, two a day: the Dante Festival in May, then the four days of the Ebor Festival in August. Group 1s, the Ebor itself and plenty in between.",
    watchHere: "Watch a race to see it run on the Knavesmire in 3D",
    weekWord: "the racing", weekDone: "the season is run", weekHead: "THE RACING", bestWord: "season",
    goingWhen: "The going for each day is declared when you go to the races, after your entries are in.", goingCounts: "on the day", backToRacing: "Back to the races",
    coverPicture: "img/york-cover.jpg",
    cardBack: "YORK", dayWord: "day",
    entryRule: "One horse per race",
    film: null, still: "img/york-still.jpg",
    filmCaption: "",
    coverKicker: "York · the Dante and the Ebor · one season",
    coverLede: "Build a stable in Newmarket, breed and buy your string, then take them north to York for the Dante in May and the Ebor Festival in August. Win enough and you're crowned <b>York Champion</b>.",
    coverRaces: ["The York season", "Ten races over five days, watched in 3D on the Knavesmire. Prize money is its own pot."],
    howRaces: "<b>The York season</b>: two races a day at the Dante and the Ebor Festival. Watch each race in 3D or sim it.",
    howTitle: "Race at York",
    howLine: "Ten races over five days, two a day: the Dante in May and the Ebor Festival in August",
    howLineBeginner: "Five races, one a day: the Dante in May and the four days of the Ebor",
  },
};
