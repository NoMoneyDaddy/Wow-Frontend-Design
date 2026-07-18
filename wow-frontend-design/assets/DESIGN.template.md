---
version: alpha
name: Project Design System
description: Replace this guidance with the product's evidence-derived visual contract.
---

# Project Design System

## Overview

Name the product evidence that determines audience, tasks, personality, density, and emotional intent. State which decisions are explicit, observed, inferred, inherited, or still unknown.

## Colors

Define only product-required semantic color roles. For each role, identify the surface or state it serves, its foreground/background relationship, and where it must not be used.

## Typography

Derive type roles from the product's information hierarchy and content. Explain the relationships among those roles, localization needs, and long-content behavior before adding project-owned typography tokens.

## Layout

Describe the product's information order, spatial relationships, reading measure, density, and how composition transforms across supported viewports and input modes. Add spacing tokens only when repeated runtime relationships require them.

## Elevation & Depth

Explain how product hierarchy and interaction states use depth. Write `none` when depth is intentionally absent, or `inherited` with the source when an existing system owns it.

## Shapes

Explain any product-derived shape roles and their relationships to content or interaction. Write `none` when no shape system is needed, or `inherited` with the source when an existing system owns it.

## Components

Document only shared components earned by repeated product behavior, including their role relationships, states, and responsive representation. Write `none` when no shared component contract is needed, or `inherited` with the source when an existing system owns it.

## Do's and Don'ts

- Do add only project-derived tokens that are consumed by the runtime.
- Do preserve `none`, `inherited`, and `unknown` when the product evidence does not justify a new visual decision.
- Don't fork the design system per page or breakpoint.
- Don't treat this token-free template as a palette, type scale, spacing scale, shape recipe, or component inventory.
