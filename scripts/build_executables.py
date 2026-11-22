"""
Automated Build and Packaging Script for DizoClip.
Compiles standalone Portable and Installed executables using PyInstaller and Inno Setup,
organizes them into Portable/ and Installed/ directories, and cleans up build artifacts.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
from app import __version__ as APP_VERSION  # noqa: E402
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
RELEASE_DIR = ROOT_DIR / "release"
PORTABLE_DIR = RELEASE_DIR / "Portable"
INSTALLED_DIR = RELEASE_DIR / "Installed"
ASSETS_DIR = ROOT_DIR / "assets"
ICON_PATH = ASSETS_DIR / "app_logo.ico"


def find_iscc() -> Path | None:
    """Find Inno Setup Compiler (ISCC.exe) if installed."""
    # Check PATH
    iscc_path = shutil.which("iscc")
    if iscc_path:
        return Path(iscc_path)

    # Standard Windows install locations
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 7" / "ISCC.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
        Path("C:/Program Files/Inno Setup 7/ISCC.exe"),
        Path("C:/Program Files (x86)/Inno Setup 7/ISCC.exe"),
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def find_compat_binaries() -> list[Path]:
    """Find python3t.dll or other compat DLLs required by free-threaded Python on Windows."""
    python_dir = Path(sys.executable).parent
    candidates = [
        python_dir / "abi3t-compat" / "python3t.dll",
        python_dir / "python3t.dll",
    ]
    return [p for p in candidates if p.is_file()]


def run_pyinstaller() -> Path:
    """Compile the single standalone executable with PyInstaller."""
    print("=" * 60)
    print("STEP 1: Compiling DizoClip executable with PyInstaller...")
    print("=" * 60)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconsole",
        "--onefile",
        "--collect-all",
        "cryptography",
        "--name",
        "DizoClip",
        "--icon",
        str(ICON_PATH),
        "--add-data",
        f"{ASSETS_DIR};assets",
    ]
    for binary in find_compat_binaries():
        cmd.extend(["--add-binary", f"{binary};."])
    cmd.append(str(ROOT_DIR / "main.py"))

    print("Running:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        raise RuntimeError(f"PyInstaller failed with return code {res.returncode}")

    built_exe = DIST_DIR / "DizoClip.exe"
    if not built_exe.is_file():
        raise FileNotFoundError(f"Expected compiled binary not found at {built_exe}")

    print(f"Successfully compiled: {built_exe} ({built_exe.stat().st_size // (1024*1024)} MB)")
    return built_exe


def setup_portable_package(built_exe: Path) -> Path:
    """Package the Portable Edition."""
    print("\n" + "=" * 60)
    print("STEP 2: Organizing Portable Edition...")
    print("=" * 60)

    PORTABLE_DIR.mkdir(parents=True, exist_ok=True)
    portable_exe = PORTABLE_DIR / "DizoClip-Portable.exe"
    shutil.copy2(built_exe, portable_exe)

    # Create portable.flag
    (PORTABLE_DIR / "portable.flag").write_text(
        "# DizoClip Portable Mode Indicator\n"
        "# When this file is present, user data is saved inside the local User_Data/ directory.\n",
        encoding="utf-8",
    )

    # Create Portable README
    (PORTABLE_DIR / "README.txt").write_text(
        "DizoClip - Portable Edition\n"
        "===========================\n\n"
        "Features:\n"
        "- 100% Self-Contained: Zero installation or admin rights required.\n"
        "- Local Data Storage: All your settings, API keys (DPAPI-protected),\n"
        "  prompts, AI models, links, and commands are stored inside the\n"
        "  adjacent 'User_Data' folder.\n"
        "- Your API keys are tied to your Windows account and will not open on a different PC.\n\n"
        "To Run:\n"
        "Double-click 'DizoClip-Portable.exe'.\n",
        encoding="utf-8",
    )

    print(f"Portable edition ready at: {PORTABLE_DIR}")
    return portable_exe


def setup_installed_package(built_exe: Path) -> Path:
    """Package the Installed Edition."""
    print("\n" + "=" * 60)
    print("STEP 3: Organizing Installed Edition...")
    print("=" * 60)

    INSTALLED_DIR.mkdir(parents=True, exist_ok=True)
    installed_exe = INSTALLED_DIR / "DizoClip.exe"
    shutil.copy2(built_exe, installed_exe)

    # Create Installed README
    (INSTALLED_DIR / "README.txt").write_text(
        "DizoClip - Installed Edition\n"
        "============================\n\n"
        "Features:\n"
        "- Standard Windows Application: Stores all durable user data inside\n"
        "  %APPDATA%\\DizoClip\\User_Data, keeping application files clean.\n"
        "- Windows Integration: Taskbar pinning and clean native desktop integration.\n\n"
        "Files:\n"
        "- DizoClip-Setup.exe : Run this to install DizoClip with Desktop and Start Menu shortcuts.\n"
        "- DizoClip.exe       : Standalone installed executable (runs directly using %APPDATA%).\n",
        encoding="utf-8",
    )

    # Build Setup Installer using Inno Setup if available
    iscc = find_iscc()
    if iscc:
        print(f"Found Inno Setup Compiler at: {iscc}")
        iss_script = create_inno_script(built_exe)
        iss_path = ROOT_DIR / "setup_script.iss"
        iss_path.write_text(iss_script, encoding="utf-8")

        print("Compiling Windows Installer (DizoClip-Setup.exe)...")
        res = subprocess.run([str(iscc), str(iss_path)], cwd=str(ROOT_DIR))
        if iss_path.exists():
            iss_path.unlink()

        if res.returncode == 0:
            setup_exe = INSTALLED_DIR / "DizoClip-Setup.exe"
            if setup_exe.is_file():
                print(f"Windows Setup Installer ready at: {setup_exe}")
                # Keep only the installer in Installed/ folder
                if installed_exe.is_file():
                    installed_exe.unlink()
        else:
            print("Warning: Inno Setup compilation returned non-zero code.")
    else:
        print("Note: Inno Setup compiler not detected. Skipping DizoClip-Setup.exe compilation.")

    print(f"Installed edition ready at: {INSTALLED_DIR}")
    return INSTALLED_DIR / "DizoClip-Setup.exe" if (INSTALLED_DIR / "DizoClip-Setup.exe").is_file() else installed_exe



def create_inno_script(exe_path: Path) -> str:
    """Generate Inno Setup script content."""
    return f"""
