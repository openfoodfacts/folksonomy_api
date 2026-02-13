# Property Documentation Integration Guide

This guide explains how to integrate the property documentation system into web components and mobile applications.

## Overview

The property documentation system provides metadata that can be used to:

1. **Generate dynamic input forms** with appropriate widgets
2. **Display property information** in knowledge panels
3. **Validate user input** against permitted values
4. **Provide multilingual UI** based on user preferences
5. **Show visual aids** like icons and images

## API Endpoints

### Get All Properties

```http
GET /properties
```

Returns a list of all documented properties with basic information.

**Optional Parameters:**
- `q` - Search query to filter properties
- `language` - Language code for search (default: en)

**Response:**
```json
[
  {
    "key": "scoville_scale",
    "name": {
      "en": "Scoville Scale",
      "fr": "Échelle de Scoville"
    },
    "icon": "🌶️",
    "value_type": "number"
  }
]
```

### Get Property Documentation

```http
GET /properties/{key}
```

Returns complete documentation for a specific property.

**Response:**
```json
{
  "key": "scoville_scale",
  "name": {
    "en": "Scoville Scale",
    "fr": "Échelle de Scoville"
  },
  "description": {
    "en": "Measures the spiciness or heat of chili peppers..."
  },
  "icon": "🌶️",
  "value_type": "number",
  "unit": "SHU",
  "permitted_values": [...],
  "input_widget": {
    "type": "slider",
    "min": 0,
    "max": 100000,
    "step": 100
  },
  "knowledge_panel": {...}
}
```

### Get Knowledge Panel Configuration

```http
GET /properties/{key}/knowledge-panel
```

Returns knowledge panel configuration for displaying a property.

## Web Component Integration

### Example: Dynamic Form Generator

```javascript
// Fetch property documentation
async function createPropertyInput(propertyKey, language = 'en') {
  const response = await fetch(`/properties/${propertyKey}`);
  const property = await response.json();
  
  // Create input based on widget type
  switch (property.input_widget.type) {
    case 'slider':
      return createSliderInput(property, language);
    case 'select':
      return createSelectInput(property, language);
    case 'multiselect':
      return createMultiSelectInput(property, language);
    case 'color':
      return createColorInput(property, language);
    default:
      return createTextInput(property, language);
  }
}

function createSliderInput(property, language) {
  const widget = property.input_widget;
  const label = property.name[language] || property.name.en;
  const helpText = widget.helper_text?.[language] || widget.helper_text?.en || '';
  
  return `
    <div class="property-input">
      <label>
        ${property.icon} ${label}
        <span class="help-text">${helpText}</span>
      </label>
      <input 
        type="range" 
        min="${widget.min}" 
        max="${widget.max}" 
        step="${widget.step}"
        data-property="${property.key}"
        data-unit="${widget.unit_display || property.unit || ''}"
      />
      <output></output>
    </div>
  `;
}

function createSelectInput(property, language) {
  const label = property.name[language] || property.name.en;
  const options = property.permitted_values.map(pv => {
    const optionLabel = pv.label[language] || pv.label.en;
    const image = property.images?.[pv.value];
    
    if (image) {
      return `<option value="${pv.value}" data-image="${image}">${optionLabel}</option>`;
    }
    return `<option value="${pv.value}">${optionLabel}</option>`;
  });
  
  return `
    <div class="property-input">
      <label>
        ${property.icon} ${label}
      </label>
      <select data-property="${property.key}">
        ${options.join('\n')}
      </select>
    </div>
  `;
}
```

### Example: Knowledge Panel Display

```javascript
async function displayPropertyInKnowledgePanel(propertyKey, value, language = 'en') {
  const response = await fetch(`/properties/${propertyKey}/knowledge-panel`);
  const panel = await response.json();
  const property = await (await fetch(`/properties/${propertyKey}`)).json();
  
  const name = property.name[language] || property.name.en;
  const displayValue = formatPropertyValue(property, value, language);
  
  return `
    <div class="knowledge-panel-item level-${panel.level}">
      <span class="icon">${property.icon}</span>
      <div class="content">
        <strong>${name}</strong>
        <span class="value">${displayValue}</span>
      </div>
    </div>
  `;
}

function formatPropertyValue(property, value, language) {
  // Find label for permitted value
  const permittedValue = property.permitted_values?.find(pv => pv.value === value);
  if (permittedValue) {
    return permittedValue.label[language] || permittedValue.label.en;
  }
  
  // Add unit if present
  if (property.unit) {
    return `${value} ${property.unit}`;
  }
  
  return value;
}
```

## Mobile App Integration (Flutter Example)

### Example: Property Input Widget Builder

