import os
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
from supabase import Client, create_client
from dotenv import load_dotenv


load_dotenv()


def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(url, key)


app = FastAPI(
    title="Supabase User API",
    description="CRUD API backed by a Supabase PostgreSQL database.",
    version="1.0.0",
)


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: int


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    age: int | None = None


def database_error(error: Any) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(error),
    )


@app.post("/users", status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: UserCreate):
    try:
        response = get_supabase_client().table("users").insert(user.model_dump()).execute()
        return response.data[0]
    except Exception as error:
        raise database_error(error) from error


@app.post("/users/bulk", status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_users(users: list[UserCreate]):
    try:
        values = [user.model_dump() for user in users]
        response = get_supabase_client().table("users").insert(values).execute()
        return response.data
    except Exception as error:
        raise database_error(error) from error


@app.get("/users", tags=["Users"])
def get_users():
    try:
        response = get_supabase_client().table("users").select("*").order("id").execute()
        return response.data
    except Exception as error:
        raise database_error(error) from error


@app.get("/users/{user_id}", tags=["Users"])
def get_user(user_id: int):
    try:
        response = (
            get_supabase_client()
            .table("users")
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        if response.data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return response.data
    except HTTPException:
        raise
    except Exception as error:
        raise database_error(error) from error


@app.patch("/users/{user_id}", tags=["Users"])
def update_user(user_id: int, user: UserUpdate):
    values = user.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    try:
        response = (
            get_supabase_client()
            .table("users")
            .update(values)
            .eq("id", user_id)
            .select()
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as error:
        raise database_error(error) from error


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
def delete_user(user_id: int):
    try:
        response = (
            get_supabase_client()
            .table("users")
            .delete()
            .eq("id", user_id)
            .select("id")
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except HTTPException:
        raise
    except Exception as error:
        raise database_error(error) from error