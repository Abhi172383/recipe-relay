import React, { useState } from "react";

const EMPTY_ING = { name: "", quantity: "", unit: "", notes: "" };

export default function RecipeForm({ initialRecipe, onSubmit, onCancel, submitting }) {
  const [title, setTitle] = useState(initialRecipe?.title || "");
  const [authorName, setAuthorName] = useState(
    initialRecipe?.author_name || "Home Cook (Synthetic)"
  );
  const [description, setDescription] = useState(initialRecipe?.description || "");
  const [instructions, setInstructions] = useState(initialRecipe?.instructions || "");
  const [prepTime, setPrepTime] = useState(initialRecipe?.prep_time_minutes || 20);
  const [servings, setServings] = useState(initialRecipe?.servings || 2);
  const [tagsText, setTagsText] = useState((initialRecipe?.dietary_tags || []).join(", "));
  const [ingredients, setIngredients] = useState(
    initialRecipe?.ingredients?.length
      ? initialRecipe.ingredients.map((i) => ({
          name: i.name || "",
          quantity: i.quantity || "",
          unit: i.unit || "",
          notes: i.notes || "",
        }))
      : [{ ...EMPTY_ING }]
  );

  function updateIngredient(index, field, value) {
    setIngredients((prev) =>
      prev.map((row, idx) => (idx === index ? { ...row, [field]: value } : row))
    );
  }

  function addIngredientRow() {
    setIngredients((prev) => [...prev, { ...EMPTY_ING }]);
  }

  function removeIngredientRow(index) {
    if (ingredients.length <= 1) return;
    setIngredients((prev) => prev.filter((_, idx) => idx !== index));
  }

  function handleSubmit(event) {
    event.preventDefault();
    const cleanedIngredients = ingredients.filter((i) => i.name.trim() !== "");
    const dietaryTags = tagsText
      .split(",")
      .map((t) => t.trim().toLowerCase())
      .filter(Boolean);

    onSubmit({
      title: title.trim(),
      author_name: authorName.trim() || "Home Cook (Synthetic)",
      description: description.trim(),
      instructions: instructions.trim(),
      prep_time_minutes: Number(prepTime) || 20,
      servings: Number(servings) || 2,
      dietary_tags: dietaryTags,
      is_public: true,
      ingredients: cleanedIngredients,
    });
  }

  return (
    <section className="card" aria-labelledby="recipe-form-heading" data-testid="recipe-form">
      <h2 id="recipe-form-heading" style={{ marginTop: 0 }}>
        {initialRecipe ? "Edit Recipe" : "Share a New Recipe"}
      </h2>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "0.75rem" }}>
          <label htmlFor="recipe-title" style={{ display: "block", fontWeight: 600 }}>
            Recipe Title *
          </label>
          <input
            id="recipe-title"
            className="input"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Dairy-Free Garlic Pasta"
            data-testid="recipe-title-input"
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.6rem", marginBottom: "0.75rem" }}>
          <div>
            <label htmlFor="recipe-author" style={{ display: "block", fontWeight: 600 }}>
              Author Alias
            </label>
            <input
              id="recipe-author"
              className="input"
              value={authorName}
              onChange={(e) => setAuthorName(e.target.value)}
              data-testid="recipe-author-input"
            />
          </div>
          <div>
            <label htmlFor="recipe-prep" style={{ display: "block", fontWeight: 600 }}>
              Prep (mins)
            </label>
            <input
              id="recipe-prep"
              type="number"
              min="1"
              className="input"
              value={prepTime}
              onChange={(e) => setPrepTime(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="recipe-servings" style={{ display: "block", fontWeight: 600 }}>
              Servings
            </label>
            <input
              id="recipe-servings"
              type="number"
              min="1"
              className="input"
              value={servings}
              onChange={(e) => setServings(e.target.value)}
            />
          </div>
        </div>

        <div style={{ marginBottom: "0.75rem" }}>
          <label htmlFor="recipe-desc" style={{ display: "block", fontWeight: 600 }}>
            Short Description
          </label>
          <input
            id="recipe-desc"
            className="input"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Quick overview for home cooks"
            data-testid="recipe-desc-input"
          />
        </div>

        <div style={{ marginBottom: "0.75rem" }}>
          <label htmlFor="recipe-tags" style={{ display: "block", fontWeight: 600 }}>
            Dietary Tags (comma-separated)
          </label>
          <input
            id="recipe-tags"
            className="input"
            value={tagsText}
            onChange={(e) => setTagsText(e.target.value)}
            placeholder="vegan, gluten-free, dairy-free"
            data-testid="recipe-tags-input"
          />
        </div>

        <div style={{ marginBottom: "0.75rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
            <span style={{ fontWeight: 600 }}>Ingredients *</span>
            <button
              type="button"
              className="btn btn-secondary btn-small"
              onClick={addIngredientRow}
              data-testid="add-ingredient-btn"
            >
              + Add Ingredient
            </button>
          </div>
          {ingredients.map((ing, idx) => (
            <div
              key={idx}
              style={{
                display: "grid",
                gridTemplateColumns: "2fr 1fr 1fr auto",
                gap: "0.45rem",
                marginBottom: "0.45rem",
              }}
            >
              <input
                aria-label={`Ingredient ${idx + 1} name`}
                className="input"
                required
                placeholder="Ingredient (e.g. butter)"
                value={ing.name}
                onChange={(e) => updateIngredient(idx, "name", e.target.value)}
                data-testid={`ingredient-name-${idx}`}
              />
              <input
                aria-label={`Ingredient ${idx + 1} quantity`}
                className="input"
                placeholder="Qty (e.g. 2)"
                value={ing.quantity}
                onChange={(e) => updateIngredient(idx, "quantity", e.target.value)}
                data-testid={`ingredient-qty-${idx}`}
              />
              <input
                aria-label={`Ingredient ${idx + 1} unit`}
                className="input"
                placeholder="Unit (tbsp)"
                value={ing.unit}
                onChange={(e) => updateIngredient(idx, "unit", e.target.value)}
                data-testid={`ingredient-unit-${idx}`}
              />
              <button
                type="button"
                className="btn btn-secondary btn-small"
                onClick={() => removeIngredientRow(idx)}
                disabled={ingredients.length <= 1}
                aria-label={`Remove ingredient ${idx + 1}`}
              >
                Remove
              </button>
            </div>
          ))}
        </div>

        <div style={{ marginBottom: "0.9rem" }}>
          <label htmlFor="recipe-instructions" style={{ display: "block", fontWeight: 600 }}>
            Cooking Instructions *
          </label>
          <textarea
            id="recipe-instructions"
            className="textarea"
            rows={4}
            required
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="Step-by-step instructions..."
            data-testid="recipe-instructions-input"
          />
        </div>

        <div style={{ display: "flex", gap: "0.6rem" }}>
          <button
            type="submit"
            className="btn"
            disabled={submitting}
            data-testid="submit-recipe-btn"
          >
            {submitting ? "Saving..." : initialRecipe ? "Update Recipe" : "Publish Recipe"}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </section>
  );
}
