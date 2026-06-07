function toggleSidebarSub(btn) {
  const wrap = btn.closest('.sidebar-item-wrap');
  const sub = wrap.nextElementSibling;
  const isActive = btn.classList.toggle('active');
  if (isActive) {
    sub.style.maxHeight = sub.scrollHeight + 'px';
  } else {
    sub.style.maxHeight = '0';
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const searchInputs = document.querySelectorAll(".search-box");
  searchInputs.forEach(input => {
    input.addEventListener("input", function () {
      const query = this.value.toLowerCase().trim();
      const serviceItems = document.querySelectorAll(".service-item");
      serviceItems.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(query) ? "" : "none";
      });
    });
  });
});

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) target.scrollIntoView({ behavior: "smooth" });
  });
});
