const fs = require('fs');
const content = fs.readFileSync('dist/assets/KnowledgePage-BAoAzn8P.js', 'utf8');
const idx = content.indexOf('addConceptOpen');
if (idx > -1) {
    console.log('Found at:', idx);
    console.log(content.substring(Math.max(0, idx-100), idx+200));
} else {
    console.log('NOT FOUND');
}