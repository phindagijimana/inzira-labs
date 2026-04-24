const RECOMMENDED_LINKS_KEY = "inziraLabsRecommendedLinks";

function getLicenseServiceEndpoints() {
  if (Array.isArray(window.INZIRA_LICENSE_ENDPOINTS) && window.INZIRA_LICENSE_ENDPOINTS.length) {
    return window.INZIRA_LICENSE_ENDPOINTS.filter(Boolean);
  }
  if (window.INZIRA_LICENSE_ENDPOINT) {
    return [window.INZIRA_LICENSE_ENDPOINT];
  }
  return [
    "https://license.inzira-labs.com/api/license/request",
    "https://inzira-labs-license-service.onrender.com/api/license/request",
  ];
}

function showPage(pageId) {
  document.querySelectorAll(".page").forEach((page) => page.classList.remove("active"));
  const page = document.getElementById(pageId);
  if (page) page.classList.add("active");
  window.scrollTo(0, 0);
}

function goPage(pageId) {
  showPage(pageId);
  closeMenu();
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
    statusEl.textContent = "Verified install links are locked until a license request succeeds.";
    statusEl.className = "installers-gate-status locked";
    renderRecommendedLinksBox(linksEl, [], "Verified NIR install links");
    return;
  }
  statusEl.textContent = "NIR install links are unlocked for this request. Use verified links below.";
  statusEl.className = "installers-gate-status unlocked";
  renderRecommendedLinksBox(linksEl, links, "Verified NIR install links");
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
  const targetOs = document.getElementById("target-os");
  if (targetOs) targetOs.value = "";
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
    targetOS: formData.get("targetOS"),
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
    const endpoints = getLicenseServiceEndpoints();
    let response = null;
    let lastErr = null;
    for (const endpoint of endpoints) {
      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          response = res;
          break;
        }
        const text = await res.text();
        lastErr = new Error(
          `License service request failed with status ${res.status}. ${text}`.trim()
        );
      } catch (e) {
        lastErr = e;
      }
    }
    if (!response) {
      throw lastErr || new Error("No reachable license service endpoint.");
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
    const osLabel = (payload.targetOS || "").toString().trim().toLowerCase();
    const osMap = { linux: "Linux", windows: "Windows", macos: "macOS" };
    const osTitle = osMap[osLabel]
      ? `${osMap[osLabel]} — verified NIR installers (verify, then install)`
      : "Verified NIR installers (verify, then install)";
    renderRecommendedLinksBox(recEl, recommendedLinks, osTitle);
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
  const rawHash = (location.hash || "").replace(/^#/, "");
  if (rawHash === "join") {
    showPage("team");
    requestAnimationFrame(() => document.getElementById("join")?.scrollIntoView({ behavior: "smooth" }));
  } else if (rawHash === "platforms" || rawHash === "downloads") {
    showPage("rd");
    requestAnimationFrame(() => {
      document.getElementById("platforms")?.scrollIntoView({ behavior: "smooth" });
      history.replaceState(null, "", `${location.pathname}${location.search}#platforms`);
    });
  } else if (
    rawHash === "rd" ||
    rawHash === "publications" ||
    rawHash === "team" ||
    rawHash === "news" ||
    rawHash === "builder-review" ||
    rawHash === "home"
  ) {
    showPage(rawHash);
  }
  setDownloadsGate(loadStoredRecommendedLinks());
});
