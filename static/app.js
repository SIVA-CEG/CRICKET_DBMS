document.addEventListener("DOMContentLoaded", () => {
  const animated = document.querySelectorAll(".animate-on-load");
  animated.forEach(el => el.classList.add("animate__animated", "animate__fadeInUp"));
});
