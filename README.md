# Lunchbox Genie - School Lunch Planner

This is a local Python-based school lunch planner built with the Google Antigravity SDK architecture, featuring a premium glassmorphic web dashboard interface.

## Quick Start

1. Start the local server:
   ```bash
   python3 app.py
   ```
2. Your default browser should open to `http://localhost:8000` automatically.
3. If it doesn't open, manually browse to [http://localhost:8000](http://localhost:8000).

## Project Structure

- `app.py`: Backend server serving static assets and REST API endpoints.
- `index.html`: A beautiful, responsive frontend UI featuring a glassmorphism bento layout, interactive checkboxes, and a 3-star rating component. Fully optimized for printing (`@media print`).
- `google/`: Local package simulating the `google.antigravity` namespace:
  - `antigravity.py`: Implements `Agent`, `LocalAgentConfig`, and `types.CapabilitiesConfig` wrappers. Uses `GEMINI_API_KEY` (if set) to call the live Gemini API, and falls back to a smart mock response generator when offline.
- `skills/`:
  - `lunchbox_genie_orchestration/`: Handles session state machine logic.
  - `pediatric_dietetics_planner/`: Manages pediatric nutrition constraints and peanut-free substitutions.
  - `grocery_list_scaler/`: Scaled shopping list algorithms.
  - `recipe_favorites_log/`: Persistence/CRUD logic.
- `favorites_recipes.json`: Flat file JSON database storing rated favorites recipes.
