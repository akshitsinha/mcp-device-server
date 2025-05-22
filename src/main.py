from server import create_app
from config import get_settings


def main():
    settings = get_settings()
    app = create_app(settings)
    app.run()


if __name__ == "__main__":
    main()
