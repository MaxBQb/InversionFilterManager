# InversionFilterManager [![Latest](https://img.shields.io/github/v/tag/MaxBQb/InversionFilterManager?sort=date&label=&style=for-the-badge&color=424242)](https://github.com/MaxBQb/InversionFilterManager/releases/latest/download/release.zip)
![Windows](https://img.shields.io/badge/platform-Windows-green)
[![GitHub license](https://img.shields.io/github/license/MaxBQb/InversionFilterManager.svg)](https://github.com/MaxBQb/InversionFilterManager/blob/master/LICENSE.md)
![Admin privileges required](https://img.shields.io/badge/-Admin_privileges_required*-red)

## How to install

### Automatic

1. Choose folder for this program (must not contain non-ASCII symbols) 
2. Run cmd in this folder (paste `cmd` in explorer folder path field)
3. Run this code in cmd:

```cmd
mkdir InversionManager && cd InversionManager
start /WAIT bitsadmin /transfer "Download Inversion Manager" /download /priority normal https://github.com/MaxBQb/InversionFilterManager/releases/latest/download/release.zip "%cd%\release.zip" && tar -xf release.zip && del release.zip && start main.exe
```

### Manual

1. Download the latest [![Latest](https://img.shields.io/github/v/tag/MaxBQb/InversionFilterManager?sort=date&label=&style=flat-square&color=424242)](https://github.com/MaxBQb/InversionFilterManager/releases/latest/download/release.zip) release [**here**](https://github.com/MaxBQb/InversionFilterManager/releases/latest/download/release.zip)
2. Unpack downloaded file
3. Move inner folder in place of your choice (path must not contain non-ASCII symbols) 
4. Run `main.exe`

## Features

- Invert colors depend on window opened
- Inversion rules can be set via .yaml file (changes handled at runtime)
- Settings can be set via .yaml file (changes handled at runtime)
- Use `ctrl + alt + '+'` for add current window to inversion rules
- Use `ctrl + alt + '-'` for remove current window from inversion rules
- New rule can:
  - Check if program located at specific path (regex supported)
  - Check if program has specific title (regex supported)
  - Check if specific title used by program parent window (regex supported)
  - Remember process once captured by this rule (useful when path is java/python path)
  - Set custom color filter to apply on program has been opened (see configs to edit list of color filters)
  - Set opacity of filter applied (just like css `filter: invert(85%)`)
- Rule types: Exclude/Include/Ignore:
  - Include used by default and applies color filter when specific window opened
  - Exclude used to restrict rule that captures too mach entries
  - Ignore used to don't change current filter used in response on this program captured 
- All functionality available in system tray menu
- App can automatically download and install updates (check settings to prevent or configure this)
- App can run itself at system startup
- App makes backup for older version on updates (overrides previous backup)
- Rules checks can be disabled
