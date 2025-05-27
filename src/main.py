from server import create_app
from config import get_settings
import asyncio


def main():
    settings = get_settings()
    app = create_app(settings)
    app.run()


if __name__ == "__main__":
    asyncio.run(main())
