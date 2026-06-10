# Roadmap

## Open Issues
- [ ] Fix port probe which is currently sometimes detecting port 49672 though it should be 49672.
- [ ] Move switcher related documentation from the root folder README.md to a dedicated README.md within the
  `tools/switcher/` folder.

## Current Goals
- [x] Restructure project into `focusrite-tools` to accommodate multiple utilities.
- [x] Automate Focusrite Scarlett 18i8 routing profile switching.
- [x] Provide an automated installer for Windows deployment.
- [x] Document development principles and technical specifications.
- [x] Provide a fully working CLI interface for managing routing profiles. (Yay!)
- [ ] Finalize installer for Windows deployment.

## Future Enhancements
- Add more tools (e.g., gain control, monitor control) to the `tools/` suite.
- Support for other Focusrite Gen 2/3 interfaces.
- Improved error handling for network communication.
- User-configurable routing profiles via a simple config file.
