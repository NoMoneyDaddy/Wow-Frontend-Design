const filterButtons = [...document.querySelectorAll('[data-filter]')];
const products = [...document.querySelectorAll('[data-category]')];
const favoriteButtons = [...document.querySelectorAll('[data-favorite]')];
const favoriteCount = document.querySelector('#favorite-count');
const favoriteButton = document.querySelector('#favorites');
const collectionSummary = document.querySelector('#collection-summary');
const form = document.querySelector('#newsletter-form');
const formStatus = document.querySelector('#form-status');
const emailInput = document.querySelector('#email');
const menuToggle = document.querySelector('#menu-toggle');
const menuClose = document.querySelector('#menu-close');
const mobileMenu = document.querySelector('#mobile-menu');
const themeChoice = document.querySelector('#theme-choice');
const themeStatus = document.querySelector('#theme-status');
const themeColor = document.querySelector('meta[name="theme-color"]');
const productCards = [...document.querySelectorAll('.product-card')];
const menuBackground = [
  document.querySelector('.skip-link'),
  document.querySelector('.site-header'),
  document.querySelector('main'),
  document.querySelector('.site-footer'),
].filter((element) => element instanceof HTMLElement);

let menuScrollY = 0;
let menuTrigger = null;

const clearFormStatus = () => {
  if (!formStatus) {
    return;
  }

  formStatus.textContent = '';
  formStatus.removeAttribute('data-state');
};

const setFormStatus = (message, state) => {
  if (!formStatus) {
    return;
  }

  formStatus.textContent = message;
  formStatus.setAttribute('data-state', state);
};

const menuFocusables = () =>
  mobileMenu
    ? [...mobileMenu.querySelectorAll('a, button, [tabindex]:not([tabindex="-1"])')].filter(
        (element) => !element.hasAttribute('disabled')
      )
    : [];

const setFavoriteSummary = (count) => {
  if (favoriteCount) {
    favoriteCount.textContent = String(count);
  }

  if (favoriteButton) {
    favoriteButton.setAttribute('aria-label', `前往收藏清單，目前收藏 ${count} 件`);
  }
};

const readStoredTheme = () => {
  try {
    const value = window.localStorage.getItem('wow-theme');
    return value === 'light' || value === 'dark' ? value : 'system';
  } catch {
    return 'system';
  }
};

