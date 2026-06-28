# Garden Farm Macro

Simple external macro for custom Minecraft garden plots. Farms rows back and forth with held movement + attack keys, and detects row ends via orange pixel color.

> Use only on servers where automation is allowed.

## How it works

1. **Farm right** — hold attack + strafe right (`F` + `D`)
2. **Orange pixel** (row end) — release keys, tap forward briefly (`W`)
3. **Farm left** — hold attack + strafe left (`A` + `F`)
4. Repeat, alternating direction each row

## Download executable

**[GardenFarmMacro.exe](https://github.com/JadeSCRIPTZ/garden-fish-macro/raw/main/dist/GardenFarmMacro.exe)**

Or open `dist\GardenFarmMacro.exe` from the repo. Config saves as `config.json` next to the exe.

## Hotkeys (app focused)

| Key | Action |
|-----|--------|
| F8 | Start / stop |
| F9 | Sample row-end pixel at cursor |
| Esc | Stop |

Move mouse to **top-left corner** for pyautogui failsafe stop.

## Calibration

1. Open Minecraft in windowed/borderless mode.
2. Hover the HUD corner that turns **orange** at row end → press **F9**.
3. Adjust forward time if needed → **Save**.
4. Press **F8** to start.

## Build from source

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
.\scripts\build.ps1
```

## Run from source

```powershell
python -m garden_macro
```

## Tests

```powershell
pytest
```
