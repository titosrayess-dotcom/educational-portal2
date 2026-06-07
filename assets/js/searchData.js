const searchData = [
  {
    "title": "التعليم الابتدائي",
    "desc": "مناهج التعليم الابتدائي، نتائج الامتحانات، فضاء الأولياء، التسجيلات المدرسية",
    "url": "sectors/primary.html",
    "keywords": ["ابتدائي", "تعليم", "مدرسة", "أولياء", "تسجيل", "امتحان", "منهاج", "طور أول", "طور ثاني", "طور ثالث"]
  },
  {
    "title": "التعليم المتوسط",
    "desc": "مناهج التعليم المتوسط، شهادة التعليم المتوسط BEM، فضاء الأستاذ والتلميذ",
    "url": "sectors/middle.html",
    "keywords": ["متوسط", "bem", "شهادة", "تعليم متوسط", "أستاذ", "تلميذ", "امتحان", "نتائج", "تسجيل"]
  },
  {
    "title": "التعليم الثانوي والبكالوريا",
    "desc": "شهادة البكالوريا، التسجيل في الامتحانات، نتائج البكالوريا، فضاء الأستاذ",
    "url": "sectors/secondary.html",
    "keywords": ["بكالوريا", "bac", "ثانوي", "شهادة", "نتائج", "تسجيل", "امتحان", "أستاذ", "تعليم ثانوي"]
  },
  {
    "title": "بنك الفروض والاختبارات",
    "desc": "جميع منصات الفروض والاختبارات للتعليم في الجزائر مع التصحيح",
    "url": "sectors/exam-compos.html",
    "keywords": ["فرض", "اختبار", "بنك", "تصحيح", "تمارين", "فروض", "اختبارات", "مراجعة", "دروس"]
  },
  {
    "title": "الخدمات الجامعية",
    "desc": "التسجيل الجامعي، منصة Progres، الإيواء الجامعي، التحويلات، المنح الجامعية",
    "url": "sectors/university.html",
    "keywords": ["جامعة", "progres", "mesrs", "طالب", "إيواء", "منحة", "تسجيل جامعي", "تحويل", "سكن جامعي", "ليسانس", "ماستر", "دكتوراه"]
  },
  {
    "title": "التكوين والتعليم المهني",
    "desc": "التسجيل في التكوين المهني، الامتحانات، التخصصات المهنية، شهادات التكوين",
    "url": "sectors/vocational.html",
    "keywords": ["تكوين", "مهني", "تعليم مهني", "mfp", "تسجيل", "امتحان", "حرفة", "مهنة", "تخصص"]
  },
];

const searchInput = document.getElementById("globalSearch");
const searchResults = document.getElementById("searchResults");

searchInput.addEventListener("input", function () {
  const query = this.value.trim().toLowerCase();
  searchResults.innerHTML = "";
  if (query.length < 2) {
    searchResults.style.display = "none";
    return;
  }
  const filtered = searchData.filter(item => {
    return (
      item.title.toLowerCase().includes(query) ||
      item.desc.toLowerCase().includes(query) ||
      item.keywords.some(keyword => keyword.toLowerCase().includes(query))
    );
  });
  if (filtered.length === 0) {
    searchResults.innerHTML = `<div class="no-results">لا توجد نتائج</div>`;
    searchResults.style.display = "block";
    return;
  }
  filtered.forEach(item => {
    searchResults.innerHTML += `
      <a href="${item.url}" class="search-result-item">
        <div class="search-result-icon"><i class="fas fa-search"></i></div>
        <div class="search-result-content">
          <h4>${item.title}</h4>
          <p>${item.desc}</p>
        </div>
      </a>`;
  });
  searchResults.style.display = "block";
});

document.addEventListener("click", (e) => {
  if (!e.target.closest(".search-container")) {
    searchResults.style.display = "none";
  }
});
