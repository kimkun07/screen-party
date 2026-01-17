# Refactoring: UI State Management

## Goal
1. **Declarative UI**: Create a central State object that manages all application state
2. **Centralized Updates**: One place that updates all UI elements based on state changes
3. **Reduce Code Duplication**: Eliminate repeated participant initialization and dual-canvas updates
4. **Remove Unused Code**: Delete unused files and unnecessary code

## Current Problems
- Dual canvas synchronization scattered across 6+ locations
- Participant color/alpha initialization duplicated 3 times
- Direct mutable state access (user_colors, user_alphas dicts)
- 1,049-line MainWindow with mixed responsibilities
- Unused files: floating_menu.py (136 lines), window_selector.py (153 lines)
- State updates are imperative and scattered

## Tasks

### Phase 1: Create State Management System
[x] Create `AppState` class to hold all application state
  - Connection state: session_id, user_id, is_connected
  - Overlay state: is_sharing, overlay_window reference
  - Drawing state: current_alpha, pen_color
  - Participants: centralized user_colors and user_alphas
[x] Create state update methods with notifications
[x] Add state observers/listeners pattern

### Phase 2: Centralize Canvas Management
[x] Create `CanvasManager` to handle dual-canvas synchronization
  - Manages both main canvas and overlay canvas
  - Single update methods for color/alpha changes
  - Single update methods for drawing events
  - Participant add/remove methods
[x] Remove duplicated canvas update logic from MainWindow (done in CanvasManager)

### Phase 3: Refactor MainWindow
[x] Extract message handling to `MessageHandler` class
[ ] Simplify MainWindow to use State + CanvasManager (in progress)
[ ] Make UI updates declarative (read state, update UI)
[ ] Remove direct state mutation from UI components

### Phase 4: Remove Code Duplication
[x] Extract participant initialization to single method (done via AppState)
[x] Use CanvasManager for all canvas updates
[x] Consolidate color/alpha update logic (centralized in MessageHandler)

### Phase 5: Clean Up Unused Code
[x] Delete floating_menu.py (unused)
[x] Delete window_selector.py (unused)
[x] Remove test_clickthrough.py if not needed
[x] Clean up any other dead code

### Phase 6: Testing & Validation
[ ] Test session creation flow
[ ] Test session join flow
[ ] Test drawing functionality
[ ] Test overlay creation and resize
[ ] Test participant join/leave
[ ] Test color/alpha changes
[ ] Run linting and type checking

## File Structure (Proposed)
```
client/src/screen_party_client/
├── gui/
│   ├── main_window.py (simplified)
│   ├── overlay_window.py
│   ├── constants.py
│   └── state.py (NEW - AppState class)
├── drawing/
│   ├── canvas.py
│   ├── canvas_manager.py (NEW - manages dual canvas)
│   └── ...
├── network/
│   ├── client.py
│   └── message_handler.py (NEW - extracted from MainWindow)
└── ...
```

## Success Criteria
- State is managed centrally in AppState
- UI updates are declarative
- No duplicated participant initialization code
- No duplicated canvas synchronization code
- Unused files removed
- All tests pass
- Code is more maintainable and readable
