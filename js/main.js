// Jahr im Footer
document.getElementById("year").textContent = new Date().getFullYear();

// Mobile-Menü
const toggle = document.querySelector(".nav-toggle");
const links = document.querySelector(".nav-links");
toggle.addEventListener("click", () => {
  const open = links.classList.toggle("open");
  toggle.setAttribute("aria-expanded", open);
});
links.querySelectorAll("a").forEach((a) =>
  a.addEventListener("click", () => links.classList.remove("open"))
);

// Elemente beim Scrollen einblenden
// (Auf der Startseite übernimmt js/motion.js die Animationen.)
if (!document.body.classList.contains("page-home")) {
const revealEls = document.querySelectorAll(".card, .quests li, .section-title, .cta");
revealEls.forEach((el) => el.classList.add("reveal"));
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.15 }
);
revealEls.forEach((el) => observer.observe(el));
}
