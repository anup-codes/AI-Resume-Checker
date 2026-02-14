const signUpButton = document.getElementById("signUp");
const signInButton = document.getElementById("signIn");
const container = document.getElementById("container");

// Sliding
signUpButton.addEventListener("click", () => {
  container.classList.add("right-panel-active");
});

signInButton.addEventListener("click", () => {
  container.classList.remove("right-panel-active");
});

// Password toggle
document.querySelectorAll(".toggle-pass").forEach(icon => {
  icon.addEventListener("click", () => {
    const target = document.getElementById(icon.dataset.target);
    target.type = target.type === "password" ? "text" : "password";
  });
});

// Toast
function showToast(message, type) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = "toast show " + (type || "");

  setTimeout(() => {
    toast.className = "toast";
  }, 3000);
}

// AJAX Submit
document.querySelectorAll("form").forEach(form => {
  form.addEventListener("submit", function (e) {
    e.preventDefault();

    const button = form.querySelector(".auth-btn");
    button.classList.add("loading");
    button.disabled = true;

    const formData = new FormData(form);

    fetch("/auth/", {
      method: "POST",
      body: formData,
      headers: {
        "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
      }
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === "success") {

        // Smooth fade out
        document.body.style.opacity = "0";
        document.body.style.transition = "opacity 0.4s ease";

        setTimeout(() => {
          window.location.href = data.redirect;
        }, 400);

      } else {
        showToast(data.message, "error");
        button.classList.remove("loading");
        button.disabled = false;

        // If error in register → show register panel
        if (form.querySelector('[name="form_type"]').value === "register") {
          container.classList.add("right-panel-active");
        }
      }
    })
    .catch(() => {
      showToast("Something went wrong!", "error");
      button.classList.remove("loading");
      button.disabled = false;
    });

  });
});
