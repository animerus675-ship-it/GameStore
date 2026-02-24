(function () {
  var storageKey = "bbgame_theme";
  var root = document.documentElement;
  var toggleButton = document.getElementById("themeToggle");
  var toggleIcon = document.getElementById("themeToggleIcon");

  function setTheme(theme) {
    var isDark = theme === "dark";
    root.classList.toggle("theme-dark", isDark);
    if (toggleIcon) {
      toggleIcon.textContent = isDark ? "☀" : "🌙";
    }
    if (toggleButton) {
      toggleButton.setAttribute("title", isDark ? "Switch to light" : "Switch to dark");
      toggleButton.setAttribute("aria-label", isDark ? "Switch to light" : "Switch to dark");
    }
  }

  var savedTheme = null;
  try {
    savedTheme = localStorage.getItem(storageKey);
  } catch (error) {
    savedTheme = null;
  }

  setTheme(savedTheme === "dark" ? "dark" : "light");

  if (toggleButton) {
    toggleButton.addEventListener("click", function () {
      var nextTheme = root.classList.contains("theme-dark") ? "light" : "dark";
      setTheme(nextTheme);
      try {
        localStorage.setItem(storageKey, nextTheme);
      } catch (error) {
        // Ignore storage errors (private mode, blocked storage, etc.)
      }
    });
  }
})();
