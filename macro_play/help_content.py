from __future__ import annotations


HELP_SECTIONS: tuple[tuple[str, str], ...] = (
    (
        "Quick start",
        """Macro Play records mouse and keyboard activity, turns it into an editable action timeline, and plays it back later.

1. Select Record.
2. Perform the task in the other application.
3. Return to Macro Play and select Stop.
4. Review the recorded actions.
5. Save the macro.
6. Select Play, or use an assigned global hotkey.

Start with one repeat and normal speed until you have confirmed that a new macro behaves correctly.""",
    ),
    (
        "Main window",
        """The top controls start recording and playback and provide New, Open, Save, and Help commands.

The Action timeline lists every recorded step. The Wait column is the pause before an action starts. Length is the time used by actions such as mouse movement or an explicit Wait action.

Playback settings control the macro name, repeat count, continuous looping, playback speed, window restoration, and global hotkeys. The progress area shows the macro currently playing.""",
    ),
    (
        "Numbered macro selector",
        """The red buttons across the top are independent macro slots. Ten buttons are visible at a time. Use the left and right arrow buttons to move between Macro 1–10, Macro 11–20, and higher ranges.

Select a slot before recording or opening a file. Each slot keeps its own action timeline, loaded file, unsaved state, and hotkey for the current session. Switching slots does not erase unsaved work. An asterisk on a button means that slot has unsaved changes.

To build several macros, select Macro 1, record or open its actions, and assign its hotkey. Then select Macro 2 and repeat. A slot hotkey plays that slot directly even while a different slot is visible.

Macro slots are cleared when the application starts. Save each macro to a .macro.json file if you want to use it in a later session.""",
    ),
    (
        "Record a macro",
        """Select Record, then perform the workflow normally. Macro Play captures global mouse movement, clicks, dragging, scrolling, and keyboard input. Ordinary typing is consolidated into readable Type text actions. Mouse movement between interactions is consolidated so the timeline is not flooded with coordinate samples.

Return to Macro Play and select Stop when finished. Interactions performed inside Macro Play are ignored while recording.

If the current timeline already contains actions, Macro Play asks before replacing it. Save work you want to keep before starting a new recording.""",
    ),
    (
        "Edit actions",
        """Select an action and choose Edit, or double-click its row. Depending on the action, you can change its wait time, duration, coordinates, mouse button, key, text, or window details.

Use Add to insert a new action after the current selection. Duplicate copies the selected action. The up and down arrows reorder one selected action. Delete removes every selected action. Enable / disable keeps selected actions in the file but excludes them from playback.

Selecting a mouse action displays a temporary crosshair at its recorded screen position. This preview does not move the pointer or perform a click.""",
    ),
    (
        "Set wait times and lengths",
        """Wait is the pause before an action begins. Length is the action's duration, such as the travel time for mouse movement, the hold time for a click, or the duration of an explicit Wait action.

1. Select the first action you want to change.
2. Hold Ctrl while clicking additional individual actions, or hold Shift to select a range.
3. Select Set wait or Set length.
4. Enter the value in seconds and select OK.

The same value is applied to every selected action. All other action settings remain unchanged, and the edited rows stay selected. A wait value of 0 removes the added pre-action pause. A length of 0 makes supported actions complete immediately.""",
    ),
    (
        "Play a macro",
        """Set Repeat to the number of times the macro should run, or enable Loop until stopped. Playback speed ranges from slower than recorded to faster than recorded. Restore window positions asks Macro Play to focus and resize recorded windows before their actions run.

Select Play to begin. Pause temporarily stops progress; Resume continues. Select Stop to end playback. Ctrl+F8 is the emergency stop and works even when another application has focus.

Playback sends real mouse and keyboard input. Avoid touching the mouse or typing unless the macro is paused or stopped.""",
    ),
    (
        "Selected slot hotkey",
        """The Current macro hotkey belongs to the selected numbered slot. When you open a macro file into that slot, the loaded macro immediately becomes its hotkey target. Macro 1 defaults to Ctrl+F9.

Select Change, then physically press the desired combination. Modifier combinations, function keys, and navigation keys are supported. Letters and numbers require Ctrl, Alt, Shift, or Cmd. Select Disable hotkey if you do not want a global shortcut for the open macro.

F8 and Ctrl+F8 cannot be assigned because they are reserved for emergency stop. If a shortcut is already used by another slot or saved-macro assignment, a warning explains that it is already in use for the session. Custom hotkeys are cleared and Macro 1's Ctrl+F9 is restored whenever Macro Play starts.""",
    ),
    (
        "Saved macro hotkeys",
        """Different hotkeys can launch different saved macros.

1. Save each recording as a .macro.json file.
2. Select Saved macro hotkeys.
3. Select Add saved macro and choose its file.
4. Press the shortcut you want to assign.
5. Repeat for each additional macro, then select Save.

Use Change hotkey or Remove to maintain an assignment. Duplicate shortcuts are not allowed. Macro Play must remain running for global hotkeys to work. Saved-macro assignments are session-only and are cleared the next time Macro Play starts; saved .macro.json files are not deleted.

An assigned macro is read from its saved file each time its hotkey is pressed. It does not replace unsaved work in the editor. It uses the repeat, loop, speed, and window-restore settings currently displayed in Macro Play. If a file was moved or deleted, the manager marks it as missing; remove that assignment and add the file again from its new location.""",
    ),
    (
        "Save and open files",
        """Select Save or press Ctrl+S to store a recording. Macro Play uses the .macro.json extension. The files are human-readable, portable recordings that include the macro name and all action settings.

Select Open or press Ctrl+O to load a saved macro. New or Ctrl+N clears the editor after giving you an opportunity to save unsaved changes.

Moving a macro file does not damage it. When a file is opened, the current macro hotkey immediately targets it. Saved-macro assignments still point to their original locations for the rest of that session.""",
    ),
    (
        "Keyboard shortcuts",
        """F1 — Open this Help manual
F5 — Play the macro currently open in the editor
Ctrl+R — Start or stop recording
Ctrl+O — Open a saved macro
Ctrl+S — Save the current macro
Ctrl+N — Create a new macro
Delete — Remove selected timeline actions
Ctrl+F8 — Emergency playback stop
Ctrl+F — Focus search while the Help manual is open
Esc — Close the Help manual

The current macro hotkey and saved-macro hotkeys are user configurable.""",
    ),
    (
        "Troubleshooting",
        """A hotkey does nothing: Keep Macro Play running, confirm the assignment is not marked missing, and make sure another Macro Play playback or recording is not already active.

Clicks target the wrong place: Restore the target window to the layout used during recording, enable Restore window positions, or edit the recorded coordinates. Select the action to preview its target.

An application ignores playback: On Windows, an elevated application may require Macro Play to run as administrator. On macOS, grant Accessibility permission to Macro Play, or to Terminal when running from source.

A saved macro cannot be found: Open Saved macro hotkeys, remove the missing assignment, and add the file from its new location.

Playback timing is unreliable: Increase the wait before actions that depend on a window, page, or application finishing work. Slower playback can also improve reliability.

Windows shows Unknown publisher: The executable is not digitally code-signed. More info followed by Run anyway starts a build you trust, but only download releases from the official project page.""",
    ),
    (
        "Safety",
        """Test a new or edited macro with one repeat before using a long repeat count or continuous loop.

Do not use unattended playback where an unexpected click or keystroke could delete data, approve a purchase, expose confidential information, or send a message.

Keep Ctrl+F8 available for emergency stop. Stop playback before switching to unrelated or sensitive work. Review macros received from someone else before running them.""",
    ),
)

