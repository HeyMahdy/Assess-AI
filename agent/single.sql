 SELECT id, name, entity_type, description, difficulty_level, week_or_unit,
               1 - (embedding <=> %s::vector) as similarity
        FROM public.syllabus_entities
        WHERE syllabus_id = %s AND embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s;