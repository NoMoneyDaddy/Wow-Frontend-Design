/* 港務巡檢工單控制台 — 本機 demo 狀態，不進行任何網路請求 */
(function () {
  "use strict";

  var TODAY = new Date("2026-07-14T00:00:00");

  var STATUS = {
    pending: { label: "待處理", cls: "pending" },
    active:  { label: "處理中", cls: "active" },
    waiting: { label: "待料",  cls: "waiting" },
    done:    { label: "已完成", cls: "done" }
  };
  var PRIORITY = {
    high: { label: "高", cls: "high" },
    mid:  { label: "中", cls: "mid" },
    low:  { label: "低", cls: "low" }
  };

  var ZONES = ["北碼頭 A", "南碼頭 B", "貨櫃場 C", "油品儲區", "倉儲區", "客運棧橋"];
  var ASSIGNEES = ["陳志明", "林淑芬", "黃建宏", "王美玲", "張偉倫"];
  var UNASSIGNED = "（未指派）";

  // 種子資料：本機狀態，非伺服器資料
  var orders = [
    { id: "WO-2418", zone: "北碼頭 A", title: "起重機軌道異音檢查", priority: "high", status: "active",  due: "2026-07-11", assignee: "陳志明", syncError: true,
      desc: "3 號門式起重機於行走時出現週期性金屬異音，需檢查軌道接縫與滾輪軸承，並記錄振動值。" },
    { id: "WO-2419", zone: "油品儲區", title: "管線洩漏偵測器校驗", priority: "high", status: "pending", due: "2026-07-13", assignee: UNASSIGNED, syncError: false,
      desc: "輸油管線沿線氣體偵測器已屆校驗週期，需以標準氣體逐點校正並更新校驗標籤。" },
    { id: "WO-2421", zone: "貨櫃場 C", title: "場橋供電電纜巡查", priority: "mid", status: "active",  due: "2026-07-16", assignee: "林淑芬", syncError: false,
      desc: "沿場橋供電捲線區檢查電纜外皮磨損與拖鏈狀況，標記需更換的區段。" },
    { id: "WO-2422", zone: "南碼頭 B", title: "繫船柱鏽蝕評估", priority: "low", status: "waiting", due: "2026-07-20", assignee: "黃建宏", syncError: false,
      desc: "B 席 5～8 號繫船柱基座出現鏽蝕，等待除鏽材料到場後進行評估與防蝕處理。" },
    { id: "WO-2423", zone: "倉儲區", title: "消防泵浦週檢", priority: "mid", status: "pending", due: "2026-07-15", assignee: "王美玲", syncError: false,
      desc: "倉儲區消防泵浦例行週檢，含啟動測試、壓力讀值與備援電源切換確認。" },
    { id: "WO-2424", zone: "客運棧橋", title: "護欄結構點檢", priority: "high", status: "pending", due: "2026-07-12", assignee: "張偉倫", syncError: false,
      desc: "旅客登船棧橋護欄多處固定件鬆動，需逐段檢查焊道與螺栓扭力並即時補強。" },
    { id: "WO-2425", zone: "北碼頭 A", title: "照明塔燈具更換", priority: "low", status: "done", due: "2026-07-09", assignee: "林淑芬", syncError: false,
      desc: "北碼頭高桿照明塔 2 具投光燈故障，已完成更換並確認夜間照度達標。" },
    { id: "WO-2426", zone: "貨櫃場 C", title: "地磅感測器校正", priority: "mid", status: "active", due: "2026-07-18", assignee: "陳志明", syncError: false,
      desc: "進場地磅稱重誤差偏大，以標準砝碼進行多點校正並記錄修正係數。" },
    { id: "WO-2427", zone: "油品儲區", title: "防溢堤排水閥檢查", priority: "high", status: "waiting", due: "2026-07-14", assignee: "黃建宏", syncError: false,
      desc: "防溢堤雨水排放閥啟閉不順，等待備品閥件更換前先確認手動排放路徑暢通。" },
    { id: "WO-2428", zone: "南碼頭 B", title: "岸電箱接地量測", priority: "mid", status: "pending", due: "2026-07-22", assignee: UNASSIGNED, syncError: false,
      desc: "新設岸電箱啟用前需完成接地電阻量測與絕緣測試，並登錄量測值。" }
  ];

  var filters = { search: "", zone: "", priority: "", status: "", overdue: false };
  var selectedId = null;
  var lastFocusedRow = null;
  var mobileQuery = window.matchMedia("(max-width: 860px)");

  // ---- 工具 ----
  function dayDiff(dueStr) {
    var d = new Date(dueStr + "T00:00:00");
    return Math.round((d - TODAY) / 86400000);
  }
  function dueInfo(o) {
    var diff = dayDiff(o.due);
    if (o.status === "done") return { text: "已結案 " + o.due.slice(5), cls: "" };
    if (diff < 0) return { text: "逾期 " + Math.abs(diff) + " 天", cls: "due--over" };
    if (diff === 0) return { text: "今日到期", cls: "due--today" };
    return { text: "尚餘 " + diff + " 天", cls: "" };
  }
  function isOverdue(o) { return o.status !== "done" && dayDiff(o.due) < 0; }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  // ---- 篩選 ----
  function applyFilters() {
    var q = filters.search.trim().toLowerCase();
    return orders.filter(function (o) {
      if (filters.zone && o.zone !== filters.zone) return false;
      if (filters.priority && o.priority !== filters.priority) return false;
      if (filters.status && o.status !== filters.status) return false;
      if (filters.overdue && !isOverdue(o)) return false;
      if (q) {
        var hay = (o.id + " " + o.title + " " + o.assignee + " " + o.zone).toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    });
  }

  // ---- 摘要指標 ----
  function renderMetrics() {
    var wrap = document.getElementById("metrics");
    wrap.textContent = "";
    var overdue = orders.filter(isOverdue).length;
    var high = orders.filter(function (o) { return o.priority === "high" && o.status !== "done"; }).length;
    var active = orders.filter(function (o) { return o.status === "active"; }).length;
    var total = orders.length;
    var data = [
      { v: overdue, l: "逾期工單", cls: "metric--alert" },
      { v: high, l: "高優先待辦", cls: "metric--high" },
      { v: active, l: "處理中", cls: "metric--active" },
      { v: total, l: "工單總數", cls: "" }
    ];
    data.forEach(function (m) {
      var li = el("li", "metric " + m.cls);
      li.appendChild(el("div", "metric__value", String(m.v)));
      li.appendChild(el("div", "metric__label", m.l));
      wrap.appendChild(li);
    });
  }

  // ---- 列表 ----
  function renderList() {
    var list = document.getElementById("work-list");
    var empty = document.getElementById("empty-state");
    var count = document.getElementById("result-count");
    var rows = applyFilters();

    list.textContent = "";
    count.textContent = "顯示 " + rows.length + " / " + orders.length + " 筆工單";

    if (rows.length === 0) {
      empty.hidden = false;
      list.hidden = true;
      return;
    }
    empty.hidden = true;
    list.hidden = false;

    rows.forEach(function (o) {
      var st = STATUS[o.status], pr = PRIORITY[o.priority], du = dueInfo(o);
      var li = el("li");
      var btn = el("button", "wo wo--" + o.priority);
      btn.type = "button";
      btn.setAttribute("aria-current", o.id === selectedId ? "true" : "false");
      btn.dataset.id = o.id;

      btn.appendChild(el("span", "wo__rail"));

      var main = el("div", "wo__main");
      main.appendChild(el("div", "wo__id", o.id + " · " + pr.label + "優先"));
      main.appendChild(el("div", "wo__title", o.title));
      var meta = el("div", "wo__meta");
      meta.appendChild(el("span", null, o.zone));
      meta.appendChild(el("span", null, "負責：" + o.assignee));
      main.appendChild(meta);
      btn.appendChild(main);

      var aside = el("div", "wo__aside");
      aside.appendChild(el("span", "chip chip--" + st.cls, st.label));
      aside.appendChild(el("span", "due " + du.cls, du.text));
      if (o.syncError) {
        var sf = el("span", "sync-flag");
        sf.appendChild(el("span", null, "⚠ 同步失敗"));
        aside.appendChild(sf);
      }
      btn.appendChild(aside);

      btn.addEventListener("click", function () { selectOrder(o.id, btn); });
      li.appendChild(btn);
      list.appendChild(li);
    });
  }

  // ---- 詳情 ----
  function findOrder(id) {
    for (var i = 0; i < orders.length; i++) if (orders[i].id === id) return orders[i];
    return null;
  }

  function selectOrder(id, rowEl) {
    selectedId = id;
    lastFocusedRow = rowEl || null;
    renderList();
    renderDetail();
    if (mobileQuery.matches) openMobileDetail();
    else {
      var h = document.getElementById("detail-heading");
      if (h) h.focus();
    }
  }

  function renderDetail() {
    var placeholder = document.getElementById("detail-empty");
    var body = document.getElementById("detail-body");
    var o = findOrder(selectedId);
    if (!o) {
      placeholder.hidden = false;
      body.hidden = true;
      body.textContent = "";
      return;
    }
    placeholder.hidden = true;
    body.hidden = false;
    body.textContent = "";

    var st = STATUS[o.status], pr = PRIORITY[o.priority], du = dueInfo(o);

    // 手機用關閉列
    var closebar = el("div", "detail__closebar");
    var back = el("button", "btn btn--ghost");
    back.type = "button";
    back.textContent = "← 返回工單列表";
    back.addEventListener("click", closeMobileDetail);
    closebar.appendChild(back);
    body.appendChild(closebar);

    body.appendChild(el("p", "detail__id", o.id + " · " + o.zone));
    var h = el("h2", "detail__title", o.title);
    h.id = "detail-heading";
    h.tabIndex = -1;
    body.appendChild(h);

    // 錯誤／復原狀態
    if (o.syncError) {
      var banner = el("div", "error-banner");
      var t = el("div", "error-banner__t", "⚠ 上次狀態更新未成功");
      banner.appendChild(t);
      banner.appendChild(el("p", "error-banner__b",
        "此工單的變更僅保存在本機，尚未套用。可重試以在本機重新套用，稍後再由系統同步。"));
      var retry = el("button", "btn btn--primary");
      retry.type = "button";
      retry.textContent = "在本機重試套用";
      retry.style.justifySelf = "start";
      retry.addEventListener("click", function () {
        o.syncError = false;
        renderList();
        renderDetail();
        notify("已於本機重新套用變更（尚未同步至伺服器）。");
        var hd = document.getElementById("detail-heading");
        if (hd) hd.focus();
      });
      banner.appendChild(retry);
      body.appendChild(banner);
    }

    var facts = el("div", "detail__facts");
    facts.appendChild(fact("優先度", pr.label));
    facts.appendChild(fact("目前狀態", st.label));
    var dueFact = fact("到期", du.text);
    if (du.cls) dueFact.querySelector(".fact__v").classList.add(du.cls);
    facts.appendChild(dueFact);
    facts.appendChild(fact("目前負責人", o.assignee));
    body.appendChild(facts);

    body.appendChild(el("p", "detail__desc", o.desc));

    // 更新表單
    var form = el("form", "update-form");
    form.setAttribute("aria-label", "更新工單負責人與狀態");
    form.appendChild(el("h3", null, "更新指派與狀態"));

    var f1 = el("div", "field");
    var l1 = el("label", null, "負責人");
    l1.setAttribute("for", "u-assignee");
    var s1 = el("select");
    s1.id = "u-assignee";
    s1.name = "assignee";
    [UNASSIGNED].concat(ASSIGNEES).forEach(function (a) {
      var op = el("option", null, a); op.value = a;
      if (a === o.assignee) op.selected = true;
      s1.appendChild(op);
    });
    f1.appendChild(l1); f1.appendChild(s1);

    var f2 = el("div", "field");
    var l2 = el("label", null, "處理狀態");
    l2.setAttribute("for", "u-status");
    var s2 = el("select");
    s2.id = "u-status";
    s2.name = "status";
    Object.keys(STATUS).forEach(function (k) {
      var op = el("option", null, STATUS[k].label); op.value = k;
      if (k === o.status) op.selected = true;
      s2.appendChild(op);
    });
    f2.appendChild(l2); f2.appendChild(s2);

    form.appendChild(f1);
    form.appendChild(f2);

    var feedback = el("p", "detail__feedback");
    feedback.id = "u-feedback";
    feedback.setAttribute("role", "status");
    feedback.setAttribute("aria-live", "polite");

    var actions = el("div", "update-form__actions");
    var save = el("button", "btn btn--primary");
    save.type = "submit";
    save.textContent = "儲存變更（本機）";
    actions.appendChild(save);
    form.appendChild(actions);
    form.appendChild(feedback);

    // 任一欄位變更即清除舊的成功訊息，避免過期狀態殘留
    function clearFeedback() { feedback.classList.remove("is-shown"); feedback.textContent = ""; }
    s1.addEventListener("change", clearFeedback);
    s2.addEventListener("change", clearFeedback);

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      o.assignee = s1.value;
      o.status = s2.value;
      renderMetrics();
      renderList();
      // 保留選取並更新事實區塊
      updateFactsInline(o);
      feedback.textContent = "✓ 已於本機更新：負責人為 " + o.assignee + "，狀態為 " + STATUS[o.status].label + "。（demo 狀態，未送出網路請求）";
      feedback.classList.add("is-shown");
      notify("工單 " + o.id + " 已於本機更新。");
    });

    body.appendChild(form);
  }

  function fact(k, v) {
    var d = el("div", "fact");
    d.appendChild(el("div", "fact__k", k));
    d.appendChild(el("div", "fact__v", v));
    return d;
  }

  function updateFactsInline(o) {
    // 重繪事實區塊中的狀態與負責人（不重建整個表單，保留焦點）
    var body = document.getElementById("detail-body");
    var facts = body.querySelector(".detail__facts");
    if (!facts) return;
    var vals = facts.querySelectorAll(".fact__v");
    // 順序：優先度, 狀態, 到期, 負責人
    if (vals[1]) vals[1].textContent = STATUS[o.status].label;
    if (vals[3]) vals[3].textContent = o.assignee;
    var du = dueInfo(o);
    if (vals[2]) { vals[2].textContent = du.text; vals[2].className = "fact__v" + (du.cls ? " " + du.cls : ""); }
  }

  // ---- 手機詳情層 ----
  function openMobileDetail() {
    var detail = document.getElementById("detail");
    detail.classList.add("is-open");
    document.body.classList.add("detail-open");
    var h = document.getElementById("detail-heading");
    if (h) h.focus();
    document.addEventListener("keydown", onDetailKeydown);
  }
  function closeMobileDetail() {
    var detail = document.getElementById("detail");
    detail.classList.remove("is-open");
    document.body.classList.remove("detail-open");
    document.removeEventListener("keydown", onDetailKeydown);
    if (lastFocusedRow && document.contains(lastFocusedRow)) lastFocusedRow.focus();
  }
  function onDetailKeydown(e) {
    if (e.key === "Escape") { e.preventDefault(); closeMobileDetail(); }
  }
  // 由手機切回桌機時，確保詳情層狀態一致
  mobileQuery.addEventListener("change", function (e) {
    if (!e.matches) {
      document.getElementById("detail").classList.remove("is-open");
      document.body.classList.remove("detail-open");
      document.removeEventListener("keydown", onDetailKeydown);
    }
  });

  // ---- Toast ----
  var toastTimer = null;
  function notify(msg) {
    var t = document.getElementById("toast");
    t.textContent = msg;
    t.classList.add("is-shown");
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove("is-shown"); }, 3200);
  }

  // ---- 篩選控制 ----
  function initFilters() {
    var zoneSel = document.getElementById("f-zone");
    var opt = el("option", null, "全部區域"); opt.value = "";
    zoneSel.appendChild(opt);
    ZONES.forEach(function (z) { var o = el("option", null, z); o.value = z; zoneSel.appendChild(o); });

    var search = document.getElementById("f-search");
    search.addEventListener("input", function (e) {
      if (e.isComposing) return; // 尊重中文 IME 組字
      filters.search = search.value;
      renderList();
    });
    search.addEventListener("compositionend", function () {
      filters.search = search.value;
      renderList();
    });

    document.getElementById("f-zone").addEventListener("change", function (e) { filters.zone = e.target.value; renderList(); });
    document.getElementById("f-priority").addEventListener("change", function (e) { filters.priority = e.target.value; renderList(); });
    document.getElementById("f-status").addEventListener("change", function (e) { filters.status = e.target.value; renderList(); });
    document.getElementById("f-overdue").addEventListener("change", function (e) { filters.overdue = e.target.checked; renderList(); });

    document.getElementById("clear-filters").addEventListener("click", clearFilters);
    document.getElementById("empty-clear").addEventListener("click", clearFilters);
  }

  function clearFilters() {
    filters = { search: "", zone: "", priority: "", status: "", overdue: false };
    document.getElementById("f-search").value = "";
    document.getElementById("f-zone").value = "";
    document.getElementById("f-priority").value = "";
    document.getElementById("f-status").value = "";
    document.getElementById("f-overdue").checked = false;
    renderList();
    notify("已清除所有篩選條件。");
  }

  // ---- 啟動 ----
  initFilters();
  renderMetrics();
  renderList();
  renderDetail();
})();
