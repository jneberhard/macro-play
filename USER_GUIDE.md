# Macro Play User Guide

## Quick start

1. Select **Record**.
2. Perform the task in the other application.
3. Return to Macro Play and select **Stop**.
4. Review and edit the recorded actions.
5. Select **Save** to create a `.macro.json` file.
6. Select **Play**, or use an assigned global hotkey.

Test a new macro with one repeat and normal speed before using a long repeat count or continuous loop.

## Main window

The top controls start recording and playback and provide **New**, **Open**, **Save**, and **Help** commands. The **Action timeline** lists every recorded step. **Wait** is the pause before an action starts; **Length** is the time used by actions such as mouse movement or an explicit Wait action.

Playback settings control the macro name, repeat count, continuous looping, playback speed, window restoration, and global hotkeys. The progress area shows the macro currently playing.

## Numbered macro selector

The compact red buttons across the top are independent macro slots. Up to ten are visible at once. A narrower screen or window automatically shows fewer slots so the left and right arrows stay visible. Use the arrows to move through higher or lower numbered ranges.

Select a slot before recording or opening a macro. Every slot keeps its own timeline, loaded file, unsaved status, and hotkey during the current session. Switching slots does not erase unsaved work, and an asterisk identifies an unsaved slot.

To build several macros, select **Macro 1**, create or open it, and assign its hotkey. Select **Macro 2** and repeat. A slot hotkey plays that macro even when another slot is currently visible. Slots are cleared at startup, so save macros to `.macro.json` files for future sessions.

## Recording

Select **Record**, then perform the workflow normally. Macro Play captures global mouse movement, clicks, dragging, scrolling, and keyboard input. Ordinary typing becomes readable **Type text** actions, and mouse movement is consolidated to avoid a timeline full of coordinate samples.

Return to Macro Play and select **Stop**. Interactions inside Macro Play are ignored while recording. If the timeline already contains actions, Macro Play asks before replacing it.

## Editing actions

Select an action and choose **Edit**, or double-click it. Depending on the action, you can change its wait, duration, coordinates, mouse button, key, text, or window details.

- **Add** inserts a new action after the selection.
- **Duplicate** copies the selected action.
- **Up/Down** reorders one selected action.
- **Delete** removes every selected action.
- **Enable / disable** keeps selected actions in the file but excludes them from playback.

Selecting a mouse action displays a temporary crosshair at its recorded position without moving or clicking the pointer.

### Set the wait time or length on several actions

1. Select the first action.
2. Use **Ctrl-click** to add individual actions or **Shift-click** to select a range.
3. Select **Set wait** or **Set length**.
4. Enter the time in seconds and select **OK**.

Every selected action receives the same value. Other settings remain unchanged. **Wait** is the pause before an action. **Length** controls duration for supported actions such as mouse movement, click holds, and explicit Wait actions. Enter `0` to remove a pause or make a supported action complete immediately.

## Playback

Set **Repeat** to the desired number of runs, or enable **Loop until stopped**. Adjust playback speed as needed. **Restore window positions** asks Macro Play to focus and resize recorded windows before their actions run.

Select **Play** to begin. Use **Pause/Resume** or **Stop** as needed. Press **Ctrl+F8** for an emergency stop, even while another application has focus.

Playback sends real mouse and keyboard input. Avoid touching the mouse or typing unless playback is paused or stopped.

## Hotkeys

### Current macro

The current macro hotkey belongs to the selected numbered slot. Opening a macro file into that slot immediately makes the loaded macro its shortcut target. Select **Change**, then physically press the desired combination. Letters and numbers require Ctrl, Alt, Shift, or Cmd. Select **Disable hotkey** to turn it off. F8 and Ctrl+F8 are reserved for emergency stop. If a shortcut is already used in the session, Macro Play displays a warning and preserves the existing assignment. Custom hotkeys are cleared and Macro 1's Ctrl+F9 is restored whenever Macro Play starts.

### Several saved macros

1. Save every recording as a `.macro.json` file.
2. Select **Saved macro hotkeys**.
3. Select **Add saved macro** and choose its file.
4. Press the desired shortcut.
5. Repeat as needed and select **Save**.

Macro Play must remain running. An assigned macro is read from its file whenever its hotkey is pressed, without replacing unsaved editor work. It uses the repeat, loop, speed, and window-restore settings currently displayed. Saved-macro assignments are session-only and are cleared at the next startup; the `.macro.json` files are never deleted.

## Files

Use **Save** or **Ctrl+S** to create a `.macro.json` recording. Use **Open** or **Ctrl+O** to load one. Use **New** or **Ctrl+N** to clear the editor after saving or discarding changes.

## Keyboard reference

| Shortcut | Action |
| --- | --- |
| F1 | Open Help |
| F5 | Play the open macro |
| Ctrl+R | Start or stop recording |
| Ctrl+O | Open a macro |
| Ctrl+S | Save the current macro |
| Ctrl+N | Create a new macro |
| Delete | Remove selected actions |
| Ctrl+F8 | Emergency playback stop |
| Ctrl+F | Focus search while Help is open |
| Esc | Close Help |

## Troubleshooting

- **A hotkey does nothing:** Keep Macro Play running, confirm its file is not marked missing, and make sure recording or playback is not already active.
- **Clicks target the wrong place:** Recreate the recorded window layout, enable window restoration, or edit the coordinates. Select a mouse action to preview its target.
- **An application ignores playback:** On Windows, an elevated target may require Macro Play to run as administrator. On macOS, grant Accessibility permission.
- **Timing is unreliable:** Increase the wait before actions that depend on other software finishing, or reduce playback speed.
- **Windows shows Unknown publisher:** The executable is not digitally code-signed. Only run downloads you trust from the official project page.

## Safety

- Test new or edited macros with one repeat.
- Keep **Ctrl+F8** available for emergency stop.
- Stop playback before switching to unrelated or sensitive work.
- Do not run unattended macros where an unexpected action could delete data, approve a purchase, expose confidential information, or send a message.
- Review macros received from someone else before running them.

