(function () {
  const THEME_KEY = 'vortex-theme';

  function getTheme() {
    return localStorage.getItem(THEME_KEY) ||
      (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
  }

  function setTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    localStorage.setItem(THEME_KEY, t);
  }

  setTheme(getTheme());

  document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.getElementById('themeToggle');
    if (toggle) {
      toggle.addEventListener('click', function () {
        const current = document.documentElement.getAttribute('data-theme');
        setTheme(current === 'dark' ? 'light' : 'dark');
      });
    }

    const links = document.querySelectorAll('.nav-link');
    const path = window.location.pathname;
    links.forEach(function (link) {
      link.classList.remove('active');
      const href = link.getAttribute('href');
      if (href === path || (path === '/' && href === '/') ||
        (path !== '/' && href && path.endsWith(href))) {
        link.classList.add('active');
      }
    });
  });
})();
