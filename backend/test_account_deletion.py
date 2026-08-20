from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from backend.app import auth
from backend.app.models import Base, Media, Profile, User
from backend.app.storage import MediaStorage


class AccountDeletionTests(TestCase):
    def test_deleting_account_removes_owned_media_record_and_file(self) -> None:
        with TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'accounts.db'}")

            @event.listens_for(engine, "connect")
            def enable_foreign_keys(connection, _record):
                connection.execute("PRAGMA foreign_keys=ON")

            Base.metadata.create_all(engine)
            storage = MediaStorage(Path(directory) / "media")
            media_path = storage.local_root / "avatar.jpg"
            media_path.write_bytes(b"avatar")

            with Session(engine) as session:
                user = User(email="delete@example.com", password_hash="hash")
                user.profile = Profile(username="delete-user", display_name="Delete User")
                user.media.append(Media(url="/media/avatar.jpg", content_type="image/jpeg"))
                session.add(user)
                session.commit()
                user_id = user.id

            @contextmanager
            def session_context():
                with Session(engine) as session:
                    yield session

            with patch.object(auth, "get_session", session_context), patch.object(
                auth, "media_storage", storage
            ):
                self.assertTrue(auth.delete_user_account(user_id))

            self.assertFalse(media_path.exists())
            with Session(engine) as session:
                self.assertIsNone(session.get(User, user_id))
                self.assertEqual(session.query(Media).count(), 0)
            engine.dispose()


if __name__ == "__main__":
    import unittest

    unittest.main()
