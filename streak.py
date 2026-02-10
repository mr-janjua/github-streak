#!/usr/bin/env python3

import os
import json
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
import time
import schedule
from plyer import notification
import sys
import random

class GitHubStreakTracker:
    def __init__(self):
        self.config_dir = Path.home() / ".github_streak"
        self.config_file = self.config_dir / "config.json"
        self.streak_file = self.config_dir / "streak.json"
        
        self.config_dir.mkdir(exist_ok=True)
        
        self.username = None
        self.token = None
        self.reminder_mode = "normal"
        self.streak_data = self.load_streak_data()
        
    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.username = config.get('username')
                self.token = config.get('token')
                self.reminder_mode = config.get('reminder_mode', 'normal')
            return True
        return False
    
    def save_config(self):
        config = {
            'username': self.username,
            'token': self.token,
            'reminder_mode': self.reminder_mode
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_streak_data(self):
        if self.streak_file.exists():
            with open(self.streak_file, 'r') as f:
                return json.load(f)
        return {
            'current_streak': 0,
            'longest_streak': 0,
            'last_commit_date': None,
            'total_days': 0,
            'commit_history': {}
        }
    
    def save_streak_data(self):
        with open(self.streak_file, 'w') as f:
            json.dump(self.streak_data, f, indent=2)
    
    def setup(self):
        # If a config already exists, confirm before overwriting
        existing = None
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    existing = json.load(f)
            except Exception:
                existing = None

            print("Configuration already exists.")
            if existing:
                print(f"Username: {existing.get('username')}")

            ans = input("Overwrite existing configuration? (y/N): ").strip().lower()
            if ans != 'y':
                print("Setup aborted. Existing configuration preserved.")
                return

            del_ans = input("Delete previous streak records as well? (y/N): ").strip().lower()
            if del_ans == 'y':
                try:
                    if self.streak_file.exists():
                        self.streak_file.unlink()
                except Exception as e:
                    print(f"Could not delete streak file: {e}")

                self.streak_data = {
                    'current_streak': 0,
                    'longest_streak': 0,
                    'last_commit_date': None,
                    'total_days': 0,
                    'commit_history': {}
                }
                self.save_streak_data()
            else:
                # Keep existing streak data if present
                self.streak_data = self.load_streak_data()

        print("🔥 GitHub Streak Tracker Setup 🔥\n")

        existing_username = existing.get('username') if existing else None
        if existing_username:
            prompt = f"Enter your GitHub username [{existing_username}]: "
            inp = input(prompt).strip()
            self.username = inp if inp else existing_username
        else:
            self.username = input("Enter your GitHub username: ").strip()

        print("\nTo get your GitHub Personal Access Token:")
        print("1. Go to https://github.com/settings/tokens")
        print("2. Generate new token (classic)")
        print("3. Make sure you read and understand what a token is and the permissions it has!")
        print("4. Select 'repo' and 'user' scopes")
        print("5. Copy the token\n")

        existing_token = existing.get('token') if existing else None
        if existing_token:
            token_prompt = "Enter your GitHub token (leave blank to keep existing): "
            token_inp = input(token_prompt).strip()
            self.token = token_inp if token_inp else existing_token
        else:
            self.token = input("Enter your GitHub token: ").strip()

        print("\nReminder Mode:")
        print("1. Normal - Friendly reminders")
        print("2. Strict - Aggressive Duolingo-style reminders")

        current_mode = existing.get('reminder_mode', 'normal') if existing else 'normal'
        default_choice = '2' if current_mode == 'strict' else '1'
        mode_choice = input(f"Choose mode (1 or 2) [{default_choice}]: ").strip()
        if mode_choice == '':
            mode_choice = default_choice
        self.reminder_mode = "strict" if mode_choice == "2" else "normal"

        self.save_config()
        print("\n✓ Setup complete!")
    
    def check_github_activity(self):
        today = datetime.now().date().isoformat()
        
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f'https://api.github.com/users/{self.username}/events'
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            events = response.json()
            
            for event in events:
                created = event.get('created_at')
                if not created:
                    continue

                # Parse GitHub event timestamp (UTC) and convert to local date
                try:
                    event_dt = datetime.strptime(created, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).astimezone()
                except Exception:
                    # Fallback for other ISO formats with offset
                    try:
                        event_dt = datetime.fromisoformat(created.replace('Z', '+00:00')).astimezone()
                    except Exception:
                        continue

                event_date = event_dt.date().isoformat()
                if event_date == today:
                    if event['type'] in ['PushEvent', 'PullRequestEvent', 'IssuesEvent', 
                                        'CreateEvent', 'CommitCommentEvent']:
                        return True
            
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"Error checking GitHub: {e}")
            return None
    
    def update_streak(self, has_activity):
        today = datetime.now().date().isoformat()
        yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
        
        last_date = self.streak_data['last_commit_date']
        
        if has_activity:
            # Activity detected today
            self.streak_data['commit_history'][today] = True
            
            if last_date == yesterday:
                # Had activity yesterday, continue the streak
                self.streak_data['current_streak'] += 1
            else:
                # No activity yesterday or ever, start new streak
                self.streak_data['current_streak'] = 1
            
            self.streak_data['last_commit_date'] = today
            
            if self.streak_data['current_streak'] > self.streak_data['longest_streak']:
                self.streak_data['longest_streak'] = self.streak_data['current_streak']
            
            self.streak_data['total_days'] = len(self.streak_data['commit_history'])
            self.save_streak_data()
            
            return True
        else:
            # No activity today
            if last_date != yesterday:
                # Activity was not yesterday, so streak is broken (no activity for 2+ consecutive days)
                self.streak_data['current_streak'] = 0
                self.save_streak_data()
            # If last_date == yesterday, just remind the user but keep the streak alive
            
            return False
    
    def get_reminder_message(self):
        streak = self.streak_data['current_streak']
        yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
        last_date = self.streak_data['last_commit_date']
        
        # If we have an active streak from yesterday, show THAT streak at risk
        if last_date == yesterday and streak > 0:
            at_risk_streak = streak
        else:
            at_risk_streak = 0
        
        if self.reminder_mode == "strict":
            if at_risk_streak == 0:
                return "🦉 Your streak is DEAD. Get coding NOW or lose everything!"
            elif at_risk_streak == 1:
                return "🔥 You have 1 day streak! Don't break it NOW, pathetic! COMMIT NOW"
            elif at_risk_streak < 5:
                return f"⚡ {at_risk_streak} day streak! One lazy day = GONE FOREVER! COMMIT NOW"
            elif at_risk_streak < 10:
                return f"💪 {at_risk_streak} days! But I'm watching... Don't break it! COMMIT NOW"
            elif at_risk_streak < 20:
                return f"🎯 {at_risk_streak} DAYS! Miss today and cry tomorrow! COMMIT NOW"
            elif at_risk_streak < 30:
                return f"👑 {at_risk_streak} DAYS LEGEND! One miss = back to ZERO, loser! COMMIT NOW"
            elif at_risk_streak < 50:
                return f"🚀 {at_risk_streak} DAYS INSANE! Don't you DARE break this NOW! COMMIT NOW"
            else:
                return f"🏆 {at_risk_streak} DAYS ABSOLUTE UNIT! Keep going or regret it FOREVER! COMMIT NOW"
        else:
            if at_risk_streak == 0:
                return "💚 Start your GitHub streak today!"
            elif at_risk_streak == 1:
                return "🌱 1 day streak! Keep it going, commit something today!"
            elif at_risk_streak < 5:
                return f"🔥 {at_risk_streak} day streak! Don't break the momentum!"
            elif at_risk_streak < 10:
                return f"⭐ {at_risk_streak} days! You're on fire, keep it going!"
            elif at_risk_streak < 20:
                return f"🎉 {at_risk_streak} days! This is becoming a habit!"
            elif at_risk_streak < 30:
                return f"💎 {at_risk_streak} days! You're a GitHub legend, don't stop!"
            elif at_risk_streak < 50:
                return f"🚀 {at_risk_streak} DAYS! Incredible dedication, keep going!"
            else:
                return f"👑 {at_risk_streak} DAYS! You're unstoppable, don't break it!"

    def random_reminder(self, streak=None):
        """Return a reminder string prefixed with today's date, choosing one of 20 messages at random."""
        today = datetime.now().date().isoformat()
        if streak is None:
            streak = self.streak_data.get('current_streak', 0)

        messages = []

        # Create 20 variations depending on mode and streak
        if self.reminder_mode == 'strict':
            templates = [
                "🔴 FINAL WARNING! Your {s} day streak dies at midnight!",
                "⏰ TIME IS RUNNING OUT! {s} days on the line!",
                "💀 LAST CHANCE! Commit NOW or lose {s} days!",
                "🚨 Don't be lazy — {s} day(s) will vanish without a commit!",
                "🔥 {s} day streak! One miss = back to ZERO! COMMIT NOW",
                "👑 {s} DAYS LEGEND! Protect it with a commit NOW!",
                "⚡ {s} days! This is serious — commit this minute!",
                "💣 Danger: your {s} day streak can end TODAY! Commit!",
                "🦉 The owl is watching. {s} day streak at risk — commit now!",
                "💥 Don't lose {s} days of work — push something now!"
            ]
        else:
            templates = [
                "💚 Start your GitHub streak today!",
                "🌱 {s} day streak! Keep it going, commit something today!",
                "🔥 {s} day streak! Don't break the momentum!",
                "⭐ {s} days! You're on fire, keep it going!",
                "🎉 {s} days! This is becoming a habit!",
                "💎 {s} days! You're a GitHub legend, don't stop!",
                "🚀 {s} DAYS! Incredible dedication, keep going!",
                "⏰ Evening reminder: Keep your {s} day streak alive!",
                "🌙 Don't forget! Commit before bed to maintain your streak.",
                "💚 Quick reminder: Your {s} day streak needs attention!"
            ]

        # Ensure we have exactly 20 messages by adding small variations
        for i in range(20):
            t = templates[i % len(templates)]
            msg = t.format(s=streak)
            # Add a tiny variation for uniqueness
            if i >= len(templates):
                msg = f"{msg} ({i+1})"
            messages.append(msg)

        chosen = random.choice(messages)
        return f"{today} - {chosen}"
    
    def send_notification(self, title, message):
        try:
            notification.notify(
                title=title,
                message=message,
                app_name='GitHub Streak',
                timeout=10
            )
        except Exception as e:
            print(f"Notification error: {e}")
    
    def morning_check(self):
        print(f"\n{'='*50}")
        print(f"Morning Check - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*50}")
        
        today = datetime.now().date().isoformat()
        
        if self.streak_data['commit_history'].get(today):
            streak = self.streak_data['current_streak']
            print(f"✓ Already committed today! Streak: {streak} days 🔥")
            return
        
        has_activity = self.check_github_activity()
        
        if has_activity is None:
            print("⚠️  Could not check GitHub. Check your connection.")
            return
        
        if has_activity:
            self.update_streak(True)
            streak = self.streak_data['current_streak']
            msg = f"✓ Activity detected! Current streak: {streak} days 🔥"
            print(msg)
            self.send_notification("GitHub Streak", msg)
        else:
            streak = self.streak_data['current_streak']
            reminder = self.random_reminder(streak)
            print(f"\n⚠️  NO ACTIVITY TODAY")
            print(f"Current streak: {streak} days")
            print(f"\n{reminder}\n")
            self.send_notification("GitHub Streak Reminder", reminder)
    
    def evening_check(self):
        print(f"\n{'='*50}")
        print(f"Evening Check - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*50}")
        
        today = datetime.now().date().isoformat()
        
        if self.streak_data['commit_history'].get(today):
            streak = self.streak_data['current_streak']
            print(f"✓ Already committed today! Streak safe: {streak} days 🔥")
            return
        
        has_activity = self.check_github_activity()
        
        if has_activity is None:
            return
        
        if has_activity:
            self.update_streak(True)
            streak = self.streak_data['current_streak']
            msg = f"✓ Last minute commit! Streak saved: {streak} days 🔥"
            print(msg)
            self.send_notification("GitHub Streak", msg)
        else:
            streak = self.streak_data['current_streak']
            
            if self.reminder_mode == "strict":
                messages = [
                    f"🔴 FINAL WARNING! Your {streak} day streak dies at midnight!",
                    f"⏰ TIME IS RUNNING OUT! {streak} days on the line!",
                    f"💀 LAST CHANCE! Commit NOW or lose {streak} days!"
                ]
                title = "🚨 URGENT: GitHub Streak Dying!"
            else:
                messages = [
                    f"⏰ Evening reminder: Keep your {streak} day streak alive!",
                    f"🌙 Don't forget! Commit before bed to maintain your streak.",
                    f"💚 Quick reminder: Your {streak} day streak needs attention!"
                ]
                title = "GitHub Streak Reminder"
            
            message = self.random_reminder(streak)
            print(f"\n{message}\n")
            self.send_notification(title, message)
    
    def show_stats(self):
        print("\n" + "="*50)
        print("📊 YOUR GITHUB STREAK STATS")
        print("="*50)
        print(f"Current Streak:    {self.streak_data['current_streak']} days 🔥")
        print(f"Longest Streak:    {self.streak_data['longest_streak']} days 🏆")
        print(f"Total Active Days: {self.streak_data['total_days']} days")
        print(f"Last Commit:       {self.streak_data['last_commit_date'] or 'Never'}")
        print(f"Reminder Mode:     {self.reminder_mode.upper()}")
        print("="*50 + "\n")
    
    def run_scheduler(self):
        print("\n🔥 GitHub Streak Tracker Running 🔥")
        print(f"Mode: {self.reminder_mode.upper()}")
        print("\nScheduled checks:")
        print("  • Morning: 9:00 AM")
        print("  • Afternoon: 2:00 PM") 
        print("  • Evening: 8:00 PM")
        print("\nPress Ctrl+C to stop\n")
        
        schedule.every().day.at("09:00").do(self.morning_check)
        schedule.every().day.at("14:00").do(self.morning_check)
        schedule.every().day.at("20:00").do(self.evening_check)
        
        self.morning_check()
        
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    tracker = GitHubStreakTracker()
    
    if not tracker.load_config():
        tracker.setup()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "stats":
            tracker.show_stats()
        elif cmd == "check":
            tracker.morning_check()
        elif cmd == "setup":
            tracker.setup()
        elif cmd == "mode":
            if len(sys.argv) > 2:
                mode = sys.argv[2]
                if mode in ["normal", "strict"]:
                    tracker.reminder_mode = mode
                    tracker.save_config()
                    print(f"✓ Mode changed to: {mode}")
                else:
                    print("Usage: streak.py mode [normal|strict]")
            else:
                print(f"Current mode: {tracker.reminder_mode}")
        else:
            print("Commands:")
            print("  stats  - Show your streak statistics")
            print("  check  - Check GitHub activity now")
            print("  setup  - Run setup again")
            print("  mode   - Change reminder mode (normal/strict)")
    else:
        try:
            tracker.run_scheduler()
        except KeyboardInterrupt:
            print("\n\n👋 Streak tracker stopped. Don't forget to commit today!")

if __name__ == "__main__":
    main()