# Security & Privacy Policy

## 🛡️ DizoClip Security Overview

DizoClip is engineered with **security-first principles**. Your data is encrypted, local, and never transmitted anywhere.

---

## 🔐 Encryption & Data Protection

### Windows DPAPI Encryption

All sensitive data (API keys, secrets) is encrypted using **Windows Data Protection API (DPAPI)**.

#### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│ Plain Secret Input                                           │
│ "sk-proj-abc123..."                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Windows DPAPI Encryption                                    │
│ CryptProtectData (crypt32.dll)                             │
│ Encryption key bound to:                                    │
│ - Windows User Account                                      │
│ - Machine Specific                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Encrypted at Rest                                           │
│ "dpapi:AQAAANCMn3eHwn9/VKxHiFs8..." (Base64)             │
│ Stored in User_Data/DC_Keys.json                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Atomic Disk Write                                           │
│ Temp file → Flush to disk → Commit                         │
│ (Never corrupted, even during power loss)                  │
└─────────────────────────────────────────────────────────────┘
```

#### Key Security Properties

- ✅ **User Account Bound**: Encryption key is tied to your Windows user account
- ✅ **Machine Specific**: Tied to your Windows user account; normally not decryptable elsewhere
- ✅ **Automatic**: No manual key management required
- ✅ **Transparent**: Encryption/decryption happens automatically

### Data Encrypted

| Data Type | Encrypted? | Protected Location |
| :--- | :---: | :--- |
| API Keys & Secrets | ✅ Yes (Windows DPAPI) | `User_Data/DC_Keys.json` |
| Prompts (text) | ❌ No (Plain JSON for Git tracking) | `User_Data/DC_Prompts.json` |
| Code Snippets / Models | ❌ No (Plain JSON for Git tracking) | `User_Data/DC_AI_Models.json` |
| Terminal Commands | ❌ No (Plain JSON for Git tracking) | `User_Data/DC_Commands.json` |
| Links | ❌ No (Plain JSON) | `User_Data/DC_Links.json` |
| Settings | ❌ No (Plain JSON) | `User_Data/DC_Settings.json` |
| Custom Colors | ❌ No (Plain JSON) | `User_Data/DC_Custom_Colors.json` |

API keys and secrets are strictly protected on disk using Windows DPAPI. Prompts, commands, and snippets are stored as transparent, readable JSON so you can version-control, inspect, and diff them in Git without friction. Before reinstalling Windows or migrating PCs, use **Settings → Data → Export Data (.dizoclip)** to create a password-protected backup.
- **Sensitive content in prompts? Use the API Keys module instead**

---

## 💾 Atomic Writes & Data Integrity

DizoClip uses **atomic write operations** to ensure data integrity:

### The Process

```
1. Data modification in memory
   ↓
2. Write to temporary file (DC_Keys.json.tmp)
   ↓
3. Flush to disk (os.fsync)
   ↓
4. Rename temp to permanent (atomic operation)
   ↓
