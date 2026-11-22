(() => {
  "use strict";
  const doc = document;
  const byId = (id) => doc.getElementById(id);
  const standalone = doc.body.dataset.standalone === "true";
  const form = byId("enquiry");
  // Old links to organised events now open their records on Service.
  const movedEvents = new Map([
    ["talks--organised", "service--event-organization"],
    ["talks--ecml-diversity", "service--ecml-diversity"],
    ["talks--ecml-womens-night", "service--ecml-womens-night"],
    ["talks--elsa-tradeoffs", "service--elsa-tradeoffs"],
  ]);
  function followMovedEvent() {
    const destination = movedEvents.get(location.hash.slice(1));
    if (!destination) return false;
    location.replace((standalone ? "" : "service.html") + "#" + destination);
    return true;
  }
  function applyInterest(value) {
    if (!form || !value) return;
    if (
      Array.from(form.elements.topic.options).some(
        (option) => option.value === value,
      )
    ) {
      form.elements.topic.value = value;
      byId("draft").hidden = true;
    }
  }
  function showPage(focus) {
    if (followMovedEvent()) return;
    const [target = "home", query = ""] = location.hash.slice(1).split("?");
    const element = byId(target);
    const panel = element?.closest("[data-page]") || byId("home");
    for (const page of doc.querySelectorAll("[data-page]"))
      page.hidden = page !== panel;
    for (const nav of doc.querySelectorAll("[data-nav]")) {
      if (nav.dataset.nav === panel.dataset.page)
        nav.setAttribute("aria-current", "page");
      else nav.removeAttribute("aria-current");
    }
    doc.title =
      panel.dataset.page === "home"
        ? "Rūta Binkytė · AI Bias & Safety"
        : panel.querySelector("h1").textContent + " · Rūta Binkytė";
    applyInterest(new URLSearchParams(query).get("interest"));
    if (focus) {
      const active =
        target === "main"
          ? byId("main")
          : element && element !== panel
            ? element
            : panel.querySelector("h1");
      active.tabIndex = -1;
      active.focus({ preventScroll: true });
      if (element && element !== panel) active.scrollIntoView();
      else window.scrollTo(0, 0);
    }
  }
  if (standalone) {
    const choices = byId("design-options");
    choices.hidden = false;
    choices.querySelectorAll("input:checked").forEach(input => {
      doc.body.dataset[input.name] = input.value;
    });
    choices.addEventListener("change", event => {
      const input = event.target;
      if (input.type === "radio") doc.body.dataset[input.name] = input.value;
    });
    choices.addEventListener("keydown", event => {
      if (event.key === "Escape" && choices.open) {
        choices.open = false;
        choices.querySelector("summary").focus();
      }
    });
    showPage(false);
    window.addEventListener("hashchange", () => showPage(true));
    doc.querySelector(".skip").addEventListener("click", (event) => {
      event.preventDefault();
      byId("main").focus();
    });
  } else {
    followMovedEvent();
    window.addEventListener("hashchange", followMovedEvent);
    applyInterest(new URLSearchParams(location.search).get("interest"));
  }

  const search = byId("paper-search");
  if (search) {
    doc.querySelector(".filters").hidden = false;
    const year = byId("paper-year");
    const fold = (text) =>
      text
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase();
    function filter() {
      const terms = fold(search.value.trim()).split(/\s+/).filter(Boolean);
      let count = 0;
      for (const group of doc.querySelectorAll(".yeargroup")) {
        let visible = 0;
        for (const article of group.querySelectorAll(".paper")) {
          const haystack = fold(article.textContent + " " + article.dataset.aliases);
          article.hidden =
            !!(year.value && group.dataset.year !== year.value) ||
            !terms.every((term) => haystack.includes(term));
          if (!article.hidden) visible++;
        }
        group.hidden = !visible;
        count += visible;
      }
      byId("matches").textContent =
        count + (count === 1 ? " paper" : " papers");
      byId("no-papers").hidden = count !== 0;
    }
    search.addEventListener("input", filter);
    year.addEventListener("change", filter);
    filter();
  }
  if (form) {
    form.hidden = false;
    const draft = byId("draft");
    const preview = byId("draft-text");
    const status = byId("copy-status");
    let clipboardText = "";
    form.addEventListener("input", () => {
      draft.hidden = true;
      status.textContent = "";
    });
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const fields = form.elements;
      for (const key of ["name", "idea"]) {
        if (!fields[key].value.trim()) {
          fields[key].setCustomValidity("Please add a little detail here.");
          fields[key].reportValidity();
          fields[key].setCustomValidity("");
          return;
        }
      }
      const data = new FormData(form);
      const value = (field) => String(data.get(field)).trim();
      const subject = [value("kind"), value("topic"), value("name")].join(
        " · ",
      );
      const body = [
        "Dear Rūta,",
        "",
        "I’m writing about a possible collaboration.",
        "",
        "Collaboration format: " + value("kind"),
        "Research interest: " + value("topic"),
        "",
        value("idea"),
        "",
        "Best wishes,",
        value("name"),
        value("email"),
      ].join("\r\n");
      clipboardText =
        "To: " +
        form.dataset.recipient +
        "\r\nSubject: " +
        subject +
        "\r\n\r\n" +
        body;
      preview.textContent = clipboardText;
      byId("open-mail").href =
        "mailto:" +
        form.dataset.recipient +
        "?subject=" +
        encodeURIComponent(subject) +
        "&body=" +
        encodeURIComponent(body);
      draft.hidden = false;
      byId("draft-heading").focus();
    });
    byId("copy-mail").addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(clipboardText);
        status.textContent = "Message copied.";
      } catch {
        const range = doc.createRange();
        range.selectNodeContents(preview);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        status.textContent =
          "Message selected. Use your device’s Copy command.";
      }
    });
  }
})();
