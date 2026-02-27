from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings


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
    """One practice attempt: user + question set + when started."""
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
