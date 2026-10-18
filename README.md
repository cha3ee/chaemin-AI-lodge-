# Family Digital Scrapbook (우리 가족 디지털 스크랩북)

A cosy, bilingual (Korean / English) web scrapbook where family members send each other letters, photos and voice messages, and pin their favourites to a personal mood board.

---

## Problem Statement

**What problem are we solving?**
Families who live apart, across cities, countries or generations, mostly keep in touch through busy group chats. Meaningful moments like a handwritten-style letter, a favourite photo or a grandparent's voice get buried under hundreds of everyday messages and are hard to find again.

**Who experiences it?**
- Families separated by distance (for example, children studying or working overseas).
- Multi-generational, bilingual families, where grandparents may be more comfortable in Korean and younger members in English.
- Older family members who find modern chat apps cluttered and hard to navigate.

**Why is it worth solving?**
Keepsakes matter. A dedicated, calm space for family memories makes it easier to send something heartfelt, and easier to revisit it years later. Making that space bilingual and visually simple lowers the barrier for every generation to take part.

## Solution Overview

Family Digital Scrapbook is a Flask web app designed like a picnic table. Each object on the table opens a different part of the scrapbook:

| Object | Page | What it does |
|---|---|---|
| Note | Notes | Write and receive letters, shown as envelopes |
| Camera | Photos | Upload or share photos, shown as polaroids |
| Radio | Voice Messages | Upload or share audio recordings, shown as cassette tapes |
| Basket | Mood Board | Pin personal sticky notes and see all your favourited items |

Each family member creates an account, sends items to another member by username (optionally anonymously), and favourites the items they want to keep. The whole interface switches between Korean and English with one button.

## Key Features

- **Accounts:** register, log in and log out. Passwords are stored as secure hashes.
- **Letters (Notes):** send a note to any family member, optionally anonymously. Received notes appear as envelopes you can open and read.
- **Photo album:** upload photos for yourself or share them with a family member, with a caption. View them full-screen in a lightbox.
- **Voice messages:** record straight in the browser, or upload an audio file, and share it. Play it back in a cassette-style player.
- **Favourites (♥):** favourite any note, photo or voice message.
- **Personal mood board:** pin your own sticky notes and see all your favourited letters, photos (as pinned pictures) and voice messages (with a player) in one place.
- **Korean / English toggle:** every page, including login and register, switches language instantly, and the choice is remembered.
- **Local-time dates:** timestamps are stored in UTC and shown in the family's time zone (configurable).
- **Friendly validation:** clear messages for unknown recipients, unsupported file types and files that are too large.

## AI Integration

> **TODO: complete this section before submitting.** The app does not currently call any AI model at runtime. Describe the AI feature here once it is added (see the suggestions in the project notes), including:
> - Where AI is used (which page or feature).
> - Which model or API is called, and what is sent to it.
> - How the output is shown to the user and whether the user can edit or reject it.

AI-assisted development: an AI coding assistant (Claude) was used during development to diagnose bugs (an outdated database schema, broken upload folders and the language toggle), fix them, and add validation and favourites. All changes were reviewed and tested by the team.

## External Tools & Datasets

No external datasets are used. All content is created by users.

| Tool | Purpose |
|---|---|
| [Flask](https://flask.palletsprojects.com/) | Web framework |
| [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) / SQLite | Database and ORM |
| [Flask-Login](https://flask-login.readthedocs.io/) | Session-based authentication |
| [Werkzeug](https://werkzeug.palletsprojects.com/) | Password hashing (scrypt) and safe filenames |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Loads configuration and secrets from `.env` |
| [tzdata](https://pypi.org/project/tzdata/) | Time zone data for displaying local dates |
| [Gunicorn](https://gunicorn.org/) | Production web server (for deployment) |
| [python-telegram-bot](https://python-telegram-bot.org/) | Planned Telegram bot integration (see Roadmap) |
| "Garlic Bread" font | Display typeface (not bundled; see setup step 6) |

## Installation & Setup

**Requirements:** Python 3.10 or newer, and Git.

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd digital-scrapbook
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the project root:
   ```env
   SECRET_KEY=replace-with-a-long-random-string
   PORT=5000
   # Optional
   APP_TIMEZONE=Asia/Singapore
   FLASK_DEBUG=1
   TELEGRAM_BOT_TOKEN=your-bot-token
   ```
   You can generate a secret key with:
   `python -c "import secrets; print(secrets.token_hex(32))"`

5. **Run the app**
   ```bash
   python app.py
   ```
   Open <http://127.0.0.1:5000>. The SQLite database (`instance/scrapbook.db`) and the upload folders are created automatically on first run. Older databases are upgraded in place at startup.

6. **(Optional) Add the display font.** Place `GarlicBread.ttf` or `GarlicBread.otf` in `static/fonts/`. Without it, the app falls back to a default font.

7. **Try it out.** Register two accounts (for example `Mom` and `Sis`), send a note, a photo and a voice message from one to the other, favourite them, and open the mood board.

**Production:** set `FLASK_DEBUG=0` and a strong `SECRET_KEY`, then run with `gunicorn app:app`. The host needs persistent storage for `instance/` and `static/uploads/`.

## AI Safety & Limitations

### Risks and limitations
- **Uploaded files are not access-controlled.** Photos and voice messages are served from `static/uploads/`. Anyone who knows or guesses a file's URL can open it without logging in. Filenames include a timestamp, but this is not real protection.
- **Anyone can message anyone.** There are no family groups or invitations. Any registered user can send items to any username. Usernames are case-sensitive.
- **Anonymous messages could be misused.** There is no reporting, blocking or moderation feature.
- **No account recovery.** There is no email, password reset or account deletion.
- **No content moderation** of uploaded images or audio.
- **Storage:** SQLite and local file storage suit a small family deployment, not large-scale use. Data is not encrypted at rest.
- **AI-specific risks:** *(fill in once the AI feature is added, for example incorrect output, privacy of data sent to the model, and bias.)*

### Guardrails implemented
- Passwords hashed with scrypt. Plain-text passwords are never stored.
- Login required for every scrapbook page.
- Users can only view and favourite items they sent or received.
- Upload type allow-lists (images: png, jpg, jpeg, gif, webp, heic; audio: mp3, wav, m4a, webm, ogg, oga, aac).
- 20 MB upload size limit with a friendly error message.
- `secure_filename` on all uploads to prevent path traversal.
- Recipients are checked to exist before anything is sent.
- Secret key and bot token loaded from `.env`, which is excluded from Git.
- Jinja2 auto-escaping on all user-supplied text to prevent HTML and script injection.
- Debug mode can be turned off for deployment (`FLASK_DEBUG=0`).
- The microphone is only used after the user presses Record and grants browser permission. Recording stops automatically after 5 minutes.

### Testing done
Automated tests were run with Flask's test client against a copy of a real database. They checked that:
- All pages (`/`, `/login`, `/register`, `/notes`, `/photos`, `/voice`, `/board`) load for both logged-in and logged-out users.
- An old-version database is upgraded automatically, with existing users and notes kept.
- Photo and voice uploads succeed for valid files, including browser recordings (webm, m4a, ogg).
- Unknown recipients, disallowed file types and files over 20 MB are rejected with messages.
- Favourited photos and voice messages appear on the mood board.
- A user who is neither sender nor recipient cannot favourite someone else's item.
- Pinned board notes appear on the board.

## Roadmap

- **Telegram bot:** send a note, photo or voice message to the family bot and have it appear in the scrapbook.
- Family groups with invite links.
- Access-controlled media URLs.
