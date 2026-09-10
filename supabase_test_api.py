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
    title="Supabase Student Management API",
    description="CRUD API backed by a Supabase PostgreSQL database.",
    version="1.0.0",
)


class studentCreate(BaseModel):
    name: str
    grade: str
    age: int


class studentUpdate(BaseModel):
    name: str | None = None
    grade: str | None = None
    age: int | None = None


def database_error(error: Any) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(error),
    )


@app.post("/students", status_code=status.HTTP_201_CREATED, tags=["students"])
def create_student(student: studentCreate):
    try:
        response = get_supabase_client().table("students").insert(student.model_dump()).execute()
        return response.data[0]
    except Exception as error:
        raise database_error(error) from error


@app.get("/students", tags=["students"])
def get_students():
    try:
        response = get_supabase_client().table("students").select("*").order("id").execute()
        return response.data
    except Exception as error:
        raise database_error(error) from error


@app.get("/students/{student_id}", tags=["students"])
def get_student(student_id: int):
    try:
        response = (
            get_supabase_client()
            .table("students")
            .select("*")
            .eq("id", student_id)
            .maybe_single()
            .execute()
        )
        if response.data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="student not found")
        return response.data
    except HTTPException:
        raise
    except Exception as error:
        raise database_error(error) from error


@app.patch("/students/{student_id}", tags=["students"])
def update_student(student_id: int, student: studentUpdate):
    values = student.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    try:
        response = (
            get_supabase_client()
            .table("students")
            .update(values)
            .eq("id", student_id)
            .select()
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="student not found")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as error:
        raise database_error(error) from error


@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["students"])
def delete_student(student_id: int):
    try:
        response = (
            get_supabase_client()
            .table("students")
            .delete()
            .eq("id", student_id)
            .select("id")
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="student not found")
    except HTTPException:
        raise
    except Exception as error:
        raise database_error(error) from error