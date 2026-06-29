---
name: pediatric-dietetics-planner
description: "Generates nutritionally balanced, kid-friendly school lunch menus. Enforces strict peanut-free and allergy-safe guidelines."
---

# Pediatric Dietetics & School Menu Planner

This skill outlines guidelines for formulating lunch menus that fit school policies and children's nutritional targets.

## Core Directives

### 1. Allergy-Safe Protocol (Zero Tolerance)
Schools frequently enforce strict allergen rules. If a user defines an allergy:
- Check `references/allergy_substitutions.json` for alternatives.
- Avoid raw ingredients and processed items containing traces of the allergen.
- Common alternatives:
  - Peanut Butter -> Sunflower Seed Butter (SunButter) or Soy Butter.
  - Gluten/Wheat -> Rice-based or Corn-based pasta/tortillas.
  - Dairy -> Oat milk, coconut yogurt, dairy-free cheese.

### 2. Nutritional Balance Targets
Every daily lunch box must contain:
- **Protein**: 1 serving (chicken breast, hard-boiled eggs, beans, chickpeas, turkey slices).
- **Vitamins/Fiber**: 1 fruit AND 1 vegetable (sliced strawberries, apple slices, baby carrots, cucumber wheels).
- **Grains/Carbs**: 1 complex carbohydrate (whole wheat sandwich bread, quinoa, brown rice pasta).
- **Fat/Dairy**: 1 healthy fat/calcium source (cheese stick, avocado cubing, yogurt).

### 3. Packing & Portability
Lunches are eaten 4–6 hours after packing. 
- Choose items that do not get soggy (avoid placing wet dressings directly on bread).
- Categorize meals into **Cold Packs** (salads, wraps, cold dishes) and **Thermos Warmers** (soups, pasta, chili).

## Menu Generation Schema
Output a structured Markdown table matching this header structure:
`| Day | Meal Name | Portions per Kid | Nutritional Profile | Packing & Prep Tips |`
