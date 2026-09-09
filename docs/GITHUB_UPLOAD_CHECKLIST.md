# GitHub upload checklist

Before publishing:

- [ ] Confirm `accounts.json`, passwords, email addresses, cookies, screenshots, and private notes are absent.
- [ ] Run `git status --ignored` and verify `config/local/` stays ignored.
- [ ] Run `python -m compileall -q src scripts`.
- [ ] Run `pytest`.
- [ ] Run `python scripts/verify_setup.py` on the Windows machine that will run the bot.
- [ ] Decide whether to add an open-source license. The repository currently uses an all-rights-reserved notice.
- [ ] Review `config/examples/` and keep only sanitized sample values.
- [ ] Do not commit Tesseract/Sandboxie/game EXE or DLL files.
- [ ] If the old repository was ever pushed with credentials, rotate those credentials and purge the old Git history before making it public.

Suggested first commit:

```powershell
git init
git add .
git status
git commit -m "Rebuild WOTK Mod 2.0"
```

Check `git status` carefully before committing. Local calibration files under `config/local/` should
not appear in the staged set.
