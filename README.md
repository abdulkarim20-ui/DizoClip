<div align="center">

  <img src="assets/app_logo.png" alt="DizoClip Logo" width="120" height="120" />

  # DizoClip

  **The Lightweight, Privacy-First Developer Clipboard Manager**
  
  *Keep your API keys, prompts, code snippets, and terminal commands instantly accessible on your desktop.*

  [![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
  [![PySide6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://wiki.qt.io/Qt_for_Python)
  [![Windows](https://img.shields.io/badge/Platform-Windows%2010%2B-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://microsoft.com/windows)
  [![License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge)](LICENSE)
  [![Security](https://img.shields.io/badge/Security-DPAPI%20Encrypted-success?style=for-the-badge)](SECURITY.md)

  [🚀 Quick Start](#-quick-start) • [📖 Features](#-features) • [🎨 Screenshots](#-screenshots) • [🛡️ Security](#-security) • [📝 License](#-license)

</div>

---

## 🎯 The Problem

Developers constantly suffer from **context switching**:

- 🔑 Hunting through scattered `.env` files and cloud consoles for API keys
- 📝 Digging through old chat histories to find that perfect system prompt
- 🔄 Re-googling boilerplates and SDK examples every time you start a new project
- 💻 Re-typing complex terminal commands from browser history
- ⏱️ Losing 5-10 minutes per day just searching for developer essentials

**DizoClip solves this.** Keep everything you need just one click away—right on your desktop.

---

## ✨ Why DizoClip?

| Challenge | DizoClip Solution |
| :--- | :--- |
| **Scattered API Keys** | Encrypted local storage with one-click copy and secure reveal toggle |
| **Lost Prompts** | Dedicated prompts library with multiline preview and instant access |
| **Language Switching** | Multi-language code snippets (Python, Node.js, Shell, LangChain) in every card |
| **Bookmark Hell** | Consolidated quick links hub with direct browser launch |
| **Forgotten Commands** | Terminal command library with instant copy |
| **Clipboard History Leaks** | **Clipboard Guard**: Exemption from Windows History (`Win+V`) and optional 30-second auto-clear |
| **Cross-PC Migration** | **Selective `.dizoclip` Archives**: Password-encrypted Scrypt + AES-128 export with pre-import diff preview |
| **Bloated Desktop Utilities** | **Blazing Native Speed**: Zero-lag DWM launch, lazy widget loading, and ultra-lean memory (~35–45 MB) |
| **Privacy Concerns** | **100% Offline & Local**: No cloud sync, no accounts, no telemetry. Your data never leaves your device. |

---

## 🚀 Quick Start

### Prerequisites
- **Windows 10** or **Windows 11**
- **Python 3.10+** ([download](https://www.python.org/downloads/))

### Installation

```bash
# Clone the repository
git clone https://github.com/abdulkarim20-ui/DizoClip.git
cd DizoClip

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run DizoClip
python main.py
```

> **First Launch?** DizoClip will guide you through a quick onboarding tour. Don't skip it!

---

## 📖 Features

### 🔐 1. Encrypted API Keys & Secrets Manager

Store, organize, and instantly access your API keys, tokens, and environment variables—all protected with Windows DPAPI hardware/account-bound encryption.

**What it does:**
- ✅ Encrypt secrets at rest using Windows DPAPI (`crypt32.dll` bound to your Windows user account)
- ✅ Mask sensitive data with crisp asterisks
- ✅ Assign color-coded categories (Production, Staging, Personal, etc.)
- ✅ One-click copy with visual confirmation
- ✅ Reveal/hide toggle for secure viewing
- ✅ Exclude secrets from Windows 10/11 Clipboard History (`Win+V`) and cloud clipboard sync

**Why it helps:**
- Eliminates the need to hunt through multiple `.env` files
- Keeps sensitive data protected on your local machine with OS-level hardware-backed keys
- Color-coded organization for quick identification
- No cloud exposure, no accidental pastes in chat, and no leaking into Windows clipboard history

<div align="center">
  <img src="docs/screenshots/01_api_keys.png" alt="API Keys Manager" width="360" />
</div>

---

### 📚 2. AI Prompts Library

Build a personal repository of system prompts, instructions, and templates for ChatGPT, Claude, Gemini, and other LLM agents.

**What it does:**
- ✅ Store multiline prompts with full formatting preserved
- ✅ Clean, human-readable plain JSON storage (`DC_Prompts.json`) for seamless Git tracking and developer backups
- ✅ Quick preview cards with automatic height balancing
- ✅ One-click copy to clipboard for direct pasting
- ✅ Color-coded categorization
- ✅ Full-text search across all prompts

**Why it helps:**
- Never dig through old chat histories for that perfect system prompt again
- Test and refine prompts without re-typing them every time
- Build a personal knowledge base of effective AI instructions
- Easily commit, inspect, or version-control your prompts in plain JSON
- Instantly apply tested prompts to new conversations

<div align="center">
  <img src="docs/screenshots/02_prompts.png" alt="Prompts Library" width="360" />
</div>

---

### 💻 3. AI Models & Code Snippets

Reference multi-language code examples for initializing and using your favorite AI model APIs.

**What it does:**
- ✅ **Multi-language switcher**: Python, Node.js, Shell (cURL), LangChain
- ✅ Clean monospace code display
- ✅ Stored in human-readable plain JSON (`DC_AI_Models.json`)
- ✅ One-click copy with language-aware formatting
- ✅ Color-coded categorization
- ✅ Full-text search across models and snippets
- ✅ Quick reference for authentication and configuration

**Why it helps:**
- Stop re-googling "how to initialize Claude in Python" every time
- Language-agnostic reference—find examples in any language instantly
- Copy boilerplate code directly into your project
- Consistent, tested initialization patterns

<div align="center">
  <img src="docs/screenshots/03_ai_models.png" alt="AI Models & Snippets" width="360" />
</div>

---

### 🔗 4. Quick Links Hub

Centralize your most-used dashboards, cloud consoles, documentation, and environment URLs in one accessible place.

**What it does:**
- ✅ Store frequently-accessed URLs (AWS Console, GitHub, Docs, etc.)
- ✅ One-click launch in default browser
- ✅ Quick copy of URLs for terminal use or sharing
- ✅ Color-coded organization by project or service
- ✅ Full-text search across links and titles
- ✅ No browser bookmark hunting required

**Why it helps:**
- Eliminate tab clutter—everything in one place
- Launch environments without searching bookmarks
- Access staging/production URLs instantly
- Share links without manually copying from browser

<div align="center">
  <img src="docs/screenshots/04_quick_links.png" alt="Quick Links Hub" width="360" />
</div>

---

### 🖥️ 5. Terminal Commands Library

Keep your Docker commands, Git recipes, Kubernetes manifests, and database queries organized and instantly copyable.

**What it does:**
- ✅ Store complex CLI commands with a title
- ✅ Stored in human-readable plain JSON (`DC_Commands.json`) for effortless Git diffing
- ✅ Monospace font rendering (JetBrains Mono) for clarity
- ✅ One-click copy with checkmark feedback
- ✅ Full-text search across all commands
- ✅ Color-coded by command type (Docker, Git, K8s, etc.)

**Why it helps:**
- Never re-type `git rebase -i HEAD~5` or complex Docker builds again
- Keep Kubernetes manifests and database queries organized
- Copy commands instantly instead of hunting browser history
- Reduce typos and syntax errors in complex CLI operations

<div align="center">
  <img src="docs/screenshots/05_terminal_commands.png" alt="Terminal Commands" width="360" />
</div>

---

### 📦 6. Password-Protected Selective Export & Import (`.dizoclip`)

Safely backup or migrate your data across devices with single-format, military-grade encrypted archives and selective item control.

**What it does:**
- ✅ **Single Secure Container Format (`.dizoclip`)**: Encrypted using Fernet AES-128 with keys derived via Scrypt (`n=2^14, r=8, p=1`) from your password + 16-byte cryptographic salt
- ✅ **Selective Tree Checklist**: Export exactly what you need—choose entire modules or pick individual keys, prompts, models, links, and commands with category badges and real-time item counters
- ✅ **Dynamic Empty-Module Filtering**: Sections with 0 items are automatically hidden from the tree view so you only see categories containing data
- ✅ **Single Password Box with Eye Reveal Toggle (`👁️`)**: Embedded reveal toggle lets you quickly inspect what you typed before exporting—cleaner UI, faster workflow, zero double-typing
- ✅ **Clear Security Guidelines**: Direct inline guidance reminds you that the password is required to decrypt and import your `.dizoclip` archive on any machine
- ✅ **Non-Destructive Import Preview**: Inspect incoming archives before anything is touched. The preview categorizes items into **New** (green), **Matched** (identical, skipped or updated), and **Changed** (conflicts)
- ✅ **Cross-Machine Portability**: Safely move secrets across different Windows user accounts and PCs without exposing plaintext keys
- ✅ **Zero Plaintext Leaks**: Legacy unencrypted JSON and plain `.env` file exports are eliminated to guarantee that secrets never sit exposed on disk

**Why it helps:**
- Share specific prompts or command sets with teammates without sharing your API keys
- Move your entire developer workbench to a new laptop with a single password-protected file
- Never wonder what an import will overwrite thanks to the real-time visual comparison preview

<p align="center">
  <img src="docs/screenshots/08_Export_view.png" alt="Selective Export Dialog" width="360" />
  &nbsp;&nbsp;
  <img src="docs/screenshots/09_Import_view.png" alt="Import Preview Dialog" width="360" />
</p>

---

### ⚙️ 7. Smart Settings & Customization

Tailor DizoClip to your exact workflow and desktop setup.

**What it does:**
- ✅ **Clipboard Guard & Auto-Clear**: Automatically wipe the Windows clipboard after 30 seconds (Default: OFF for user control), with built-in exclusion flags that prevent secrets from showing in Windows 10/11 Clipboard History (`Win+V`) and cloud clipboard sync
- ✅ **Context-Aware Smart Search**: Top search bar automatically hides when a module has 0 items to maintain a distraction-free view, and reappears dynamically as soon as an item is added
- ✅ **Polished Empty-State Guidance**: When a section has no entries, an icon, helper description, and an auto-sized centered action button (`+ Add API Key`, `+ Add Command`, etc.) provide instant action
- ✅ **Always on Top**: Keep DizoClip floating above all windows for rapid multitasking
- ✅ **Startup Module Selector**: Choose which module (API Keys, Prompts, Snippets, Links, or Commands) opens immediately on application launch
- ✅ **Module Visibility Toggle**: Hide modules you don't need and show only the tools you use daily
- ✅ **Hold-and-Drag Tab Reordering**: Hold and drag any module tab at the top of the window to arrange them in your preferred sequence
- ✅ **Hold-and-Drag Card Reordering**: Rearrange cards within any module effortlessly by clicking, holding, and dragging a card to its new position with automatic persistent saving
- ✅ **Custom Brand Color Picker**: Pick any custom brand color for your resources with the interactive 2D HSV gradient canvas, hue slider, RGB/Hex inputs, or the precision screen eyedropper pipette tool with real-time dark-theme contrast validation
- ✅ **Delete Safeguard**: Optional confirmation dialog to prevent accidental deletions
- ✅ **Native Windows DWM Performance**: Instant window activation without opacity delay, lazy-loaded widget trees (startup widget count dropped from ~263 to ~43), and working-set memory trimming (~35–45 MB idle footprint)

**Why it helps:**
- Position DizoClip next to your IDE or terminal without losing focus
- Faster access by opening your most-used module first
- Keep your workspace minimal by showing only active tools
- Arrange cards and tabs by project priority or frequency of use
- Protect secrets from clipboard sniffers and Windows history logs
- Match cards to official brand colors (e.g., Anthropic orange, OpenAI teal, Docker blue, GitHub purple)

<p align="center">
  <img src="docs/screenshots/07_settings_A.png" alt="Settings - Preferences & Modules" width="360" />
  &nbsp;&nbsp;
  <img src="docs/screenshots/07_settings_B.png" alt="Settings - Data & Storage" width="360" />
</p>

---

## 🎨 Screenshots

### Welcome Onboarding

<div align="center">
  <img src="docs/screenshots/welcome_dialog.png" alt="Welcome Dialog" width="360" />
</div>

First-time launch includes a clean onboarding tour introducing DizoClip's local-first philosophy and core features.

### Selective Export & Import Dialogs

<p align="center">
  <img src="docs/screenshots/08_Export_view.png" alt="Selective Export Dialog" width="360" />
  &nbsp;&nbsp;
  <img src="docs/screenshots/09_Import_view.png" alt="Import Preview Dialog" width="360" />
</p>

Export exactly what you need with granular checklist filtering and single-password encryption with show/hide reveal (left), or preview incoming archives before merging with smart New/Matched/Changed status badges and collapsed categories (right).

### Custom Color Picker & Brand Colors

<div align="center">
  <img src="docs/screenshots/08_color_picker.png" alt="Custom Color Picker" width="360" />
</div>

Precision 2D HSV color canvas, rainbow hue slider, RGB/HEX numeric inputs, and screen eyedropper pipette tool with real-time dark-theme contrast validation. Pick any brand color to categorize your API keys, prompts, snippets, links, and commands.

### Add & Edit Forms

<div align="center">
  <img src="docs/screenshots/06_add_key_form.png" alt="Add/Edit Forms" width="360" />
</div>

Intuitive forms with interactive toggles, color pickers, and validation for adding new resources.

---

## 🎨 Design System

DizoClip uses a carefully crafted **Midnight Slate** color palette optimized for dark environments and reduced eye strain:

| Element | Color | Purpose |
| :--- | :--- | :--- |
| **Main Background** | `#0f111a` | Deep midnight slate canvas |
| **Card Background** | `#141722` | Elevated surfaces with soft contrast |
| **Accent Color** | `#ff8c5a` | Coral orange for actions and highlights |
| **Primary Text** | `#e2e8f0` | High-contrast readable text |
| **Secondary Text** | `#7a8292` | Subdued labels and metadata |
| **Borders** | `#232838` | Structural separators |

**Typography:**
- **UI Text**: Inter Variable Font (clean, modern)
- **Code Snippets**: JetBrains Mono (monospace, readable)

**Icons:**
- All vector SVGs with runtime color tinting for flexibility

---

## 🛡️ Security & Privacy

### Your Data, Your Control

DizoClip is engineered with privacy-first and defense-in-depth security principles:

#### 🔐 Hardware/Account-Bound DPAPI Encryption (At Rest)
```
Secret Key → Windows DPAPI CryptProtectData → User SID Encryption → DC_Keys.json
```
- API keys and secret tokens are strictly encrypted at rest via Windows Data Protection API (`crypt32.dll`)
- Encryption keys are tied directly to your Windows user account SID and machine hardware
- Only your Windows login profile can decrypt the data; unauthorized processes or other user accounts cannot read keys
- No master password required for everyday use

#### 📦 Scrypt + AES-128 Encrypted Archives (`.dizoclip`)
```
Password + 16-byte Salt → Scrypt (n=16384, r=8, p=1) → 256-bit Key → Fernet AES-128 CBC → .dizoclip
```
- Single standard export format eliminates plaintext leaks
- Protects your data in transit when migrating across devices or backing up to external drives
- Non-destructive import preview inspects the payload in RAM before committing changes

#### 🛡️ Clipboard Guard & Windows History (`Win+V`) Exemption
- **Clipboard History Bypass**: Prevents copied API keys and tokens from being permanently recorded in Windows 10/11 Clipboard History (`Win+V`) by registering OS exclusion flags (`CanIncludeInClipboardHistory = 0`, `CanUploadToCloudStore = 0`)
- **Configurable Auto-Clear**: Automatically wipes the Windows clipboard after 30 seconds (Toggleable in Settings, Default: OFF for maximum user flexibility)

#### 📝 Transparent Plain JSON for Developer Content
- Prompts (`DC_Prompts.json`), Commands (`DC_Commands.json`), and Snippets (`DC_AI_Models.json`) are stored as clean, readable plain JSON
- Free from proprietary locks: inspect, diff, search, or version-control your prompt engineering and terminal one-liners in Git without hurdles

#### 💾 Atomic Writes & Crash-Safe Backups
- Atomic write pattern (write to `.tmp` file, flush to disk, then replace target file) guarantees zero file corruption during power failures
- Automated timestamped snapshots stored in `User_Data/Backups/` before any write operations

#### 🚫 100% Offline & Zero Telemetry
- ✅ 100% offline desktop application
- ✅ No internet connection or network listening sockets required
- ✅ Zero telemetry, analytics, tracking, or crash pings
- ✅ No user accounts, registration, or cloud dependencies
- ✅ Your data never leaves your computer

---

## 💾 Storage & Persistence

DizoClip automatically adapts to your operating environment:

| Mode | Location | When |
| :--- | :--- | :--- |
| **Development** | `<project>/User_Data/` | Running from source (`python main.py`) |
| **Portable** | `<exe_dir>/User_Data/` | When `portable.flag` exists next to executable |
| **Installed** | `%APPDATA%\DizoClip\User_Data\` | Standard Windows installation |

### File Storage Schema

| File | Format | Encryption / Protection | Purpose |
| :--- | :--- | :--- | :--- |
| `DC_Keys.json` | JSON | **Windows DPAPI** (`CryptProtectData`) | API keys, secret tokens, environment credentials |
| `DC_Prompts.json` | Plain JSON | None (Human-readable UTF-8) | AI prompts, system instructions, and templates |
| `DC_Commands.json` | Plain JSON | None (Human-readable UTF-8) | Terminal commands, shell scripts, Docker/K8s recipes |
| `DC_AI_Models.json` | Plain JSON | None (Human-readable UTF-8) | Multi-language code snippets (Python, Node, Shell, LangChain) |
| `settings.json` | Plain JSON | None (Human-readable UTF-8) | User preferences, active tab, module visibility, theme settings |
| `Backups/` | JSON | Matches source dataset encryption | Automated timestamped pre-save snapshots for disaster recovery |
| `*.dizoclip` | Container | **Fernet AES-128 + Scrypt** | Password-protected selective export archive |

---

## 🏗️ Architecture

### Project Structure

```
DizoClip/
├── app/
│   ├── core/              # Core utilities (encryption, storage, fonts)
│   ├── components/        # Reusable UI components
│   ├── sections/          # Feature modules (keys, prompts, etc.)
│   ├── views/             # Main UI layouts
│   ├── window/            # Window management
│   ├── config/            # Configuration and theme
│   └── utils/             # Helper utilities
├── assets/                # Icons, fonts, images
├── docs/                  # Documentation
├── main.py                # Application entry point
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

### Tech Stack

- **Framework**: PySide6 (Qt 6)
- **Language**: Python 3.10+
- **Encryption**: Windows DPAPI
- **UI Theme**: Custom Fusion-based palette
- **Platform**: Windows 10+ only

---

## 🚀 Getting Started

### First Launch

1. **Run DizoClip**: `python main.py`
2. **View Onboarding**: Brief intro to local-first philosophy
3. **Start Adding Content**: Click **+** to add your first key, prompt, or command
4. **Pin to Desktop**: Use "Always on Top" in Settings
5. **Customize**: Arrange modules and toggle visibility as needed

### Basic Workflows

#### Adding an API Key
1. Go to **API Keys** tab
2. Click **+** button
3. Enter key name and secret value
4. Pick a color category
5. Click **Save**
6. One-click copy anytime!

#### Creating a Prompt Template
1. Go to **Prompts** tab
2. Click **+** button
3. Enter name and multiline prompt text
4. Assign color category
5. Click **Save**
6. Copy to clipboard instantly

#### Storing a Terminal Command
1. Go to **Commands** tab
2. Click **+** button
3. Enter command name and full command
4. Click **Save**
5. One-click copy when you need it

---

## 📊 Features at a Glance

| Feature | API Keys | Prompts | Snippets | Links | Commands |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Add / Edit / Delete | ✅ | ✅ | ✅ | ✅ | ✅ |
| Full-Text Search | ✅ | ✅ | ✅ | ✅ | ✅ |
| Context-Aware Search Auto-Toggle | ✅ | ✅ | ✅ | ✅ | ✅ |
| Color Categories & Custom HSV Picker | ✅ | ✅ | ✅ | ✅ | ✅ |
| Drag-and-Drop Card Reordering | ✅ | ✅ | ✅ | ✅ | ✅ |
| One-Click Instant Copy | ✅ | ✅ | ✅ | ✅ | ✅ |
| Reveal / Hide Secret Toggle | ✅ | ❌ | ❌ | ❌ | ❌ |
| One-Click Browser Launch | ❌ | ❌ | ❌ | ✅ | ❌ |
| Multi-Language Code Switcher | ❌ | ❌ | ✅ | ❌ | ❌ |
| Windows DPAPI Encryption (At Rest) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Human-Readable Plain JSON Storage | ❌ | ✅ | ✅ | ✅ | ✅ |
| Selective `.dizoclip` Export & Import | ✅ | ✅ | ✅ | ✅ | ✅ |
| Windows History (`Win+V`) Exemption | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 🧪 Testing

Run the automated test suite:

```bash
pytest
```

Tests cover:
- Data persistence and storage
- Encryption/decryption workflows
- UI component interactions
- Settings and configuration

---

## 🤝 Contributing

We welcome contributions! Feel free to:
- Report bugs and request features via [GitHub Issues](https://github.com/abdulkarim20-ui/DizoClip/issues)
- Submit pull requests to improve functionality
- Share feedback and suggestions

---

## 📖 Documentation

- [Security & Privacy](SECURITY.md) - Encryption, local storage, and security details

---

## 🗺️ Roadmap

### Next
- [ ] Tags system for advanced organization
- [ ] Custom hotkey support for quick access
- [ ] Command execution helpers
- [ ] Prompt variables (`{{name}}`)
- [ ] Global search across all modules

---

## 🆘 Troubleshooting

### DizoClip won't launch
```bash
# Run from a terminal to see errors
python main.py
```

### Data not saving
- Check that `User_Data/` directory has write permissions
- Ensure you have space on disk
- Review backups in `User_Data/Backups/`
- Use Settings → Data → Restore from Backup

### Secrets not decrypting
- Only accessible from the Windows user account that encrypted them
- Use Settings → Data → Export / Import to migrate between accounts or PCs

For more help, open a [GitHub Issue](https://github.com/abdulkarim20-ui/DizoClip/issues).

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for full details.

You are free to:
- ✅ Use DizoClip personally and commercially
- ✅ Modify and distribute the code
- ✅ Create derivative works

---

## 👨‍💻 About the Creator

**DizoClip** was created with ❤️ by **AbdulKarim** to solve real developer pain points.

- 🐙 **GitHub**: [@abdulkarim20-ui](https://github.com/abdulkarim20-ui)
- 💼 **LinkedIn**: [AbdulKarim](https://www.linkedin.com/in/abdulkarim27)

### Support DizoClip

If you find DizoClip helpful:
- ⭐ Star this repository
- 🐛 Report bugs and suggest features
- 📢 Share with other developers
- 💬 Provide feedback and ideas

---

## 🙏 Acknowledgments & Attributions

- **App Logo**: "Letter d" icon designed by [edt.im](https://www.flaticon.com/authors/edtim) from [Flaticon.com](https://www.flaticon.com/) (Licensed under Free for commercial use with attribution).
- **GUI Framework**: Built with **PySide6 (Qt 6)** - Python bindings for Qt
- **Typography**: **Inter** (by Rasmus Andersson) and **JetBrains Mono** (by JetBrains)
- **UI Icons**: Lucide icon collection
- Inspired by developer productivity and privacy-first workflow optimization

---

<div align="center">

**Made with ❤️ for developers who value time and security**

[Back to Top](#dizoclip)

</div>