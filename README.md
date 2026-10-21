# Macro Play

Macro Play is a no-code desktop recorder for repetitive computer work. It captures global mouse and keyboard input, turns the recording into a compact action timeline, and replays it as many times as needed.

## What it does

- Records mouse moves, clicks, drags, and scroll-wheel input anywhere on the desktop.
- Provides numbered red macro slots, ten at a time, with left/right paging for additional macros.
- Records normal typing as readable **Type text** actions and preserves modifier/special-key presses.
- Consolidates hundreds of raw mouse coordinates into one editable move between interactions.
- Tracks the active window's title, position, and size and restores it during playback.
- Lets you add, edit, duplicate, reorder, disable, or delete actions without writing code.
- Bulk-edits the wait time or length for any group of selected timeline actions.
- Supports adjustable playback speed, pause/resume, up to 999 repeats, or looping until stopped.
- Provides a selectable global Play hotkey that works while another application has focus.
- Assigns separate global hotkeys to any number of saved macros, so the right workflow plays instantly.
- Rejects invalid system-uptime values in recorded waits and repairs affected saved macros on load.
- Shows a temporary crosshair at the recorded cursor coordinates when a mouse action is selected.
- Saves portable, human-readable `.macro.json` files for later recall.
- Includes a searchable in-app instruction manual, available from **Help** or **F1**.
- Runs on Windows and macOS. Linux input works where the desktop session permits global hooks.

## Run from source

Python 3.10 or newer is required.

```powershell
python -m pip install -r requirements.txt
python run.py
```

On macOS, grant **Accessibility** permission to Terminal (for source runs) or Macro Play (for packaged builds) under System Settings → Privacy & Security. Windows may require running Macro Play as administrator only when automating an elevated application.

## Typical workflow

1. Select a red **Macro 1**, **Macro 2**, or other numbered slot.
2. Press **Record**, or open an existing macro file into that slot.
3. Perform the task in your other applications.
4. Return to Macro Play and press **Stop**. Interactions with Macro Play itself are ignored while recording.
5. Double-click timeline actions to review or edit them.
6. Assign a hotkey to the selected slot, then choose another numbered slot and repeat.
7. Use **Save** to store each macro as a `.macro.json` file.

The selector displays ten red macro buttons at a time. Use the left and right arrow buttons to move between Macro 1–10, 11–20, and higher ranges. Each slot keeps its own timeline, file, unsaved state, and hotkey for the current session. An asterisk marks an unsaved slot.

To give several actions the same timing, select their rows with **Ctrl-click** or **Shift-click**, choose **Set wait** or **Set length**, enter the time once, and press **OK**. Every selected action is updated together.

Under **Playback settings → Selected slot hotkey**, click **Change** and physically press the shortcut you want. The shortcut is assigned to the selected numbered slot. Macro Play accepts modifier combinations, function keys, and navigation keys. Macro 1 starts as **Ctrl+F9** each time the app opens. When you open a macro file into a slot, that slot's shortcut plays the loaded macro. If a shortcut is already assigned anywhere in the session, Macro Play displays an error and does not replace the existing assignment.

To control several macros during the current session, save each recording first, then select **Saved macro hotkeys**. Choose **Add saved macro**, select its `.macro.json` file, and press the shortcut you want to assign. Repeat for every macro. While Macro Play is running, each shortcut plays its assigned file without replacing the macro currently open in the editor. Assigned macros use the repeat, loop, speed, and window-restore settings currently shown in the app. Custom hotkeys and saved-macro assignments are cleared the next time Macro Play starts; the `.macro.json` files themselves are never deleted.

Press **Ctrl+F8** at any time during playback for an emergency stop, even when another application has focus.

Select **Help** or press **F1** to open the complete searchable instruction manual. The same manual is also available in [USER_GUIDE.md](USER_GUIDE.md).

## Build a desktop app

On Windows:

```powershell
.\build.ps1
```

The standalone app is written to `release\Macro Play.exe`.

On macOS:

```bash
chmod +x build.sh
./build.sh
```

The app is written to `release/Macro Play.app` by PyInstaller.

Build on the operating system you plan to distribute to; PyInstaller does not cross-compile between Windows and macOS.

## Macro file format

Recordings are JSON documents with versioned actions. Each action stores its wait time, duration, enabled state, and action-specific data. This keeps saved macros inspectable and makes future migrations possible.

## Safety notes

- Test a new macro with one repeat before running a long loop.
- Playback sends real input to your computer. Use **Stop** before switching to sensitive work.
- Window matching uses recorded titles. If an application changes its title, edit the corresponding **Focus window** action.