```dart
import 'package:flutter/material.dart';

class PropertyInputBuilder {
  Future<Widget> buildInput(String propertyKey, {String language = 'en'}) async {
    final property = await fetchProperty(propertyKey);
    
    switch (property.inputWidget.type) {
      case 'slider':
        return _buildSliderInput(property, language);
      case 'select':
        return _buildSelectInput(property, language);
      case 'multiselect':
        return _buildMultiSelectInput(property, language);
      case 'color':
        return _buildColorInput(property, language);
      default:
        return _buildTextInput(property, language);
    }
  }
  
  Widget _buildSliderInput(Property property, String language) {
    final label = property.name[language] ?? property.name['en']!;
    final widget = property.inputWidget;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(property.icon, style: TextStyle(fontSize: 24)),
            SizedBox(width: 8),
            Text(label, style: TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
        Slider(
          min: widget.min.toDouble(),
          max: widget.max.toDouble(),
          divisions: ((widget.max - widget.min) / widget.step).round(),
          label: '${_currentValue} ${widget.unitDisplay ?? property.unit ?? ''}',
          onChanged: (value) {
            // Handle value change
          },
        ),
        if (widget.helperText != null)
          Text(
            widget.helperText[language] ?? widget.helperText['en']!,
            style: TextStyle(fontSize: 12, color: Colors.grey),
          ),
      ],
    );
  }
  
  Widget _buildSelectInput(Property property, String language) {
    final label = property.name[language] ?? property.name['en']!;
    final items = property.permittedValues.map((pv) {
      final itemLabel = pv.label[language] ?? pv.label['en']!;
      return DropdownMenuItem(
        value: pv.value,
        child: Row(
          children: [
            if (property.images?.containsKey(pv.value) ?? false)
              Image.network(property.images![pv.value]!, width: 24, height: 24),
            SizedBox(width: 8),
            Text(itemLabel),
          ],
        ),
      );
    }).toList();
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(property.icon, style: TextStyle(fontSize: 24)),
            SizedBox(width: 8),
            Text(label, style: TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
        DropdownButton(
          items: items,
          onChanged: (value) {
            // Handle value change
          },
        ),
      ],
    );
  }
}
```

## React Native Integration

### Example: Property Input Component

```javascript
import React from 'react';
import { View, Text, Slider, Picker } from 'react-native';

const PropertyInput = ({ propertyKey, value, onChange, language = 'en' }) => {
  const [property, setProperty] = React.useState(null);
  
  React.useEffect(() => {
    fetch(`/properties/${propertyKey}`)
      .then(res => res.json())
      .then(setProperty);
  }, [propertyKey]);
  
  if (!property) return null;
  
  const label = property.name[language] || property.name.en;
  const widget = property.input_widget;
  
  switch (widget.type) {
    case 'slider':
      return (
        <View>
          <Text>{property.icon} {label}</Text>
          <Slider
            minimumValue={widget.min}
            maximumValue={widget.max}
            step={widget.step}
            value={value}
            onValueChange={onChange}
          />
          <Text>{value} {widget.unit_display || property.unit || ''}</Text>
        </View>
      );
      
    case 'select':
      return (
        <View>
          <Text>{property.icon} {label}</Text>
          <Picker
            selectedValue={value}
            onValueChange={onChange}
          >
            {property.permitted_values.map(pv => (
              <Picker.Item
                key={pv.value}
                label={pv.label[language] || pv.label.en}
                value={pv.value}
              />
            ))}
          </Picker>
        </View>
      );
      
    default:
      return <Text>Unsupported widget type: {widget.type}</Text>;
  }
};

export default PropertyInput;
```

## Best Practices

1. **Cache property documentation** to reduce API calls
2. **Fallback to English** if requested language is not available
3. **Validate user input** against permitted values and formats
4. **Show helpful error messages** using the property's description
5. **Use icons and images** to improve visual clarity
6. **Implement responsive layouts** for different screen sizes
7. **Support keyboard navigation** for accessibility

## Example: Full Form Integration

```javascript
// Web Component Example
class FolksonomyPropertyForm extends HTMLElement {
  async connectedCallback() {
    const properties = await this.fetchRelevantProperties();
    const language = this.getAttribute('language') || 'en';
    
    this.innerHTML = `
      <form class="folksonomy-form">
        ${properties.map(prop => this.renderPropertyInput(prop, language)).join('')}
        <button type="submit">Save Properties</button>
      </form>
    `;
    
    this.setupEventListeners();
  }
  
  async fetchRelevantProperties() {
    // Fetch properties relevant to the product
    const category = this.getAttribute('category');
    const response = await fetch(`/properties?q=${category}`);
    return response.json();
  }
  
  renderPropertyInput(property, language) {
    // Render appropriate input based on property configuration
    // Implementation from examples above
  }
  
  setupEventListeners() {
    this.querySelector('form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      await this.saveProperties(formData);
    });
  }
}

customElements.define('folksonomy-property-form', FolksonomyPropertyForm);
```

## Testing Your Integration

```javascript
// Test that property documentation is correctly fetched
test('fetch property documentation', async () => {
  const response = await fetch('/properties/scoville_scale');
  const property = await response.json();
  
  expect(property.key).toBe('scoville_scale');
  expect(property.input_widget.type).toBe('slider');
  expect(property.name.en).toBe('Scoville Scale');
});

// Test widget rendering
test('render slider widget', () => {
  const property = {
    key: 'scoville_scale',
    name: { en: 'Scoville Scale' },
    icon: '🌶️',
    input_widget: { type: 'slider', min: 0, max: 100000, step: 100 }
  };
  
  const widget = createSliderInput(property, 'en');
  expect(widget).toContain('type="range"');
  expect(widget).toContain('min="0"');
  expect(widget).toContain('max="100000"');
});
```

## Additional Resources

- [Property Documentation README](./README.md) - YAML schema and structure
- [API Documentation](https://api.folksonomy.openfoodfacts.org/docs) - Interactive API docs
- [openfoodfacts-webcomponents](https://github.com/openfoodfacts/openfoodfacts-webcomponents) - Web components repository
- [smooth-app](https://github.com/openfoodfacts/smooth-app) - Mobile app repository
