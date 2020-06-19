## v1.4.0 ()
### Changes
- Version numbers now follow the semantic versioning specification. https://semver.org/
- Changed this mod's namespace from NeonOcean.Order to NeonOcean.S4.Order.
- Changed load order file naming scheme, check the documentation for more information.
- Updated mod information file loading to follow changes in the mod Main.
- Settings are now listed in dialog instead of an interaction menu.
- Added icons to some mod interactions and interaction categories.

### Fixed bugs
- Fixed mod documentation links.

______________________________

## v1.3.0 (July 15, 2019)
### Changes
- All of Order's interactions will now only show up when clicking on Sims instead of everything.
- Change the way persistent files are formatted, this will likely cause settings to reset.
- More changes occurred in Main involving mod information files, these changes where, again, copied to Order for this update.
- Removed a space in the keyword arguments dictionary key for load order functions.
- Load order functions no longer require a 'Arguments' or 'KeywordArguments' value.

### Fixed Bugs
- Fixed potential problem involving exit exceptions being caught by the load order system.
- Invalid order file path roots are now caught as they should have been.
- Modules named \_\_init\_\_ are no longer imported twice.

______________________________

## v1.2.0 (June 12, 2019)
### Changes
- Many changes occurred this update to a system that reads the mod information files in order to conform to changes made in the mod Main.
- Added an icon to the root NeonOcean pie menu category.
- Changed this mod's license to CC BY.

### Fixed Bugs
- Fixed problem where NeonOcean update notifications sent users to the mod's documentation page instead the mod page.
- The notification showing that some mods have compatibility problems now correctly lists the mods in question.
- Debug session files now display certain information correctly.
- Fixed potential bugs in the debug system related to threads.
- Debug write failure notifications now correctly display the error information.

______________________________

## v1.1.0 (March 26, 2019)
 
- The relative paths pointed to in load order files now require specification of the root.
- Functions specified to be called by the load order now allow for the passing of arguments.
- In-game notifications will now appear telling you when an update is available.
- Interactions now exist that can direct you to web pages relevant to this mod, such as the documentation.
- Addition and removal of this mod are can now be facilitated through an installer or uninstaller. These currently are only usable on windows computers.

______________________________
 
## v1.0.0 (July 26, 2018)
 - Initial release