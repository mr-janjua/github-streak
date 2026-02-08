# GitHub Streak Tracker 🔥

Duolingo-style streak tracker for GitHub. Reminds you to commit every day and tracks your consistency.

## Features

- **Streak Tracking**: Current streak, longest streak, total active days
- **Smart Detection**: Monitors pushes, PRs, issues, and commits
- **Two Reminder Modes**:
  - **Normal**: Friendly, encouraging reminders
  - **Strict**: Aggressive Duolingo-style notifications that won't let you forget
- **Multiple Daily Checks**: Morning, afternoon, and evening reminders
- **Desktop Notifications**: System notifications that pop up automatically
- **Persistent Stats**: Your streak data is saved locally

## Installation

```bash
./install.sh
source ~/.bashrc  # or restart terminal
```

## Setup

Run the setup wizard:
```bash
streak setup
```

You'll need:
1. Your GitHub username
2. A Personal Access Token from https://github.com/settings/tokens
   - Required scopes: `repo` and `user`

## Usage

**Start the tracker** (runs in background):
```bash
streak
```

**Check stats anytime**:
```bash
streak stats
```

**Manual check**:
```bash
streak check
```

**Change reminder mode**:
```bash
streak mode strict   # Aggressive reminders
streak mode normal   # Friendly reminders
```

## Reminder Examples

### Normal Mode
- "💚 Start your GitHub streak today!"
- "🔥 5 day streak! You're building momentum!"
- "⏰ Evening reminder: Keep your streak alive!"

### Strict Mode
- "🦉 Your streak is DEAD. Get coding NOW or lose everything!"
- "🔴 FINAL WARNING! Your 15 day streak dies at midnight!"
- "💀 LAST CHANCE! Commit NOW or lose everything!"

## Schedule

The tracker runs checks at:
- **9:00 AM** - Morning check
- **2:00 PM** - Afternoon reminder
- **8:00 PM** - Evening warning (if no activity)

## Auto-Start on Boot

**Linux (systemd)**:
```bash
mkdir -p ~/.config/systemd/user
cp github-streak.service ~/.config/systemd/user/
systemctl --user enable github-streak.service
systemctl --user start github-streak.service
```

**macOS (launchd)**:
Add to `~/Library/LaunchAgents/com.github.streak.plist`

**Windows**:
Add `streak.py` to Task Scheduler

## Data Storage

All data stored in `~/.github_streak/`:
- `config.json` - Your username, token, and settings
- `streak.json` - Your streak history and stats

## Example Stats Output

```
==================================================
📊 YOUR GITHUB STREAK STATS
==================================================
Current Streak:    47 days 🔥
Longest Streak:    52 days 🏆
Total Active Days: 183 days
Last Commit:       2026-02-01
Reminder Mode:     STRICT
==================================================
```

## Tips

- Commit early in the day to avoid evening panic
- Even small commits count - update a README, fix a typo
- The tracker checks for: pushes, PRs, issues, comments
- Strict mode gets progressively more aggressive with longer streaks
- Break the streak and start over - no shame, just consistency

## Requirements

- Python 3.7+
- GitHub account with personal access token
- Desktop notification support

## Why?

GitHub contributions look impressive. A green grid shows consistency. This app makes sure you never forget to contribute, just like Duolingo makes sure you never forget your Spanish lessons (or else the owl comes for you).
