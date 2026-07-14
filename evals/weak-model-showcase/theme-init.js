(() => {
  document.documentElement.classList.add('js');

  try {
    const storedTheme = window.localStorage.getItem('wow-theme');
    if (storedTheme === 'light' || storedTheme === 'dark') {
      document.documentElement.dataset.theme = storedTheme;
    }

    const effectiveTheme =
      storedTheme === 'light' || storedTheme === 'dark'
        ? storedTheme
        : window.matchMedia('(prefers-color-scheme: dark)').matches
          ? 'dark'
          : 'light';
    document
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute('content', effectiveTheme === 'dark' ? '#171411' : '#f3ede2');
  } catch {
    // Storage can be unavailable in privacy-restricted contexts; system mode remains usable.
  }
})();
