(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const escape = value => String(value).replace(/[&<>"']/g, char =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
  const message = $("message");
  function fail(text) {
    message.textContent = text;
    message.hidden = false;
  }
  let data;
  try {
    data = JSON.parse($("handbook-data").textContent);
    if (data.schema !== "ai-forward-handbook/1" || !Array.isArray(data.pages) || !data.pages.length
        || !Array.isArray(data.groups) || !Array.isArray(data.skill_groups)
        || !data.aliases || typeof data.aliases !== "object"
        || !data.pages.every(page => page && typeof page.id === "string"
          && typeof page.title === "string" && typeof page.markdown === "string")) {
      throw new Error("invalid handbook data");
    }
  } catch {
    fail("The handbook content could not be loaded. Reload the page, or read the plain-text overview linked below.");
    const link = document.createElement("a");
    link.href = "../handbook/overview.md";
    link.textContent = "Read the plain-text overview";
    $("article").append(link);
    return;
  }
  const pages = new Map(data.pages.map(page => [page.id, page]));
  const order = data.groups.flatMap(group => group.pages);
  document.querySelector(".skip").addEventListener("click", event => {
    event.preventDefault();
    $("content").focus();
    $("content").scrollIntoView();
  });
  function safeHref(value) {
    const href = String(value || "").trim();
    if (!href || /[\u0000-\u0020\u007f]/.test(href) || href.startsWith("//") || href.startsWith("\\")) return null;
    if (/^[a-z][a-z0-9+.-]*:/i.test(href) && !/^(https?:|mailto:)/i.test(href)) return null;
    return href;
  }
  let parser = null;
  if (window.marked && window.marked.Marked) {
    const renderer = new window.marked.Renderer();
    renderer.html = ({ text }) => escape(text);
    renderer.link = function ({ href, title, tokens }) {
      const text = this.parser.parseInline(tokens);
      const target = safeHref(href);
      return target ? `<a href="${escape(target)}"${title ? ` title="${escape(title)}"` : ""}>${text}</a>` : text;
    };
    renderer.image = ({ text }) => `<span>[Image not embedded: ${escape(text)}]</span>`;
    parser = new window.marked.Marked({ renderer, gfm: true, breaks: false });
  }
  function anchor(id, label) {
    const link = document.createElement("a");
    link.href = "#" + id;
    link.textContent = label;
    link.dataset.page = id;
    return link;
  }
  for (const group of data.groups) {
    const section = document.createElement("section");
    section.className = "nav-group";
    const heading = document.createElement("h2");
    heading.textContent = group.title;
    const list = document.createElement("ul");
    for (const id of group.pages) {
      const item = document.createElement("li");
      item.append(anchor(id, pages.get(id).title));
      list.append(item);
    }
    section.append(heading, list);
    $("chapters").append(section);
  }
  const skillHeading = document.createElement("h2");
  skillHeading.textContent = "Skill reference";
  $("skill-nav").className = "nav-group";
  $("skill-nav").append(skillHeading);
  for (const group of data.skill_groups) {
    const disclosure = document.createElement("details");
    disclosure.className = "skill-group";
    const summary = document.createElement("summary");
    summary.textContent = group.title;
    const list = document.createElement("ul");
    for (const name of group.skills) {
      const item = document.createElement("li");
      item.append(anchor("skill-" + name, "/" + name));
      list.append(item);
    }
    disclosure.append(summary, list);
    $("skill-nav").append(disclosure);
  }
  const mobile = matchMedia("(max-width:760px)");
  $("navigation").open = !mobile.matches;
  mobile.addEventListener("change", event => { $("navigation").open = !event.matches; });
  function clearSearch() {
    $("search").value = "";
    $("search-results").replaceChildren();
    $("search-results").hidden = true;
    $("search-status").textContent = "";
    $("clear-search").hidden = true;
  }
  $("search-form").addEventListener("submit", event => event.preventDefault());
  $("clear-search").addEventListener("click", () => { clearSearch(); $("search").focus(); });
  $("search").addEventListener("input", () => {
    const query = $("search").value.trim().toLowerCase();
    if (!query) { clearSearch(); return; }
    const terms = query.split(/\s+/);
    const results = data.pages.filter(page =>
      terms.every(term => `${page.title} ${page.summary} ${page.markdown}`.toLowerCase().includes(term)))
      .sort((a, b) => {
        const score = page => terms.reduce((sum, term) => sum + (page.title.toLowerCase().includes(term) ? 3 : 0)
          + (page.summary.toLowerCase().includes(term) ? 1 : 0), 0);
        return score(b) - score(a) || a.title.localeCompare(b.title, "en");
      });
    $("clear-search").hidden = false;
    $("search-results").hidden = false;
    $("search-results").replaceChildren();
    $("search-status").textContent = results.length
      ? `${results.length} matching ${results.length === 1 ? "page" : "pages"}`
      : "No matching guide. Try fewer words, or browse the workflow reference.";
    const list = document.createElement("ul");
    for (const page of results) {
      const item = document.createElement("li");
      const kind = document.createElement("span");
      kind.className = "search-kind";
      kind.textContent = page.kind === "skill" ? `Skill · /${page.skill}` : "Guide";
      const description = document.createElement("p");
      description.textContent = page.summary;
      item.append(kind, anchor(page.id, page.title), description);
      list.append(item);
    }
    $("search-results").append(list);
  });
  function render(focusContent = true) {
    clearSearch();
    let hash;
    try { hash = decodeURIComponent(location.hash.slice(1)) || "overview"; }
    catch { hash = ""; }
    const [requested, ...sectionParts] = hash.split("--");
    const id = data.aliases[requested] || requested;
    const page = pages.get(id);
    message.hidden = true;
    $("contents").replaceChildren();
    $("page-turn").replaceChildren();
    if (!page) {
      document.title = "Page not found · AI-Forward";
      $("page-context").textContent = "Find your next step";
      $("article").replaceChildren();
      const heading = document.createElement("h1");
      heading.textContent = "We could not find that handbook page";
      const explanation = document.createElement("p");
      explanation.textContent = "The address may have changed. Start with the overview or use search to find the topic.";
      $("article").append(heading, explanation, anchor("overview", "Open the handbook overview"));
      heading.tabIndex = -1;
      if (focusContent) heading.focus();
      return;
    }
    document.title = `${page.title} · AI-Forward`;
    $("page-context").textContent = page.kind === "skill" ? `Skill reference · /${page.skill}` : page.group;
    if (parser) {
      $("article").innerHTML = parser.parse(page.markdown);
    } else {
      fail("Formatting is unavailable. The complete plain-text guide is shown below.");
      const text = document.createElement("pre");
      text.className = "plain-fallback";
      text.textContent = page.markdown;
      $("article").replaceChildren(text);
    }
    for (const table of $("article").querySelectorAll("table")) {
      const wrapper = document.createElement("div");
      wrapper.className = "table-scroll";
      wrapper.tabIndex = 0;
      wrapper.setAttribute("role", "region");
      wrapper.setAttribute("aria-label", "Scrollable reference table");
      table.replaceWith(wrapper);
      wrapper.append(table);
    }
    const used = new Map();
    const tocTitle = document.createElement("p");
    tocTitle.textContent = "On this page";
    const tocList = document.createElement("ul");
    for (const heading of $("article").querySelectorAll("h2, h3")) {
      const base = heading.textContent.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
      const count = (used.get(base) || 0) + 1;
      used.set(base, count);
      heading.id = base + (count > 1 ? "-" + count : "");
      heading.tabIndex = -1;
      if (heading.tagName === "H2") {
        const item = document.createElement("li");
        item.append(anchor(id + "--" + heading.id, heading.textContent));
        tocList.append(item);
      }
    }
    $("contents").append(tocTitle, tocList);
    for (const link of document.querySelectorAll("#navigation a")) {
      if (link.dataset.page === id) {
        link.setAttribute("aria-current", "page");
        const disclosure = link.closest(".skill-group");
        if (disclosure) disclosure.open = true;
      } else { link.removeAttribute("aria-current"); }
    }
    if (page.kind === "skill") {
      $("page-turn").append(anchor("skills", "Back to the workflow chooser"), anchor(page.guide, "Read the related guide"));
    } else {
      const index = order.indexOf(id);
      if (index > 0) $("page-turn").append(anchor(order[index - 1], "Previous: " + pages.get(order[index - 1]).title));
      if (index < order.length - 1) $("page-turn").append(anchor(order[index + 1], "Next: " + pages.get(order[index + 1]).title));
    }
    if (mobile.matches) $("navigation").open = false;
    const target = sectionParts.length ? document.getElementById(sectionParts.join("--")) : $("article").querySelector("h1");
    if (target) {
      target.tabIndex = -1;
      if (focusContent) target.focus({ preventScroll: true });
      if (focusContent || sectionParts.length) target.scrollIntoView();
    }
  }
  addEventListener("hashchange", () => render(true));
  addEventListener("error", () => fail("Part of this page could not be displayed. Reload it, or use the plain-text guide links."));
  render(false);
})();
