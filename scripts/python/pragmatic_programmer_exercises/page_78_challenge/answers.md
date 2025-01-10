# Answers to Questions in the exercise

## Which form was easier to modify?

The JSON/plain-text version was easier to modify because you could directly add fields (e.g., directions) without changing the binary representation or structure.

## What about converting existing data?

With the JSON format, you can write a simple script to read the old data, add default values for new fields, and save the updated version. Binary formats would require more complex parsing and encoding logic.

## Versioning and Extensibility Issues?

Adding a version field to the JSON data helps manage backward compatibility. Converting existing data requires handling missing fields gracefully.
