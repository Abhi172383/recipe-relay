import React, { useEffect, useState } from "react";

const ALLERGY_OPTIONS = [
  { value: "dairy", label: "Dairy" },
  { value: "peanut", label: "Peanut" },
  { value: "tree_nut", label: "Tree Nuts" },
  { value: "gluten", label: "Gluten / Wheat" },
  { value: "egg", label: "Egg" },
  { value: "soy", label: "Soy" },
  { value: "shellfish", label: "Shellfish" },
  { value: "sesame", label: "Sesame" },
];

const DIET_OPTIONS = [
  { value: "vegan", label: "Vegan" },
  { value: "vegetarian", label: "Vegetarian" },
  { value: "dairy-free", label: "Dairy-Free" },
  { value: "gluten-free", label: "Gluten-Free" },
  { value: "nut-free", label: "Nut-Free" },
];

export default function PreferencesPanel({ allergies, dietaryPreferences, onSave, saving }) {
  const [selectedAllergies, setSelectedAllergies] = useState(allergies || []);
  const [selectedDiets, setSelectedDiets] = useState(dietaryPreferences || []);

  useEffect(() => {
    setSelectedAllergies(allergies || []);
  }, [allergies]);

  useEffect(() => {
    setSelectedDiets(dietaryPreferences || []);
  }, [dietaryPreferences]);

  function toggleItem(list, setList, value) {
    if (list.includes(value)) {
      setList(list.filter((item) => item !== value));
    } else {
      setList([...list, value]);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSave({
      allergies: selectedAllergies,
      dietary_preferences: selectedDiets,
    });
  }

  return (
    <aside className="card" aria-labelledby="preferences-heading" data-testid="preferences-panel">
      <h2 id="preferences-heading" style={{ marginTop: 0, fontSize: "1.1rem" }}>
        Dietary &amp; Allergy Profile
      </h2>
      <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: 0 }}>
        All AI substitution candidates are checked deterministically against these exclusions.
      </p>

      <form onSubmit={handleSubmit}>
        <fieldset style={{ border: "none", padding: 0, margin: "0 0 0.75rem 0" }}>
          <legend style={{ fontWeight: 600, marginBottom: "0.4rem", fontSize: "0.9rem" }}>
            Allergy Exclusions
          </legend>
          <div className="checkbox-grid">
            {ALLERGY_OPTIONS.map((opt) => (
              <label key={opt.value} className="checkbox-label">
                <input
                  type="checkbox"
                  data-testid={`allergy-${opt.value}`}
                  checked={selectedAllergies.includes(opt.value)}
                  onChange={() => toggleItem(selectedAllergies, setSelectedAllergies, opt.value)}
                />
                <span>{opt.label}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset style={{ border: "none", padding: 0, margin: "0 0 0.75rem 0" }}>
          <legend style={{ fontWeight: 600, marginBottom: "0.4rem", fontSize: "0.9rem" }}>
            Dietary Preferences
          </legend>
          <div className="checkbox-grid">
            {DIET_OPTIONS.map((opt) => (
              <label key={opt.value} className="checkbox-label">
                <input
                  type="checkbox"
                  data-testid={`diet-${opt.value}`}
                  checked={selectedDiets.includes(opt.value)}
                  onChange={() => toggleItem(selectedDiets, setSelectedDiets, opt.value)}
                />
                <span>{opt.label}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <button
          type="submit"
          className="btn"
          disabled={saving}
          data-testid="save-preferences-btn"
          style={{ width: "100%" }}
        >
          {saving ? "Saving..." : "Save Safety Profile"}
        </button>
      </form>
    </aside>
  );
}
