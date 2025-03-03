"""https://github.com/pydantic/pydantic/issues/6768"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Callable
from uuid import UUID

import pytest
from annotated_types import Gt

from pydantic import AnyUrl, BaseModel, EmailStr, TypeAdapter
from pydantic.functional_validators import AfterValidator
from pydantic.types import StringConstraints

try:
    import email_validator
except ImportError:
    email_validator = None


@pytest.mark.skipif(not email_validator, reason='email_validator not installed')
def test_fastapi_startup_perf(benchmark: Callable[[Callable[[], Any]], None]):
    def run() -> None:
        class User(BaseModel):
            id: int
            username: str
            email: EmailStr
            full_name: str | None = None

        class Address(BaseModel):
            street: str
            city: str
            state: Annotated[str, AfterValidator(lambda x: x.upper())]
            postal_code: Annotated[str, StringConstraints(min_length=5, max_length=5, pattern=r'[A-Z0-9]+')]

        class Product(BaseModel):
            id: int
            name: str
            price: Annotated[float, Gt(0)]
            description: str | None = None

        class BlogPost(BaseModel):
            title: Annotated[str, StringConstraints(pattern=r'[A-Za-z0-9]+')]
            content: str
            author: User
            published: bool = False

        class Website(BaseModel):
            name: str
            url: AnyUrl
            description: str | None = None

        class Order(BaseModel):
            order_id: str
            customer: User
            shipping_address: Address
            products: list[Product]

        class Comment(BaseModel):
            text: str
            author: User
            post: BlogPost
            created_at: datetime

        class Event(BaseModel):
            event_id: UUID
            name: str
            date: datetime
            location: str

        class Category(BaseModel):
            name: str
            description: str | None = None

        ReviewGroup = list[dict[tuple[User, Product], Comment]]

        data_models = [
            User,
            Address,
            Product,
            BlogPost,
            Website,
            Order,
            Comment,
            Event,
            Category,
            ReviewGroup,
        ]

        for _ in range(5):  # FastAPI creates a new TypeAdapter for each endpoint
            for model in data_models:
                TypeAdapter(model)

    benchmark(run)


if __name__ == '__main__':
    # run with `uv run tests/benchmarks/test_fastapi_startup_simple.py`
    import cProfile
    import sys
    import time

    print(f'Python version: {sys.version}')
    if sys.argv[-1] == 'cProfile':
        cProfile.run(
            'test_fastapi_startup_perf(lambda f: f())',
            sort='tottime',
            filename=Path(__file__).name.strip('.py') + '.cprof',
        )
    else:
        start = time.perf_counter()
        test_fastapi_startup_perf(lambda f: f())
        end = time.perf_counter()
        print(f'Time taken: {end - start:.6f}s')
