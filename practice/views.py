from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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
    """Start a new practice session for the given set and redirect to first question."""
    qs = get_object_or_404(QuestionSet, pk=set_id)
    questions = list(qs.questions.all())
    if not questions:
        messages.warning(request, 'This set has no questions yet.')
        return redirect('practice:practice_index')
    session = PracticeSession.objects.create(user=request.user, question_set=qs)
    return redirect('practice:practice_session', session_id=session.pk)


@login_required
def practice_session(request, session_id):
    """Show current question or session complete; save response on POST. In review mode (?review=1), always show read-only summary."""
    session = get_object_or_404(PracticeSession, pk=session_id, user=request.user)
    questions = list(session.questions_in_order())
    next_idx = session.next_question_index()

    # Review mode (from History): show read-only summary only, no Save & Next
    if request.GET.get('review'):
        responses_by_question = {
            pr.question_id: (pr.response_text or '')
            for pr in session.responses.all()
        }
        responses_display = []
        for question in session.questions_in_order():
            responses_display.append({
                'question': question,
                'answer_text': responses_by_question.get(question.pk, ''),
            })
        return render(request, 'practice/practice_complete.html', {
            'session': session,
            'responses': responses_display,
        })

    if next_idx is None:
        # Build (question, answer_text) list in question order; load all responses in one query
        responses_by_question = {
            pr.question_id: (pr.response_text or '')
            for pr in session.responses.all()
        }
        responses_display = []
        for question in session.questions_in_order():
            responses_display.append({
                'question': question,
                'answer_text': responses_by_question.get(question.pk, ''),
            })
        return render(request, 'practice/practice_complete.html', {
            'session': session,
            'responses': responses_display,
        })

    question = questions[next_idx]
    if request.method == 'POST':
        answer = (request.POST.get('response_text') or '').strip()
        form = PracticeResponseForm(request.POST)
        if not answer and form.is_valid():
            answer = (form.cleaned_data.get('response_text') or '').strip()
        PracticeResponse.objects.update_or_create(
            session=session,
            question=question,
            defaults={'response_text': answer},
        )
        return redirect('practice:practice_session', session_id=session_id)
    else:
        form = PracticeResponseForm(initial={'response_text': ''})

    return render(request, 'practice/practice_question.html', {
        'session': session,
        'question': question,
        'form': form,
        'question_number': next_idx + 1,
        'total_questions': len(questions),
    })


@login_required
def history(request):
    """List previous practice attempts/sessions for the logged-in user."""
    sessions = PracticeSession.objects.filter(user=request.user).select_related('question_set').order_by('-started_at')
    return render(request, 'practice/history.html', {'sessions': sessions})


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
    """List questions in a set."""
    question_set = get_object_or_404(QuestionSet, pk=set_id)
    questions = question_set.questions.all()
    can_edit = _can_edit_set(request, question_set)
    return render(request, 'practice/question_list.html', {'question_set': question_set, 'questions': questions, 'can_edit': can_edit})


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
