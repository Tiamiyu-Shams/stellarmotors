import os

# Render sets DATABASE_URL automatically.
ON_RENDER = "RENDER" in os.environ or "DATABASE_URL" in os.environ

if ON_RENDER:
    from db_render import (
        init_db,
        seed_data,
        get_db_connection,
        query,
        modify,
    )
else:
    from db_local import (
        init_db,
        seed_data,
        get_db_connection,
        query,
        modify,
    )
