# 🔐 Security Setup Guide

## ⚠️ **IMPORTANT: API Key Security**

### **🚨 Never commit `.env` files to Git!**

Your `.env` file contains sensitive API keys that should NEVER be shared publicly.

## 🛠️ **Initial Setup**

### **Step 1: Copy the environment template**
```bash
cp .env.example .env
```

### **Step 2: Add your actual API keys to `.env`**
Edit the `.env` file and replace the placeholder values:

```bash
# Required for AI form handling
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Optional (only if you need them)
ANTHROPIC_API_KEY=your-actual-anthropic-key
XAI_API_KEY=your-actual-xai-key
GROQ_API_KEY=your-actual-groq-key
```

### **Step 3: Verify `.env` is ignored**
```bash
git status
# .env should NOT appear in untracked files
# If it does, check your .gitignore file
```

## 🔍 **Security Checklist**

### ✅ **Before Every Commit:**
- [ ] Run `git status` and ensure `.env` is not listed
- [ ] Check that no API keys are in any committed files
- [ ] Use `git diff --cached` to review staged changes

### ✅ **Repository Security:**
- [ ] `.env` file is in `.gitignore`
- [ ] Only `.env.example` is committed (with placeholder values)
- [ ] No real API keys in any Python files or config files

## 🚨 **If You Accidentally Commit API Keys:**

### **Option 1: Remove from latest commit**
```bash
git rm --cached .env
git commit --amend --no-edit
git push --force origin master
```

### **Option 2: Remove from entire history (what we just did)**
```bash
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch .env' --prune-empty --tag-name-filter cat -- --all
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force origin master
```

### **Option 3: Regenerate API keys**
- Go to your API provider (OpenAI, etc.)
- Regenerate/revoke the exposed keys
- Update your `.env` file with new keys

## 📋 **Best Practices**

1. **Use environment variables**: Always load sensitive data from `.env` files
2. **Regular audits**: Periodically check your repository for accidentally committed secrets
3. **GitHub Secret Scanning**: Enable secret scanning in your repository settings
4. **API key rotation**: Regularly rotate your API keys for security

## 🔗 **Useful Links**

- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [OpenAI API Key Management](https://platform.openai.com/account/api-keys)
- [Git Filter Branch Documentation](https://git-scm.com/docs/git-filter-branch)

---

**Remember: Security is everyone's responsibility! 🛡️**