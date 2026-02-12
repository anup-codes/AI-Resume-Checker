const BASE_URL = "http://127.0.0.1:8000/api/accounts/";

// ===============================
// CHECK LOGIN ON PAGE LOAD
// ===============================
document.addEventListener("DOMContentLoaded", function () {
  const token = localStorage.getItem("access_token");

  if (!token) {
    // No token → go back to login page
    window.location.href = "login.html";
  } else {
    loadDashboard();
  }
});


// ===============================
// LOAD PROTECTED DASHBOARD
// ===============================
async function loadDashboard() {
  const token = localStorage.getItem("access_token");

  try {
    const response = await fetch(BASE_URL + "dashboard/", {
      method: "GET",
      headers: {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
      },
    });

    if (response.status === 401) {
      // Token expired or invalid
      logout();
      return;
    }

    const data = await response.json();

    // Show welcome message
    const welcomeElement = document.getElementById("welcomeMessage");
    if (welcomeElement) {
      welcomeElement.innerText = data.message;
    }

  } catch (error) {
    console.log("Error loading dashboard:", error);
  }
}


// ===============================
// LOGOUT FUNCTION
// ===============================
function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");

  window.location.href = "login.html";
}
