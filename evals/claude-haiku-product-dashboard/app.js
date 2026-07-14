// === Sample workorder data ===
const workorders = [
  {
    id: "WO-001",
    description: "A區碼頭配電盤檢查",
    area: "north",
    priority: "high",
    status: "open",
    deadline: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
    assignee: "alice",
    created: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
    isOverdue: true
  },
  {
    id: "WO-002",
    description: "B區照明系統維護",
    area: "south",
    priority: "high",
    status: "in-progress",
    deadline: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000),
    assignee: "bob",
    created: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
    isOverdue: false
  },
  {
    id: "WO-003",
    description: "C區安全護欄巡檢",
    area: "east",
    priority: "medium",
    status: "open",
    deadline: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000),
    assignee: "charlie",
    created: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
    isOverdue: false
  },
  {
    id: "WO-004",
    description: "D區消防設備檢驗",
    area: "west",
    priority: "high",
    status: "completed",
    deadline: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
    assignee: "diana",
    created: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000),
    isOverdue: false
  },
  {
    id: "WO-005",
    description: "A區排水系統清理",
    area: "north",
    priority: "medium",
    status: "open",
    deadline: new Date(Date.now() + 8 * 24 * 60 * 60 * 1000),
    assignee: "unassigned",
    created: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
    isOverdue: false
  },
  {
    id: "WO-006",
    description: "B區儲藏室庫存點檢",
    area: "south",
    priority: "low",
    status: "completed",
    deadline: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000),
    assignee: "alice",
    created: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    isOverdue: false
  },
  {
    id: "WO-007",
    description: "C區油漆補修",
    area: "east",
    priority: "low",
    status: "open",
    deadline: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000),
    assignee: "bob",
    created: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000),
    isOverdue: false
  },
  {
    id: "WO-008",
    description: "D區標誌檢查與更新",
    area: "west",
    priority: "medium",
    status: "in-progress",
    deadline: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000),
    assignee: "diana",
    created: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000),
    isOverdue: false
  }
];

// === Assignee labels ===
const assigneeLabels = {
  unassigned: "未指派",
  alice: "Alice 王",
  bob: "Bob 李",
  charlie: "Charlie 陳",
  diana: "Diana 黃"
};

const areaLabels = {
  north: "北區",
  south: "南區",
  east: "東區",
  west: "西區"
};

const statusLabels = {
  open: "待處理",
  "in-progress": "進行中",
  completed: "已完成"
};

const priorityLabels = {
  high: "高",
  medium: "中",
  low: "低"
};

// === State ===
let filteredWorkorders = [...workorders];
let currentDetailId = null;
const changes = {};

// === DOM References ===
const searchInput = document.getElementById("search-input");
const areaFilter = document.getElementById("area-filter");
const statusFilter = document.getElementById("status-filter");
const priorityFilter = document.getElementById("priority-filter");
const clearFiltersBtn = document.getElementById("clear-filters");
const filterToggle = document.getElementById("filter-toggle");
const filterControls = document.getElementById("filter-controls");
const resultMessage = document.getElementById("result-message");
const emptyState = document.getElementById("empty-state");
const workorderBody = document.getElementById("workorder-body");
const workorderTable = document.getElementById("workorder-table");
const detailOverlay = document.getElementById("detail-overlay");
const detailBackdrop = document.querySelector(".detail-backdrop");
const detailClose = document.getElementById("detail-close");
const detailCancel = document.getElementById("detail-cancel");
const detailSave = document.getElementById("detail-save");
const detailStatus = document.getElementById("detail-status");
const detailAssignee = document.getElementById("detail-assignee");
const detailSuccess = document.getElementById("detail-success");
const totalCount = document.getElementById("total-count");
const overdueCount = document.getElementById("overdue-count");
const urgentCount = document.getElementById("urgent-count");
const completedCount = document.getElementById("completed-count");
const errorSection = document.getElementById("error-section");
const errorDemo = document.getElementById("error-demo");
const errorClose = document.getElementById("error-close");
const errorDismiss = document.getElementById("error-dismiss");
const errorRetry = document.getElementById("error-retry");

