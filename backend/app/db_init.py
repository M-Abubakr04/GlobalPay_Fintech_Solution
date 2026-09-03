import app.models  # noqa: F401
from app.core.database import Base, engine


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database schema is ready.")


if __name__ == "__main__":
    main()
