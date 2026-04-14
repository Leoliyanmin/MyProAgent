const fs = require('fs');
let code = fs.readFileSync('src/stores/theme.js', 'utf8');
code = code.replace(
  "bgSidebarImage: '',",
  "bgSidebarImage: 'data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"100\" height=\"100\"><rect width=\"100\" height=\"100\" fill=\"red\"/></svg>',"
);
fs.writeFileSync('src/stores/theme.js', code);