// === Format date ===
function formatDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

// === Utility functions ===
function updateMetrics() {
  const total = workorders.length;
  const overdue = workorders.filter(w => w.isOverdue).length;
  const urgent = workorders.filter(w => w.priority === "high").length;
  const completed = workorders.filter(w => w.status === "completed").length;

  totalCount.textContent = total;
  overdueCount.textContent = overdue;
  urgentCount.textContent = urgent;
  completedCount.textContent = completed;
}

function updateResultCount() {
  const count = filteredWorkorders.length;
  if (count === 0) {
    resultMessage.textContent = "沒有符合的工單";
  } else {
    resultMessage.textContent = `顯示 ${count} 筆工單`;
  }
}

function applyFilters() {
  const searchTerm = searchInput.value.toLowerCase();
  const selectedArea = areaFilter.value;
  const selectedStatus = statusFilter.value;
  const selectedPriority = priorityFilter.value;

  filteredWorkorders = workorders.filter(wo => {
    const matchesSearch =
      wo.id.toLowerCase().includes(searchTerm) ||
      wo.description.toLowerCase().includes(searchTerm);
    const matchesArea = !selectedArea || wo.area === selectedArea;
    const matchesStatus = !selectedStatus || wo.status === selectedStatus;
    const matchesPriority = !selectedPriority || wo.priority === selectedPriority;

    return matchesSearch && matchesArea && matchesStatus && matchesPriority;
  });

  updateResultCount();
  renderWorkorders();
}

function clearAllFilters() {
  searchInput.value = "";
  areaFilter.value = "";
  statusFilter.value = "";
  priorityFilter.value = "";
  filteredWorkorders = [...workorders];
  updateResultCount();
  renderWorkorders();
}

// === Render workorder table ===
function renderWorkorders() {
  workorderBody.innerHTML = "";

  if (filteredWorkorders.length === 0) {
    workorderTable.style.display = "none";
    emptyState.style.display = "block";
    return;
  }

  workorderTable.style.display = "table";
  emptyState.style.display = "none";

  filteredWorkorders.forEach(wo => {
    const row = document.createElement("tr");

    const deadlineClass = wo.isOverdue ? "deadline-overdue" : "";
    const deadlineText = wo.isOverdue
      ? `${formatDate(wo.deadline)} (逾期)`
      : formatDate(wo.deadline);

    const statusBadgeClass = `status-badge status-${wo.status}`;
    const priorityBadgeClass = `priority-badge priority-${wo.priority}`;

    row.innerHTML = `
      <td data-label="工單編號">${wo.id}</td>
      <td data-label="描述">${wo.description}</td>
      <td data-label="區域">${areaLabels[wo.area]}</td>
      <td data-label="優先度"><span class="${priorityBadgeClass}">${priorityLabels[wo.priority]}</span></td>
      <td data-label="狀態"><span class="${statusBadgeClass}">${statusLabels[wo.status]}</span></td>
      <td data-label="期限" class="${deadlineClass}">${deadlineText}</td>
      <td data-label="負責人">${assigneeLabels[wo.assignee]}</td>
      <td data-label="操作"><button class="table-action-btn view-detail-btn" data-id="${wo.id}" aria-label="檢視 ${wo.id} 的詳情">詳情</button></td>
    `;

    workorderBody.appendChild(row);
  });

  // Attach event listeners to detail buttons
  document.querySelectorAll(".view-detail-btn").forEach(btn => {
    btn.addEventListener("click", e => {
      e.preventDefault();
      const id = btn.dataset.id;
      openDetail(id);
    });
  });
}

