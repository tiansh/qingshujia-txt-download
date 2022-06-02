// Reference font may be downloaded from
// https://www.onlinewebfonts.com/download/796a8aac411b7d0cce8b49865160eb63

const fs = require('fs');

const express = require('express')
const cors = require('cors');
const bodyParser = require('body-parser'); 

const { Font, woff2 } = require('fonteditor-core');

// The font parser library seems sucks on memory leak
// There is few thing I can do
// So why not halt the program and let some one restart me again and again
let globalCounter = 0;
const incCounter = function () {
  if (++globalCounter > 100) {
    setTimeout(() => {
      require('process').exit();
    }, 3000);
  }
};

; (async function () {
  await woff2.init();

  const shapeStr = glyf => JSON.stringify({ contours: glyf.contours, advanceWidth: glyf.advanceWidth });
  const parseFont = (function () {
    const ref = Font.create(fs.readFileSync('./MI-LANTING.ttf'), { type: 'ttf', combinePath: false, compound2simple: true });
    const lookup = new Map();
    ref.data.glyf.forEach(glyf => {
      if (!glyf.unicode) return;
      if (!glyf.contours?.length && !glyf.advanceWidth) return;
      const shape = shapeStr(glyf);
      if (lookup.has(shape)) {
        lookup.get(shape).push(...glyf.unicode);
      } else {
        lookup.set(shape, [...glyf.unicode]);
      }
    });
    return function (file) {
      incCounter();
      const font = Font.create(file, { type: 'woff2', combinePath: false, compound2simple: true });
      let miss = 0;
      const table = {};
      font.data.glyf.forEach(glyf => {
        if (!glyf.unicode) return;
        let matched = null;
        if (!glyf.contours?.length && !glyf.advanceWidth) {
          matched = [];
        } else {
          shape = shapeStr(glyf);
          matched = lookup.get(shape);
        }
        if (!matched) miss++;
        glyf.unicode.forEach(from => {
          if (matched.includes(from)) return;
          table[String.fromCharCode(from)] = matched.length ? String.fromCharCode(matched[0]) : '';
        });
      });
      if (miss) console.warn(`Build font table: ${miss} characters missing.`);
      else console.log('Build font table successfully.');
      return table;
    };
  }());

  const app = express()
  app.post('/font/parse', cors(), bodyParser.raw({inflate: true, limit: '50mb', type: () => true }), function (req, res) {
    res.send(parseFont(req.body));
  });
  const port = +process.argv[2] || 9000;
  app.listen(port, '0.0.0.0', () => {
    console.log(`Listening on 0.0.0.0:${port}`);
  });
}());

