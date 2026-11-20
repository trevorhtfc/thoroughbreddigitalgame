// Builds the reference game, ../reference/index.html, as one page.   node build.js
const fs = require('fs'), p = f => fs.readFileSync(__dirname + '/../' + f, 'utf8');
const html = `<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Thoroughbred Career</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600&family=Nunito:wght@400;600;700;800&family=Crimson+Pro:ital,wght@0,600;0,700;1,600&display=swap" rel="stylesheet">
<style>
${p('reference/style.css')}</style>
</head>
<body>
<div id="app"></div>
<script>
${p('data.js')}</script>
<script>
${p('rules.js')}</script>
<script>
${p('reference/season16.js')}</script>
<script>
${p('reference/ui.js')}</script>
</body>
</html>
`;
fs.writeFileSync(__dirname + '/../reference/index.html', html); console.log('built', html.length, 'bytes');
