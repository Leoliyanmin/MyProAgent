# ProAgent Theme Settings TODO

## Sprint Goal
- Build a theme customization workflow with edit mode, live preview, and backend persistence.

## Progress Rules
- Status values: `todo` | `doing` | `blocked` | `done`
- Every task must include owner + expected output
- Daily update: move at least 1 item to `done` or explain blocker

## Milestone M1: Frontend Theme Editor MVP (You own)
- [x] status: done  | owner: FE | Add "主题设置" entry in common features and route/view switch.
- [x] status: done  | owner: FE | Implement "主题编辑模式" toggle (normal/edit mode).
- [x] status: done  | owner: FE | Overlay editor directly on top of live workspace UI (not separate preview page).
- [x] status: done  | owner: FE | Add clickable region layer (sidebar/topbar/content) with active highlight.
- [x] status: done  | owner: FE | Build floating right-side style panel (primary color, text color, card bg color).
- [x] status: done  | owner: FE | Add color picker + hex input + radius slider.
- [x] status: done  | owner: FE | Apply live preview using CSS variables.
- [x] status: done  | owner: FE | Add reset/undo/redo/save buttons.

## Milestone M1.5: Overlay UX Refinement
- [ ] status: todo | owner: FE | Make overlay region boxes auto-fit actual layout bounds (agent sidebar open/closed aware).
- [ ] status: todo | owner: FE | Add click-through lock option to prevent accidental interactions in underlying page.
- [ ] status: todo | owner: FE | Add tooltip labels following cursor like screenshot tools.

## Milestone M2: Module-Level Style Customization
- [ ] status: todo | owner: FE | Define module map: dashboard widgets, calendar blocks, topbar, sidebar.
- [ ] status: todo | owner: FE | Support per-module style override on top of global theme tokens.
- [ ] status: todo | owner: FE | Add visual indicator showing which module is currently editable.
- [ ] status: todo | owner: FE | Add conflict fallback (module override missing -> use global token).

## Milestone M3: Image Upload + Background Customization
- [ ] status: todo | owner: FE | Add image upload button in theme panel.
- [ ] status: todo | owner: FE | Add upload preview (cover/contain/repeat/position/overlay opacity).
- [ ] status: todo | owner: FE | Add upload state UI (uploading/success/error).
- [ ] status: todo | owner: FE | Add image validation (type/size constraints).

## Milestone M4: Backend API (You can also own)
- [ ] status: todo | owner: BE | POST /assets/upload: upload user background image and return URL.
- [ ] status: todo | owner: BE | GET /theme/current: return current theme by user.
- [ ] status: todo | owner: BE | POST /theme/draft: save user draft theme.
- [ ] status: todo | owner: BE | POST /theme/publish: publish draft and increment themeVersion.
- [ ] status: todo | owner: BE | Add schema: globalTokens + moduleOverrides + metadata.
- [ ] status: todo | owner: BE | Add validation: contrast checks, token whitelist, URL safety.

## Integration & QA
- [ ] status: todo | owner: FE+BE | Define API contract examples (request/response JSON).
- [ ] status: todo | owner: FE+BE | End-to-end test: save theme -> refresh -> consistent render.
- [ ] status: todo | owner: FE+BE | Error fallback: API failure keeps previous stable theme.
- [ ] status: todo | owner: FE+BE | Performance check for edit mode interactions.

## This Week Suggested Start Order
1. M1.1 + M1.2 + M1.6 (entry, edit-mode switch, CSS variable live preview)
2. M1.4 + M1.5 (right panel + color controls)
3. M4 API skeleton (upload + current + draft)
4. Integration test and bug fixing
