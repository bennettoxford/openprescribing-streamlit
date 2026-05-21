import logging

from db import (
    create_materialised_view,
    materialised_views_db_path,
    materialised_views_dir,
)

logger = logging.getLogger(__name__)


def recreate_materialised_views():
    logging.debug("Removing all materialised views")
    if materialised_views_db_path.exists():
        materialised_views_db_path.unlink()

    logging.debug("Creating all materialised views")
    for f in sorted(materialised_views_dir.iterdir()):
        short_name = f.name.removesuffix(".sql")
        logging.debug(f"Creating materialised view {short_name}")
        create_materialised_view(short_name, force=True)

    logging.info("All materialised views (re-)created")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    recreate_materialised_views()