5. Backup previous version to User_Data/Backups/
```

### Benefits

- ✅ **No Corruption**: Even if power fails during write, data is safe
- ✅ **No Partial Writes**: Either the full write completes or nothing is changed
- ✅ **Automatic Rollback**: Previous version is always available in Backups/
- ✅ **Crash Safe**: Application crash during save = no data loss

---

## 🔒 Access Control

### Reveal/Hide Toggle

Sensitive fields (like API keys) can be masked in the UI:

- **Hidden State**: Shows asterisks `* * * * * * *` instead of actual value
- **Reveal State**: Shows full secret on click (no timeout auto-hide)
- **Not Logged**: Reveal actions are not logged anywhere
- **Memory Safe**: Secrets stay in application memory only; a copied secret sits in the Windows clipboard until cleared (auto-clears after 30 seconds)

### File Permissions

User data directory files inherit the parent folder's permissions.

---

## 🌐 Network & Privacy

### Zero Network Activity

DizoClip performs **ZERO network calls on its own**:

- ✅ No telemetry or analytics
- ✅ No crash reporting to external servers
- ✅ No updates checking over internet
- ✅ No user tracking
- ✅ No data transmission anywhere

### Completely Offline

- Works without internet connection
- No cloud sync
- No account creation or login
- No backend servers

---

## 🔑 Key Management Best Practices

### Store Keys Safely

Use DizoClip's encrypted storage for:
- ✅ API keys and tokens
- ✅ OAuth tokens
- ✅ Database passwords
- ✅ SSH keys (copy content)
- ✅ Private credentials

### DO NOT Use DizoClip For

- ❌ Master passwords (use a dedicated password manager)
- ❌ Private SSH keys (use SSH-Agent instead)
- ❌ Very long-term credentials (rotate regularly)

### Rotation & Cleanup

- Regularly rotate old API keys
- Delete unused tokens
- Review stored secrets quarterly

---

## 🚨 Security Incident Response

### If You Suspect a Breach

1. **Rotate All Keys**: Update all API keys stored in DizoClip
2. **Check Backups**: Review `User_Data/Backups/` for unauthorized access
3. **Review Logs**: Check Windows Event Viewer for suspicious activity
4. **Export & Delete**: Use export feature, then uninstall

### Report Security Issues

If you discover a security vulnerability:

1. **Do NOT open a public GitHub issue**
2. **Report privately**: Use GitHub Security Advisories (Private Vulnerability Reporting)
3. **Include**: Version, OS, steps to reproduce

---

## 🔄 Backup Strategy

### Automatic Backups

DizoClip creates timestamped backups per dataset before every modification:

```
User_Data/Backups/
├── DC_Keys/
│   ├── 20260918-143022-123456.json
│   └── ...
├── DC_Prompts/
└── ...
```

### Retention

- Kept per dataset: saving settings can never evict API key backups
- Policy: newest 10 snapshots per dataset + 1 per day for the last 14 days
- Debounced: burst saves (e.g. dragging cards) are limited to 1 snapshot every 30 seconds
- Unchanged saves: byte-identical data creates no backup and writes nothing

### Restore from Backup

To restore data:
- In app: open **Settings → Data → Restore from Backup**, choose the dataset and timestamp, and click **Restore**.
- If a data file is damaged on start-up, DizoClip automatically displays a recovery dialog offering to restore the most recent valid backup. Damaged files are quarantined in `User_Data/Corrupt/`.

---

## 🔍 Windows Security Features

### Windows Defender

DizoClip is compatible with Windows Defender:
- ✅ No interference with antivirus scans
- ✅ Safe from malware signatures
- ✅ No exclusions needed

### UAC (User Account Control)

DizoClip **does not require admin privileges**:
- Runs as standard user
- No elevation necessary
- Safer for overall system

### Windows Firewall

DizoClip **does not need firewall exceptions**:
- No incoming connections
- No outgoing internet traffic
- Firewall won't interfere

---

## 🛠️ Security Maintenance

### Update Regularly

Keep DizoClip updated for:
- Latest security patches
- Dependency updates
- Windows compatibility

### Python Dependency Security

Dependencies are regularly scanned for vulnerabilities:

```bash
# Check for vulnerable packages
pip audit

# Update all packages
pip install -U -r requirements.txt
```

### Windows Updates

Always install Windows security updates:
- Keeps DPAPI secure
- Patches OS vulnerabilities
- Improves overall system security

---

## 📋 Compliance & Standards

DizoClip is a local developer tool and has not been independently audited.

---

## ❓ Frequently Asked Questions

### Q: Is my data encrypted end-to-end?
**A:** Encrypted at rest with Windows DPAPI. There is no sync, so end-to-end encryption does not apply.

### Q: Can I access my encrypted keys from another computer?
**A:** DPAPI keys are bound to your Windows account. To transfer data to another computer, use **Settings → Data → Export Data (.dizoclip)** to create a password-protected encrypted `.dizoclip` bundle, then import it on the new machine.

### Q: What if I forget my Windows password?
**A:** Unfortunately, you cannot decrypt DPAPI data without your Windows user credentials. Create a password-protected export before reinstalling or resetting your account.

### Q: Is the source code auditable?
**A:** Yes! DizoClip is open-source. You can review the security implementation in `app/core/security.py` and `app/core/data_manager.py`.

### Q: How do I verify the app isn't sending data somewhere?
**A:** Use network monitoring tools like Wireshark. DizoClip has zero internet connectivity and makes no external requests.

### Q: What if the executable is corrupted?
**A:** Always download from the official [GitHub releases](https://github.com/abdulkarim20-ui/DizoClip/releases) page. Verify the checksum if provided.

---

## 🔐 Security Roadmap

### v1.1 (Planned)

- [ ] Local password vault integration
- [ ] Biometric unlock (Windows Hello)
- [ ] Session timeout with auto-lock
- [ ] Audit logging of all access

### v1.2 (Planned)

- [ ] Key rotation reminders
- [ ] Weak password detection
- [ ] Encryption strength reporting
- [ ] Security health dashboard

---

## 📞 Support & Contact

For security questions or concerns:

- **Security Issues**: Report privately via GitHub Security Advisories
- **General Questions**: Open an issue on GitHub
- **Feature Requests**: Discussions tab on GitHub

---

<div align="center">

**Your security is our priority. Your data, your control.**

</div>
