from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from django.core.exceptions import FieldError
from django.utils import timezone
import json

from .models import QuestionSet, Question, PracticeSession, PracticeResponse
from .forms import PracticeResponseForm, QuestionSetForm, QuestionForm


def practice_index(request):
    """Choose a question set and start a practice session."""
    sets = _unique_question_sets_by_name(QuestionSet.objects.all().order_by('-updated_at'))
    return render(request, 'practice/practice_index.html', {'question_sets': sets})


def _unique_question_sets_by_name(queryset):
    """Return question sets deduplicated by name (case-insensitive). Keeps most recently updated per name."""
    seen = set()
    result = []
    for qs in queryset:
        key = qs.name.strip().lower()
        if key not in seen:
            seen.add(key)
            result.append(qs)
    return result


@login_required
def practice_start(request, set_id):
    """Start a new practice session for the given set and redirect to first question.
    GET param timer=0 to start without timer; timer=1 or omit for timer enabled."""
    qs = get_object_or_404(QuestionSet, pk=set_id)
    questions = list(qs.questions.all())
    if not questions:
        messages.warning(request, 'This set has no questions yet.')
        return redirect('practice:practice_index')
    timer_enabled = request.GET.get('timer', '1') != '0'
    session = PracticeSession.objects.create(
        user=request.user,
        question_set=qs,
        timer_enabled=timer_enabled,
    )
    return redirect('practice:practice_session', session_id=session.pk)


def _build_responses_display(session):
    """Build list of {question, answer_text, self_rating} in question order."""
    responses_by_question = {
        pr.question_id: {'answer_text': pr.response_text or '', 'self_rating': pr.self_rating}
        for pr in session.responses.all()
    }
    return [
        {
            'question': q,
            'answer_text': responses_by_question.get(q.pk, {}).get('answer_text', ''),
            'self_rating': responses_by_question.get(q.pk, {}).get('self_rating'),
        }
        for q in session.questions_in_order()
    ]


@login_required
def practice_session(request, session_id):
    """Show current question or session complete; save response on POST. In review mode (?review=1), always show read-only summary."""
    session = get_object_or_404(PracticeSession, pk=session_id, user=request.user)
    questions = list(session.questions_in_order())
    next_idx = session.next_question_index()

    # Timer controls: pause, resume, end (when timer enabled, not in review, session in progress)
    if not request.GET.get('review') and not session.ended_at and session.timer_enabled:
        action = request.GET.get('action')
        now = timezone.now()
        if action == 'pause':
            session.paused_at = now
            session.save(update_fields=['paused_at'])
            return redirect('practice:practice_session', session_id=session_id)
        if action == 'resume' and session.paused_at:
            session.total_paused_seconds += int((now - session.paused_at).total_seconds())
            session.paused_at = None
            session.save(update_fields=['total_paused_seconds', 'paused_at'])
            return redirect('practice:practice_session', session_id=session_id)
        if action == 'end_timer':
            session.ended_at = now
            session.save(update_fields=['ended_at'])
            return redirect('practice:practice_session', session_id=session_id)

    # Review mode (from History): show read-only summary only, no Save & Next
    if request.GET.get('review'):
        return render(request, 'practice/practice_complete.html', {
            'session': session,
            'responses': _build_responses_display(session),
        })

    # Timed mode: if time is up (and not paused), mark session ended and show complete
    if session.time_limit_minutes and not session.ended_at and not session.paused_at:
        end_time = session.end_time()
        if end_time and timezone.now() >= end_time:
            session.ended_at = end_time
            session.save(update_fields=['ended_at'])
            return redirect('practice:practice_session', session_id=session_id)

    # Session already ended (e.g. time ran out) or all questions answered: show complete
    if session.ended_at or next_idx is None:
        # Time ran out if we have a time limit, ended_at is set, and not all questions were answered
        time_ran_out = (
            bool(session.time_limit_minutes and session.ended_at) and
            session.next_question_index() is not None
        )
        return render(request, 'practice/practice_complete.html', {
            'session': session,
            'responses': _build_responses_display(session),
            'time_ran_out': time_ran_out,
        })

    question = questions[next_idx]
    if request.method == 'POST':
        answer = (request.POST.get('response_text') or '').strip()
        form = PracticeResponseForm(request.POST)
        if not answer and form.is_valid():
            answer = (form.cleaned_data.get('response_text') or '').strip()
        self_rating = request.POST.get('self_rating')
        if self_rating and self_rating.isdigit():
            r = int(self_rating)
            self_rating = r if 1 <= r <= 5 else None
        else:
            self_rating = None
        defaults = {'response_text': answer, 'self_rating': self_rating}
        PracticeResponse.objects.update_or_create(
            session=session,
            question=question,
            defaults=defaults,
        )
        # If that was the last question, mark session ended for duration
        session.refresh_from_db()
        if session.next_question_index() is None and not session.ended_at:
            session.ended_at = timezone.now()
            session.save(update_fields=['ended_at'])
        return redirect('practice:practice_session', session_id=session_id)
    else:
        form = PracticeResponseForm(initial={'response_text': ''})

    # Elapsed timer data only when timer is enabled for this session
    timer_enabled = session.timer_enabled
    ctx = {
        'session': session,
        'question': question,
        'form': form,
        'question_number': next_idx + 1,
        'total_questions': len(questions),
        'session_id': session_id,
        'timer_enabled': timer_enabled,
    }
    if timer_enabled:
        ctx['session_start_timestamp_ms'] = int(session.started_at.timestamp() * 1000)
        ctx['timer_paused'] = bool(session.paused_at)
        ctx['paused_at_timestamp_ms'] = int(session.paused_at.timestamp() * 1000) if session.paused_at else None
        ctx['total_paused_seconds'] = session.total_paused_seconds or 0
    return render(request, 'practice/practice_question.html', ctx)


