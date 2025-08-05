from flask import Blueprint, render_template, request, redirect, url_for
from app.models.habit_tracker import HabitTracker

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    """Home page route"""
    tracker = HabitTracker()
    
    return render_template('index.html',
                         started_date=tracker.get_started_date(),
                         frequency=tracker.get_frequency(),
                         counter=tracker.get_counter(),
                         habit_done=tracker.is_done_today(),
                         not_done=tracker.is_not_done_today(),
                         why_text=tracker.get_why_today(),
                         success_percentage=tracker.get_success_percentage(),
                         completed_dates=tracker.get_completed_dates(),
                         not_done_dates=tracker.get_not_done_dates(),
                         why_entries=tracker.get_why_entries())


@main_bp.route('/toggle-habit', methods=['POST'])
def toggle_habit():
    """Toggle habit completion for today"""
    tracker = HabitTracker()
    tracker.toggle_today()
    
    return redirect(url_for('main.home'))