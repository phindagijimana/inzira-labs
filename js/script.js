const RECOMMENDED_LINKS_KEY = "inziraLabsRecommendedLinks";
const PLATFORM_LINK_SETS = "inziraLabsPlatformLinkSetsV1";

const PLATFORM_GATES = {
  "nir-desktop": {
    statusId: "downloads-gate-status",
    boxId: "downloads-unlocked-links",
    product: "NIR",
  },
  bidshub: {
    statusId: "bidshub-gate-status",
    boxId: "bidshub-unlocked-links",
    product: "BIDSHub",
  },
};

function loadAllPlatformLinks() {
  try {
    const raw = localStorage.getItem(PLATFORM_LINK_SETS);
    if (raw) {
      const o = JSON.parse(raw);
      return {
        "nir-desktop": Array.isArray(o["nir-desktop"]) ? o["nir-desktop"] : [],
        bidshub: Array.isArray(o.bidshub) ? o.bidshub : [],
      };
    }
    const oldRaw = localStorage.getItem(RECOMMENDED_LINKS_KEY);
    if (oldRaw) {
      const o = JSON.parse(oldRaw);
      const links = Array.isArray(o.links) ? o.links : [];
      const next = { "nir-desktop": links, bidshub: [] };
      localStorage.setItem(PLATFORM_LINK_SETS, JSON.stringify(next));
      return next;
    }
  } catch (_e) {
    /* ignore */
  }
  return { "nir-desktop": [], bidshub: [] };
}

function saveAllPlatformLinks(sets) {
  localStorage.setItem(PLATFORM_LINK_SETS, JSON.stringify(sets));
}

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
    <p>Follow any verification or checksum steps sent with these links before use.</p>
    <ul>${items}</ul>
  `;
  targetEl.classList.remove("hidden");
}

function setPlatformGate(platformId, links) {
  const g = PLATFORM_GATES[platformId];
  if (!g) return;
  const statusEl = document.getElementById(g.statusId);
  const linksEl = document.getElementById(g.boxId);
  if (!statusEl || !linksEl) return;
  const unlocked = Array.isArray(links) && links.length > 0;
  const lockedMessage =
    g.product === "BIDSHub"
      ? "Verified download links are locked until a license request succeeds."
      : "Verified install links are locked until a license request succeeds.";
  if (!unlocked) {
    statusEl.textContent = lockedMessage;
    statusEl.className = "installers-gate-status locked";
    renderRecommendedLinksBox(linksEl, [], `${g.product} — verified links`);
    return;
  }
  statusEl.textContent = `${g.product} links are unlocked for this request. Use verified links below.`;
  statusEl.className = "installers-gate-status unlocked";
  renderRecommendedLinksBox(linksEl, links, `Verified ${g.product} (verify, then use)`);
}

function applyAllPlatformGates() {
  const all = loadAllPlatformLinks();
  setPlatformGate("nir-desktop", all["nir-desktop"]);
  setPlatformGate("bidshub", all.bidshub);
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
    const platform = (payload.requestedPlatform || "").toString();
    const sets = loadAllPlatformLinks();
    if (platform === "nir-desktop") sets["nir-desktop"] = recommendedLinks;
    if (platform === "bidshub") sets.bidshub = recommendedLinks;
    saveAllPlatformLinks(sets);
    localStorage.setItem(
      RECOMMENDED_LINKS_KEY,
      JSON.stringify({ links: recommendedLinks, platform, savedAt: new Date().toISOString() })
    );
    const osLabel = (payload.targetOS || "").toString().trim().toLowerCase();
    const osMap = { linux: "Linux", windows: "Windows", macos: "macOS" };
    const productLabel = platform === "bidshub" ? "BIDSHub" : "NIR";
    const baseTitle = `verified ${productLabel} (verify, then use)`;
    const osTitle = osMap[osLabel] ? `${osMap[osLabel]} — ${baseTitle}` : `Verified ${productLabel} (verify, then use)`;
    renderRecommendedLinksBox(recEl, recommendedLinks, osTitle);
    applyAllPlatformGates();
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

function initBuilderReviewFullMd() {
  const details = document.getElementById("builder-review-ebm-doc");
  const pre = document.getElementById("builder-review-ebm-md");
  const loading = document.getElementById("builder-review-loading");
  const fallback = document.getElementById("builder-review-md-fallback");
  if (!details || !pre) return;
  const load = () => {
    if (details.dataset.ebmBrLoaded) return;
    if (details.dataset.ebmBrLoading) return;
    details.dataset.ebmBrLoading = "1";
    if (loading) {
      loading.hidden = false;
    }
    fetch("content/EBM_TLE_br.md", { cache: "no-cache" })
      .then((r) => {
        if (!r.ok) throw new Error("load failed");
        return r.text();
      })
      .then((text) => {
        pre.textContent = text;
        pre.hidden = false;
        details.dataset.ebmBrLoaded = "1";
        delete details.dataset.ebmBrLoading;
        if (loading) loading.hidden = true;
        if (fallback) fallback.hidden = true;
      })
      .catch(() => {
        delete details.dataset.ebmBrLoading;
        if (loading) loading.hidden = true;
        if (fallback) fallback.hidden = false;
      });
  };
  if (details.open) load();
  details.addEventListener("toggle", () => {
    if (details.open) load();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initBuilderReviewFullMd();
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
    rawHash === "research" ||
    rawHash === "team" ||
    rawHash === "news" ||
    rawHash === "builder-review" ||
    rawHash === "home"
  ) {
    showPage(rawHash === "publications" ? "research" : rawHash);
  }
  applyAllPlatformGates();
});