@login_required
def history(request):
    """List previous practice attempts/sessions for the logged-in user."""
    sessions = PracticeSession.objects.filter(user=request.user).select_related('question_set').order_by('-started_at')
    return render(request, 'practice/history.html', {'sessions': sessions})


@login_required
def dashboard(request):
    """Progress dashboard: attempts by topic (question set), average self-rating, recent sessions."""
    base_responses = PracticeResponse.objects.filter(session__user=request.user)
    has_rating = False
    try:
        topic_stats = (
            base_responses.values('question__question_set__name')
            .annotate(response_count=Count('id'), avg_rating=Avg('self_rating'))
            .order_by('-response_count')
        )
        has_rating = True
    except FieldError:
        topic_stats = (
            base_responses.values('question__question_set__name')
            .annotate(response_count=Count('id'))
            .order_by('-response_count')
        )

    recent_sessions = (
        PracticeSession.objects.filter(user=request.user)
        .select_related('question_set')
        .order_by('-started_at')[:10]
    )
    total_sessions = PracticeSession.objects.filter(user=request.user).count()
    total_responses = base_responses.count()

    topic_stats_list = list(topic_stats)
    topic_stats_json = json.dumps([
        {
            'name': r.get('question__question_set__name') or '—',
            'count': r['response_count'],
            'avg': float(r['avg_rating']) if r.get('avg_rating') is not None else None,
        }
        for r in topic_stats_list
    ])

    return render(
        request,
        'practice/dashboard.html',
        {
            'topic_stats': topic_stats_list,
            'topic_stats_json': topic_stats_json,
            'recent_sessions': recent_sessions,
            'total_sessions': total_sessions,
            'total_responses': total_responses,
            'has_rating': has_rating,
        },
    )


# ---- Question sets CRUD ----

def _can_edit_set(request, qs):
    """Allow edit/delete when set has no owner or user is owner."""
    return qs.owner is None or (request.user.is_authenticated and qs.owner == request.user)


def question_set_list(request):
    """List all question sets (one per unique name)."""
    all_sets = QuestionSet.objects.all().order_by('-updated_at')
    sets = _unique_question_sets_by_name(all_sets)
    editable_ids = {qs.pk for qs in sets if _can_edit_set(request, qs)}
    return render(request, 'practice/question_set_list.html', {'question_sets': sets, 'editable_set_ids': editable_ids})


