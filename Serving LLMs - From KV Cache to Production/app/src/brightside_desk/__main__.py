"""python -m brightside_desk: start the app on the port from .env (BRIGHTSIDE_PORT, default 8980)."""
import uvicorn

from .config import get_settings


def main() -> None:
    uvicorn.run("brightside_desk.api:app", host="127.0.0.1", port=get_settings().port)


if __name__ == "__main__":
    main()
