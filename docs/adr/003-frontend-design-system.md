# ADR-003: Frontend Design System and Interaction Model

- Status: Accepted
- Date: 2026-06-25

## Audience and Style

The console is an operational workbench for consultants who review many
controls and documents for long periods. The interface uses a restrained,
dark, information-dense visual system inspired by professional coding tools.

## Layout

- Fixed 224px desktop navigation and a 56px context header.
- Mobile navigation uses an accessible drawer.
- Page sections are unframed; cards are reserved for bounded tools and repeated
  records.
- Control Matrix uses three stable panes: controls, evidence/draft, review.
- Long lists use tables, filters, sticky headers, and keyboard navigation.

## Components

- Tailwind CSS variables define semantic colors.
- Radix Primitives provide accessible dialogs, menus, tabs, and tooltips.
- Lucide supplies all standard interface icons.
- TanStack Query owns server state.
- TanStack Table owns dense control and review grids.
- React Hook Form and Zod will own complex forms.
- OpenAPI-generated types define the transport contract.

## Actions

- One primary action per page.
- Familiar icon-only actions use tooltips and accessible names.
- Destructive actions live in overflow menus and require confirmation.
- Disabled actions explain the missing prerequisite.
- Layout dimensions remain stable during loading and mutation states.

## Quality Gates

- TypeScript strict mode
- Vitest and Testing Library component tests
- MSW-backed API behavior tests
- Playwright desktop and narrow-screen workflows
- screenshot regression for core pages
- WCAG 2.2 keyboard, focus, name, and contrast checks
