const app = {
  init() {
    this.cacheElements();
    this.setupFiltering();
    this.setupSaveButtons();
    this.setupForm();
    this.restoreSavedState();
  },

  cacheElements() {
    this.filterToggle = document.getElementById('filter-toggle');
    this.filterSheet = document.getElementById('filter-sheet');
    this.filterClose = document.getElementById('filter-close');
    this.filterOptions = document.querySelectorAll('input[name="location"]');
    this.filterChips = document.querySelectorAll('.filter-chip');
    this.soundscapesGrid = document.getElementById('soundscapes-grid');
    this.cards = document.querySelectorAll('.soundscape-card');
    this.saveButtons = document.querySelectorAll('.save-button');
    this.form = document.getElementById('subscription-form');
    this.emailInput = document.getElementById('subscriber-email');
    this.emailError = document.getElementById('email-error');
    this.formSuccess = document.getElementById('form-success');
    this.formSubmit = document.querySelector('.form-submit');
  },

  setupFiltering() {
    // Mobile sheet toggle
    if (this.filterToggle) {
      this.filterToggle.addEventListener('click', () => {
        const isOpen = !this.filterSheet.hasAttribute('hidden');
        this.setSheetOpen(!isOpen);
      });
    }

    // Close sheet button
    if (this.filterClose) {
      this.filterClose.addEventListener('click', () => {
        this.setSheetOpen(false);
      });
    }

    // Close sheet on Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !this.filterSheet.hasAttribute('hidden')) {
        this.setSheetOpen(false);
      }
    });

    // Filter by radio buttons
    this.filterOptions.forEach((option) => {
      option.addEventListener('change', () => {
        this.filterByLocation(option.value);
        this.setSheetOpen(false);
      });
    });

    // Filter chips (desktop)
    this.filterChips.forEach((chip) => {
      chip.addEventListener('click', () => {
        const location = chip.dataset.filter;
        this.filterByLocation(location);
        this.updateFilterUI(location);
      });
    });
  },

  setSheetOpen(isOpen) {
    if (isOpen) {
      this.filterSheet.removeAttribute('hidden');
      this.filterToggle.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
    } else {
      this.filterSheet.setAttribute('hidden', '');
      this.filterToggle.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
      this.filterToggle.focus();
    }
  },

  filterByLocation(location) {
    this.cards.forEach((card) => {
      const cardLocation = card.dataset.location;
      if (location === 'all' || cardLocation === location) {
        card.style.display = '';
      } else {
        card.style.display = 'none';
      }
    });
  },

  updateFilterUI(location) {
    this.filterChips.forEach((chip) => {
      const isActive = chip.dataset.filter === location;
      chip.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });

    this.filterOptions.forEach((option) => {
      option.checked = option.value === location;
    });
  },

  setupSaveButtons() {
    this.saveButtons.forEach((button) => {
      button.addEventListener('click', () => {
        this.toggleSave(button);
      });
    });
  },

  toggleSave(button) {
    const id = button.dataset.id;
    const isSaved = button.getAttribute('aria-pressed') === 'true';
    const newState = !isSaved;

    button.setAttribute('aria-pressed', newState ? 'true' : 'false');
    this.updateSaveCount(id, newState);
    this.persistSaveState(id, newState);
  },

  updateSaveCount(id, isSaved) {
    const countEl = document.querySelector(`.save-count[data-id="${id}"]`);
    if (!countEl) return;

    const savedItems = this.getSavedItems();
    const count = Object.values(savedItems).filter(Boolean).length;
    countEl.textContent = count;
  },

  persistSaveState(id, isSaved) {
    const saved = this.getSavedItems();
    saved[id] = isSaved;
    localStorage.setItem('saved-soundscapes', JSON.stringify(saved));
  },

  getSavedItems() {
    const saved = localStorage.getItem('saved-soundscapes');
    return saved ? JSON.parse(saved) : {};
  },

  restoreSavedState() {
    const saved = this.getSavedItems();
    let totalSaved = 0;

    this.saveButtons.forEach((button) => {
      const id = button.dataset.id;
      if (saved[id]) {
        button.setAttribute('aria-pressed', 'true');
        totalSaved++;
      }
    });

    this.saveButtons.forEach((button) => {
      const id = button.dataset.id;
      const countEl = document.querySelector(`.save-count[data-id="${id}"]`);
      if (countEl) {
        countEl.textContent = totalSaved;
      }
    });
  },

  setupForm() {
    if (!this.form) return;

    this.emailInput.addEventListener('blur', () => {
      this.validateEmail();
    });

    this.emailInput.addEventListener('input', () => {
      if (this.emailInput.value) {
        this.emailError.textContent = '';
      }
    });

    this.form.addEventListener('submit', (e) => {
      e.preventDefault();
      if (this.validateEmail()) {
        this.submitForm();
      }
    });
  },

  validateEmail() {
    const email = this.emailInput.value.trim();
    const isValid = email && this.emailInput.checkValidity();

    if (!isValid && email) {
      this.emailError.textContent = '請輸入有效的電子郵件地址';
      return false;
    }

    if (!email) {
      this.emailError.textContent = '電子郵件為必填欄位';
      return false;
    }

    this.emailError.textContent = '';
    return true;
  },

  submitForm() {
    this.formSubmit.disabled = true;
    this.formSubmit.textContent = '處理中…';

    setTimeout(() => {
      this.formSuccess.removeAttribute('hidden');
      this.form.reset();
      this.formSubmit.disabled = false;
      this.formSubmit.textContent = '加入通知';
      this.emailError.textContent = '';

      setTimeout(() => {
        this.formSuccess.setAttribute('hidden', '');
      }, 5000);
    }, 800);
  },
};

document.addEventListener('DOMContentLoaded', () => {
  app.init();
});
