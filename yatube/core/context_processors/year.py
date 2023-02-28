from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом."""
    year_now = timezone.now()
    return {
        'year': year_now.year,
    }
