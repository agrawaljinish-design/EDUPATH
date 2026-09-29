/**
 * EduPath SaaS Client Engine
 * Centralized API client, session management, topbar live hydration, and struggle modal controller.
 */

const API_BASE = window.location.origin;

// Session Management
function getUserId() {
  let uid = localStorage.getItem("edupath_user_id");
  if (!uid) {
    uid = "user_" + Math.random().toString(36).substring(2, 9);
    localStorage.setItem("edupath_user_id", uid);
    localStorage.setItem("edupath_user_mode", "real");
  }
  return uid;
}

function getUserMode() {
  const uid = getUserId();
  return uid === "demo_learner" ? "demo" : "real";
}

function setDemoMode() {
  localStorage.setItem("edupath_user_id", "demo_learner");
  localStorage.setItem("edupath_user_mode", "demo");
}

function setRealUserMode(customId = null) {
  const uid = customId || "user_" + Math.random().toString(36).substring(2, 9);
  localStorage.setItem("edupath_user_id", uid);
  localStorage.setItem("edupath_user_mode", "real");
  return uid;
}

// Alias used in login.html
function setRealMode(customId = null) {
  return setRealUserMode(customId);
}

// Unified API Client
const api = {
  async get(endpoint) {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`);
      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errData.detail || `Request failed with status ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      console.error(`GET ${endpoint} error:`, err);
      showToast(err.message, "error");
      throw err;
    }
  },

  async post(endpoint, data = {}) {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errData.detail || `Request failed with status ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      console.error(`POST ${endpoint} error:`, err);
      showToast(err.message, "error");
      throw err;
    }
  },

  async upload(endpoint, formData) {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        body: formData
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errData.detail || `Upload failed with status ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      console.error(`UPLOAD ${endpoint} error:`, err);
      showToast(err.message, "error");
      throw err;
    }
  }
};

// UI Notification Toast
function showToast(message, type = "info") {
  let toastContainer = document.getElementById("edupathToastContainer");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "edupathToastContainer";
    toastContainer.style.position = "fixed";
    toastContainer.style.bottom = "24px";
    toastContainer.style.right = "24px";
    toastContainer.style.zIndex = "9999";
    toastContainer.style.display = "flex";
    toastContainer.style.flexDirection = "column";
    toastContainer.style.gap = "8px";
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement("div");
  toast.className = `alert-banner ${type === 'error' ? 'warning' : 'info'}`;
  toast.style.margin = "0";
  toast.style.boxShadow = "0 8px 24px rgba(0,0,0,0.5)";
  toast.style.minWidth = "280px";
  toast.innerHTML = `<span>${type === 'error' ? '⚠️' : '✨'} ${message}</span>`;

  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.4s";
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}

// Global Hydration on DOM Ready
document.addEventListener("DOMContentLoaded", async () => {
  const uid = getUserId();
  const userMode = getUserMode();

  // Highlight active nav item
  const currentPath = window.location.pathname.split("/").pop() || "index.html";
  const navLinks = document.querySelectorAll(".nav-menu a");
  navLinks.forEach(link => {
    const href = link.getAttribute("href");
    if (href === currentPath || (currentPath === "" && href === "index.html")) {
      link.parentElement.classList.add("active");
    } else {
      link.parentElement.classList.remove("active");
    }
  });

  // Hydrate Topbar Metrics
  try {
    const progressRes = await api.get(`/progress/${uid}`).catch(() => null);
    if (progressRes && progressRes.summary) {
      const streakEl = document.getElementById("topbarStreak");
      if (streakEl) streakEl.innerHTML = `🔥 ${progressRes.summary.streak}d`;

      const xpEl = document.getElementById("topbarXP");
      if (xpEl) xpEl.innerHTML = `⭐ ${progressRes.summary.total_xp.toLocaleString()} XP`;
    }

    const profileRes = await api.get(`/profile/${uid}`).catch(() => null);
    if (profileRes) {
      const nameEl = document.getElementById("topbarUserName");
      if (nameEl) nameEl.innerText = profileRes.name || "Learner";

      const avatarEl = document.getElementById("topbarAvatarText");
      if (avatarEl) {
        const initial = (profileRes.name || "L").charAt(0).toUpperCase();
        avatarEl.innerText = initial;
      }
    }
  } catch (e) {
    // Non-blocking fallback
  }

  // Hydrate Mode Indicator
  const modeBadge = document.getElementById("modeIndicator");
  if (modeBadge) {
    if (userMode === "demo") {
      modeBadge.className = "mode-badge demo";
      modeBadge.innerHTML = "🎯 Demo Mode (Alex Demo)";
    } else {
      modeBadge.className = "mode-badge real";
      modeBadge.innerHTML = `👤 Real Learner (${uid.substring(0, 8)})`;
    }
  }

  // Keyboard shortcut '/' for Search
  const searchInput = document.querySelector(".topbar-search-input");
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && document.activeElement !== searchInput) {
      if (searchInput) {
        e.preventDefault();
        searchInput.focus();
      }
    }
  });

  // Setup "I'm Stuck" Modal Controller
  setupStuckModal();
});

