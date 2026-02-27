from django.contrib import admin
from .models import QuestionSet, Question, PracticeSession, PracticeResponse


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(QuestionSet)
class QuestionSetAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'created_at']
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text_short', 'question_set', 'difficulty', 'order']
    list_filter = ['difficulty', 'question_set']

    def text_short(self, obj):
        return obj.text[:50] + ('...' if len(obj.text) > 50 else '')
    text_short.short_description = 'Text'


@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'question_set', 'started_at']


@admin.register(PracticeResponse)
class PracticeResponseAdmin(admin.ModelAdmin):
    list_display = ['session', 'question', 'response_short', 'saved_at']
    list_filter = ['session']
    search_fields = ['response_text']

    def response_short(self, obj):
        if not obj.response_text:
            return '(no answer)'
        return obj.response_text
    response_short.short_description = 'Answer'
