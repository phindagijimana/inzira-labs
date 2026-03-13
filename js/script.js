const NIR_DOWNLOAD_URL = "https://github.com/phindagijimana/neuroinsight_research/releases";
const LICENSE_SERVICE_ENDPOINT =
  window.INZIRA_LICENSE_ENDPOINT || "https://license.inzira-labs.com/api/license/request";

function showPage(pageId) {
  document.querySelectorAll(".page").forEach((page) => page.classList.remove("active"));
  const page = document.getElementById(pageId);
  if (page) page.classList.add("active");
  window.scrollTo(0, 0);
}

function toggleMenu() {
  const menu = document.getElementById("nav-menu");
  menu.classList.toggle("active");
}

function closeMenu() {
  const menu = document.getElementById("nav-menu");
  menu.classList.remove("active");
}

function openLicenseModal(platformId) {
  document.getElementById("requested-platform").value = platformId;
  document.getElementById("form-status").textContent = "";
  document.getElementById("form-status").className = "form-status";
  document.getElementById("license-modal").classList.remove("hidden");
}

function closeLicenseModal() {
  document.getElementById("license-modal").classList.add("hidden");
}

async function submitLicenseRequest(event) {
  event.preventDefault();
  const statusEl = document.getElementById("form-status");
  const form = document.getElementById("license-form");
  const formData = new FormData(form);
  const payload = {
    requestedPlatform: formData.get("requestedPlatform"),
    name: formData.get("name"),
    email: formData.get("email"),
    institution: formData.get("institution"),
    purpose: formData.get("purpose"),
    source: "inzira-labs-landing",
    submittedAt: new Date().toISOString(),
  };

  statusEl.textContent = "Submitting license request...";
  statusEl.className = "form-status";

  try {
    const response = await fetch(LICENSE_SERVICE_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(
        `License service request failed with status ${response.status}. ${text}`.trim()
      );
    }
    localStorage.setItem("inziraLabsLastLicenseRequest", JSON.stringify(payload));

    statusEl.textContent = "License generated and emailed. Redirecting to download page...";
    statusEl.className = "form-status success";
    setTimeout(() => {
      window.location.href = NIR_DOWNLOAD_URL;
    }, 800);
  } catch (err) {
    statusEl.textContent = `Unable to submit request: ${err.message}`;
    statusEl.className = "form-status error";
  }
}

document.addEventListener("click", (event) => {
  const modal = document.getElementById("license-modal");
  const content = document.querySelector(".modal-content");
  if (!modal.classList.contains("hidden") && !content.contains(event.target) && event.target === modal) {
    closeLicenseModal();
  }
});