// "I'm Stuck" Adaptive Modal Setup
function setupStuckModal() {
  const stuckBtn = document.getElementById("btnImStuck");
  const stuckModal = document.getElementById("stuckModal");
  const stuckClose = document.getElementById("stuckModalClose");
  const stuckSubmit = document.getElementById("stuckFormSubmit");

  if (stuckBtn && stuckModal) {
    stuckBtn.addEventListener("click", () => {
      stuckModal.classList.add("active");
      // Auto populate skill if in demo mode
      const uid = getUserId();
      const skillInput = document.getElementById("stuckSkillInput");
      const topicInput = document.getElementById("stuckTopicInput");
      if (skillInput && !skillInput.value) {
        if (uid === "demo_learner") {
          skillInput.value = "SQL & Data Querying";
          if (topicInput) topicInput.value = "Multi-table JOINs";
        }
      }
    });
  }

  if (stuckClose && stuckModal) {
    stuckClose.addEventListener("click", () => {
      stuckModal.classList.remove("active");
    });
  }

  // Reason Chips Click
  const reasonChips = document.querySelectorAll(".stuck-reason-chip");
  reasonChips.forEach(chip => {
    chip.addEventListener("click", () => {
      reasonChips.forEach(c => c.classList.remove("selected"));
      chip.classList.add("selected");
      const hiddenInput = document.getElementById("stuckReasonChoice");
      if (hiddenInput) hiddenInput.value = chip.getAttribute("data-reason");
    });
  });

  if (stuckSubmit) {
    stuckSubmit.addEventListener("click", async (e) => {
      e.preventDefault();
      const skillInput = document.getElementById("stuckSkillInput");
      const topicInput = document.getElementById("stuckTopicInput");
      const reasonInput = document.getElementById("stuckReasonChoice");
      const resultBox = document.getElementById("stuckInterventionResult");
      const formBox = document.getElementById("stuckFormWrapper");

      const skill = skillInput ? skillInput.value.trim() : "";
      const topic = topicInput ? topicInput.value.trim() : "";
      const reason = reasonInput ? reasonInput.value : "Struggling with concept";

      if (!skill) {
        showToast("Please enter or select the skill you are stuck on.", "error");
        return;
      }

      stuckSubmit.disabled = true;
      stuckSubmit.innerText = "Diagnosing & Replanning Roadmap...";

      try {
        const res = await api.post("/struggle/detect", {
          user_id: getUserId(),
          skill: skill,
          topic: topic || "Core operations",
          details: reason
        });

        if (formBox) formBox.style.display = "none";

        if (resultBox) {
          resultBox.style.display = "block";
          resultBox.innerHTML = `
            <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 12px; padding: 20px; margin-top: 10px;">
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="font-size: 20px;">⚡</span>
                <h4 style="color: #FBBF24; font-size: 16px; font-weight: 700;">AI Detected a Learning Struggle</h4>
              </div>
              <p style="font-size: 13.5px; color: var(--text-primary); margin-bottom: 16px; line-height: 1.6;">
                ${res.event.explanation}
              </p>
              
              <div style="background: var(--bg-card); border: 1px solid var(--border-card); border-radius: 8px; padding: 14px; margin-bottom: 16px;">
                <div style="font-size: 11.5px; font-weight: 700; text-transform: uppercase; color: #34D399; margin-bottom: 8px; letter-spacing: 0.5px;">
                  EDUPATH WILL ADAPT YOUR PATH:
                </div>
                <div style="display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: var(--text-secondary);">
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="color: #34D399;">✓</span> Insert targeted revision module
                  </div>
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="color: #34D399;">✓</span> Provide low-friction guided micro-practice
                  </div>
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="color: #34D399;">✓</span> Schedule reassessment checkpoint
                  </div>
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="color: #34D399;">✓</span> Pause downstream modules until unblocked
                  </div>
                </div>
              </div>

              <!-- Before vs After Visualization -->
              <div style="background: var(--bg-surface); border: 1px solid var(--border-card); border-radius: 8px; padding: 14px; margin-bottom: 20px;">
                <div style="font-size: 12px; font-weight: 700; color: var(--text-muted); margin-bottom: 6px; text-transform: uppercase;">
                  Roadmap Comparison:
                </div>
                <div style="font-size: 12.5px; color: var(--text-muted); margin-bottom: 6px;">
                  <strong style="color: #94A3B8;">Before:</strong> ${res.event.before_roadmap_summary.join(" → ")}
                </div>
                <div style="font-size: 12.5px; color: #FBBF24;">
                  <strong style="color: #FBBF24;">After:</strong> ${res.event.after_roadmap_summary.join(" → ")}
                </div>
              </div>

              <div style="display: flex; gap: 12px;">
                <a href="plan.html" class="btn btn-primary" style="flex: 1; text-align: center;">
                  Start Easier Practice →
                </a>
                <a href="roadmap.html" class="btn btn-secondary" style="flex: 1; text-align: center;">
                  View Updated Roadmap
                </a>
              </div>
            </div>
          `;
        }
        showToast("Adaptive replanning complete! Path updated.", "info");
      } catch (err) {
        console.error(err);
      } finally {
        stuckSubmit.disabled = false;
        stuckSubmit.innerText = "Diagnose & Adapt Path ⚡";
      }
    });
  }
}
