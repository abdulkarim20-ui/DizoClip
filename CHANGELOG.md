# Changelog

All notable changes to DizoClip are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-11-21

### Added
- **.env File Export & Import**: Export API keys directly into clean, standardized project `.env` files (`NAME=KEY`) with zero metadata, and import existing `.env` files directly into DizoClip with interactive preview.
- **Selective Export & Import Preview**: Choose categories or single items to share via an interactive checklist dialog.
- **Plain JSON Export**: Export unencrypted, cleanly formatted `.json` files (readable in VS Code) in addition to encrypted `.dizoclip`.
- **API Key Secret Control**: Option to include or leave out API key secrets on export, with safety confirmation warnings for plain JSON.
- **Import Preview**: Displays New / Matched / Changed items before importing; only New items are selected by default, and Changed items can be imported as non-destructive `(imported)` copies.
- **Unified Import**: Import accepts both `.json` and `.dizoclip` files with automatic wrong-passphrase retry.
- **Clipboard Auto-Clear**: Automatically wipes copied API keys after 30 seconds if still on the clipboard. Marks clipboard mime data to request exclusion from Windows Clipboard History (`Win+V`) and cloud syncing.
- **Passphrase-Protected Export & Import**: Export all your data into an encrypted `.dizoclip` bundle using Scrypt and Fernet (AES-128). Safely migrate data to a new PC or Windows account.
- **Encrypt All Data Setting**: Protect prompts, terminal commands, and AI model snippets on disk using DPAPI encryption (`dzc1:` prefix). Default enabled in Settings.
- **File Logging**: Standardized rotating diagnostic logs in `User_Data/Logs/dizoclip.log` with automatic secret redaction.
- **Single-Instance Protection**: Enforced using `QLockFile` so concurrent app instances cannot corrupt data files.

### Fixed
- Importing an old export after editing an item no longer creates duplicates.
- Importing damaged data can no longer break the AI Models tab; search and cards tolerate damaged data.
- A failed save during import no longer leaves unsaved items on screen.
- Export reports locked items it skipped; export files are written atomically.

### Changed
- Surface save failures: disk write errors are shown in a prompt dialog rather than failing silently.
- Refactored `ListView.rebuild()` to be registry-driven and modular.
- Unified copy and delete handling across the main window.

---

## [1.0.1] - 2026-11-21

### Security
- API-key records no longer store a partially readable `masked` copy of the secret on disk. Existing files and old backups are migrated and scrubbed automatically.
- Editing or copying a key whose secret is missing can no longer copy or save the mask as if it were the key.
- Keys that cannot be decrypted (e.g. from another Windows account) are preserved untouched rather than overwritten.

### Fixed
- Backups are now kept per data file (newest 10 plus one per day for 14 days). Saving settings or reordering cards can no longer push key backups out. Unchanged saves no longer create backups.
- A corrupt data file no longer crashes the app on start-up. A recovery dialog offers to restore the latest backup.
- Tests no longer read or write real `User_Data/`.

### Added
- Settings → Data: Restore from Backup, Open Data Folder.

### Changed
- Documentation corrected to match actual behaviour.

---

## [1.0.0] - 2026-01-15

### ✨ Initial Release

DizoClip launches as a lightweight, privacy-first developer clipboard manager for Windows.

#### 🎉 Features

- **🔐 Encrypted API Keys Manager**
  - Windows DPAPI encryption for sensitive data
  - One-click copy functionality
  - Reveal/hide toggle for secure viewing
  - Color-coded categorization
  - Full-text search

- **📚 AI Prompts Library**
  - Store and organize AI model prompts
  - Multiline prompt support
  - Quick copy to clipboard
  - Color-coded organization
  - Full-text search

- **💻 AI Models & Code Snippets**
  - Multi-language code reference (Python, Node.js, Shell, LangChain)
  - Language-aware copying
  - Clean monospace code display
  - Color-coded categorization
  - Full-text search across models and snippets

- **🔗 Quick Links Hub**
  - Centralized URL storage
  - One-click browser launch
  - URL copy functionality
  - Color-coded organization
  - Full-text search across links and titles

- **🖥️ Terminal Commands Library**
  - Store complex CLI commands
  - Monospace font rendering
  - One-click copy with confirmation
  - Color-coded categorization (Docker, Git, Kubernetes, etc.)
  - Full-text search

- **👋 Integrated Single-Window Onboarding**
  - Seamless `WelcomeView` embedded directly inside the primary window
  - Zero secondary popup windows or taskbar duplicates on fresh launch
  - Smooth in-place transition to main list view upon clicking "Get Started"

- **⚙️ Settings & Customization**
  - Always on Top window mode
  - Startup module selector (choose default module on launch)
  - Module visibility toggle (show or hide modules from view)
  - Hold-and-drag tab reordering on top navigation
  - Hold-and-drag card reordering across all 5 modules with automatic persistent saving
  - Custom brand color picker with 2D HSV canvas, hue slider, RGB/Hex inputs, and screen eyedropper tool
  - Real-time dark-theme contrast validation preventing low-contrast colors
  - Delete safeguard confirmation toggle

- **🛡️ Security & Privacy**
  - 100% offline operation
  - No telemetry or tracking
  - No account creation required
  - Automatic atomic writes
  - Timestamped backups
  - Windows DPAPI encryption

#### 🎨 Design & Transitions

- Custom Midnight Slate color palette
- Dark theme optimized for developers
- Snappy 200ms fade-in launch animation (`QEasingCurve.InOutQuad`)
- Matching 200ms fade-out close animation
- Professional UI components
- Native Windows integration & Taskbar AppUserModelID registration

