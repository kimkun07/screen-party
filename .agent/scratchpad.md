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
[x] Simplify MainWindow to use State + CanvasManager
[x] Make UI updates declarative (read state, update UI)
[x] Remove direct state mutation from UI components

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
[x] Test session creation flow
[x] Test session join flow
[x] Test drawing functionality
[x] Test overlay creation and resize
[x] Test participant join/leave
[x] Test color/alpha changes
[x] All 91 tests passing

## Final Cleanup

[x] Fix linting errors (31 errors found)
  - Removed unused imports (26 auto-fixed)
  - Fixed E402 import order in scripts/main.py (added noqa comments)
  - Removed extraneous f-string prefixes (auto-fixed)
  - Removed unused local variable in test_incremental_fitter.py

## Refactoring Complete! ✅

### Summary of Changes

**Files Created:**
- `client/src/screen_party_client/gui/state.py` - AppState class (201 lines)
- `client/src/screen_party_client/drawing/canvas_manager.py` - CanvasManager (117 lines)
- `client/src/screen_party_client/network/message_handler.py` - MessageHandler (165 lines)

**Files Modified:**
- `client/src/screen_party_client/gui/main_window.py` - Refactored (1,050 → 984 lines, -66 lines)
- `client/src/screen_party_client/drawing/canvas.py` - Fixed None color handling
- `client/tests/test_main_window_gui.py` - Updated tests for new architecture

**Files Deleted:**
- `client/src/screen_party_client/gui/floating_menu.py` (136 lines, unused)
- `client/src/screen_party_client/gui/window_selector.py` (153 lines, unused)
- `client/src/screen_party_client/test_clickthrough.py` (366 lines, test utility)

**Total Code Reduction:**
- Removed: ~655 lines (unused code)
- Added: ~483 lines (new architecture)
- Net: -172 lines with better organization

### Key Improvements

1. **Single Source of Truth**: All state centralized in AppState
2. **No Code Duplication**: Eliminated participant init and canvas sync duplication
3. **Separation of Concerns**: Clear boundaries between UI, state, canvas, and network
4. **Declarative UI**: Observer pattern for reactive UI updates
5. **Testability**: State and message handling can be tested independently
6. **Maintainability**: Clear data flow and responsibilities

### Test Results
✅ **91/91 tests passing**
- All drawing engine tests passing
- All GUI tests passing
- All state management tests passing

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
