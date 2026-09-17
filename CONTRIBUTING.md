# Contributing to DizoClip

Thanks for considering contributing to DizoClip! Whether it's bug reports, feature requests, or code contributions, we appreciate your help.

---

## 🤝 How to Contribute

### 1. Report a Bug

Found an issue? Help us fix it!

**Before Reporting:**
- Check existing [GitHub Issues](https://github.com/abdulkarim20-ui/DizoClip/issues) to avoid duplicates
- Try running the latest version from source
- Test with Python 3.10+ and Windows 10/11

**How to Report:**

1. Go to [GitHub Issues](https://github.com/abdulkarim20-ui/DizoClip/issues)
2. Click **New Issue** → **Bug Report**
3. Provide:
   - **Title**: Clear, specific description
   - **Environment**: Windows version, Python version, DizoClip version
   - **Steps to Reproduce**: Exact steps to replicate the bug
   - **Expected Behavior**: What should happen
   - **Actual Behavior**: What actually happened
   - **Screenshots**: If applicable (for UI issues)
   - **Error Logs**: Console output or crash logs

**Example Bug Report:**

```
Title: API Keys window doesn't save new key on first try

Environment:
- Windows 11 (Build 22621)
- Python 3.11.1
- DizoClip v1.0.0

Steps to Reproduce:
1. Launch DizoClip
2. Click API Keys tab
3. Click + button
4. Enter name "TestKey" and secret "abc123"
5. Click Save

Expected: Key appears in list
Actual: Save button does nothing, no error shown

Screenshots: [attached]
```

---

### 2. Request a Feature

Have an idea to improve DizoClip?

**Before Requesting:**
- Check existing [GitHub Discussions](https://github.com/abdulkarim20-ui/DizoClip/discussions)
- Ensure it aligns with DizoClip's privacy-first philosophy
- Consider if it's feasible for a single-user app

**How to Request:**

1. Go to [GitHub Discussions](https://github.com/abdulkarim20-ui/DizoClip/discussions)
2. Click **New Discussion** → **Feature Request**
3. Provide:
   - **Title**: Clear feature name
   - **Problem**: What pain point does this solve?
   - **Proposed Solution**: Your idea (if any)
   - **Alternative Approaches**: Other ways to solve it
   - **Use Case**: When would you use this?

**Example Feature Request:**

```
Title: Dark/Light theme toggle

Problem: Some users prefer light backgrounds

Proposed Solution:
Add toggle in Settings → Appearance that switches between:
- Current Midnight Slate (dark)
- New Light theme (light backgrounds)

Use Case: Working in bright environments
```

---

### 3. Contribute Code

Want to contribute code? Follow these guidelines:

#### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/abdulkarim20-ui/DizoClip.git
cd DizoClip

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dev dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run tests to verify setup
pytest
```

#### Development Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix-name
   ```

2. **Make Changes**
   - Follow the code style guidelines (see below)
   - Write clear commit messages
   - Add tests for new features
   - Update documentation if needed

3. **Test Your Changes**
   ```bash
   pytest
   python main.py  # Manual testing
   ```

4. **Format & Lint**
   ```bash
   black .
   flake8 app/
   ```

5. **Commit & Push**
   ```bash
   git add .
   git commit -m "feat: add awesome feature"
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**
   - Go to [GitHub](https://github.com/abdulkarim20-ui/DizoClip)
   - Click **Pull Request** → **New Pull Request**
   - Select your branch
   - Provide clear description of changes

#### Code Style Guidelines

**PEP 8 Compliance:**
```python
# Good
def calculate_age(birth_year: int) -> int:
    """Calculate age from birth year."""
    return 2024 - birth_year

# Bad
def calc_age(by):
    return 2024-by
```

**Type Hints:**
```python
# Good
def save_data(filename: str, data: dict) -> bool:
    pass

# Bad
def save_data(filename, data):
    pass
```

**Docstrings:**
```python
def protect_secret(value: str) -> str:
    """
    Encrypt a secret using Windows DPAPI.
    
    Args:
        value: The plaintext secret to protect
        
    Returns:
        Protected secret prefixed with 'dpapi:' (or 'plain:' fallback)
        
    Raises:
        TypeError: If value is not a string
    """
    pass
```

**Comments:**
```python
# Explain WHY, not WHAT
# Good: Wait 50ms to ensure rendering completes before animation
QTimer.singleShot(50, self.show_animation)

# Bad: Wait 50ms
QTimer.singleShot(50, self.show_animation)
```

---

### 4. Improve Documentation

Help make DizoClip easier to use!

#### Documentation Types

- **README.md**: Main documentation
- **SECURITY.md**: Security details
- **Code Comments**: In-code documentation
- **Docstrings**: Function documentation
- **User Guides**: Tutorials and walkthroughs

#### How to Contribute

1. Fork and create a branch: `git checkout -b docs/improvement`
2. Make changes to `.md` files
3. Test formatting: Markdown should render correctly on GitHub
4. Submit PR with clear description

---

## 📋 Pull Request Process

### Before Submitting

- [ ] Tests pass: `pytest`
- [ ] Code formatted: `black .`
- [ ] Linting clean: `flake8 app/`
- [ ] No debug code (`print()`, `breakpoint()`)
- [ ] Updated related docs
- [ ] Clear commit messages
- [ ] Only one feature/fix per PR

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Related Issue
Fixes #123

## Testing Done
- [ ] Unit tests added
- [ ] Manual testing completed
- [ ] No breaking changes

## Screenshots (if UI changes)
<!-- Attach screenshots -->

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
```

### Review Process

1. Maintainer reviews code
2. Changes requested if needed
3. You make updates
4. Approved and merged

---

## 🗂️ Project Structure

```
DizoClip/
├── app/
│   ├── core/              # Core functionality
│   │   ├── security.py    # DPAPI encryption
│   │   ├── storage.py     # Data persistence
│   │   └── ...
│   ├── components/        # Reusable UI components
│   ├── sections/          # Feature modules
│   ├── views/             # Main UI layouts
│   └── window/            # Window management
├── tests/                 # Unit tests
├── assets/                # Images, icons, fonts
└── docs/                  # Documentation
```

---

## 🧪 Testing Guidelines

### Write Tests For

- ✅ New features
- ✅ Bug fixes
- ✅ Security-related changes
- ✅ Data persistence
- ✅ Encryption/decryption

### Test Structure

```python
import pytest
from app.core.security import protect_secret, unprotect_secret

def test_encrypt_decrypt_roundtrip():
    """Test that encrypted secret can be decrypted."""
    original = "test-secret-123"
    protected = protect_secret(original)
    unprotected = unprotect_secret(protected)
    assert unprotected == original

def test_non_string_secret_raises_error():
    """Test that non-string secret raises TypeError."""
    with pytest.raises(TypeError):
        protect_secret(12345)
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_security.py::test_encrypt_decrypt_roundtrip

# Run with coverage
pytest --cov=app
```

---

## 🔒 Security Considerations

For security-related changes:

1. **Responsible Disclosure**: Don't open public issues for vulnerabilities
2. **Test Thoroughly**: Security changes need extra testing
3. **Document Impact**: Explain security implications
4. **Review Carefully**: Security changes get extra scrutiny
5. **No Hardcoded Secrets**: Never commit API keys or tokens

---

## 📝 Commit Message Guidelines

### Format

```
<type>: <subject>

<body>

<footer>
```

### Type

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting, missing semicolons, etc)
- `refactor`: Code refactoring without feature changes
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Dependency updates, build changes

### Examples

```
feat: add biometric unlock support

- Integrate Windows Hello API
- Add Face/Fingerprint unlock option
- Auto-lock after 5 minutes idle

Fixes #234

fix: prevent clipboard data loss on close

Ensure all pending writes complete before application exit.
Use atomic write operations for safety.

Fixes #567

docs: update security documentation

Add section on DPAPI encryption and key rotation best practices.
```

---

## 🚀 Development Tips

### Run DizoClip from Source

```bash
# Simple run
python main.py

# With debug output
python main.py --debug

# With profiling
python -m cProfile -s cumtime main.py
```

### Debug Mode

```python
# Add debug prints
if __debug__:
    print("Debug info:", variable)

# Use pdb for debugging
import pdb; pdb.set_trace()
```

### Common Tasks

```bash
# Install new dependency
pip install package_name
pip freeze > requirements.txt

# Format all code
black .

# Check code quality
flake8 app/ tests/

# Update dependencies
pip install --upgrade -r requirements.txt
```

---

## 🎯 Contribution Ideas

### Great First Issues

- Fix typos in documentation
- Improve error messages
- Add unit tests
- Create user guides
- Optimize performance

### Medium Difficulty

- New settings options
- Additional UI themes
- Improved search
- Export/import features

### Advanced

- Multi-device sync
- Browser extensions
- Mobile companion app
- Team collaboration

---

## ❓ Questions or Need Help?

- **GitHub Issues**: For bugs and features
- **GitHub Discussions**: For questions and ideas
- **Email**: Contact AbdulKarim directly

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## 🙏 Thank You!

Every contribution matters. Whether it's code, documentation, bug reports, or just spreading the word—thank you for helping make DizoClip better!

<div align="center">

**Happy Contributing! 🎉**

</div>
