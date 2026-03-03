# Signal Handler Race Condition Fix #1184

## Problem
The SIGTERM handler was directly calling `graceful_shutdown()`, which performed database operations synchronously. This could cause deadlocks during shutdown, especially:
- Shutdown during active transaction
- Concurrent termination signals
- Heavy load scenarios

## Solution
Modified the signal handler in `app/main.py` to defer the shutdown operation using Tkinter's `root.after(0, app.graceful_shutdown)`. This ensures:
- Signal handler returns immediately (no blocking DB operations)
- Shutdown cleanup happens in the Tkinter event loop
- Race conditions are avoided

## Changes Made
1. **app/main.py**: Changed signal handler to defer shutdown call
2. **test_signal_race_condition_fix.py**: Added comprehensive test suite

## Technical Details
- Signal handlers should be fast and not perform complex operations
- DB operations during shutdown can deadlock if transactions are active
- Using `root.after()` schedules the cleanup in the event loop, allowing the signal handler to return quickly

## Testing
- Created test script that validates the deferral mechanism
- Checks for proper DB session handling in shutdown
- Verifies logging of shutdown sequence
- All tests pass

## Edge Cases Handled
- Concurrent signals: Multiple `root.after()` calls are queued safely
- Active transactions: DB operations happen after signal handler returns
- Platform compatibility: SIGTERM handling remains optional for Windows