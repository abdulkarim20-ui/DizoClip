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
- ✅ **Machine Specific**: Encrypted data cannot be transferred between computers
- ✅ **Automatic**: No manual key management required
- ✅ **Hardware Backed** (Optional): Uses TPM if available for additional security
- ✅ **Transparent**: Encryption/decryption happens automatically

### Data Encrypted

| Data Type | Encrypted? | Protected Location |
| :--- | :---: | :--- |
| API Keys & Secrets | ✅ Yes | `User_Data/DC_Keys.json` |
| Environment Variables | ✅ Yes | `User_Data/DC_Keys.json` |
| Tokens & Credentials | ✅ Yes | `User_Data/DC_Keys.json` |
| Prompts (text) | ❌ No | `User_Data/DC_Prompts.json` |
| Code Snippets / Models | ❌ No | `User_Data/DC_AI_Models.json` |
| Links | ❌ No | `User_Data/DC_Links.json` |
| Terminal Commands | ❌ No | `User_Data/DC_Commands.json` |
| Settings | ❌ No | `User_Data/DC_Settings.json` |
| Custom Colors | ❌ No | `User_Data/DC_Custom_Colors.json` |

### Data NOT Encrypted

Prompts, code snippets, links, and commands are stored in **plaintext JSON**. This is intentional:

- These items typically contain no sensitive information
- Encryption adds unnecessary complexity
- Plaintext allows easier manual editing if needed
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
- **Memory Safe**: Secrets stay in application memory only

### File Permissions

User data directory permissions:

```bash
User_Data/                    # Owner: Current User (RW)
├── DC_Keys.json              # Owner: Current User (RW)
├── DC_Prompts.json           # Owner: Current User (RW)
├── DC_AI_Models.json         # Owner: Current User (RW)
├── DC_Links.json             # Owner: Current User (RW)
├── DC_Commands.json          # Owner: Current User (RW)
├── DC_Settings.json          # Owner: Current User (RW)
├── DC_Custom_Colors.json     # Owner: Current User (RW)
└── Backups/                  # Owner: Current User (RW)
```

Only your user account has access to these files.

---

## 🌐 Network & Privacy

### Zero Network Activity

DizoClip performs **ZERO network calls**:

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

### Blocked Domains (Windows Firewall)

If you want extra assurance, you can block these domains in Windows Firewall:

```
- analytics.*.com
- telemetry.microsoft.com
- cdn.*.com
```

(These won't help since DizoClip doesn't call them, but good general practice)

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
2. **Email privately**: Send details to security@abdulkarim.dev
3. **Include**: Version, OS, steps to reproduce
4. **Responsible Disclosure**: Allow 90 days for fix before publishing

---

## 🔄 Backup Strategy

### Automatic Backups

DizoClip creates timestamped backups before every modification:

```
User_Data/Backups/
├── DC_Keys_2026-09-18_143022.json.bak
├── DC_Keys_2026-09-18_150145.json.bak
├── DC_Keys_2026-09-18_152330.json.bak
└── ...
```

### Retention

- Keeps last 100 backups
- Automatically removes older backups
- **Never deleted manually** unless you delete the Backups folder

### Manual Backup

To create a manual backup:

```bash
# Copy entire User_Data folder
xcopy User_Data C:\Backups\DizoClip_backup /E /I /H
```

### Restore from Backup

```bash
# Stop DizoClip (close the app)
# Replace corrupted file with backup
copy User_Data\Backups\DC_Keys_2026-09-18_143022.json.bak User_Data\DC_Keys.json
# Restart DizoClip
```

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

### What DizoClip Follows

| Standard | Compliance | Notes |
| :--- | :---: | :--- |
| OWASP Top 10 | ✅ | Secure coding practices |
| NIST Cybersecurity | ✅ | Defense in depth approach |
| GDPR (Personal Data) | ✅ | Your data stays local |
| HIPAA (Healthcare) | ⚠️ | Use only for non-regulated data |
| PCI-DSS (Payment Cards) | ❌ | Not certified for card storage |
| SOC 2 | ❌ | Single-user app, not required |

### What DizoClip Does NOT Comply With

- PCI-DSS: Don't store payment card numbers
- HIPAA: Don't store protected health information
- SOX: Not for regulated financial use

---

## ❓ Frequently Asked Questions

### Q: Is my data encrypted end-to-end?
**A:** Yes. Encryption is applied at rest locally on your machine using Windows DPAPI.

### Q: Can I access my encrypted keys from another computer?
**A:** No. DPAPI encryption is machine-specific and user-specific. Keys cannot be transferred between computers.

### Q: What if I forget my Windows password?
**A:** Unfortunately, you cannot decrypt DPAPI data without your Windows user credentials. Create a recovery disk before this happens.

### Q: Is the source code auditable?
**A:** Yes! DizoClip is open-source. You can review the security implementation in `app/core/security.py` and `app/core/storage.py`.

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

- **Security Issues**: security@abdulkarim.dev (responsible disclosure)
- **General Questions**: Open an issue on GitHub
- **Feature Requests**: Discussions tab on GitHub

---

<div align="center">

**Your security is our priority. Your data, your control.**

</div>
