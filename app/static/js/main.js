// Filter bar: auto-submit on select change
document.addEventListener("DOMContentLoaded", function () {
  const filterForm = document.querySelector(".filter-bar");
  if (filterForm) {
    filterForm.querySelectorAll("select").forEach(function (sel) {
      sel.addEventListener("change", function () { filterForm.submit(); });
    });
  }

  // Hamburger menu toggle
  const toggle = document.getElementById("navToggle");
  const wrap   = document.getElementById("headerNavWrap");
  if (toggle && wrap) {
    toggle.addEventListener("click", function () {
      const open = wrap.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open);
    });
  }

  // Close mobile nav when clicking outside
  document.addEventListener("click", function (e) {
    if (wrap && wrap.classList.contains("is-open") &&
        !wrap.contains(e.target) && !toggle.contains(e.target)) {
      wrap.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    }
  });
});
