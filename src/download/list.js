; (function (callback) {
  ; (async function () {
    const containers = [...document.querySelectorAll('main a[href^="/book/info/"]')].map(link => {
      return link.parentNode;
    });
    for (let i = 0; i < containers.length; i++) {
      const container = containers[i];
      for (let retry = 0; !container.querySelector('.q-img__content') && retry < 300; ++retry) {
        window.scrollTo(0, container.offsetTop);
        await new Promise(resolve => { setTimeout(resolve, 100); });
      }
    }
    return JSON.stringify([...document.querySelectorAll('main a[href^="/book/info/"]')].map(link => {
      const container = link.parentNode;
      const title = container.querySelector('.book-name-text').title.replace(/\n/g, ' ');
      const remark = container.querySelector('.q-img__content')?.textContent ?? '';
      const url = link.href;
      const id = link.pathname.split('/')[3];
      return { title, url, id, remark };
    }));
  }()).then(callback, callback);
}(arguments[0]));