// === Detail view ===
function openDetail(id) {
  const wo = workorders.find(w => w.id === id);
  if (!wo) return;

  currentDetailId = id;
  changes[id] = {};

  document.getElementById("detail-id").textContent = wo.id;
  document.getElementById("detail-description").textContent = wo.description;
  document.getElementById("detail-area").textContent = areaLabels[wo.area];
  document.getElementById("detail-priority").textContent = priorityLabels[wo.priority];
  document.getElementById("detail-deadline").textContent = formatDate(wo.deadline);
  document.getElementById("detail-created").textContent = formatDate(wo.created);

  detailStatus.value = wo.status;
  detailAssignee.value = wo.assignee;
  detailSuccess.style.display = "none";

  detailOverlay.removeAttribute("hidden");
  detailStatus.focus();
}

function closeDetail() {
  detailOverlay.setAttribute("hidden", "");
  currentDetailId = null;
  changes[Object.keys(changes)[0]] = {};
  detailSuccess.style.display = "none";
}

function saveDetail() {
  if (!currentDetailId) return;

  const wo = workorders.find(w => w.id === currentDetailId);
  const newStatus = detailStatus.value;
  const newAssignee = detailAssignee.value;

  if (wo.status !== newStatus) {
    wo.status = newStatus;
  }
  if (wo.assignee !== newAssignee) {
    wo.assignee = newAssignee;
  }

  detailSuccess.style.display = "block";
  detailSuccess.setAttribute("role", "status");
  detailSuccess.setAttribute("aria-live", "polite");
  detailSuccess.setAttribute("aria-atomic", "true");

  setTimeout(() => {
    closeDetail();
    applyFilters();
    updateMetrics();
  }, 1200);
}

// === Error demo ===
function showErrorDemo() {
  errorDemo.removeAttribute("hidden");
  errorClose.focus();
}

function closeErrorDemo() {
  errorDemo.setAttribute("hidden", "");
}

// === Event listeners ===
searchInput.addEventListener("input", applyFilters);
areaFilter.addEventListener("change", applyFilters);
statusFilter.addEventListener("change", applyFilters);
priorityFilter.addEventListener("change", applyFilters);
clearFiltersBtn.addEventListener("click", clearAllFilters);

filterToggle.addEventListener("click", () => {
  const isOpen = filterControls.classList.contains("open");
  if (isOpen) {
    filterControls.classList.remove("open");
    filterToggle.setAttribute("aria-expanded", "false");
  } else {
    filterControls.classList.add("open");
    filterToggle.setAttribute("aria-expanded", "true");
  }
});

detailClose.addEventListener("click", closeDetail);
detailCancel.addEventListener("click", closeDetail);
detailSave.addEventListener("click", saveDetail);
detailBackdrop.addEventListener("click", closeDetail);

errorClose.addEventListener("click", closeErrorDemo);
errorDismiss.addEventListener("click", closeErrorDemo);
errorRetry.addEventListener("click", () => {
  closeErrorDemo();
  showErrorDemo();
});

// === Keyboard handlers ===
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && !detailOverlay.hasAttribute("hidden")) {
    closeDetail();
  }
  if (e.key === "Escape" && !errorDemo.hasAttribute("hidden")) {
    closeErrorDemo();
  }
});

// === Mobile filter handling ===
if (window.matchMedia("(max-width: 640px)").matches) {
  filterToggle.setAttribute("aria-expanded", "false");
} else {
  filterToggle.style.display = "none";
}

window.addEventListener("resize", () => {
  if (window.matchMedia("(max-width: 640px)").matches) {
    if (filterToggle.style.display === "none") {
      filterToggle.style.display = "flex";
    }
  } else {
    if (filterToggle.style.display === "flex") {
      filterToggle.style.display = "none";
      filterControls.classList.add("open");
    }
  }
});

// === Prevent form submission when user presses Enter in filters ===
searchInput.addEventListener("keydown", e => {
  if (e.key === "Enter") {
    e.preventDefault();
  }
});

// === Initialize ===
document.addEventListener("DOMContentLoaded", () => {
  updateMetrics();
  renderWorkorders();
});
