
function showSignup() {
  document.getElementById("loginForm").classList.add("hidden");
  document.getElementById("signupForm").classList.remove("hidden");
  document.getElementById("message").innerText = "";
}

function showLogin() {
  document.getElementById("signupForm").classList.add("hidden");
  document.getElementById("loginForm").classList.remove("hidden");
  document.getElementById("message").innerText = "";
}

function signup(event) {
  event.preventDefault();

  const name = document.getElementById("signupName").value;
  const email = document.getElementById("signupEmail").value;

  document.getElementById("message").innerText =
    "Account created successfully for " + name + " 🎉";

  showLogin();
}

function login(event) {
  event.preventDefault();

  const email = document.getElementById("loginEmail").value;

  document.getElementById("message").innerText =
    "Welcome back, " + email + " 🚀";
}