# Reusable Floating Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the current TOC sidebar/dialog shell into a reusable responsive floating panel and use it to place `/posts/` tags beside the post-entry list.

**Architecture:** A Hugo partial renders one self-contained panel instance from caller-provided title, icon, content, ID, and class. Shared CSS and JavaScript own layout, dialog behavior, animation, and focus, while TOC and tags files own only their content-specific presentation and behavior.

**Tech Stack:** Hugo templates and Pipes, HTML `<dialog>`, CSS media/container selectors, vanilla JavaScript, Python browser regression harness with headless Chrome.

**Spec:** `docs/superpowers/specs/2026-09-29-reusable-floating-panel-design.md`

## Global Constraints

- Use a 1000px breakpoint: sidebar above 1000px, trigger and dialog at 1000px and below.
- Keep the desktop sidebar exactly 240px wide and preserve the current left content width.
- Preserve the current 200ms dialog and backdrop animation, including reduced-motion behavior.
- Preserve existing tag ordering, destinations, counts, wrapping, rounded style, pagination, and post entries.
- Preserve all current TOC active-section, read-track, partial-progress, active-frame, and anchor-focus behavior.
- Move one content host between sidebar and dialog; never clone it.
- Render no component for empty TOC or tags content.
- Add no dependencies.

## Review Focus

- A component whose required child element is missing must be ignored without breaking other page scripts; pin this in Task 1's browser assertions.
- A width change while a dialog is open must close it, restore the content host to the correct container, and avoid duplicate content; pin this in Task 1.
- Multiple component instances must initialize independently without global ID or selector collisions; pin unique derived IDs and per-root queries in Task 1.
- A long tags collection must scroll inside the dialog and sidebar without horizontal page overflow; pin this in Task 2.
- Pages with no headings or without `showTags` must expose no empty trigger or dialog; pin this in Tasks 1 and 2.

---

### Task 1: Extract the shared panel and migrate TOC

**Files:**
- Create: `layouts/_partials/floating_panel.html`
- Create: `layouts/_partials/toc_content.html`
- Create: `assets/css/extended/floating-panel.css`
- Create: `assets/js/floating-panel.js`
- Modify: `layouts/_partials/toc.html`
- Modify: `layouts/_partials/header.html`
- Modify: `layouts/_partials/extend_footer.html`
- Modify: `assets/css/extended/toc.css`
- Modify: `assets/js/floating-toc.js`
- Test: `scripts/test_toc.py`

**Interfaces:**
- Consumes: the approved design and the existing `.toc`, `.inner`, `.toc-active-frame`, `.toc-section-progress`, and `.toc-section-progress-fill` hooks.
- Produces: `partial "floating_panel.html"` accepting `ID`, `Title`, `Label`, `TriggerIcon`, `Content`, and `Class`; a `.floating-panel[data-panel-id]` root with derived `-sidebar`, `-trigger`, and `-dialog` IDs; a `.floating-panel-content` host; a generic controller that initializes every `.floating-panel` root.

- [ ] **Step 1: Add failing shared-structure and ownership assertions**

Extend the existing article checks in `scripts/test_toc.py` to assert that the TOC lives inside `.floating-panel[data-panel-id="toc"]`, all trigger/sidebar/dialog IDs are unique and derived from `toc`, the content host is the same node after responsive moves, resize closes an open dialog, incomplete injected panel markup is ignored without an uncaught error, and a no-heading page has no TOC panel. Add source assertions that `header.html` contains no `toc-trigger`, `floating-panel.css` owns the 1000px/240px/dialog rules, `floating-panel.js` owns dialog calls, and `floating-toc.js` contains no `showModal`, `close()`, or `matchMedia` call.

- [ ] **Step 2: Run the browser regression and verify the new assertions fail**

Run: `python scripts/test_toc.py`

Expected: FAIL because `.floating-panel[data-panel-id="toc"]` and the shared files do not exist.

- [ ] **Step 3: Implement the shared Hugo markup**

Create `floating_panel.html` with the six documented inputs. Render a `.floating-panel` root, hidden `.floating-panel-trigger`, `.floating-panel-sidebar`, `.floating-panel-content`, and `.floating-panel-dialog` whose IDs derive from `ID`; wire `aria-controls`, `aria-expanded`, `aria-labelledby`, and the close button. Move the current TOC list generation into `toc_content.html`, and make `toc.html` render nothing when no headers exist or call the shared partial with `ID = "toc"` and `Class = "toc-panel"` when they do. Remove the global TOC trigger from `header.html`.

- [ ] **Step 4: Implement shared CSS and controller behavior**

Move all current responsive layout, 240px sidebar, fixed trigger, dialog, animation, backdrop, close-control, content scrolling, and modal-open rules from `toc.css` to class-based rules in `floating-panel.css`. Implement `floating-panel.js` as an IIFE that queries each root locally, validates required children, moves the single content host at `(min-width: 1001px)`, manages `showModal()`, animated close, Escape/backdrop clicks, `aria-expanded`, page scroll locking, resize closure, focus restoration, and same-page hash focus.

- [ ] **Step 5: Restrict TOC files to TOC behavior**

