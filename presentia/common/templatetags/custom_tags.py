from django import template
from django.db import connection

register = template.Library()

@register.simple_tag
def contar_turmas(nucleo_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM tb_turmas WHERE nucleo_id = %s::uuid", [str(nucleo_id)])
            return cursor.fetchone()[0]
    except Exception:
        return 0