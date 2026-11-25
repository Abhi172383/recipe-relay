const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  if (response.status === 204) {
    return null;
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.detail || JSON.stringify(data) || "Request failed";
    throw new Error(message);
  }
  return data;
}

export const api = {
  listRecipes({ q = "", ingredient = "", diet = "" } = {}) {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (ingredient) params.set("ingredient", ingredient);
    if (diet) params.set("diet", diet);
    const query = params.toString();
    return request(`/recipes/${query ? `?${query}` : ""}`);
  },
  getRecipe(id) {
    return request(`/recipes/${id}/`);
  },
  getSharedRecipe(shareToken) {
    return request(`/recipes/share/${encodeURIComponent(shareToken)}/`);
  },
  createRecipe(payload) {
    return request("/recipes/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateRecipe(id, payload) {
    return request(`/recipes/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  deleteRecipe(id) {
    return request(`/recipes/${id}/`, { method: "DELETE" });
  },
  getPreferences(profileKey = "default") {
    return request(`/preferences/?profile_key=${encodeURIComponent(profileKey)}`);
  },
  savePreferences(payload) {
    return request("/preferences/", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
  suggestSubstitution(payload) {
    return request("/substitutions/suggest/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getHealth() {
    return request("/health/");
  },
};
