window.addEventListener('load', () => {
  const loader = document.getElementById('loader');
  const loaderShown = sessionStorage.getItem('loaderShown');
  if (loaderShown) {
    loader.style.display = 'none';
  } else {
    sessionStorage.setItem('loaderShown', 'true');
    setTimeout(() => {
      loader.classList.add('hidden');
      setTimeout(() => { loader.style.display = 'none'; }, 500);
    }, 700);
  }
});

function toggleTheme() {
  document.body.classList.toggle('dark-mode');
  const icon = document.querySelector('.theme-toggle i');
  icon.classList.toggle('fa-moon');
  icon.classList.toggle('fa-sun');
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function toggleGroup(btn) {
  const group = btn.closest('.hierarchy-group');
  group.classList.toggle('active');
}

function openGroup(index) {
  const groups = document.querySelectorAll('.hierarchy-group');
  groups.forEach((g, i) => {
    if (i === index) {
      g.classList.add('active');
    } else {
      g.classList.remove('active');
    }
  });
  const target = document.getElementById('sectors');
  if (target) target.scrollIntoView({ behavior: 'smooth' });
}

document.getElementById('globalSearch').addEventListener('input', function (e) {
  const query = e.target.value.toLowerCase();
  const groups = document.querySelectorAll('.hierarchy-group');
  groups.forEach(group => {
    const text = group.textContent.toLowerCase();
    if (text.includes(query)) {
      group.style.display = '';
      if (query.length > 0) group.classList.add('active');
    } else {
      group.style.display = 'none';
    }
  });
});

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth' });
  });
});

const style = document.createElement('style');
style.textContent = `@keyframes bounce { 0%, 100% { transform: translateX(-50%) translateY(0); } 50% { transform: translateX(-50%) translateY(-10px); } }`;
document.head.appendChild(style);

document.addEventListener("DOMContentLoaded", function () {
  const dailyEl = document.getElementById('daily-visits');
  const totalEl = document.getElementById('total-visits');
  if (!dailyEl || !totalEl) return;
  let daily = Math.floor(Math.random() * 10000 + 1000);
  let total = 3000000 + Math.floor(Math.random() * 50000);
  function updateCounter() {
    dailyEl.textContent = daily.toLocaleString('en-US');
    totalEl.textContent = total.toLocaleString('en-US');
  }
  updateCounter();
  setInterval(() => {
    daily += Math.floor(Math.random() * 10 + 1);
    total += Math.floor(Math.random() * 20 + 1);
    updateCounter();
  }, 1200);
});

function loadAnalytics() {
  if (window.analyticsLoaded) return;
  window.analyticsLoaded = true;
}
window.addEventListener('scroll', loadAnalytics, { once: true });
window.addEventListener('click', loadAnalytics, { once: true });

let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  document.querySelector('.pwa-badge').style.display = 'inline-flex';
  document.querySelector('.pwa-badge').addEventListener('click', async () => {
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    console.log(outcome);
    deferredPrompt = null;
  });
});

const filterBtns = document.querySelectorAll('.filter-btn');
const cards = document.querySelectorAll('.sector-card');
filterBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    filterBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const filter = btn.dataset.filter;
    cards.forEach(card => {
      const isNew = card.querySelector('.service-badge');
      if (filter === 'all') { card.style.display = ''; }
      else { card.style.display = isNew ? '' : 'none'; }
    });
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("newServicesBtn");
  const count = document.querySelectorAll(".sector-card[data-new='true']").length;
  if (count > 0) {
    btn.innerHTML = `<i class="fas fa-sparkles"></i> الخدمات الجديدة (${count})`;
  } else {
    btn.style.display = "none";
  }
});
