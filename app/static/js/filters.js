// Auto-submit filter form on select change (brand input still requires Enter/button)
document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector(".filter-bar");
  if (!form) return;
  form.querySelectorAll("select").forEach(function (sel) {
    sel.addEventListener("change", function () {
      form.submit();
    });
  });
});
