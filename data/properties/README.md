# Property Documentation System

This directory contains YAML-based documentation for folksonomy properties that can be used in the Open Food Facts ecosystem.

## Purpose

The property documentation system provides:

1. **Standardized metadata** for properties with icons, descriptions, and examples
2. **Multilingual support** for property names, descriptions, and value options
3. **Input widget configuration** for property-specific user interfaces
4. **Value validation** through permitted values, types, and formats
5. **Knowledge panel integration** for rich property display
6. **Wikidata linking** for semantic web integration

## YAML File Structure

Each property should have its own YAML file named after the property key (e.g., `color.yaml`, `scoville_scale.yaml`).

### Required Fields

- `key`: The property key (lowercase, alphanumeric with underscores/hyphens)
- `name`: Multilingual property names
- `description`: Multilingual descriptions of what the property represents

### Optional Fields

- `icon`: Icon identifier or URL for visual representation
- `images`: Map of property values to image URLs or identifiers
- `wikidata_property`: Wikidata property ID (e.g., "P1552")
- `wikidata_url`: Full URL to the Wikidata property page
- `open_food_facts_wiki`: URL to the Open Food Facts wiki documentation
- `value_type`: Type of value (string, number, boolean, enum, etc.)
- `permitted_values`: List of allowed values with multilingual labels
- `unit`: Unit of measurement (if applicable)
- `format`: Validation format or pattern
- `examples`: Example values with explanations
- `input_widget`: Configuration for input UI component
- `categories`: Open Food Facts categories this property applies to
- `tags`: Related tags or themes
- `knowledge_panel`: Configuration for knowledge panel display

## Example Property Definition

```yaml
key: scoville_scale
name:
  en: Scoville Scale
  fr: Échelle de Scoville
  es: Escala Scoville
description:
  en: Measures the spiciness or heat of chili peppers and spicy foods
  fr: Mesure le piquant des piments et des aliments épicés
  es: Mide el picante de los chiles y alimentos picantes
icon: 🌶️
wikidata_property: P5196
wikidata_url: https://www.wikidata.org/wiki/Property:P5196
open_food_facts_wiki: https://wiki.openfoodfacts.org/Folksonomy/Property
value_type: number
unit: SHU
format: "^[0-9]+$"
permitted_values:
  - value: "0-100"
    label:
      en: Mild
      fr: Doux
  - value: "100-1000"
    label:
      en: Medium
      fr: Moyen
  - value: "1000-10000"
    label:
      en: Hot
      fr: Piquant
  - value: "10000+"
    label:
      en: Very Hot
      fr: Très Piquant
examples:
  - value: "2500"
    description:
      en: Jalapeño pepper
      fr: Piment jalapeño
input_widget:
  type: slider
  min: 0
  max: 100000
  step: 100
  unit_display: SHU
categories:
  - en:spices
  - en:sauces
  - en:condiments
tags:
  - spicy
  - heat
knowledge_panel:
  panel_id: scoville_scale
  level: info
  display_type: value_with_scale
```

## Input Widget Types

The `input_widget.type` field can specify different UI components:

- `text`: Simple text input
- `number`: Numeric input with optional min/max
- `slider`: Range slider with min/max/step
- `select`: Dropdown selection from permitted_values
- `multiselect`: Multiple selection from permitted_values
- `boolean`: Yes/No or checkbox
- `date`: Date picker
- `color`: Color picker
- `autocomplete`: Text input with suggestions

## Usage in Applications

These property definitions can be used by:

1. **Web components** (`openfoodfacts-webcomponents`) to render appropriate input fields
2. **Mobile apps** (`smooth-app`) to provide native property input experiences
3. **Knowledge panels** to display property information in a user-friendly way
4. **API clients** to validate property values before submission
5. **Documentation** to help users understand available properties

## Adding a New Property

1. Create a new YAML file in this directory named `{property_key}.yaml`
2. Follow the structure outlined above
3. Include at least the required fields
4. Add multilingual support for key user-facing strings
5. Configure appropriate input widgets based on the property type
6. Test the property through the API endpoint `/properties/{key}`

## API Access

Property documentation is available through the API:

- `GET /properties` - List all documented properties
- `GET /properties/{key}` - Get documentation for a specific property
- `GET /properties/{key}/knowledge-panel` - Get knowledge panel configuration for a property
