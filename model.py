from datetime import date
from typing import Dict, Any
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column


engine = create_engine("sqlite:///database.db", echo=True)
Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id: Mapped[str] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(64), unique=True)
    password: Mapped[str] = mapped_column(String(128))
    exams_starts: Mapped[date] = mapped_column(Date)

    def __repr__(self):
        return f'User({self.id}, "{self.email}")'


class Todo(Base):
    __tablename__ = "todo"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"))
    task: Mapped[str] = mapped_column(String(5000))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    date: Mapped[date] = mapped_column(Date)

    def __repr__(self):
        return f"Todo({self.id})"


class Exam(Base):
    __tablename__ = "exam"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"))
    exam: Mapped[str] = mapped_column(String(500))
    table: Mapped[Dict[str, Any]] = mapped_column(JSON)

    def __repr__(self):
        return f"Exam({self.id})"


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
