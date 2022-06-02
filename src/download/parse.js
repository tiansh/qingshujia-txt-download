; (function (callback) {
  ; (async function () {
    const read = document.querySelector('.read');
    if (!read) return 'null';
    if (!read.querySelector('.read-font-fixed')) {
      let fix = null;
      const url = read_style.textContent.match(/url\((.*)\)/)[1];
      const cache = window.__FONT_CACHE__ = window.__FONT_CACHE__ ?? {};
      if (cache[url]) {
        fix = cache[url];
      } else {
        const font = await fetch(url)
          .then(r => r.arrayBuffer());
        const table = await fetch('http://localhost:9000/font/parse',
          { method: 'POST', body: font }).then(r => r.json());
        fix = text => [...text].map(t => table[t] ?? t).join('');
        cache[url] = fix;
      }
      read.style.setProperty('font-family', 'fangsong', 'important');
      read.style.setProperty('user-select', 'auto', 'important');
      ; (function parse(node) {
        if (node.nodeType === Node.TEXT_NODE) {
          node.nodeValue = fix(node.nodeValue);
        } else if (node.nodeType === Node.ELEMENT_NODE) {
          [...node.childNodes].forEach(parse);
        }
      }(read));
      read.appendChild(document.createElement('span')).className = 'read-font-fixed';
    }
    const body = (function parse(node) {
      if (node.nodeType === Node.TEXT_NODE) {
        return node.nodeValue;
      } else if (node.nodeType !== Node.ELEMENT_NODE) {
        return '';
      } else if (node.matches('style, script, template, textarea')) {
        return '';
      } else if (node.matches('.duokan-footnote')) {
        return '';
      } else if (node.matches('br')) {
        if (node) return '\n';
      } else if (node.matches('p, div, ul, ol, li, h1, h2, h3, h4, h5, h6')) {
        return [...node.childNodes].map(parse).join('').replace(/\n?$/, '\n');
      } else if (node.matches('span, sup, sub, a, b, i, s, strong, em, mark, del, ins')) {
        return [...node.childNodes].map(parse).join('');
      } else if (node.matches('ruby')) {
        return [...node.childNodes].map(child => {
          if (child.nodeType === Node.TEXT_NODE) return child.textContent;
          if (child instanceof HTMLElement && child.matches('rp')) return '';
          if (child instanceof HTMLElement && child.matches('rt')) return '(' + child.textContent + ')';
          return '';
        }).join('');
      } else if (node.matches('img')) {
        return `[图 ${node.src}]`;
      } else {
        console.warn('Unknown node: ', node);
        return node.innerText;
      }
    }(read));
    return JSON.stringify({ result: body });
  }()).then(callback, err => { callback(JSON.stringify({ error: '' + err })); });
}(...arguments));

