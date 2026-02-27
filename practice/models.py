from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings
from django.utils import timezone


class QuestionSet(models.Model):
    """A set of practice questions (e.g. "Python Basics", "System Design")."""
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='question_sets',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name


class Question(models.Model):
    """A single question belonging to a set, with difficulty and tags."""
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    question_set = models.ForeignKey(
        QuestionSet,
        on_delete=models.CASCADE,
        related_name='questions',
    )
    text = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    tags = models.CharField(max_length=255, blank=True, help_text='Comma-separated tags')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'pk']

    def __str__(self):
        return self.text[:50] + ('...' if len(self.text) > 50 else '')


class PracticeSession(models.Model):
    """One practice attempt: user + question set + when started. Optional time limit."""
    TIME_LIMIT_CHOICES = [5, 10, 15]  # minutes; None = no limit

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='practice_sessions',
    )
    question_set = models.ForeignKey(
        QuestionSet,
        on_delete=models.CASCADE,
        related_name='practice_sessions',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Optional time limit in minutes (e.g. 5, 10, 15). Null = no limit.',
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the session ended (completed or time ran out).',
    )
    paused_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the timer was paused; None = running.',
    )
    total_paused_seconds = models.PositiveIntegerField(
        default=0,
        help_text='Total seconds the timer has been paused (extends effective end time).',
    )
    timer_enabled = models.BooleanField(
        default=True,
        help_text='Whether to show the session timer (elapsed time, pause, end) on question pages.',
    )

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user} – {self.question_set.name} @ {self.started_at}"

    def questions_in_order(self):
        return self.question_set.questions.all()

    def next_question_index(self):
        """Index (0-based) of the next question to answer, or None if complete."""
        answered_count = self.responses.count()
        total = self.questions_in_order().count()
        if answered_count >= total:
            return None
        return answered_count

    def is_complete(self):
        return self.next_question_index() is None

    def end_time(self):
        """Return the moment the session must end (for timed mode), or None. Includes pause extension."""
        if not self.time_limit_minutes:
            return None
        from datetime import timedelta
        return self.started_at + timedelta(minutes=self.time_limit_minutes) + timedelta(seconds=self.total_paused_seconds or 0)

    def duration_seconds(self):
        """Return active session time in seconds (excludes paused time). Uses ended_at or now as end."""
        end = self.ended_at or timezone.now()
        wall_seconds = int((end - self.started_at).total_seconds())
        return max(0, wall_seconds - (self.total_paused_seconds or 0))

    def duration_display(self):
        """Return human-readable duration, e.g. '4m 32s' or '1m 0s'."""
        secs = self.duration_seconds()
        m, s = divmod(secs, 60)
        if m > 0:
            return f'{m}m {s}s'
        return f'{s}s'


class PracticeResponse(models.Model):
    """User's text response to one question within a session."""
    session = models.ForeignKey(
        PracticeSession,
        on_delete=models.CASCADE,
        related_name='responses',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='practice_responses',
    )
    response_text = models.TextField(blank=True)
    self_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Self-rating 1–5',
    )
    saved_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['pk']
        unique_together = [['session', 'question']]

    def __str__(self):
        return f"Response for Q{self.question_id} in session {self.session_id}"
