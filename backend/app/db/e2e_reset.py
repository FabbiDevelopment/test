"""Reset only the allowlisted Playwright users and their Todos."""

import asyncio
import os

from sqlalchemy import delete, select

from app.db.session import async_session_maker, engine
from app.models.todo import Todo
from app.models.user import User

RESET_CONFIRMATION_ENV = "E2E_ALLOW_RESET"
E2E_ACCOUNT_ROLES = ("journey1", "journey2-a", "journey2-b", "tier4", "pagination")
E2E_RETRY_INDEXES = range(3)
E2E_EMAILS = tuple(
    f"e2e-{role}-r{retry_index}@example.com"
    for role in E2E_ACCOUNT_ROLES
    for retry_index in E2E_RETRY_INDEXES
)


async def reset_e2e_data() -> None:
    if os.getenv(RESET_CONFIRMATION_ENV) != "1":
        raise RuntimeError(
            f"Refusing to reset E2E data without {RESET_CONFIRMATION_ENV}=1"
        )

    async with async_session_maker() as session:
        async with session.begin():
            user_ids_result = await session.execute(
                select(User.id).where(User.email.in_(E2E_EMAILS))
            )
            user_ids = list(user_ids_result.scalars().all())

            deleted_todos = 0
            if user_ids:
                todo_result = await session.execute(
                    delete(Todo).where(Todo.user_id.in_(user_ids))
                )
                deleted_todos = todo_result.rowcount or 0

            user_result = await session.execute(
                delete(User).where(User.email.in_(E2E_EMAILS))
            )
            deleted_users = user_result.rowcount or 0

    print(
        "Reset deterministic Playwright data: "
        f"{deleted_users} users, {deleted_todos} todos"
    )


async def main() -> None:
    try:
        await reset_e2e_data()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
