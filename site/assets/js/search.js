/*
 * Lightweight client-side post search for the masthead search box.
 * Fetches /search.json once (on first focus), then live-filters by
 * title / tags / excerpt with simple case-insensitive substring matching.
 */
(function () {
  var input = document.getElementById("site-search-input");
  var results = document.getElementById("site-search-results");
  if (!input || !results) return;

  var index = null;
  var loading = false;

  function load() {
    if (index || loading) return;
    loading = true;
    fetch("/search.json", { credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (data) { index = data; render(input.value); })
      .catch(function () { loading = false; });
  }

  function escapeHtml(s) {
    return (s || "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function render(query) {
    if (!index) return;
    var q = (query || "").trim().toLowerCase();
    if (!q) {
      results.innerHTML = "";
      results.classList.remove("is-open");
      return;
    }
    var matches = index
      .filter(function (p) {
        var hay = (p.title + " " + (p.tags || []).join(" ") + " " + (p.excerpt || "")).toLowerCase();
        return hay.indexOf(q) !== -1;
      })
      .slice(0, 8);

    if (!matches.length) {
      results.innerHTML = '<li class="site-search__result site-search__result--empty">No matching posts</li>';
    } else {
      results.innerHTML = matches
        .map(function (p) {
          return (
            '<li class="site-search__result" role="option">' +
            '<a href="' + escapeHtml(p.url) + '">' +
            '<span class="site-search__result-title">' + escapeHtml(p.title) + "</span>" +
            '<span class="site-search__result-date">' + escapeHtml(p.date) + "</span>" +
            "</a></li>"
          );
        })
        .join("");
    }
    results.classList.add("is-open");
  }

  input.addEventListener("focus", load);
  input.addEventListener("input", function () { render(input.value); });
  input.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      input.value = "";
      render("");
      input.blur();
    }
  });

  // Close the dropdown when clicking outside the search widget.
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".site-search")) {
      results.classList.remove("is-open");
    }
  });
})();
