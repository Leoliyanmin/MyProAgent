const fs = require('fs');
const code = fs.readFileSync('src/App.vue', 'utf-8');
console.log(code.includes('background-image: var(--clr-bg-content-image, none);'));