#define MyAppName "DizoClip"
#define MyAppVersion "{APP_VERSION}"
#define MyAppPublisher "AbdulKarim"
#define MyAppURL "https://github.com/abdulkarim20-ui"
#define MyAppExeName "DizoClip.exe"
#define MyAppId "AbdulKarim.DizoClip.1.0"

[Setup]
AppId={{{{D120C119-DIZO-CLIP-2026-ABK9942}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppVerName={{#MyAppName}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DisableProgramGroupPage=yes
LicenseFile={str(ROOT_DIR / "LICENSE").replace(os.sep, "/")}
OutputDir={str(INSTALLED_DIR).replace(os.sep, "/")}
OutputBaseFilename=DizoClip-Setup
SetupIconFile={str(ICON_PATH).replace(os.sep, "/")}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
SetupAppTitle=DizoClip Setup
SetupWindowTitle=DizoClip Setup

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"

[Files]
Source: "{str(exe_path).replace(os.sep, "/")}"; DestDir: "{{app}}"; DestName: "{{#MyAppExeName}}"; Flags: ignoreversion

[Icons]
Name: "{{autoprograms}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; AppUserModelID: "{{#MyAppId}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon; AppUserModelID: "{{#MyAppId}}"

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent
"""


def cleanup_build_artifacts():
    """Remove intermediate build artifacts."""
    print("\n" + "=" * 60)
    print("STEP 4: Cleaning up temporary build directories...")
    print("=" * 60)

    # 1. Remove build directory
    if BUILD_DIR.is_dir():
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
        print(f"Removed temporary directory: {BUILD_DIR}")

    # 2. Remove spec file in root
    spec_file = ROOT_DIR / "DizoClip.spec"
    if spec_file.is_file():
        spec_file.unlink()
        print(f"Removed temporary spec file: {spec_file}")

    # 3. Clean up PyInstaller dist directory
    if DIST_DIR.is_dir():
        shutil.rmtree(DIST_DIR, ignore_errors=True)
        print(f"Removed temporary directory: {DIST_DIR}")

    print("Build cleanup completed successfully!")


def main():
    try:
        portable_only = "--portable-only" in sys.argv or "-p" in sys.argv

        built_exe = run_pyinstaller()
        setup_portable_package(built_exe)
        if not portable_only:
            setup_installed_package(built_exe)
        cleanup_build_artifacts()

        print("\n" + "*" * 60)
        print("BUILD SUCCESSFUL!")
        print(f"1. Portable Version:  {PORTABLE_DIR / 'DizoClip-Portable.exe'}")
        if not portable_only:
            if (INSTALLED_DIR / "DizoClip-Setup.exe").is_file():
                print(f"2. Windows Installer: {INSTALLED_DIR / 'DizoClip-Setup.exe'}")
            elif (INSTALLED_DIR / "DizoClip.exe").is_file():
                print(f"2. Installed Version: {INSTALLED_DIR / 'DizoClip.exe'}")
        print("*" * 60)
    except Exception as exc:
        print(f"Build failed with error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
