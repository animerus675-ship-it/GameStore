(function () {
  "use strict";

  var doc = document;

  function $(selector, root) {
    return (root || doc).querySelector(selector);
  }

  function $$(selector, root) {
    return Array.prototype.slice.call((root || doc).querySelectorAll(selector));
  }

  function normalizePath(pathname) {
    var path = pathname || "/";
    return path.length > 1 ? path.replace(/\/+$/, "") : path;
  }

  // 1) Toggle mobile menu by [data-burger] and [data-mobile-menu]
  var burger = $("[data-burger]");
  var mobileMenu = $("[data-mobile-menu]");
  if (burger && mobileMenu) {
    burger.addEventListener("click", function (event) {
      event.preventDefault();
      burger.classList.toggle("is-open");
      mobileMenu.classList.toggle("is-open");
    });
  }

  // 2) Highlight active nav item by current URL
  var currentPath = normalizePath(window.location.pathname);
  $$(".main-nav .nav a, [data-nav] a").forEach(function (link) {
    var href = link.getAttribute("href");
    if (!href || href.indexOf("javascript:") === 0 || href.charAt(0) === "#") {
      return;
    }
    var url;
    try {
      url = new URL(href, window.location.origin);
    } catch (error) {
      return;
    }
    var linkPath = normalizePath(url.pathname);
    if (linkPath === currentPath) {
      link.classList.add("active");
    }
  });

  // 3) Sticky header (.is-sticky when scrollY > 20)
  var header = $("header.header-area");
  function updateStickyHeader() {
    if (!header) return;
    header.classList.toggle("is-sticky", window.scrollY > 20);
  }
  updateStickyHeader();
  window.addEventListener("scroll", updateStickyHeader, { passive: true });

  // 4) Scroll-to-top button [data-scroll-top]
  var scrollTopBtn = $("[data-scroll-top]");
  function updateScrollTopVisibility() {
    if (!scrollTopBtn) return;
    scrollTopBtn.classList.toggle("is-visible", window.scrollY > 300);
  }
  if (scrollTopBtn) {
    updateScrollTopVisibility();
    window.addEventListener("scroll", updateScrollTopVisibility, { passive: true });
    scrollTopBtn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // 5) Store theme in localStorage key="theme"
  var themeStorageKey = "theme";
  function saveTheme(theme) {
    try {
      localStorage.setItem(themeStorageKey, theme);
    } catch (error) {
      // Ignore storage errors.
    }
  }

  // 6) Theme switcher [data-theme-toggle], toggle class dark on <html>
  function applyTheme(theme) {
    var isDark = theme === "dark";
    doc.documentElement.classList.toggle("dark", isDark);
    // Keep compatibility with existing project dark styles.
    doc.documentElement.classList.toggle("theme-dark", isDark);
  }

  var savedTheme = null;
  try {
    savedTheme = localStorage.getItem(themeStorageKey);
  } catch (error) {
    savedTheme = null;
  }
  if (savedTheme === "dark" || savedTheme === "light") {
    applyTheme(savedTheme);
  }

  $$("[data-theme-toggle]").forEach(function (toggleBtn) {
    toggleBtn.addEventListener("click", function () {
      var nextTheme = doc.documentElement.classList.contains("dark") ? "light" : "dark";
      applyTheme(nextTheme);
      saveTheme(nextTheme);
    });
  });

  // 7) Universal modal open [data-modal-open="id"] + [data-modal="id"]
  function findModalById(id) {
    if (!id) return null;
    return $$("[data-modal]").find(function (modal) {
      return modal.getAttribute("data-modal") === id;
    }) || null;
  }

  function openModal(modal) {
    if (!modal) return;
    modal.classList.add("is-open");
    modal.removeAttribute("hidden");
    doc.body.classList.add("modal-open");
  }

  function closeModal(modal) {
    if (!modal) return;
    modal.classList.remove("is-open");
    modal.setAttribute("hidden", "hidden");
    var hasOpenedModal = $$("[data-modal].is-open").length > 0;
    if (!hasOpenedModal) {
      doc.body.classList.remove("modal-open");
    }
  }

  $$("[data-modal-open]").forEach(function (openBtn) {
    openBtn.addEventListener("click", function (event) {
      event.preventDefault();
      openModal(findModalById(openBtn.getAttribute("data-modal-open")));
    });
  });

  // 8) Close modal by Esc and [data-modal-close]
  doc.addEventListener("click", function (event) {
    var closeBtn = event.target.closest("[data-modal-close]");
    if (closeBtn) {
      var modal = closeBtn.closest("[data-modal]");
      closeModal(modal);
      return;
    }

    var modalSurface = event.target.closest("[data-modal]");
    if (modalSurface && event.target === modalSurface) {
      closeModal(modalSurface);
    }
  });

  doc.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    $$("[data-modal].is-open").forEach(closeModal);
  });

  // 9) Toast notifications: showToast(text, type) + [data-toast]
  var toastContainer = null;
  function getToastContainer() {
    if (toastContainer) return toastContainer;
    toastContainer = doc.createElement("div");
    toastContainer.className = "app-toast-container";
    doc.body.appendChild(toastContainer);
    return toastContainer;
  }

  function showToast(text, type) {
    if (!text) return;
    var container = getToastContainer();
    var toast = doc.createElement("div");
    toast.className = "app-toast " + (type ? "is-" + type : "is-info");
    toast.textContent = text;
    container.appendChild(toast);
    requestAnimationFrame(function () {
      toast.classList.add("is-visible");
    });
    setTimeout(function () {
      toast.classList.remove("is-visible");
      setTimeout(function () {
        toast.remove();
      }, 220);
    }, 2200);
  }

  window.showToast = showToast;

  $$("[data-toast]").forEach(function (trigger) {
    trigger.addEventListener("click", function () {
      showToast(trigger.getAttribute("data-toast"), trigger.getAttribute("data-toast-type") || "info");
    });
  });

  // 10) Live search: [data-live-search] filters [data-search-item]
  $$("[data-live-search]").forEach(function (input) {
    var targetSelector = input.getAttribute("data-live-search-target") || "[data-search-item]";
    var items = $$(targetSelector);
    if (!items.length) return;

    function filterItems() {
      var q = (input.value || "").toLowerCase().trim();
      items.forEach(function (item) {
        var text = (item.textContent || "").toLowerCase();
        item.hidden = q ? text.indexOf(q) === -1 : false;
      });
    }

    input.addEventListener("input", filterItems);
  });

  // 11) Checkbox filter: [data-filter-checkbox] filters [data-filter-item] by data-category
  var filterCheckboxes = $$("[data-filter-checkbox]");
  if (filterCheckboxes.length) {
    function applyCheckboxFilter() {
      var activeValues = filterCheckboxes
        .filter(function (cb) { return cb.checked; })
        .map(function (cb) { return (cb.value || "").toLowerCase(); });

      $$("[data-filter-item]").forEach(function (item) {
        var categories = (item.getAttribute("data-category") || "")
          .split(",")
          .map(function (part) { return part.trim().toLowerCase(); })
          .filter(Boolean);

        var visible = !activeValues.length || activeValues.some(function (value) {
          return categories.indexOf(value) !== -1;
        });

        item.hidden = !visible;
      });
    }

    filterCheckboxes.forEach(function (checkbox) {
      checkbox.addEventListener("change", applyCheckboxFilter);
    });
    applyCheckboxFilter();
  }

  // 12) Sort by select [data-sort] for [data-sort-item] (price/rating/title)
  $$("[data-sort]").forEach(function (select) {
    select.addEventListener("change", function () {
      var container = select.closest("[data-sort-container]") ||
        (select.getAttribute("data-sort-container") ? $(select.getAttribute("data-sort-container")) : null);
      if (!container) return;

      var items = $$("[data-sort-item]", container);
      if (!items.length) return;

      var mode = select.value;
      if (mode !== "price_asc" && mode !== "price_desc" && mode !== "rating_desc") {
        return;
      }
      var sorted = items.slice().sort(function (a, b) {
        var aPrice = parseFloat(a.getAttribute("data-price") || "0");
        var bPrice = parseFloat(b.getAttribute("data-price") || "0");
        var aRating = parseFloat(a.getAttribute("data-rating") || "0");
        var bRating = parseFloat(b.getAttribute("data-rating") || "0");

        if (mode === "price_asc") return aPrice - bPrice;
        if (mode === "price_desc") return bPrice - aPrice;
        return bRating - aRating;
      });

      sorted.forEach(function (item) {
        container.appendChild(item);
      });
    });
  });

  // 13) Form validation [data-validate] (required + email), show errors near fields
  function clearFieldError(field) {
    var existing = field.parentElement ? field.parentElement.querySelector("[data-form-error]") : null;
    if (existing) existing.remove();
    field.classList.remove("is-invalid");
  }

  function setFieldError(field, message) {
    clearFieldError(field);
    var errorEl = doc.createElement("small");
    errorEl.className = "form-error";
    errorEl.setAttribute("data-form-error", "true");
    errorEl.textContent = message;
    field.classList.add("is-invalid");
    if (field.parentElement) {
      field.parentElement.appendChild(errorEl);
    }
  }

  $$("form[data-validate]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      var isValid = true;
      var fields = $$("input, textarea, select", form);
      fields.forEach(function (field) {
        clearFieldError(field);
        var value = (field.value || "").trim();
        var isRequired = field.hasAttribute("required");
        var isEmail = field.getAttribute("type") === "email";

        if (isRequired && !value) {
          setFieldError(field, "This field is required.");
          isValid = false;
          return;
        }

        if (isEmail && value) {
          var emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
          if (!emailOk) {
            setFieldError(field, "Enter a valid email address.");
            isValid = false;
          }
        }
      });

      if (!isValid) {
        event.preventDefault();
      }
    });
  });

  // 14) Textarea counter [data-counter-text] -> [data-counter-output]
  $$("[data-counter-text]").forEach(function (textarea) {
    var outputSelector = textarea.getAttribute("data-counter-output");
    var output = outputSelector ? $(outputSelector) : null;
    if (!output) {
      output = textarea.parentElement ? $("[data-counter-output]", textarea.parentElement) : null;
    }
    if (!output) return;

    var maxLength = parseInt(textarea.getAttribute("maxlength"), 10);
    function updateCounter() {
      var length = (textarea.value || "").length;
      output.textContent = Number.isFinite(maxLength) ? (length + "/" + maxLength) : String(length);
    }
    textarea.addEventListener("input", updateCounter);
    updateCounter();
  });

  // 15) Confirm delete for [data-confirm]
  $$("[data-confirm]").forEach(function (trigger) {
    trigger.addEventListener("click", function (event) {
      var message = trigger.getAttribute("data-confirm") || "Are you sure?";
      if (!window.confirm(message)) {
        event.preventDefault();
        event.stopPropagation();
      }
    });
  });
})();