const effectiveTheme = () => {
  const explicitTheme = document.documentElement.dataset.theme;
  if (explicitTheme === 'light' || explicitTheme === 'dark') {
    return explicitTheme;
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

const syncThemeColor = () => {
  themeColor?.setAttribute('content', effectiveTheme() === 'dark' ? '#171411' : '#f3ede2');
};

const applyTheme = (value, { announce = true } = {}) => {
  const explicitTheme = value === 'light' || value === 'dark' ? value : 'system';

  if (explicitTheme === 'system') {
    document.documentElement.removeAttribute('data-theme');
  } else {
    document.documentElement.dataset.theme = explicitTheme;
  }

  try {
    if (explicitTheme === 'system') {
      window.localStorage.removeItem('wow-theme');
    } else {
      window.localStorage.setItem('wow-theme', explicitTheme);
    }
  } catch {
    // The selected theme still applies for this page when storage is unavailable.
  }

  if (themeChoice) {
    themeChoice.value = explicitTheme;
  }

  syncThemeColor();
  if (announce && themeStatus) {
    const label = explicitTheme === 'system' ? '跟隨系統' : explicitTheme === 'dark' ? '深色' : '淺色';
    themeStatus.textContent = `外觀已切換為${label}。`;
  }
};

const updateCollectionSummary = () => {
  if (!collectionSummary) {
    return;
  }

  const visibleCount = products.filter((product) => !product.hidden).length;
  collectionSummary.textContent = `目前顯示 ${visibleCount} 件選物。`;
};

const updateFavoriteCount = () => {
  const count = favoriteButtons.filter((item) => item.getAttribute('aria-pressed') === 'true').length;
  setFavoriteSummary(count);
};

const applyFilter = (filter) => {
  products.forEach((product) => {
    product.hidden = filter !== 'all' && product.dataset.category !== filter;
  });

  document.body.classList.toggle('is-filter-empty', products.every((product) => product.hidden));
  updateCollectionSummary();
};

productCards.forEach((card) => {
  const button = card.querySelector('[data-favorite]');
  const title = card.querySelector('h3')?.textContent?.trim() ?? '此項目';

  if (button) {
    button.dataset.title = title;
  }
});

filterButtons.forEach((button) => {
  button.addEventListener('click', () => {
    const filter = button.dataset.filter;

    filterButtons.forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
    applyFilter(filter);
  });
});

favoriteButtons.forEach((button) => {
  button.setAttribute('aria-pressed', 'false');
  const title = button.dataset.title ?? '此項目';
  button.setAttribute('aria-label', `收藏「${title}」`);

  button.addEventListener('click', () => {
    const active = button.getAttribute('aria-pressed') === 'true';
    const nextActive = !active;
    button.setAttribute('aria-pressed', String(nextActive));
    button.setAttribute('aria-label', `${nextActive ? '取消收藏' : '收藏'}「${title}」`);
    button.textContent = active ? '加入收藏' : '已收藏';
    updateFavoriteCount();
  });
});

const lockScroll = () => {
  menuScrollY = window.scrollY || window.pageYOffset || 0;
  document.body.classList.add('menu-open');
  document.body.style.setProperty('--scroll-lock-offset', `${menuScrollY}px`);
};

const unlockScroll = () => {
  document.body.classList.remove('menu-open');
  document.body.style.removeProperty('--scroll-lock-offset');
  window.scrollTo(0, menuScrollY);
};

const setMenuBackgroundInert = (inert) => {
  menuBackground.forEach((element) => {
    element.inert = inert;
  });
};

const closeMenu = ({ restoreFocus = true } = {}) => {
  if (!mobileMenu || !menuToggle) {
    return;
  }

  mobileMenu.hidden = true;
  menuToggle.setAttribute('aria-expanded', 'false');
  setMenuBackgroundInert(false);
  unlockScroll();

  if (restoreFocus) {
    (menuTrigger ?? menuToggle).focus();
  }
};

const openMenu = () => {
  if (!mobileMenu || !menuToggle) {
    return;
  }

  menuTrigger = document.activeElement instanceof HTMLElement ? document.activeElement : menuToggle;
  mobileMenu.hidden = false;
  menuToggle.setAttribute('aria-expanded', 'true');
  setMenuBackgroundInert(true);
  lockScroll();
  const [firstFocusable] = menuFocusables();
  if (firstFocusable) {
    firstFocusable.focus();
  }
};

menuToggle?.addEventListener('click', () => {
  if (mobileMenu?.hidden) {
    openMenu();
    return;
  }

  closeMenu();
});

menuClose?.addEventListener('click', closeMenu);

mobileMenu?.addEventListener('click', (event) => {
  if (event.target === mobileMenu) {
    closeMenu();
    return;
  }

  const link = event.target instanceof Element ? event.target.closest('a[href^="#"]') : null;
  if (!link) {
    return;
  }

  event.preventDefault();
  const targetId = decodeURIComponent(link.getAttribute('href')?.slice(1) ?? '');
  const target = targetId ? document.getElementById(targetId) : null;

  closeMenu({ restoreFocus: false });

  if (target) {
    window.requestAnimationFrame(() => {
      target.scrollIntoView({ block: 'start', inline: 'nearest', behavior: 'auto' });
      target.focus({ preventScroll: true });
      history.pushState(null, '', `#${targetId}`);
    });
  }
});

document.addEventListener('keydown', (event) => {
  if (!mobileMenu || mobileMenu.hidden) {
    return;
  }

  if (event.key === 'Escape') {
    event.preventDefault();
    closeMenu();
    return;
  }

  if (event.key !== 'Tab') {
    return;
  }

  const focusables = menuFocusables();
  if (focusables.length === 0) {
    event.preventDefault();
    return;
  }

  const first = focusables[0];
  const last = focusables[focusables.length - 1];

  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
});

form?.addEventListener('input', () => {
  emailInput?.removeAttribute('aria-invalid');

  if (formStatus?.textContent) {
    clearFormStatus();
  }
});

form?.addEventListener(
  'invalid',
  (event) => {
    if (event.target === emailInput) {
      emailInput.setAttribute('aria-invalid', 'true');
    }
    setFormStatus('請輸入有效的電子信箱。', 'error');
  },
  true
);

form?.addEventListener('submit', (event) => {
  event.preventDefault();

  if (!form.checkValidity()) {
    emailInput?.setAttribute('aria-invalid', 'true');
    setFormStatus('請輸入有效的電子信箱。', 'error');
    form.reportValidity?.();
    return;
  }

  emailInput?.removeAttribute('aria-invalid');
  setFormStatus('格式檢查完成；此示範頁沒有送出或儲存電子信箱。', 'success');
});

themeChoice?.addEventListener('change', () => {
  applyTheme(themeChoice.value);
});

const colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)');
const handleSystemThemeChange = () => {
  if (themeChoice?.value === 'system') {
    syncThemeColor();
  }
};
if (typeof colorSchemeQuery.addEventListener === 'function') {
  colorSchemeQuery.addEventListener('change', handleSystemThemeChange);
} else {
  colorSchemeQuery.addListener?.(handleSystemThemeChange);
}

applyTheme(readStoredTheme(), { announce: false });
updateCollectionSummary();
updateFavoriteCount();
applyFilter('all');