#### 🏗️ Architecture

- Built on PySide6/Qt 6
- Python 3.10+ compatibility
- Modular component structure
- Atomic file operations
- Backup management system

#### 📖 Documentation

- Comprehensive README.md
- Security & Privacy guide
- Installation instructions
- Troubleshooting guide
- Contributing guidelines

#### 🧪 Testing

- Unit test suite included
- Data persistence tests
- Encryption roundtrip tests
- Windows integration tests

---

## [0.9.0] - 2025-12-15

### 🔧 Pre-Release Beta

Internal testing and bug fixes.

#### Added

- Core encryption system
- Basic UI components
- Storage system
- Window management

#### Changed

- Initial design iterations
- Color palette refinements
- Font selection

#### Fixed

- Window transition issues
- Data save bugs
- UI rendering glitches

---

## Unreleased - Upcoming Features

### 🚀 v1.1 (Planned Q2 2026)

#### New Features

- [ ] **Tags System**: Organize items with custom tags
- [ ] **Advanced Search**: Filter by date, category, tags
- [ ] **Export/Import**: Backup and restore all data
- [ ] **Custom Hotkeys**: Global keyboard shortcuts for quick access
- [ ] **Command Execution**: Run terminal commands directly
- [ ] **Prompt Versioning**: Track prompt history and changes
- [ ] **Windows Hello**: Biometric unlock support
- [ ] **Session Timeout**: Auto-lock after idle period
- [ ] **Light Theme**: Alternative light color palette

#### Improvements

- [ ] Performance optimization for 1000+ items
- [ ] Better error messages and logging
- [ ] Enhanced UI animations
- [ ] Accessibility improvements

#### Bug Fixes

- [ ] Placeholder specific bug fixes (TBD)

### 🔮 v1.2 (Planned Q4 2026)

#### Major Features

- [ ] **Local Network Sync**: Share data between work and home machines
- [ ] **Browser Extension**: Capture data directly from web pages
- [ ] **Mobile Companion App**: Access DizoClip from phone
- [ ] **Team Collaboration**: Share secrets with team members (local network)
- [ ] **Audit Logging**: Track all access and modifications

#### Enhancements

- [ ] Key rotation reminders
- [ ] Weak password detection
- [ ] Encryption strength reporting
- [ ] Security health dashboard
- [ ] Command palette (Ctrl+K)
- [ ] Plugin system

---

## Version History Details

### What Changed Between Versions

| Version | Release Date | Focus | Major Features | Breaking Changes |
| :--- | :--- | :--- | :--- | :--- |
| 1.0.0 | Jan 2026 | Launch | All 5 modules | N/A |
| 1.1.0 | Q2 2026 | Advanced Organization | Tags, Hotkeys, Export | None |
| 1.2.0 | Q4 2026 | Collaboration | Team share, Mobile, Sync | Possible |

---

## How to Update

### From v0.9.x to v1.0.0

1. **Backup your data**
   ```bash
   xcopy User_Data C:\Backups\DizoClip_v0.9_backup /E /I
   ```

2. **Update DizoClip**
   ```bash
   git pull origin main
   pip install -U -r requirements.txt
   ```

3. **Run the new version**
   ```bash
   python main.py
   ```

Data is automatically migrated. No manual action needed.

---

## Known Issues

### Current (v1.0.0)

- ✅ No known critical issues

### Fixed in v1.0.0

- Fixed window transition "False" display
- Fixed data save race conditions
- Fixed search performance with large datasets
- Fixed DPAPI encryption for non-ASCII characters

### Workarounds

If you encounter issues:

1. **Keys not saving?**
   - Ensure `User_Data/` has write permissions
   - Check disk space
   - Restart DizoClip

2. **Secrets not decrypting?**
   - Only available from original Windows user account
   - Use Export / Import to transfer between machines or accounts

3. **Data issues?**
   - Restore from backup in Settings → Data
   - Check JSON file format manually

---

## Version Naming Convention

DizoClip uses **Semantic Versioning** (MAJOR.MINOR.PATCH):

- **MAJOR** (1.x.x): Significant new features or breaking changes
- **MINOR** (x.1.x): New features without breaking changes
- **PATCH** (x.x.1): Bug fixes and minor improvements

Examples:
- 1.0.0 → Initial release
- 1.1.0 → New tags feature (backwards compatible)
- 1.1.1 → Bug fix (no new features)
- 2.0.0 → Major redesign (breaking changes)

---

## Release Notes Archive

### v1.0.0 Release Notes

**DizoClip is here!** 🎉

The lightweight, privacy-first clipboard manager for developers is now available. Keep your API keys, prompts, code snippets, and terminal commands organized and instantly accessible.

**Key Highlights:**
- Five specialized modules for different data types
- Windows DPAPI encryption
- 100% offline, no tracking, completely private
- Beautiful dark theme optimized for developers
- Atomic writes with automatic backups

**Download**: [GitHub Releases](https://github.com/abdulkarim20-ui/DizoClip/releases/tag/v1.0.0)

**Installation**: See [README.md](README.md#-quick-start)

---

## Contributing

Have an idea for the next version? Contribute to DizoClip!

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/abdulkarim20-ui/DizoClip/issues)
- **Discussions**: [GitHub Discussions](https://github.com/abdulkarim20-ui/DizoClip/discussions)
- **Security**: Report privately to security@abdulkarim.dev

---

## License

All versions of DizoClip are released under the [MIT License](LICENSE).

---

<div align="center">

**Changelog Last Updated**: 2026-01-15

[View on GitHub](https://github.com/abdulkarim20-ui/DizoClip)

</div>
