# Changelog
## [Unreleased](https://github.com/MaxBQb/InversionFilterManager/releases/tag/latest) (2022-07-29)
Nothing yet.

## [Release v0.6.0](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.6.0) (2022-07-29)
Features:
- Use independent color filter
  - Ability to apply two color filters (one by app, another by windows itself)
- New inversion rules options:
  - Color filter type
  - Color filter opacity
- Color filter types can be extended in `color_filters.yaml` config

Fix:
- Click on window preview canceled by inversion toggle

## [Release v0.5.4](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.5.4) (2022-01-03)
Features:
- Option to disable app (in system tray)
  - Disable (ignore) all
  - Use rules [default]

Fix:
- Crash on no titles found

Performance:
- Prevent settings saving on nothing has changed

## [Release v0.5.3](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.5.3) (2021-10-18)
Features:
- `Ignore` rules to disable inversion toggle for some windows whenever they appear
- Better formatting for comments in configs
- Inversion rules now also contains comments

## [Release v0.5.2](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.5.2) (2021-09-11)
Features:
- Remember id of process (once successfully correspond for the given rule)
and apply this rule for this process no matter what 
(useful for java/python apps, when app path gives a bit more than nothing)
- Show if app started in privileged mode (in system tray)

Fix: 
- Rule name suggestion sometimes contains .exe

## [Release v0.5.1](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.5.1) (2021-09-05)
Fix:
- App started from cmd in some directory confuses that dir with root app dir
- Parent console (which has started this app) may stay hidden on app closed
- App tries to await GUI windows instead of just close them

## [Release v0.5.0](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.5.0) (2021-09-04)
### Contains breaking changes!
Features:
- Reload from disk option in SystemTray
- Update checkup intervals now are configurable
- Now only one instance of this app may exist
- Choose window dialog now appears only when needed
- App tries to setup filter options at startup
- Settings for color filter setup

Changes:
- Replace config.ini with settings.yaml

Performance:
- Now config dumped only when corrupted or not found
- Rules changes now applies immediately (slower, but safer)

Fix:
- Enum fields shows correct now
- Check before creation if rule with same name is already defined

## [Release v0.4.0](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.4.0) (2021-08-21)
### Contains breaking changes!
Fix:
- Error on inverted window closed

Features:
- You may create rules, that prevent inversion now
- Now you can apply title checking for all titles between root and current window inclusive
- App functions now available from system tray:
  - Now you may add/remove windows from inversion rules via tray
  - Show/Hide console
- App windows now have icons
- Update confirmation now available for developers
> Note, that it is still .py (developer) to .exe (regular user) update
- Program now properly handle windows exit signals
> There is no difference between tray Exit and console window close

Changes:
- Change app_rules format (rename property)
- Rename app_rules to inversion_rules for clean
- Update now checks once per day (You may start check manually)
- Hide console by default (you may bring console back with tray)

## [Release v0.3.2](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.3.2) (2021-08-09)
Fix:
- win32gui not found exception

## [Release v0.3.1](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.3.1) (2021-08-08)
Fix:
- App crashes instead of update confirmation

## [~~Release v0.3.0~~](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.3.0) (2021-08-08)
Features:
- Automatically requests admin rights
- Optional check of root title
- Browse path button
- Auto escape/unescape text on regex option toggle
- Path/Title labels now acts as hyperlinks when regex option enabled

Fix:
- Now use spaces in field names, displayed in GUI

## [Release v0.2.0](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.2.0) (2021-08-05)
Features:
- GUI for rule creation
- GUI for rule removal
- GUI for update confirmation


## [Release v0.1.2](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.1.2) (2021-07-20)
Fix:
- Update could be blocked by an existing update parts

Performance:
- Use optimized yaml loader/dumper

## [Release v0.1.1](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.1.1) (2021-07-17)
Fix:
- Incorrect requirements.txt format
- Now release building works fine
- Rule name suggestions generation

Performance:
- Cache regex masks used in rules
- Omit is_regex field on default value is set

## [~~Release v0.1.0~~](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.1.0) (2021-07-12)
Features:
- App now can automatically download and install updates for itself
- Make backup for older version on updates (overrides previous backup)

## [~~Release v0.0.2~~](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.0.2) (2021-07-11)
Fixes:
- Crash on empty rules file

## [Release v0.0.1](https://github.com/MaxBQb/InversionFilterManager/releases/tag/v0.0.1) (2021-07-10)
### Initial version.
Features:
- Invert colors depend on window opened
- Inversion rules can be set via .yaml file (changes can be applied at runtime)
- Use `ctrl + alt + '+'` for add current window to inversion rules
- Use `ctrl + alt + '-'` for remove current window from inversion rules
- Use config.ini for edit settings (changes can be applied at runtime)
