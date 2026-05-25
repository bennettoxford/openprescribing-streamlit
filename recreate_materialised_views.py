import logging
from pathlib import Path

from db import (
    create_materialised_view,
    materialised_views_db_path,
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
APPS_DIR = BASE_DIR / "apps"


def recreate_materialised_views():
    logging.debug("Removing all materialised views")
    if materialised_views_db_path.exists():
        materialised_views_db_path.unlink()

    logging.debug("Creating all materialised views")
    for app_dir in sorted(APPS_DIR.iterdir()):
        if not app_dir.is_dir():
            continue

        app_file = app_dir / "app.py"
        materialised_views_dir = app_dir / "materialised_views"

        if not app_file.exists() or not materialised_views_dir.is_dir():
            continue

        for f in sorted(materialised_views_dir.iterdir()):
            short_name = f.name.removesuffix(".sql")
            logging.debug(f"Creating materialised view {short_name}")
            create_materialised_view(
                short_name,
                app_file,
                app_dir.name,
                force=True,
            )

    logging.info("All materialised views (re-)created")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    recreate_materialised_views()