from datetime import date, timedelta

from business_logic import (
    calculate_streak,
    validate_habit_title,
    calculate_weekly_progress
)


def test_calculate_streak_returns_three_for_three_consecutive_days():
    today = date.today()
    completed_dates = [
        today.isoformat(),
        (today - timedelta(days=1)).isoformat(),
        (today - timedelta(days=2)).isoformat()
    ]

    result = calculate_streak(completed_dates)

    assert result == 3


def test_calculate_streak_returns_zero_when_no_recent_completion():
    today = date.today()
    completed_dates = [
        (today - timedelta(days=3)).isoformat(),
        (today - timedelta(days=4)).isoformat()
    ]

    result = calculate_streak(completed_dates)

    assert result == 0


def test_calculate_streak_counts_from_yesterday_if_today_not_completed():
    today = date.today()
    completed_dates = [
        (today - timedelta(days=1)).isoformat(),
        (today - timedelta(days=2)).isoformat(),
        (today - timedelta(days=3)).isoformat()
    ]

    result = calculate_streak(completed_dates)

    assert result == 3


def test_validate_habit_title_accepts_valid_title():
    result = validate_habit_title("Study Python")

    assert result is True


def test_validate_habit_title_rejects_empty_title():
    result = validate_habit_title("   ")

    assert result is False


def test_validate_habit_title_rejects_none():
    result = validate_habit_title(None)

    assert result is False


def test_calculate_weekly_progress_returns_correct_percentage():
    result = calculate_weekly_progress(7, 2)

    assert result == 50


def test_calculate_weekly_progress_returns_zero_when_no_habits():
    result = calculate_weekly_progress(5, 0)

    assert result == 0


def test_calculate_weekly_progress_returns_full_percentage():
    result = calculate_weekly_progress(14, 2)

    assert result == 100


def test_calculate_weekly_progress_returns_zero_when_no_completions():
    result = calculate_weekly_progress(0, 3)

    assert result == 0