# Security Policy

## Supported Versions

We actively support the latest version of rut with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue in rut, please report it responsibly.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by:

1. **Email**: Send details to schettino72@gmail.com
2. **Subject**: Include "[SECURITY]" in the subject line
3. **Details**: Include as much information as possible:
   - Type of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Communication**: We will keep you informed about the progress
- **Timeline**: We aim to release a fix within 30 days for critical issues
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)

### Security Best Practices

When using rut:

1. **Keep dependencies updated**: Regularly update rut and its dependencies (coverage, rich)
2. **Use trusted sources**: Install rut only from PyPI or the official GitHub repository
3. **Review test code**: Be cautious when running untrusted test code, as tests execute arbitrary Python code
4. **Conftest.py security**: Be aware that conftest.py files are executed and can run arbitrary code

### Known Security Considerations

- **Code execution**: rut executes Python test code, which has inherent security implications. Only run tests from trusted sources.
- **Conftest hooks**: The `rut_session_setup` and `rut_session_teardown` hooks execute arbitrary Python code from conftest.py files.
- **Coverage data**: Coverage reports may contain file paths and code snippets from your project.

## Disclosure Policy

When a security vulnerability is reported and fixed:

1. We will publish a security advisory on GitHub
2. We will release a patch version with the fix
3. We will credit the reporter (unless anonymity is requested)
4. We will document the issue in the CHANGES file

Thank you for helping keep rut and its users safe!
