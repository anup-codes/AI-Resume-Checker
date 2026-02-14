const form = document.getElementById("resumeForm");
const toast = document.getElementById("toast");
const scoreCircle = document.querySelector(".score-circle");
const scoreValue = document.getElementById("scoreValue");
const scoreMessage = document.getElementById("scoreMessage");
const historyList = document.getElementById("resumeHistory");

function showToast(message, type) {
    toast.textContent = message;
    toast.className = "toast show " + type;
    setTimeout(() => toast.className = "toast", 3000);
}

function updateScore(score) {
    scoreValue.textContent = score + "%";
    scoreCircle.style.background =
        `conic-gradient(#4f46e5 ${score}%, #e5e7eb ${score}%)`;

    scoreMessage.textContent =
        score > 75 ? "Excellent Resume 🔥" :
        score > 50 ? "Good Resume 👍" :
        "Needs Improvement ⚠️";
}

form.addEventListener("submit", function(e) {
    e.preventDefault();

    const button = form.querySelector(".upload-btn");
    button.classList.add("loading");
    button.disabled = true;

    const formData = new FormData(form);

    fetch("/upload-resume/", {
        method: "POST",
        body: formData,
        headers: {
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            showToast(data.message, "success");

            // Fake AI Score (replace with real AI later)
            const randomScore = Math.floor(Math.random() * 40) + 60;
            updateScore(randomScore);

            // Add to history
            const li = document.createElement("li");
            li.textContent = "Resume uploaded - Score: " + randomScore + "%";
            historyList.prepend(li);

            form.reset();
        } else {
            showToast(data.message, "error");
        }

        button.classList.remove("loading");
        button.disabled = false;
    })
    .catch(() => {
        showToast("Upload failed!", "error");
        button.classList.remove("loading");
        button.disabled = false;
    });
});
