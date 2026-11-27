"""Shared FastAPI dependencies."""

# Type for a generator function that yields values asynchronously
from collections.abc import AsyncIterator

# Annotated: attach extra info (here, a Depends) to a type
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


# FastAPI calls this for each request that needs a DB session
async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    # The session factory was created at startup (see main.py) and stored on app.state
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    # "async with" guarantees the session closes after the request, even on errors
    async with session_factory() as session:
        # yield hands the session to the endpoint; code after yield runs once it's done
        yield session


# Shorthand: endpoints write `session: DbSession` instead of repeating Depends(...)
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
