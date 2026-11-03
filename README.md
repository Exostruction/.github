# Exostruction `.github`

Default files for all repositories of the organization (issue templates, pull request template, security and contributing notes) and the organization profile page.

| File | Purpose |
|---|---|
| `profile/README.md` | Shown on github.com/Exostruction |
| `profile/banner.png` | Banner for the profile page |
| `scripts/update_profile.py` | Writes latest pushes and active repos into the profile README |
| `.github/workflows/update-profile.yml` | Runs the script every 6 hours |
| `SECURITY.md`, `CONTRIBUTING.md`, `PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/` | Organization-wide defaults |

Do not edit the sections between the `<!--...:START-->` and `<!--...:END-->` markers in `profile/README.md` by hand, they are overwritten.