Keep only TOC list, nesting, active-frame, progress-segment, active-link, and heading scroll-margin rules in `toc.css`. Refactor `floating-toc.js` to query inside the `toc` panel root and retain only section construction, progress calculations, active-frame geometry, and scroll/resize scheduling. Load `floating-panel.js` before `floating-toc.js` in `extend_footer.html`, using the existing guarded Hugo Pipes pattern for both resources.

- [ ] **Step 6: Run the browser regression and verify Task 1 passes**

Run: `python scripts/test_toc.py`

Expected: PASS, including all pre-existing TOC progress and dialog assertions plus the new component-boundary assertions.

- [ ] **Step 7: Commit the shared panel migration**

```bash
git add layouts/_partials/floating_panel.html layouts/_partials/toc_content.html layouts/_partials/toc.html layouts/_partials/header.html layouts/_partials/extend_footer.html assets/css/extended/floating-panel.css assets/css/extended/toc.css assets/js/floating-panel.js assets/js/floating-toc.js scripts/test_toc.py
git commit -m "refactor: extract reusable floating panel"
```

### Task 2: Add the `/posts/` tags panel

**Files:**
- Create: `layouts/_partials/tags_panel.html`
- Create: `assets/css/extended/tags-panel.css`
- Modify: `layouts/list.html`
- Modify: `assets/css/extended/category-nav.css`
- Test: `scripts/test_toc.py`

**Interfaces:**
- Consumes: Task 1's `floating_panel.html` inputs and `.floating-panel[data-panel-id]` behavior.
- Produces: a `tags` panel instance on list pages with `showTags = true`, containing the current tag permalink, label, taxonomy count, and `category-btn` appearance.

- [ ] **Step 1: Add failing `/posts/` layout and dialog assertions**

Extend `scripts/test_toc.py` after loading `/posts/` to assert that `.floating-panel[data-panel-id="tags"]` exists, the old inline `.category-nav` is absent from the left column, every taxonomy tag retains its link text/count/href, tag buttons wrap, and the left post-entry column does not overlap the fixed 240px sidebar above 1000px. At widths 320, 390, 768, 900, and 1000 assert that the sidebar is replaced by a fixed tags trigger above the top-link position, the centered dialog opens and closes with animation/focus restoration, long injected tag content scrolls internally, and the document has no horizontal overflow. Assert that a list page without `showTags` has no tags panel.

- [ ] **Step 2: Run the browser regression and verify the tags assertions fail**

Run: `python scripts/test_toc.py`

Expected: FAIL because `/posts/` still renders `.category-nav` inline and has no `tags` floating panel.

- [ ] **Step 3: Render tags through the shared partial**

Create `tags_panel.html` to render the existing taxonomy iteration as a wrapping `.category-nav` and invoke `floating_panel.html` with `ID = "tags"`, `Title = "Tags"`, a hash/tag icon, and `Class = "tags-panel"`. In `list.html`, replace the inline `category-nav` block with this partial only when `.Params.showTags` is true and `site.Taxonomies.tags` is non-empty.

- [ ] **Step 4: Isolate tags presentation**

Move the `category-nav` and `category-btn` rules used by the panel from their current common stylesheet into `tags-panel.css`, retaining existing padding, count color, rounded shape, transitions, and wrapping. Add only the spacing needed for the shared sidebar/dialog content hosts; do not alter post-entry styling.

- [ ] **Step 5: Run the browser regression and verify Task 2 passes**

Run: `python scripts/test_toc.py`

Expected: PASS for both article TOC and `/posts/` tags behavior at every tested width.

- [ ] **Step 6: Commit the tags panel**

```bash
git add layouts/_partials/tags_panel.html layouts/list.html assets/css/extended/tags-panel.css assets/css/extended/category-nav.css scripts/test_toc.py
git commit -m "feat: add floating tags panel"
```

### Task 3: Final integration verification and generated site

**Files:**
- Modify: `public/**` generated by Hugo
- Verify: all source files changed in Tasks 1 and 2

**Interfaces:**
- Consumes: the complete shared panel, migrated TOC, and tags panel.
- Produces: a verified Hugo build and regenerated publication output.

- [ ] **Step 1: Run the complete browser regression from a clean temporary build**

Run: `python scripts/test_toc.py`

Expected: PASS with no failed assertion.

- [ ] **Step 2: Build the publication output**

Run: `hugo --noBuildLock`

Expected: exit 0 with 23 or more pages and no template/resource error.

- [ ] **Step 3: Inspect generated integration points**

Check `public/posts/index.html` for the `tags` panel IDs and shared script, check `public/posts/20260805hello-world/index.html` for the `toc` panel IDs and both shared/TOC scripts, and confirm each page references the newly fingerprinted stylesheet without duplicate panel roots.

- [ ] **Step 4: Run focused source hygiene checks**

Run trailing-whitespace checks on the changed source files and `git diff --check` limited to those source paths. Confirm that TOC-only progress selectors do not appear in `floating-panel.css` or `floating-panel.js`, and dialog/layout selectors do not remain in `toc.css` or `floating-toc.js`.

- [ ] **Step 5: Commit generated output and final integration fixes**

Stage only files belonging to this feature and the regenerated `public` output, review `git diff --cached --stat`, then commit:

```bash
git commit -m "build: publish reusable floating panels"
```
