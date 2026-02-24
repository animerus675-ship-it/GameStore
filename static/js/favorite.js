(function () {
  "use strict";

  var forms = document.querySelectorAll("[data-favorite-form]");
  if (!forms.length) {
    return;
  }

  function getCookie(name) {
    var value = "; " + document.cookie;
    var parts = value.split("; " + name + "=");
    if (parts.length === 2) {
      return parts.pop().split(";").shift();
    }
    return "";
  }

  forms.forEach(function (form) {
    var button = form.querySelector("[data-favorite-toggle]");
    if (!button) {
      return;
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();

      if (button.disabled) {
        return;
      }

      var url = button.getAttribute("data-url") || form.getAttribute("action");
      if (!url) {
        form.submit();
        return;
      }

      button.disabled = true;

      fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "XMLHttpRequest"
        }
      })
        .then(function (response) {
          var contentType = response.headers.get("content-type") || "";
          if (contentType.indexOf("application/json") === -1) {
            form.submit();
            return null;
          }
          return response.json().then(function (payload) {
            return { statusCode: response.status, payload: payload };
          });
        })
        .then(function (result) {
          if (!result) {
            return;
          }

          if (result.statusCode === 401) {
            window.location.href = "/login/?next=" + encodeURIComponent(window.location.pathname);
            return;
          }

          if (!result.payload || !result.payload.status) {
            form.submit();
            return;
          }

          if (result.payload.status === "added") {
            button.textContent = button.getAttribute("data-added-text") || "Remove from favorites";
          } else if (result.payload.status === "removed") {
            button.textContent = button.getAttribute("data-removed-text") || "Add to favorites";
          }
        })
        .catch(function () {
          form.submit();
        })
        .finally(function () {
          button.disabled = false;
        });
    });
  });
})();
