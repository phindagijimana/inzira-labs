const LICENSE_SERVICE_ENDPOINT =
  window.INZIRA_LICENSE_ENDPOINT || "https://license.inzira-labs.com/api/license/request";
const RECOMMENDED_LINKS_KEY = "inziraLabsRecommendedLinks";

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

function renderRecommendedLinksBox(targetEl, links, titleText) {
  if (!targetEl) return;
  if (!Array.isArray(links) || links.length === 0) {
    targetEl.classList.add("hidden");
    targetEl.innerHTML = "";
    return;
  }
  const items = links
    .map((item) => `<li><a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.name}</a></li>`)
    .join("");
  targetEl.innerHTML = `
    <h4>${titleText}</h4>
    <p>Use the platform helper first. It verifies checksums, then starts installation.</p>
    <ul>${items}</ul>
  `;
  targetEl.classList.remove("hidden");
}

function setDownloadsGate(links) {
  const statusEl = document.getElementById("downloads-gate-status");
  const linksEl = document.getElementById("downloads-unlocked-links");
  const unlocked = Array.isArray(links) && links.length > 0;
  if (!statusEl || !linksEl) return;
  if (!unlocked) {
    statusEl.textContent = "Downloads are locked until license form submission succeeds.";
    statusEl.className = "downloads-gate-status locked";
    renderRecommendedLinksBox(linksEl, [], "Verified NIR Install Links");
    return;
  }
  statusEl.textContent = "NIR downloads unlocked for this request. Use verified install links below.";
  statusEl.className = "downloads-gate-status unlocked";
  renderRecommendedLinksBox(linksEl, links, "Verified NIR Install Links");
}

function loadStoredRecommendedLinks() {
  try {
    const raw = localStorage.getItem(RECOMMENDED_LINKS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed.links) ? parsed.links : [];
  } catch (_err) {
    return [];
  }
}

function openLicenseModal(platformId, platformLabel = "Selected Platform") {
  document.getElementById("requested-platform").value = platformId;
  document.getElementById("requested-platform-label").value = platformLabel;
  document.getElementById("license-modal-title").textContent = `${platformLabel} License Request`;
  document.getElementById("form-status").textContent = "";
  document.getElementById("form-status").className = "form-status";
  const rec = document.getElementById("recommended-downloads");
  rec.classList.add("hidden");
  rec.innerHTML = "";
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
    requestedPlatformLabel: formData.get("requestedPlatformLabel"),
    name: formData.get("name"),
    email: formData.get("email"),
    institution: formData.get("institution"),
    purpose: formData.get("purpose"),
    source: "inzira-labs-landing",
    submittedAt: new Date().toISOString(),
  };

  statusEl.textContent = "Submitting license request...";
  statusEl.className = "form-status";
  const recEl = document.getElementById("recommended-downloads");
  recEl.classList.add("hidden");
  recEl.innerHTML = "";

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
    const result = await response.json().catch(() => ({}));
    localStorage.setItem("inziraLabsLastLicenseRequest", JSON.stringify(payload));
    statusEl.textContent =
      result.message ||
      "License generated and emailed. Check your inbox for secure download links.";
    statusEl.className = "form-status success";
    const recommendedLinks = Array.isArray(result.recommendedLinks) ? result.recommendedLinks : [];
    localStorage.setItem(
      RECOMMENDED_LINKS_KEY,
      JSON.stringify({ links: recommendedLinks, savedAt: new Date().toISOString() })
    );
    renderRecommendedLinksBox(recEl, recommendedLinks, "Recommended NIR Downloads (Verify then Install)");
    setDownloadsGate(recommendedLinks);
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

document.addEventListener("DOMContentLoaded", () => {
  setDownloadsGate(loadStoredRecommendedLinks());
});
