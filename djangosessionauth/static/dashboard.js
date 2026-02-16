/* =========================================
   AI RESUME DASHBOARD CONTROLLER
   Clean • Tactical • SaaS-Ready
========================================= */

/* ===============================
   DOM REFERENCES
=============================== */
const fileInput = document.getElementById("resume");
const fileText = document.getElementById("fileText");
const form = document.getElementById("resumeForm");
const summary = document.getElementById("summary");
const aiLoader = document.getElementById("aiLoader");
const roleSelect = document.getElementById("role");
const toggleInsights = document.getElementById("toggleInsights");
const insights = document.getElementById("insights");
const themeToggle = document.getElementById("themeToggle");
const readinessValue = document.querySelector(".score-value");
const toast = document.getElementById("toast");

/* ===============================
   FILE NAME DISPLAY
=============================== */
if (fileInput && fileText) {
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      fileText.textContent = fileInput.files[0].name;
    }
  });
}

/* ===============================
   PREMIUM TOAST
=============================== */
function showToast(message) {
  if (!toast) return;

  toast.textContent = message;
  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 3000);
}

/* ===============================
   READINESS COUNTER ANIMATION
=============================== */
function animateReadiness(target) {
  if (!readinessValue) return;

  let current = 0;
  const duration = 1200;
  const startTime = performance.now();

  function update(time) {
    const progress = Math.min((time - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const value = Math.floor(eased * target);

    readinessValue.textContent = value + "%";

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  requestAnimationFrame(update);
}

/* ===============================
   AI TYPING EFFECT
=============================== */
function aiTyping(text) {
  if (!summary) return;

  summary.textContent = "";
  let index = 0;

  function type() {
    if (index < text.length) {
      summary.textContent += text[index];
      index++;
      setTimeout(type, 18);
    }
  }

  type();
}

/* ===============================
   ROLE-BASED ACCENT SYSTEM
=============================== */
if (roleSelect) {
  roleSelect.addEventListener("change", () => {
    const role = roleSelect.value.toLowerCase();
    let accent = "#F4B400"; // default gold

    if (role.includes("data")) accent = "#00C2FF";
    if (role.includes("frontend")) accent = "#00FF9C";
    if (role.includes("backend")) accent = "#FF5C8D";
    if (role.includes("devops")) accent = "#9C6BFF";
    if (role.includes("ml")) accent = "#FF8C00";

    document.documentElement.style.setProperty("--accent", accent);
  });
}

/* ===============================
   FORM SUBMIT HANDLER
=============================== */
if (form) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const button = document.getElementById("analyze");

    try {
      aiLoader?.classList.remove("hidden");
      button?.classList.add("loading");

      const response = await fetch("/upload-resume/", {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": document.querySelector(
            "[name=csrfmiddlewaretoken]"
          ).value,
        },
      });

      const data = await response.json();

      aiLoader?.classList.add("hidden");
      button?.classList.remove("loading");

      if (data.status === "success") {
        showToast("Analysis complete");
        animateReadiness(data.score);

        aiTyping(
          "Analysis complete. Optimize keyword density, add measurable achievements, and strengthen impact statements."
        );
      } else {
        showToast(data.message || "Analysis failed");
      }

    } catch (error) {
      aiLoader?.classList.add("hidden");
      button?.classList.remove("loading");
      showToast("Upload failed. Try again.");
    }
  });
}

/* ===============================
   INSIGHT TOGGLE
=============================== */
if (toggleInsights && insights) {
  toggleInsights.addEventListener("click", () => {
    insights.classList.toggle("hidden");
  });
}

/* ===============================
   DARK MODE TOGGLE
=============================== */
if (themeToggle) {
  themeToggle.addEventListener("change", () => {
    document.body.classList.toggle("light");
  });
}

/* ===============================
   METRIC AUTO COUNTERS
=============================== */
document.querySelectorAll("[data-count]").forEach((el) => {
  const target = +el.getAttribute("data-count");
  let current = 0;

  function update() {
    current += target / 60;

    if (current < target) {
      el.textContent = Math.floor(current);
      requestAnimationFrame(update);
    } else {
      el.textContent = target;
    }
  }

  update();
});
