import React, { useState } from "react";
import SubstitutionPanel from "./SubstitutionPanel";

export default function RecipeDetail({
  recipe,
  onBack,
  onEdit,
  onDelete,
  onSuggest,
  subResult,
  subLoading,
  activeIngredient,
}) {
  const [copied, setCopied] = useState(false);

  if (!recipe) {
    return null;
  }

  function handleCopyShare() {
    const shareUrl = `${window.location.origin}/?share=${recipe.share_token}`;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(shareUrl).catch(() => {});
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  }

  return (
    <article className="card" data-testid="recipe-detail">
      <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.75rem" }}>
        <button type="button" className="btn btn-secondary btn-small" onClick={onBack}>
          &larr; Back to Recipes
        </button>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <button
            type="button"
            className="btn btn-secondary btn-small"
            onClick={handleCopyShare}
            data-testid="copy-share-btn"
          >
            {copied ? "Share Link Copied!" : "Copy Share Link"}
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-small"
            onClick={() => onEdit(recipe)}
            data-testid="edit-recipe-btn"
          >
            Edit
          </button>
          <button
            type="button"
            className="btn btn-danger btn-small"
            onClick={() => onDelete(recipe.id)}
            data-testid="delete-recipe-btn"
          >
            Delete
          </button>
        </div>
      </div>

      {copied && (
        <div className="status-banner" role="status" aria-live="polite" data-testid="share-copied-banner">
          Share URL ready: {`${window.location.origin}/?share=${recipe.share_token}`}
        </div>
      )}

      <h2 style={{ margin: "0 0 0.25rem 0" }} data-testid="detail-title">
        {recipe.title}
      </h2>
      <p style={{ margin: "0 0 0.75rem 0", color: "var(--muted)", fontSize: "0.9rem" }}>
        By {recipe.author_name} &bull; {recipe.prep_time_minutes} mins &bull; {recipe.servings} servings
      </p>

      {recipe.dietary_tags?.length > 0 && (
        <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap", marginBottom: "0.8rem" }}>
          {recipe.dietary_tags.map((tag) => (
            <span key={tag} className="badge">
              {tag}
            </span>
          ))}
        </div>
      )}

      {recipe.description && <p>{recipe.description}</p>}

      <h3>Ingredients</h3>
      <div style={{ marginBottom: "1rem" }}>
        {recipe.ingredients.map((ing) => (
          <div key={ing.id || ing.name} className="ingredient-row">
            <span>
              <strong>
                {[ing.quantity, ing.unit, ing.name].filter(Boolean).join(" ")}
              </strong>
              {ing.notes ? ` (${ing.notes})` : ""}
            </span>
            <button
              type="button"
              className="btn btn-small"
              onClick={() => onSuggest(ing.name, recipe.id)}
              data-testid={`suggest-btn-${ing.name.toLowerCase().replace(/\s+/g, "-")}`}
            >
              Suggest Substitute
            </button>
          </div>
        ))}
      </div>

      {(subLoading || subResult) && (
        <div>
          <h4 style={{ marginBottom: "0.25rem" }}>
            Substitution Check for: <em>{activeIngredient}</em>
          </h4>
          <SubstitutionPanel result={subResult} loading={subLoading} />
        </div>
      )}

      <h3 style={{ marginTop: "1.25rem" }}>Instructions</h3>
      <p style={{ whiteSpace: "pre-line" }}>{recipe.instructions}</p>
    </article>
  );
}
