/* ===============================
   ELEMENT REFERENCES
=============================== */
const fileInput = document.getElementById("resume");
const fileText = document.getElementById("fileText");
const form = document.getElementById("resumeForm");

const scoreEl = document.getElementById("score");
const progress = document.getElementById("progress");
const summary = document.getElementById("summary");
const aiLoader = document.getElementById("aiLoader");
const roleSelect = document.getElementById("role");

const toggleInsights = document.getElementById("toggleInsights");
const insights = document.getElementById("insights");
const themeToggle = document.getElementById("themeToggle");

/* ===============================
   FILE UPLOAD DISPLAY
=============================== */
if (fileInput) {
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      fileText.textContent = fileInput.files[0].name;
    }
  });
}

/* ===============================
   PREMIUM TOAST SYSTEM
=============================== */
function showToast(message, type = "success") {
  const toast = document.getElementById("toast");
  if (!toast) return;

  toast.textContent = message;
  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 3000);
}

/* ===============================
   SMOOTH SCORE ANIMATION
=============================== */
function animateScore(target) {
  let start = 0;
  const duration = 1500;
  const max = 314;
  const startTime = performance.now();

  function update(currentTime) {
    const progressTime = currentTime - startTime;
    const percentage = Math.min(progressTime / duration, 1);

    const eased = 1 - Math.pow(1 - percentage, 3);
    const value = Math.floor(eased * target);

    scoreEl.textContent = value;
    progress.style.strokeDashoffset = max - (max * value) / 100;

    if (percentage < 1) {
      requestAnimationFrame(update);
    } else {
      aiTypingEffect(
        "Your resume has been analyzed successfully. Improve measurable achievements and optimize role-specific keywords."
      );
    }
  }

  requestAnimationFrame(update);
}

/* ===============================
   AI TYPING EFFECT
=============================== */
function aiTypingEffect(text) {
  if (!summary) return;

  summary.textContent = "";
  let index = 0;

  function type() {
    if (index < text.length) {
      summary.textContent += text.charAt(index);
      index++;
      setTimeout(type, 20);
    }
  }

  type();
}

/* ===============================
   METRIC COUNTERS (TOP CARDS)
=============================== */
document.querySelectorAll("[data-count]").forEach((counter) => {
  const target = +counter.getAttribute("data-count");
  let current = 0;

  const updateCounter = () => {
    const increment = target / 80;
    current += increment;

    if (current < target) {
      counter.innerText = Math.floor(current);
      requestAnimationFrame(updateCounter);
    } else {
      counter.innerText = target;
    }
  };

  updateCounter();
});

/* ===============================
   FORM SUBMIT (REAL BACKEND)
=============================== */
if (form) {
  form.addEventListener("submit", function (e) {
    e.preventDefault();

    const formData = new FormData(form);

    aiLoader?.classList.remove("hidden");

    const button = document.getElementById("analyze");
    button?.classList.add("loading");

    fetch("/upload-resume/", {
      method: "POST",
      body: formData,
      headers: {
        "X-CSRFToken": document.querySelector(
          "[name=csrfmiddlewaretoken]"
        ).value,
      },
    })
      .then((res) => res.json())
      .then((data) => {
        aiLoader?.classList.add("hidden");
        button?.classList.remove("loading");

        if (data.status === "success") {
          showToast("Resume analyzed successfully 🎯");
          animateScore(data.score);
        } else {
          showToast(data.message || "Something went wrong", "error");
        }
      })
      .catch(() => {
        aiLoader?.classList.add("hidden");
        button?.classList.remove("loading");
        showToast("Upload failed. Try again.");
      });
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
  themeToggle.addEventListener("change", function () {
    document.body.classList.toggle("light");
  });
}