def question_set_create(request):
    """Create a new question set, or use existing one with same name so questions are appended."""
    if request.method == 'POST':
        form = QuestionSetForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name'].strip()
            # If a set with this name already exists, use it so new questions are appended
            existing = QuestionSet.objects.filter(name__iexact=name).order_by('-updated_at').first()
            if existing:
                if not _can_edit_set(request, existing):
                    messages.error(request, 'A question set with this name already exists and you cannot edit it.')
                    return redirect('practice:question_set_list')
                messages.info(request, f'A question set named "{existing.name}" already exists. Add your questions below to append to it.')
                return redirect('practice:question_list', set_id=existing.pk)
            qs = form.save(commit=False)
            qs.name = name
            qs.owner = request.user if request.user.is_authenticated else None
            qs.save()
            messages.success(request, 'Question set created.')
            return redirect('practice:question_list', set_id=qs.pk)
    else:
        form = QuestionSetForm()
    return render(request, 'practice/question_set_form.html', {'form': form, 'title': 'New question set'})


def question_set_edit(request, pk):
    """Edit a question set."""
    qs = get_object_or_404(QuestionSet, pk=pk)
    if not _can_edit_set(request, qs):
        messages.error(request, 'You cannot edit this question set.')
        return redirect('practice:question_set_list')
    if request.method == 'POST':
        form = QuestionSetForm(request.POST, instance=qs)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question set updated.')
            return redirect('practice:question_set_list')
    else:
        form = QuestionSetForm(instance=qs)
    return render(request, 'practice/question_set_form.html', {'form': form, 'question_set': qs, 'title': 'Edit question set'})


def question_set_delete(request, pk):
    """Delete a question set."""
    qs = get_object_or_404(QuestionSet, pk=pk)
    if not _can_edit_set(request, qs):
        messages.error(request, 'You cannot delete this question set.')
        return redirect('practice:question_set_list')
    if request.method == 'POST':
        qs.delete()
        messages.success(request, 'Question set deleted.')
        return redirect('practice:question_set_list')
    return render(request, 'practice/question_set_confirm_delete.html', {'question_set': qs})


# ---- Questions CRUD ----

def question_list(request, set_id):
    """List questions in a set. Optional filters: difficulty, search (keyword in question text)."""
    question_set = get_object_or_404(QuestionSet, pk=set_id)
    questions = question_set.questions.all()

    difficulty = (request.GET.get('difficulty') or '').strip().lower()
    if difficulty and difficulty in ('easy', 'medium', 'hard'):
        questions = questions.filter(difficulty=difficulty)
    else:
        difficulty = ''

    search_keyword = (request.GET.get('q') or '').strip()
    if search_keyword:
        questions = questions.filter(text__icontains=search_keyword)

    can_edit = _can_edit_set(request, question_set)
    has_active_filters = bool(difficulty or search_keyword)

    return render(request, 'practice/question_list.html', {
        'question_set': question_set,
        'questions': questions,
        'can_edit': can_edit,
        'filter_difficulty': difficulty,
        'filter_q': search_keyword,
        'has_active_filters': has_active_filters,
    })


def question_create(request, set_id):
    """Add a question to a set."""
    question_set = get_object_or_404(QuestionSet, pk=set_id)
    if not _can_edit_set(request, question_set):
        messages.error(request, 'You cannot add questions to this set.')
        return redirect('practice:question_set_list')
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            q = form.save(commit=False)
            q.question_set = question_set
            q.save()
            messages.success(request, 'Question added.')
            return redirect('practice:question_list', set_id=set_id)
    else:
        form = QuestionForm()
    return render(request, 'practice/question_form.html', {'form': form, 'question_set': question_set, 'title': 'Add question'})


def question_edit(request, set_id, pk):
    """Edit a question."""
    question_set = get_object_or_404(QuestionSet, pk=set_id)
    if not _can_edit_set(request, question_set):
        messages.error(request, 'You cannot edit questions in this set.')
        return redirect('practice:question_set_list')
    question = get_object_or_404(Question, pk=pk, question_set=question_set)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated.')
            return redirect('practice:question_list', set_id=set_id)
    else:
        form = QuestionForm(instance=question)
    return render(request, 'practice/question_form.html', {'form': form, 'question_set': question_set, 'question': question, 'title': 'Edit question'})


def question_delete(request, set_id, pk):
    """Delete a question."""
    question_set = get_object_or_404(QuestionSet, pk=set_id)
    if not _can_edit_set(request, question_set):
        messages.error(request, 'You cannot delete questions in this set.')
        return redirect('practice:question_set_list')
    question = get_object_or_404(Question, pk=pk, question_set=question_set)
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted.')
        return redirect('practice:question_list', set_id=set_id)
    return render(request, 'practice/question_confirm_delete.html', {'question_set': question_set, 'question': question})
