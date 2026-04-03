"""Асинхронний скрипт для сортування файлів за розширенням."""

import argparse
import asyncio
import logging
from pathlib import Path

import aiofiles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Обробка аргументів командного рядка."""
    parser = argparse.ArgumentParser(
        description="Асинхронне сортування файлів за розширенням."
    )
    parser.add_argument(
        "source",
        type=str,
        help="Шлях до вихідної папки з файлами для сортування.",
    )
    parser.add_argument(
        "output",
        type=str,
        nargs="?",
        default="dist",
        help="Шлях до цільової папки (за замовчуванням: dist).",
    )
    return parser.parse_args()


async def copy_file(file_path: Path, output_folder: Path) -> None:
    """Копіює файл у підпапку цільової директорії на основі розширення."""
    try:
        extension = file_path.suffix.lstrip(".")

        if not extension:
            extension = "no_extension"

        target_dir = output_folder / extension
        await asyncio.to_thread(target_dir.mkdir, parents=True, exist_ok=True)

        target_file = target_dir / file_path.name

        async with aiofiles.open(file_path, mode="rb") as src:
            content = await src.read()

        async with aiofiles.open(target_file, mode="wb") as dst:
            await dst.write(content)

        logger.info("Скопійовано: %s -> %s", file_path, target_file)
    except PermissionError:
        logger.error("Немає доступу до файлу: %s", file_path)
    except OSError as e:
        logger.error("Помилка при копіюванні файлу %s: %s", file_path, e)


async def read_folder(source_folder: Path, output_folder: Path) -> None:
    """Рекурсивно читає папку та запускає асинхронне копіювання файлів."""
    tasks = []

    try:
        items = await asyncio.to_thread(list, source_folder.iterdir())
    except PermissionError:
        logger.error("Немає доступу до папки: %s", source_folder)
        return
    except OSError as e:
        logger.error("Помилка при читанні папки %s: %s", source_folder, e)
        return

    for item in items:
        if item.is_dir():
            tasks.append(read_folder(item, output_folder))
        elif item.is_file():
            tasks.append(copy_file(item, output_folder))

    if tasks:
        await asyncio.gather(*tasks)


async def main() -> None:
    """Головна асинхронна функція."""
    args = parse_arguments()

    source_folder = Path(args.source)
    output_folder = Path(args.output)

    if not source_folder.exists():
        logger.error("Вихідна папка не існує: %s", args.source)
        return

    if not source_folder.is_dir():
        logger.error("Вказаний шлях не є директорією: %s", args.source)
        return

    output_folder.mkdir(parents=True, exist_ok=True)

    logger.info("Початок сортування файлів з '%s' до '%s'", args.source, args.output)
    await read_folder(source_folder, output_folder)
    logger.info("Сортування завершено.")


if __name__ == "__main__":
    asyncio.run(main())
