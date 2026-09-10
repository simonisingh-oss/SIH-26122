from backend.app.database import get_connection, create_tables


create_tables()

connection = get_connection()
cursor = connection.cursor()

cursor.execute("""
    SELECT
        schedule_activity_id,
        activity_description,
        discipline,
        asset_id,
        planned_start,
        planned_end
    FROM schedule_activities
""")

activities = cursor.fetchall()

print("\nSchedule Activities in Database:\n")

for activity in activities:
    print(activity)

connection.close()