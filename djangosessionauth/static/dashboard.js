const fileInput = document.getElementById("resume");
const fileText = document.getElementById("fileText");
const form = document.getElementById("resumeForm");

const scoreEl = document.getElementById("score");
const progress = document.getElementById("progress");
const summary = document.getElementById("summary");
const aiLoader = document.getElementById("aiLoader");
const roleSelect = document.getElementById("role");

/* ===============================
   FILE UPLOAD DISPLAY
=============================== */
fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    fileText.textContent = fileInput.files[0].name;
  }
});

/* ===============================
   SCORE ANIMATION
=============================== */
function animateScore(target) {
  let current = 0;
  const max = 314;
  progress.style.strokeDashoffset = max;

  const interval = setInterval(() => {
    if (current >= target) {
      clearInterval(interval);
      summary.textContent =
        "Your resume has been analyzed. Focus on keyword optimization and measurable impact.";
    } else {
      current++;
      scoreEl.textContent = current;
      progress.style.strokeDashoffset = max - (max * current) / 100;
    }
  }, 15);
}

/* ===============================
   FORM SUBMIT (REAL BACKEND)
=============================== */
form.addEventListener("submit", function (e) {
  e.preventDefault();

  const formData = new FormData(form);

  aiLoader.classList.remove("hidden");

  fetch("/upload-resume/", {
    method: "POST",
    body: formData,
    headers: {
      "X-CSRFToken": document.querySelector(
        '[name=csrfmiddlewaretoken]'
      ).value,
    },
  })
    .then((res) => res.json())
    .then((data) => {
      aiLoader.classList.add("hidden");

      if (data.status === "success") {
        animateScore(data.score);
      } else {
        alert(data.message);
      }
    })
    .catch(() => {
      aiLoader.classList.add("hidden");
      alert("Upload failed!");
    });
});

/* ===============================
   INSIGHT TOGGLE
=============================== */
const toggleInsights = document.getElementById("toggleInsights");
const insights = document.getElementById("insights");

toggleInsights.addEventListener("click", () => {
  insights.classList.toggle("hidden");
});
