from datetime import date, timedelta


def calculate_streak(completed_dates):
    streak = 0
    today = date.today()

    completed_dates_set = set(completed_dates)

    current_day = today

    if current_day.isoformat() not in completed_dates_set:
        current_day = today - timedelta(days=1)

    while current_day.isoformat() in completed_dates_set:
        streak += 1
        current_day -= timedelta(days=1)

    return streak


def validate_habit_title(title):
    if title is None:
        return False

    if title.strip() == "":
        return False

    return True


def calculate_weekly_progress(weekly_completed, habit_count):
    if habit_count <= 0:
        return 0

    weekly_goal = habit_count * 7
    return round((weekly_completed / weekly_goal) * 100)