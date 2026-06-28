# Garden Fish Macro

External Python macro for a custom Minecraft garden/fish plot. It farms rows back and forth with held movement + attack keys, detects row ends and fish spawns via pixel color, and runs a teleport/vacuum/home sequence when fish appear.

> Use only on servers where automation is allowed.

## Flow

1. **Farming right** — hold `F` + `D` (attack + strafe right)
2. **Row end (orange pixel)** — release keys, tap `W` forward briefly
3. **Farming left** — hold `A` + `F`
4. Repeat, alternating direction each row
5. **Fish spawn (rose/pink pixel)** — interrupt, press `H` (set home), `G` (tp plot), right-click vacuum, `J` (/home), resume previous direction

Two pixel detectors run in parallel on a background thread while the main loop handles movement.

## Install

```powershell
cd C:\Users\stefan\Projects\garden-fish-macro
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

Copy and edit config:

```powershell
copy config.example.json config.json
```

## Run

### Executable (double-click)

Build once:

```powershell
.\scripts\build.ps1
```

Then open `dist\GardenFishMacro.exe`. Config is saved as `config.json` in the same folder as the exe.

### From source

```powershell
python -m garden_macro
```

## Hotkeys (app focused)

| Key | Action |
|-----|--------|
| F8 | Start / stop macro |
| F9 | Sample fish-spawn pixel at cursor |
| F10 | Sample row-end pixel at cursor |
| Esc | Stop macro |

Move the mouse to the **top-left corner** to trigger pyautogui failsafe and stop immediately.

## Calibration

1. Open Minecraft in windowed/borderless mode.
2. Point at the HUD corner that turns **rose/pink** when fish spawn → press **F9**.
3. Point at the corner that turns **orange** at row end → press **F10**.
4. Adjust forward/vacuum/teleport timings in the UI, then **Save Config**.

Default key bindings (change in `config.json`):

| Key | Action |
|-----|--------|
| F | Attack / vacuum |
| D | Strafe right |
| A | Strafe left |
| W | Move forward |
| H | Set home |
| G | Teleport to fish plot |
| J | Go home |

## Tests

```powershell
pytest
```
