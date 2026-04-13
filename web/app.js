(function () {
  const form = document.getElementById("preview-form");
  const submitBtn = document.getElementById("submit-btn");
  const btnLabel = submitBtn.querySelector(".btn-label");
  const btnSpinner = submitBtn.querySelector(".btn-spinner");
  const errorBanner = document.getElementById("error-banner");
  const results = document.getElementById("results");
  const panelAlpha = document.getElementById("panel-alpha");
  const alphaOut = document.getElementById("alpha-out");
  const chunksOut = document.getElementById("chunks-out");

  function setLoading(loading) {
    submitBtn.disabled = loading;
    btnSpinner.hidden = !loading;
    if (loading) {
      btnLabel.textContent = "Retrieving…";
    } else {
      btnLabel.textContent = "Retrieve";
    }
  }

  function showError(msg) {
    errorBanner.hidden = false;
    errorBanner.textContent = msg;
  }

  function clearError() {
    errorBanner.hidden = true;
    errorBanner.textContent = "";
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderChunks(chunks) {
    chunksOut.innerHTML = "";
    if (!chunks || !chunks.length) {
      const p = document.createElement("p");
      p.className = "muted";
      p.textContent = "No chunks returned (empty index, filters too strict, or below similarity threshold).";
      chunksOut.appendChild(p);
      return;
    }
    chunks.forEach(function (c, i) {
      const card = document.createElement("article");
      card.className = "chunk-card";
      card.style.animationDelay = i * 0.05 + "s";

      const meta = document.createElement("div");
      meta.className = "chunk-meta";
      const score =
        c.score !== null && c.score !== undefined ? Number(c.score).toFixed(4) : "—";
      meta.innerHTML =
        "<span><strong>Source</strong> " +
        escapeHtml(c.id || "Unknown") +
        "</span>" +
        "<span><strong>Light</strong> " +
        escapeHtml(String(c.light_levels ?? "")) +
        "</span>" +
        "<span><strong>Score</strong> " +
        escapeHtml(score) +
        "</span>" +
        (c.category
          ? "<span><strong>Category</strong> " + escapeHtml(String(c.category)) + "</span>"
          : "");
      card.appendChild(meta);

      if (c.is_dummy) {
        const b = document.createElement("span");
        b.className = "badge-dummy";
        b.textContent = "Dummy / test data";
        meta.appendChild(b);
      }

      const text = document.createElement("p");
      text.className = "chunk-text";
      text.textContent = c.text || "";
      card.appendChild(text);

      chunksOut.appendChild(card);
    });
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    clearError();

    const fd = new FormData(form);
    const query = (fd.get("query") || "").trim();
    const plant = (fd.get("plant") || "").trim();
    const light_level = (fd.get("light_level") || "").trim();
    const top_k = fd.get("top_k");
    const action_category = (fd.get("action_category") || "").trim();
    const envRaw = (fd.get("env_context") || "").trim();

    const payload = { query: query };
    if (plant) payload.plant = plant;
    if (light_level) payload.light_level = light_level;
    if (top_k) payload.top_k = Number(top_k);
    if (action_category) {
      payload.action_category = action_category;
      let env = {};
      if (envRaw) {
        try {
          env = JSON.parse(envRaw);
          if (env === null || typeof env !== "object" || Array.isArray(env)) {
            throw new Error("env_context must be a JSON object.");
          }
        } catch (err) {
          showError(err.message || "Invalid JSON in env_context.");
          return;
        }
      }
      payload.env_context = env;
      if (!plant) {
        showError("Plant slug is required when using Engine Alpha.");
        return;
      }
    }

    setLoading(true);
    results.hidden = true;

    try {
      const res = await fetch("/api/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(function () {
        return {};
      });
      if (!res.ok) {
        showError(data.error || "Request failed (" + res.status + ").");
        return;
      }

      if (data.hard_constraints_markdown) {
        panelAlpha.hidden = false;
        alphaOut.textContent = data.hard_constraints_markdown;
      } else {
        panelAlpha.hidden = true;
        alphaOut.textContent = "";
      }

      renderChunks(data.chunks);
      results.hidden = false;
    } catch (err) {
      showError(err.message || "Network error.");
    } finally {
      setLoading(false);
    }
  });
})();
