---
name: recipe-favorites-log
description: "Manages reading, writing, and updating local JSON recipes favorites database."
---

# Recipe Favorites Database Interface

This skill details the interface guidelines for reading and writing recipes to the persistence file.

## Operations Flow

### 1. Verification
- Locate target file: `favorites_recipes.json` in the agent's application data directory.
- Parse as JSON. If empty or missing, write `[]` as the root element.

### 2. Appending Favorites
Verify schema before committing:
```json
{
  "id": "unique_string_id",
  "name": "Recipe Name",
  "ingredients": ["ingredient 1", "ingredient 2"],
  "rating": 5,
  "last_planned_date": "YYYY-MM-DD"
}
```

### 3. Updating Scores
If the user modifies ratings or provides feedback, locate the recipe by `name` or `id` and update the rating field. Save modifications atomically.
