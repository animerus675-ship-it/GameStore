(function () {
  var forms = document.querySelectorAll("[data-favorite-form]");
  if (!forms.length) return;

  function getCookie(name) {
    var value = "; " + document.cookie;
    var parts = value.split("; " + name + "=");
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }

  function parseResponse(response) {
    var contentType = response.headers.get("content-type") || "";
    if (contentType.indexOf("application/json") === -1) {
      return Promise.resolve({ status: response.status, payload: null });
    }

    return response
      .json()
      .then(function (payload) {
        return { status: response.status, payload: payload };
      })
      .catch(function () {
        return { status: response.status, payload: null };
      });
  }

  forms.forEach(function (form) {
    var button = form.querySelector("[data-favorite-toggle]");
    if (!button) return;

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      if (button.dataset.loading === "1") return;

      var url = button.getAttribute("data-url") || form.getAttribute("action");
      if (!url) return;

      var csrfToken =
        getCookie("csrftoken") ||
        (form.querySelector("input[name='csrfmiddlewaretoken']") || {}).value ||
        "";

      var addedText = button.getAttribute("data-added-text") || "Убрать из избранного";
      var removedText = button.getAttribute("data-removed-text") || "Добавить в избранное";

      button.dataset.loading = "1";
      button.disabled = true;

      fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
      })
        .then(parseResponse)
        .then(function (result) {
          if (result.status === 401) {
            window.location.href = "/login/?next=" + encodeURIComponent(window.location.pathname);
            return;
          }

          if (!result.payload || !result.payload.status) {
            form.submit();
            return;
          }

          if (result.payload.status === "added") {
            button.textContent = addedText;
          } else if (result.payload.status === "removed") {
            button.textContent = removedText;
          }
        })
        .catch(function () {
          form.submit();
        })
        .finally(function () {
          button.disabled = false;
          button.dataset.loading = "0";
        });
    });
  });
})();
