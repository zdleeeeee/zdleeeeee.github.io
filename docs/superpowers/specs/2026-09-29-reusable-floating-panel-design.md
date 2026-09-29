# Reusable Floating Panel Design

## Goal

Extract the responsive sidebar and dialog behavior from the existing floating table of contents into a reusable component. Use that component for both the post TOC and the tags navigation on `/posts/`.

The result keeps post entries in the existing left content column, places tags in a fixed right sidebar on screens wider than 1000px, and replaces that sidebar with a floating tags button and centered dialog on screens 1000px wide or narrower.

## Scope

This change covers:

- the reusable desktop sidebar, narrow-screen trigger, dialog, animation, and focus behavior;
- migration of the existing TOC to that shared structure;
- a tags panel on list pages where `showTags` is enabled;
- preservation of all TOC reading-progress behavior;
- responsive and browser regression coverage.

It does not change tag ordering, tag destinations, pagination, post-entry content, or the 1000px breakpoint.

## Component Boundary

Create a `floating_panel.html` partial that accepts:

- a unique component ID;
- a title and accessible label;
- the trigger icon markup;
- rendered panel content;
- an optional caller-specific class.

The partial renders one component containing:

- a desktop `<aside>`;
- a narrow-screen trigger button;
- a labeled `<dialog>`;
- a dialog header and close button;
- a content host that can move between the sidebar and dialog.

Each instance exposes its elements through shared classes and a `data-floating-panel` identifier. The reusable controller initializes every complete component independently and does not depend on TOC or tags selectors.

## Files and Responsibilities

### Shared floating panel

- `layouts/_partials/floating_panel.html` owns the shared markup.
- `assets/css/extended/floating-panel.css` owns the two-column layout, fixed sidebar, trigger, dialog, animation, and responsive breakpoint.
- `assets/js/floating-panel.js` owns responsive content placement, opening and closing, focus restoration, Escape handling, backdrop clicks, and shared link behavior.

### Table of contents

- `layouts/_partials/toc.html` builds only TOC content and passes it to the floating panel partial.
- `assets/css/extended/toc.css` owns TOC list hierarchy, title rows, active frame, and progress segments.
- `assets/js/floating-toc.js` owns heading lookup, visible-section state, read state, active-frame geometry, and per-section progress. It does not open dialogs, move content, or evaluate responsive breakpoints.

The TOC content retains its current DOM hooks for progress and active-section rendering.

### Tags panel

- `layouts/list.html` builds the tags content when `.Params.showTags` is true and invokes the floating panel partial.
- `assets/css/extended/tags-panel.css` owns tag wrapping, rounded tag buttons, counts, and tags-specific spacing.

The current tag links and counts remain unchanged. The panel adds a visible `Tags` heading while preserving the existing button appearance.

### Global integration

- Remove the TOC-only hidden trigger from `layouts/_partials/header.html`.
- Load the generic floating-panel script through Hugo Pipes alongside the TOC-specific script.
- Both scripts must safely return when their expected markup is absent.

## Responsive Layout

The shared breakpoint is 1000px.

Above 1000px:

- the trigger and dialog are inactive;
- the content host lives inside a fixed 240px-wide right sidebar;
- `.main` expands and reserves right-side space whenever it contains a populated floating panel;
- the left content column retains the current `--main-width` width;
- the sidebar remains within the viewport and scrolls internally when necessary.

At 1000px and below:

- the desktop sidebar is hidden;
- the content host moves into the dialog body;
- a fixed circular trigger appears above the go-to-top control;
- the dialog is centered and bounded by the viewport;
- long content scrolls inside the dialog without causing page overflow.

Only one of the current page types uses a panel at a time, but the shared controller must support multiple independent instances without duplicate IDs or global selector collisions.

## Dialog Behavior and Accessibility

The trigger carries `aria-haspopup="dialog"`, `aria-controls`, and `aria-expanded`. Opening the dialog focuses its close control. Closing it with the button, Escape, or a backdrop click restores focus to the trigger.

Opening and closing retain the current 200ms opacity, scale, vertical movement, and backdrop animations. Reduced-motion users receive an effectively immediate animation.

Clicking an ordinary link such as a tag follows the link normally. Clicking a same-page TOC hash closes the dialog first, then focuses the target heading without changing the established anchor-scroll behavior.

The trigger starts hidden and is enabled by the shared controller only after the component has valid content. This prevents an unusable control when JavaScript or required markup is unavailable.

## Empty and Failure States

- A post with no headings renders no TOC panel, trigger, or dialog.
- A list page without tags, or without `showTags`, renders no tags panel, trigger, or dialog.
- An incomplete component is ignored by the shared controller.
- A missing JavaScript resource produces a Hugo build warning through the existing guarded resource-loading pattern.
- Moving a content host between containers must not clone it, preventing duplicate links, IDs, or event targets.

## Verification

Extend the browser regression coverage in `scripts/test_toc.py` to verify both shared behavior and caller-specific behavior:

- the desktop TOC remains fixed on the right and does not overlap the article;
- TOC active headings, completed tracks, partial progress, and the active frame remain correct;
- `/posts/` renders post entries in the left column and a fixed tags panel on the right;
- existing tag labels, counts, links, wrapping, and rounded styles remain intact;
- widths up to and including 1000px show a trigger and dialog, while wider widths show the sidebar;
- the tags dialog is centered, scrollable, animated, and restores focus after closing;
- all tested widths avoid horizontal overflow;
- pages without component content do not expose an empty trigger or dialog;
- generic markup and behavior use shared selectors, while TOC progress selectors remain confined to TOC files.

Run the browser regression test and a full `hugo --noBuildLock` build before completion. Regenerate `public` only after the source implementation passes.
