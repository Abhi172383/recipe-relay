import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";

const MOCK_RECIPES = [
  {
    id: "11111111-1111-1111-1111-111111111111",
    title: "Creamy Garlic Herb Pasta",
    author_name: "Chef Aria (Synthetic)",
    description: "Quick garlic butter pasta.",
    instructions: "Cook pasta and toss with sauce.",
    prep_time_minutes: 20,
    servings: 4,
    dietary_tags: ["vegetarian"],
    share_token: "pasta-garlic-herb-01",
    ingredients: [
      { id: 1, name: "butter", quantity: "2", unit: "tbsp", notes: "" },
    ],
  },
];

describe("RecipeRelay App", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders recipes, saves allergy profile, and shows AI-assisted badge with limitations", async () => {
    const fetchMock = vi.fn(async (url, options = {}) => {
      if (url.includes("/preferences/") && (!options.method || options.method === "GET")) {
        return new Response(JSON.stringify({ profile_key: "default", allergies: [], dietary_preferences: [] }), { status: 200 });
      }
      if (url.includes("/preferences/") && options.method === "PUT") {
        return new Response(
          JSON.stringify({ profile_key: "default", allergies: ["dairy"], dietary_preferences: [] }),
          { status: 200 }
        );
      }
      if (url.includes("/recipes/")) {
        return new Response(JSON.stringify(MOCK_RECIPES), { status: 200 });
      }
      if (url.includes("/substitutions/suggest/")) {
        return new Response(
          JSON.stringify({
            status: "verified",
            ai_assisted: true,
            provider_used: "mock",
            resolved_canonical: "butter",
            message: "Found 1 rule-verified substitution(s) for 'butter'.",
            suggestions: [
              { name: "olive oil", ratio: "3/4 tbsp per 1 tbsp butter", rationale: "Great dairy-free fat." },
            ],
            rejected_candidates: [{ name: "ghee", reason: "Allergen conflict: dairy" }],
            limitations: "Always verify packaged product labels for cross-contamination.",
          }),
          { status: 200 }
        );
      }
      return new Response("{}", { status: 404 });
    });

    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<App />);

    expect(await screen.findByText("Creamy Garlic Herb Pasta")).toBeInTheDocument();

    // Toggle Dairy allergy and save
    await user.click(screen.getByTestId("allergy-dairy"));
    await user.click(screen.getByTestId("save-preferences-btn"));
    await waitFor(() => {
      expect(screen.getByTestId("active-profile-summary")).toHaveTextContent("Allergies: dairy");
    });

    // Open recipe and request substitution
    await user.click(screen.getByTestId("open-recipe-pasta-garlic-herb-01"));
    await user.click(screen.getByTestId("suggest-btn-butter"));

    expect(await screen.findByTestId("ai-assisted-badge")).toHaveTextContent("AI-Assisted");
    expect(screen.getByTestId("rule-verified-badge")).toHaveTextContent("Deterministic Rule Verified");
    expect(screen.getByTestId("suggestions-list")).toHaveTextContent("olive oil");
    expect(screen.getByTestId("limitations-disclaimer")).toHaveTextContent("cross-contamination");
  });
});
