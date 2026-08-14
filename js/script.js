const RECOMMENDED_LINKS_KEY = "inziraLabsRecommendedLinks";
const PLATFORM_LINK_SETS = "inziraLabsPlatformLinkSetsV1";

const PLATFORM_GATES = {
  "nir-desktop": {
    statusId: "downloads-gate-status",
    boxId: "downloads-unlocked-links",
    product: "NI",
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
    // Same-origin: when the site is served by the license backend (e.g. Railway),
    // this posts to the serving host with no hardcoded domain or CORS.
    "/api/license/request",
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
    const productLabel = platform === "bidshub" ? "BIDSHub" : "NI";
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

function initBuilderReviewMarkdown() {
  const renderMarkdown = (md) => {
    const m = window.marked;
    if (m && typeof m.setOptions === "function") {
      m.setOptions({ gfm: true, breaks: false });
    }
    const parse = m && (typeof m.parse === "function" ? m.parse.bind(m) : typeof m === "function" ? m : null);
    if (!parse) {
      return null;
    }
    const raw = parse(md);
    if (window.DOMPurify && typeof window.DOMPurify.sanitize === "function") {
      return window.DOMPurify.sanitize(raw);
    }
    return raw;
  };

  const bindOne = (details) => {
    const src = details.getAttribute("data-br-src");
    if (!src) return;
    const article = details.querySelector(".builder-review-article");
    if (!article) return;
    const loading = details.querySelector(".builder-review-loading");
    const fallback = details.querySelector(".builder-review-md-fallback");
    const load = () => {
      if (details.dataset.brLoaded) return;
      if (details.dataset.brLoading) return;
      details.dataset.brLoading = "1";
      if (loading) loading.hidden = false;
      fetch(src, { cache: "no-cache" })
        .then((r) => {
          if (!r.ok) throw new Error("load failed");
          return r.text();
        })
        .then((text) => {
          const html = renderMarkdown(text);
          if (html) {
            article.innerHTML = html;
          } else {
            const esc = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            article.innerHTML = `<pre class="builder-review-fallback-pre">${esc}</pre>`;
          }
          article.hidden = false;
          details.dataset.brLoaded = "1";
          delete details.dataset.brLoading;
          if (loading) loading.hidden = true;
          if (fallback) fallback.hidden = true;
        })
        .catch(() => {
          delete details.dataset.brLoading;
          if (loading) loading.hidden = true;
          if (fallback) fallback.hidden = false;
        });
    };
    if (details.open) load();
    details.addEventListener("toggle", () => {
      if (details.open) load();
    });
  };

  document.querySelectorAll("details.builder-review-details[data-br-src]").forEach(bindOne);
}

function initNewsSection() {
  const announcementsEl = document.getElementById("news-announcements");
  const catalogEl = document.getElementById("news-catalog");
  const metaEl = document.getElementById("news-catalog-meta");
  const filtersEl = document.getElementById("news-filters");
  const gridEl = document.getElementById("news-source-grid");
  const loadingEl = document.getElementById("news-catalog-loading");
  const errorEl = document.getElementById("news-catalog-error");
  const feedPanelEl = document.getElementById("news-feed-panel");
  const feedMetaEl = document.getElementById("news-feed-meta");
  const feedListEl = document.getElementById("news-feed-list");
  const feedMoreEl = document.getElementById("news-feed-more");
  if (!announcementsEl || !catalogEl || !gridEl) return;

  let feedItems = [];
  let activeFilter = "all";
  let feedExpanded = false;
  const FEED_PREVIEW = 10;

  const fetchJson = (path) =>
    fetch(path, { cache: "no-cache" }).then((r) => {
      if (!r.ok) throw new Error("load failed");
      return r.json();
    });

  const formatFeedUpdated = (iso) => {
    if (!iso) return "";
    const dt = new Date(iso);
    if (Number.isNaN(dt.getTime())) return "";
    return dt.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  };

  const renderFeed = () => {
    if (!feedPanelEl || !feedListEl) return;
    const filtered =
      activeFilter === "all" ? feedItems : feedItems.filter((item) => item.filter === activeFilter);
    const visible = feedExpanded ? filtered : filtered.slice(0, FEED_PREVIEW);

    if (feedMetaEl) {
      const updated = formatFeedUpdated(feedPanelEl.dataset.fetchedAt);
      feedMetaEl.textContent = updated
        ? `Updated ${updated} · ${filtered.length} headline${filtered.length === 1 ? "" : "s"}`
        : `${filtered.length} headline${filtered.length === 1 ? "" : "s"}`;
    }

    feedListEl.innerHTML = "";
    visible.forEach((item) => {
      const li = document.createElement("li");
      if (item.date) {
        const when = document.createElement("span");
        when.className = "news-feed-date";
        when.textContent = item.date;
        li.appendChild(when);
      }
      const a = document.createElement("a");
      a.href = item.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.className = "rd-link-ghost";
      a.textContent = item.title;
      li.appendChild(a);
      if (item.source) {
        const src = document.createElement("span");
        src.className = "news-feed-source";
        src.textContent = ` · ${item.source}`;
        li.appendChild(src);
      }
      feedListEl.appendChild(li);
    });

    if (feedMoreEl) {
      const showMore = filtered.length > FEED_PREVIEW;
      feedMoreEl.classList.toggle("hidden", !showMore);
      feedMoreEl.textContent = feedExpanded ? "Show fewer" : "Show more";
    }

    feedPanelEl.hidden = feedItems.length === 0;
  };

  const applyFilter = (filterId) => {
    activeFilter = filterId;
    feedExpanded = false;
    filtersEl.querySelectorAll(".news-filter").forEach((btn) => {
      const active = btn.dataset.filter === filterId;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });
    gridEl.querySelectorAll(".news-source-card").forEach((card) => {
      const show = filterId === "all" || card.dataset.filter === filterId;
      card.classList.toggle("is-hidden", !show);
    });
    renderFeed();
  };

  feedMoreEl?.addEventListener("click", () => {
    feedExpanded = !feedExpanded;
    renderFeed();
  });

  fetchJson("content/news-announcements.json")
    .then((items) => {
      announcementsEl.innerHTML = "";
      (Array.isArray(items) ? items : []).forEach((item) => {
        const li = document.createElement("li");
        li.className = "news-item";
        const dateLine = document.createElement("span");
        dateLine.className = "news-date";
        if (item.tag) {
          const tag = document.createElement("span");
          tag.className = "news-tag";
          tag.textContent = item.tag;
          dateLine.appendChild(tag);
        }
        dateLine.append(document.createTextNode(item.date || ""));
        const body = document.createElement("p");
        body.innerHTML = item.bodyHtml || "";
        li.append(dateLine, body);
        announcementsEl.appendChild(li);
      });
    })
    .catch(() => {
      announcementsEl.innerHTML =
        '<li class="news-item"><span class="news-date">Inzira Labs</span><p>Announcements could not be loaded.</p></li>';
    });

  fetchJson("content/news-sources.json")
    .then((data) => {
      const categories = Array.isArray(data.categories) ? data.categories : [];
      const filters = Array.isArray(data.filters) ? data.filters : [{ id: "all", label: "All" }];
      const totalLinks = categories.reduce((n, cat) => n + (cat.links?.length || 0), 0);

      if (metaEl) {
        metaEl.textContent = `${categories.length} categories · ${totalLinks} sources`;
      }

      filtersEl.innerHTML = "";
      filters.forEach((filter, index) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `news-filter${index === 0 ? " is-active" : ""}`;
        btn.textContent = filter.label;
        btn.dataset.filter = filter.id;
        btn.setAttribute("role", "tab");
        btn.setAttribute("aria-selected", index === 0 ? "true" : "false");
        filtersEl.appendChild(btn);
      });

      gridEl.innerHTML = "";
      categories.forEach((cat) => {
        const card = document.createElement("article");
        card.className = "news-source-card";
        card.dataset.filter = cat.filter || cat.id;

        const head = document.createElement("div");
        head.className = "news-source-card-head";
        const title = document.createElement("h4");
        title.textContent = cat.title || "";
        const badge = document.createElement("span");
        badge.className = "news-source-badge";
        badge.textContent = cat.badge || "Source";
        head.append(title, badge);

        const desc = document.createElement("p");
        desc.className = "news-source-desc";
        desc.textContent = cat.description || "";

        const meta = document.createElement("p");
        meta.className = "news-source-meta";
        const linkCount = cat.links?.length || 0;
        meta.textContent = `${linkCount} source${linkCount === 1 ? "" : "s"}`;

        card.append(head, desc, meta);

        if (linkCount) {
          const details = document.createElement("details");
          details.className = "news-source-details";
          const summary = document.createElement("summary");
          summary.textContent = "Browse links";
          const list = document.createElement("ul");
          list.className = "news-source-links";
          cat.links.forEach((link) => {
            const li = document.createElement("li");
            const a = document.createElement("a");
            a.href = link.url;
            a.target = "_blank";
            a.rel = "noopener noreferrer";
            a.className = "rd-link-ghost";
            a.textContent = link.label;
            li.appendChild(a);
            if (link.note) {
              const note = document.createElement("span");
              note.className = "news-source-link-note";
              note.textContent = ` (${link.note})`;
              li.appendChild(note);
            }
            list.appendChild(li);
          });
          details.append(summary, list);
          card.appendChild(details);
        }

        gridEl.appendChild(card);
      });

      filtersEl.addEventListener("click", (event) => {
        const btn = event.target.closest(".news-filter");
        if (!btn) return;
        applyFilter(btn.dataset.filter || "all");
      });

      loadingEl?.classList.add("hidden");
      catalogEl.hidden = false;
    })
    .catch(() => {
      loadingEl?.classList.add("hidden");
      errorEl?.classList.remove("hidden");
    });

  fetchJson("content/news-feed.json")
    .then((data) => {
      feedItems = Array.isArray(data.items) ? data.items : [];
      if (feedPanelEl && data.fetchedAt) {
        feedPanelEl.dataset.fetchedAt = data.fetchedAt;
      }
      renderFeed();
    })
    .catch(() => {
      feedItems = [];
      renderFeed();
    });
}

document.addEventListener("DOMContentLoaded", () => {
  initBuilderReviewMarkdown();
  initNewsSection();
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
