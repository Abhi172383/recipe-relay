import React, { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import PreferencesPanel from "./components/PreferencesPanel";
import RecipeDetail from "./components/RecipeDetail";
import RecipeForm from "./components/RecipeForm";

export default function App() {
  const [recipes, setRecipes] = useState([]);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [mode, setMode] = useState("list"); // list | detail | create | edit
  const [searchQuery, setSearchQuery] = useState("");
  const [ingredientFilter, setIngredientFilter] = useState("");
  const [dietFilter, setDietFilter] = useState("");

  const [allergies, setAllergies] = useState([]);
  const [dietaryPreferences, setDietaryPreferences] = useState([]);

  const [loadingRecipes, setLoadingRecipes] = useState(true);
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [submittingForm, setSubmittingForm] = useState(false);

  const [activeIngredient, setActiveIngredient] = useState("");
  const [subResult, setSubResult] = useState(null);
  const [subLoading, setSubLoading] = useState(false);

  const [statusMessage, setStatusMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const fetchRecipes = useCallback(async (filters = {}) => {
    setLoadingRecipes(true);
    setErrorMessage("");
    try {
      const data = await api.listRecipes(filters);
      setRecipes(data);
    } catch (err) {
      setErrorMessage(`Could not load recipes: ${err.message}`);
    } finally {
      setLoadingRecipes(false);
    }
  }, []);

  useEffect(() => {
    fetchRecipes();
    api
      .getPreferences("default")
      .then((pref) => {
        setAllergies(pref.allergies || []);
        setDietaryPreferences(pref.dietary_preferences || []);
      })
      .catch(() => {});

    const params = new URLSearchParams(window.location.search);
    const shareToken = params.get("share");
    if (shareToken) {
      api
        .getSharedRecipe(shareToken)
        .then((shared) => {
          setSelectedRecipe(shared);
          setMode("detail");
        })
        .catch(() => setErrorMessage("Shared recipe link was not found."));
    }
  }, [fetchRecipes]);

  function handleSearchSubmit(event) {
    event.preventDefault();
    setMode("list");
    fetchRecipes({ q: searchQuery, ingredient: ingredientFilter, diet: dietFilter });
  }

  function handleClearSearch() {
    setSearchQuery("");
    setIngredientFilter("");
    setDietFilter("");
    setMode("list");
    fetchRecipes({});
  }

  async function handleSavePreferences(payload) {
    setSavingPrefs(true);
    setErrorMessage("");
    try {
      const saved = await api.savePreferences({ profile_key: "default", ...payload });
      setAllergies(saved.allergies || []);
      setDietaryPreferences(saved.dietary_preferences || []);
      setStatusMessage("Safety profile updated.");
    } catch (err) {
      setErrorMessage(`Failed to save preferences: ${err.message}`);
    } finally {
      setSavingPrefs(false);
    }
  }

  async function handleCreateOrUpdateRecipe(payload) {
    setSubmittingForm(true);
    setErrorMessage("");
    try {
      let saved;
      if (mode === "edit" && selectedRecipe) {
        saved = await api.updateRecipe(selectedRecipe.id, payload);
        setStatusMessage(`Updated recipe "${saved.title}".`);
      } else {
        saved = await api.createRecipe(payload);
        setStatusMessage(`Published recipe "${saved.title}".`);
      }
      setSelectedRecipe(saved);
      setSubResult(null);
      setMode("detail");
      await fetchRecipes({ q: searchQuery, ingredient: ingredientFilter, diet: dietFilter });
    } catch (err) {
      setErrorMessage(`Could not save recipe: ${err.message}`);
    } finally {
      setSubmittingForm(false);
    }
  }

  async function handleDeleteRecipe(id) {
    setErrorMessage("");
    try {
      await api.deleteRecipe(id);
      setSelectedRecipe(null);
      setMode("list");
      setStatusMessage("Recipe deleted.");
      await fetchRecipes({ q: searchQuery, ingredient: ingredientFilter, diet: dietFilter });
    } catch (err) {
      setErrorMessage(`Could not delete recipe: ${err.message}`);
    }
  }

  async function handleSuggestSubstitution(ingredientName, recipeId) {
    setActiveIngredient(ingredientName);
    setSubLoading(true);
    setSubResult(null);
    setErrorMessage("");
    try {
      const result = await api.suggestSubstitution({
        ingredient: ingredientName,
        recipe_id: recipeId,
        profile_key: "default",
        allergies,
        dietary_preferences: dietaryPreferences,
      });
      setSubResult(result);
    } catch (err) {
      setErrorMessage(`Substitution check failed: ${err.message}`);
    } finally {
      setSubLoading(false);
    }
  }

  return (
    <div>
      <header className="app-header">
        <div>
          <h1 className="brand-title">RecipeRelay</h1>
          <p className="brand-subtitle">
            Recipe Sharing with Deterministic Allergy-Safe Substitution
          </p>
        </div>
        <div className="header-badges" aria-live="polite" data-testid="active-profile-summary">
          <span className="badge badge-ai">
            Allergies: {allergies.length ? allergies.join(", ") : "None"}
          </span>
          <span className="badge badge-safe">
            Diets: {dietaryPreferences.length ? dietaryPreferences.join(", ") : "Any"}
          </span>
        </div>
      </header>

      <main className="layout">
        <section aria-label="Recipes workspace">
          {statusMessage && (
            <div className="status-banner" role="status" aria-live="polite" data-testid="status-banner">
              {statusMessage}
            </div>
          )}
          {errorMessage && (
            <div className="error-banner" role="alert" data-testid="error-banner">
              {errorMessage}
            </div>
          )}

          <form className="card toolbar" onSubmit={handleSearchSubmit} role="search" aria-label="Search recipes">
            <div style={{ flex: "1 1 200px" }}>
              <label htmlFor="search-q" className="sr-only">
                Search by title or ingredient
              </label>
              <input
                id="search-q"
                className="input"
                placeholder="Search title or ingredient (e.g. pasta, chickpea)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                data-testid="search-query-input"
              />
            </div>
            <div style={{ flex: "1 1 150px" }}>
              <label htmlFor="search-ing" className="sr-only">
                Filter by ingredient
              </label>
              <input
                id="search-ing"
                className="input"
                placeholder="Ingredient filter..."
                value={ingredientFilter}
                onChange={(e) => setIngredientFilter(e.target.value)}
                data-testid="search-ingredient-input"
              />
            </div>
            <div style={{ flex: "0 1 140px" }}>
              <label htmlFor="search-diet" className="sr-only">
                Dietary tag filter
              </label>
              <select
                id="search-diet"
                className="select"
                value={dietFilter}
                onChange={(e) => setDietFilter(e.target.value)}
                data-testid="search-diet-select"
              >
                <option value="">All Diets</option>
                <option value="vegan">Vegan</option>
                <option value="vegetarian">Vegetarian</option>
                <option value="gluten-free">Gluten-Free</option>
                <option value="dairy-free">Dairy-Free</option>
              </select>
            </div>
            <button type="submit" className="btn" data-testid="search-submit-btn">
              Search
            </button>
            <button type="button" className="btn btn-secondary" onClick={handleClearSearch}>
              Reset
            </button>
            <button
              type="button"
              className="btn"
              onClick={() => {
                setSelectedRecipe(null);
                setSubResult(null);
                setMode("create");
              }}
              data-testid="new-recipe-btn"
            >
              + New Recipe
            </button>
          </form>

          {(mode === "create" || mode === "edit") && (
            <RecipeForm
              initialRecipe={mode === "edit" ? selectedRecipe : null}
              onSubmit={handleCreateOrUpdateRecipe}
              onCancel={() => setMode(selectedRecipe ? "detail" : "list")}
              submitting={submittingForm}
            />
          )}

          {mode === "detail" && selectedRecipe && (
            <RecipeDetail
              recipe={selectedRecipe}
              onBack={() => {
                setMode("list");
                setSubResult(null);
              }}
              onEdit={() => setMode("edit")}
              onDelete={handleDeleteRecipe}
              onSuggest={handleSuggestSubstitution}
              subResult={subResult}
              subLoading={subLoading}
              activeIngredient={activeIngredient}
            />
          )}

          {mode === "list" && (
            <div className="recipe-grid" data-testid="recipe-list">
              {loadingRecipes ? (
                <div className="card">Loading recipes...</div>
              ) : recipes.length === 0 ? (
                <div className="card">No matching recipes found. Try clearing your filters or adding a recipe!</div>
              ) : (
                recipes.map((recipe) => (
                  <article key={recipe.id} className="card" data-testid={`recipe-card-${recipe.share_token}`}>
                    <div className="recipe-card-header">
                      <div>
                        <h2 style={{ margin: "0 0 0.25rem 0", fontSize: "1.15rem" }}>
                          {recipe.title}
                        </h2>
                        <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--muted)" }}>
                          By {recipe.author_name} &bull; {recipe.prep_time_minutes} mins &bull;{" "}
                          {recipe.ingredients.length} ingredients
                        </p>
                      </div>
                      <button
                        type="button"
                        className="btn btn-small"
                        onClick={() => {
                          setSelectedRecipe(recipe);
                          setSubResult(null);
                          setMode("detail");
                        }}
                        data-testid={`open-recipe-${recipe.share_token}`}
                      >
                        View &amp; Substitute
                      </button>
                    </div>
                    {recipe.description && (
                      <p style={{ margin: "0.55rem 0 0.5rem 0", fontSize: "0.92rem" }}>
                        {recipe.description}
                      </p>
                    )}
                    <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap", marginTop: "0.45rem" }}>
                      {(recipe.dietary_tags || []).map((tag) => (
                        <span key={tag} className="badge">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </article>
                ))
              )}
            </div>
          )}
        </section>

        <PreferencesPanel
          allergies={allergies}
          dietaryPreferences={dietaryPreferences}
          onSave={handleSavePreferences}
          saving={savingPrefs}
        />
      </main>
    </div>
  );
}
