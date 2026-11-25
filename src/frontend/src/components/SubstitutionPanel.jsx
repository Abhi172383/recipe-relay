import React from "react";

export default function SubstitutionPanel({ result, loading }) {
  if (loading) {
    return (
      <div className="substitution-panel" role="status" aria-live="polite">
        Checking AI candidates against deterministic safety rules...
      </div>
    );
  }

  if (!result) {
    return null;
  }

  const isVerified = result.status === "verified" && result.suggestions?.length > 0;

  return (
    <div
      className={`substitution-panel ${isVerified ? "" : "no-safe"}`}
      role="region"
      aria-label="Ingredient substitution results"
      data-testid="substitution-panel"
    >
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", marginBottom: "0.6rem" }}>
        {result.ai_assisted && (
          <span className="badge badge-ai" data-testid="ai-assisted-badge">
            AI-Assisted
          </span>
        )}
        {isVerified ? (
          <span className="badge badge-safe" data-testid="rule-verified-badge">
            Deterministic Rule Verified
          </span>
        ) : (
          <span className="badge badge-blocked" data-testid="no-safe-badge">
            No Safe Suggestion
          </span>
        )}
        <span className="badge">Provider: {result.provider_used}</span>
        {result.resolved_canonical && (
          <span className="badge">Canonical: {result.resolved_canonical}</span>
        )}
      </div>

      <p style={{ margin: "0 0 0.6rem 0", fontWeight: 600 }} data-testid="substitution-message">
        {result.message}
      </p>

      {isVerified && (
        <ul style={{ margin: "0 0 0.75rem 0", paddingLeft: "1.2rem" }} data-testid="suggestions-list">
          {result.suggestions.map((sug) => (
            <li key={sug.name} style={{ marginBottom: "0.45rem" }}>
              <strong>{sug.name}</strong> ({sug.ratio}) — {sug.rationale}
            </li>
          ))}
        </ul>
      )}

      {result.rejected_candidates?.length > 0 && (
        <details style={{ fontSize: "0.85rem", marginTop: "0.5rem" }}>
          <summary style={{ cursor: "pointer", fontWeight: 600 }}>
            Rejected unsafe/unverified candidates ({result.rejected_candidates.length})
          </summary>
          <ul style={{ marginTop: "0.35rem" }}>
            {result.rejected_candidates.map((rej, idx) => (
              <li key={`${rej.name}-${idx}`}>
                <strong>{rej.name}</strong>: {rej.reason}
              </li>
            ))}
          </ul>
        </details>
      )}

      <p className="limitations-note" data-testid="limitations-disclaimer">
        <strong>Limitations:</strong> {result.limitations}
      </p>
    </div>
  );
}
