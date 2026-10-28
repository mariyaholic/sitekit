// SPDX-License-Identifier: Apache-2.0
// Details disclosure for every room. Buttons handle Enter and Space natively.
(() => {
  for (const toggle of document.querySelectorAll(".room__toggle")) {
    const panelId = toggle.getAttribute("aria-controls");
    const panel = panelId ? document.getElementById(panelId) : null;
    if (!panel) {
      continue;
    }

    const setExpanded = (expanded) => {
      toggle.setAttribute("aria-expanded", String(expanded));
      panel.hidden = !expanded;
    };

    setExpanded(false);
    toggle.addEventListener("click", () => {
      setExpanded(toggle.getAttribute("aria-expanded") !== "true");
    });
  }
})();
