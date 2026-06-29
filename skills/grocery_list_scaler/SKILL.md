---
name: grocery-list-scaler
description: "Consolidates ingredients from weekly lunch menus and scales them by kid count and serving size."
---

# Grocery List Scaler & Consolidation System

This skill details how to parse a menu, calculate total ingredient volumes, and structure a shopping list.

## Scaling Algorithms

### 1. Ingredient Quantity Scaling
Calculate quantities as:
$$\text{Total Grocery Quantity} = \text{Serving Size Per Kid} \times \text{Number of Kids} \times \text{Frequency in Menu}$$

### 2. Volume/Weight Consolidation
When combining ingredients, use clean fractions and unit conversions:
- Group dry ingredients by weight (ounces/grams) or count (e.g., 4 bananas).
- Round up to standard packaging sizes (e.g., if calculation is 1.2 containers of yogurt, recommend 2 containers).

### 3. Category Grouping (Aisle-Wise)
Group ingredients under these headers:
- `## Produce`
- `## Bakery & Breads`
- `## Dairy & Eggs`
- `## Meat & Proteins`
- `## Pantry & Canned Goods`
- `## Household & Containers`
