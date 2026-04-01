from django.db import connection

def reset_id_sequence(table_name: str, pk: str = "id"):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT setval(
                pg_get_serial_sequence('{table_name}', '{pk}'),
                COALESCE((SELECT MAX({pk}) FROM {table_name}), 1),
                (SELECT CASE WHEN COUNT(*)=0 THEN false ELSE true END FROM {table_name})
            )
            """
        )