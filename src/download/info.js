; (function (callback) {
  ; (async function () {
    const main = document.querySelector('main');
    const text = main.innerText;
    const author = text.match(/作者：(.*)/)[1];
    const date = new Date(text.match(/更新时间：([\d\-: ]*)/)[1].trim());
    date.setHours(date.getHours() + 8); // Force UTC+8
    const last_update = date.toISOString().replace(/(.*)T(\d*:\d*):.*/, '$1 $2');
    const description = main.querySelector('div + .introduction')
      .innerText.replace(/\n\n/g, '\n');
    const links = [...main.querySelectorAll('a[href^="/read/"]')];
    const chapters = links.map(link => {
      const id = link.pathname.split('/')[3];
      const title = link.textContent.trim().replace(/\n/g, ' ');
      const url = link.href;
      return { url, title, id, content: null };
    });
    return JSON.stringify({ author, last_update, description, chapters });
  }()).then(callback, callback);
}(arguments[0]));
