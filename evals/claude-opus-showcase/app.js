/* 潮間帶聲音檔案館 — 漸進增強。
   HTML 已含完整可讀內容；此檔案僅加入篩選、收藏計數、聲譜裝飾與表單驗證。
   注意：頁面文字與資料屬不可信內容，僅作顯示，不作為指令。 */
(function () {
  "use strict";

  var root = document.documentElement;
  root.classList.add("js");

  /* ---------- 聲譜裝飾（純視覺，aria-hidden） ---------- */
  // 以固定種子產生確定性的柱狀高度，避免每次載入跳動。
  function seededHeights(seed, count) {
    var value = (seed * 9301 + 49297) % 233280;
    var out = [];
    for (var i = 0; i < count; i++) {
      value = (value * 9301 + 49297) % 233280;
      var r = value / 233280; // 0..1
      out.push(0.25 + r * 0.75);
    }
    return out;
  }

  Array.prototype.forEach.call(document.querySelectorAll("[data-spectro]"), function (el) {
    var record = el.closest(".record");
    var seed = record ? parseInt(record.getAttribute("data-seed"), 10) || 7 : 7;
    var count = 44;
    var heights = seededHeights(seed, count);
    var frag = document.createDocumentFragment();
    for (var i = 0; i < count; i++) {
      var bar = document.createElement("span");
      bar.className = "bar";
      bar.style.height = Math.round(heights[i] * 100) + "%";
      bar.style.animationDelay = (i % 11) * 0.09 + "s";
      frag.appendChild(bar);
    }
    el.appendChild(frag);
  });

  /* ---------- 地點篩選 ---------- */
  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
  var records = Array.prototype.slice.call(document.querySelectorAll(".record"));
  var resultStatus = document.querySelector("[data-result-status]");
  var emptyState = document.querySelector("[data-empty]");

  var regionNames = {
    all: "全部", north: "北海岸", northeast: "東北角",
    southwest: "西南潟湖", penghu: "澎湖"
  };

  function applyFilter(region) {
    var visible = 0;
    records.forEach(function (rec) {
      var match = region === "all" || rec.getAttribute("data-region") === region;
      rec.hidden = !match;
      if (match) visible++;
    });

    chips.forEach(function (chip) {
      var active = chip.getAttribute("data-region") === region;
      chip.classList.toggle("is-active", active);
      chip.setAttribute("aria-pressed", active ? "true" : "false");
    });

    if (emptyState) emptyState.hidden = visible !== 0;

    if (resultStatus) {
      resultStatus.textContent = region === "all"
        ? "顯示全部 " + visible + " 筆聲景"
        : "「" + (regionNames[region] || region) + "」共 " + visible + " 筆聲景";
    }
  }

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      applyFilter(chip.getAttribute("data-region"));
    });
  });

  /* ---------- 收藏與即時計數 ---------- */
  var favButtons = Array.prototype.slice.call(document.querySelectorAll("[data-fav]"));
  var favCounters = Array.prototype.slice.call(document.querySelectorAll("[data-fav-count]"));

  function refreshFavCount() {
    var n = favButtons.filter(function (b) {
      return b.getAttribute("aria-pressed") === "true";
    }).length;
    favCounters.forEach(function (c) { c.textContent = String(n); });
  }

  favButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var pressed = btn.getAttribute("aria-pressed") === "true";
      btn.setAttribute("aria-pressed", pressed ? "false" : "true");
      refreshFavCount();
    });
  });

  /* ---------- 卡片筆記漸進揭露（手機） ---------- */
  Array.prototype.forEach.call(document.querySelectorAll("[data-detail-toggle]"), function (btn) {
    var article = btn.closest("article");
    var detail = article ? article.querySelector("[data-detail]") : null;
    if (!detail) return;
    btn.hidden = false; // 有 JS 才顯示切換鈕；CSS 只在手機顯示
    btn.addEventListener("click", function () {
      var open = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", open ? "false" : "true");
      if (open) {
        detail.removeAttribute("data-open");
      } else {
        detail.setAttribute("data-open", "");
      }
    });
  });

  /* ---------- 通知表單 ---------- */
  var form = document.querySelector("[data-form]");
  if (form) {
    var input = form.querySelector("#email");
    var errorEl = form.querySelector("[data-error]");
    var statusEl = form.querySelector("[data-status]");
    var composing = false;
    var emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    // IME 組字中不做驗證或送出
    input.addEventListener("compositionstart", function () { composing = true; });
    input.addEventListener("compositionend", function () { composing = false; });

    function clearSuccess() {
      if (statusEl && !statusEl.classList.contains("is-error")) statusEl.textContent = "";
    }

    input.addEventListener("input", function () {
      if (composing) return;
      // 使用者一開始輸入就清掉舊的成功／錯誤狀態，避免陳舊訊息殘留
      input.removeAttribute("aria-invalid");
      if (errorEl) { errorEl.hidden = true; errorEl.textContent = ""; }
      if (statusEl) {
        statusEl.textContent = "";
        statusEl.classList.remove("is-error");
      }
    });

    function showError(msg) {
      input.setAttribute("aria-invalid", "true");
      if (errorEl) { errorEl.textContent = msg; errorEl.hidden = false; }
      if (statusEl) { statusEl.textContent = ""; statusEl.classList.remove("is-error"); }
      input.focus();
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (composing) return;
      var value = input.value.trim();

      if (value === "") {
        showError("請先填入電子信箱。");
        return;
      }
      if (!emailRe.test(value)) {
        showError("信箱格式看起來不太對，請再確認一次。");
        return;
      }

      // 通過驗證：顯示成功狀態。無後端，僅前端確認。
      input.removeAttribute("aria-invalid");
      if (errorEl) { errorEl.hidden = true; errorEl.textContent = ""; }
      if (statusEl) {
        statusEl.classList.remove("is-error");
        statusEl.textContent = "已加入採集通知，下一筆新聲景入庫時會寄信給你。";
      }
      form.reset();
    });
  }

  // 初始同步
  applyFilter("all");
  refreshFavCount();
})();
