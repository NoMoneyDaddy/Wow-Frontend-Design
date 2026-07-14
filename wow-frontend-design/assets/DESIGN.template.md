---
version: alpha
name: Project Design System
description: Replace this structural example with the project's visual contract.
colors:
  primary: "#1A1C1E"
  on-primary: "#FFFFFF"
  surface: "#F7F5F2"
  on-surface: "#1A1C1E"
typography:
  headline:
    fontFamily: system-ui
    fontSize: 48px
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: -0.02em
  body:
    fontFamily: system-ui
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
rounded:
  sm: 4px
  md: 8px
spacing:
  sm: 8px
  md: 16px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "{spacing.md}"
  base-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
---

# Project Design System

## Overview

Replace this text with the product-specific audience, personality, density, and emotional intent.

## Colors

Explain each semantic color role and when it must not be used.

## Typography

Explain type roles, hierarchy, localization, and long-content behavior.

## Layout

Explain the desktop grid, content width, spacing rhythm, and mobile transformation.

## Elevation & Depth

Explain how hierarchy uses tonal layers, borders, shadows, or deliberate flatness.

## Shapes

Explain the product-specific shape language and exceptions.

## Components

Explain shared component appearance, states, responsive representation, and unsupported details that do not belong in token frontmatter.

## Do's and Don'ts

- Do replace every example token and rationale with project-derived decisions.
- Don't fork the design system per page or breakpoint.
