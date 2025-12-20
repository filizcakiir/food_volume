#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix daily_logs total_calories by recalculating from predictions
"""
from app import create_app
from models import db
from models.history import PredictionHistory, DailyLog
from datetime import datetime

def fix_daily_logs():
    """Recalculate all daily_logs from scratch"""
    app = create_app('development')

    with app.app_context():
        # Get all daily logs
        logs = DailyLog.query.all()

        if not logs:
            print("No daily logs found.")
            return

        print(f"Found {len(logs)} daily logs to fix...")

        for log in logs:
            # Get all predictions for this user on this date
            start_of_day = datetime.combine(log.date, datetime.min.time())
            end_of_day = datetime.combine(log.date, datetime.max.time())

            predictions = PredictionHistory.query.filter(
                PredictionHistory.user_id == log.user_id,
                PredictionHistory.created_at >= start_of_day,
                PredictionHistory.created_at <= end_of_day,
                PredictionHistory.meal_type != None
            ).all()

            # Reset all values
            log.total_calories = 0
            log.total_meals = 0
            log.breakfast_calories = 0
            log.lunch_calories = 0
            log.dinner_calories = 0
            log.snack_calories = 0

            # Recalculate from predictions
            for pred in predictions:
                log.total_calories += pred.calories
                log.total_meals += 1

                if pred.meal_type == 'breakfast':
                    log.breakfast_calories += pred.calories
                elif pred.meal_type == 'lunch':
                    log.lunch_calories += pred.calories
                elif pred.meal_type == 'dinner':
                    log.dinner_calories += pred.calories
                elif pred.meal_type == 'snack':
                    log.snack_calories += pred.calories

            print(f"Fixed log {log.id}: date={log.date}, total_calories={log.total_calories}, meals={log.total_meals}")

        # Commit all changes
        db.session.commit()
        print(f"\nSuccessfully fixed {len(logs)} daily logs!")

if __name__ == '__main__':
    fix_daily_logs()
