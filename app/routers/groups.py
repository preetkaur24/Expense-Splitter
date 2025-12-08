import os
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.dependencies import get_supabase
from pydantic import BaseModel

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

router = APIRouter(prefix="/groups", tags=["Groups"])


# ---------------------------
# Models
# ---------------------------

class TripSummaryResponse(BaseModel):
    summary: str


# ---------------------------
# Helper: Lazy-initialize OpenAI
# ---------------------------

def get_openai_client():
    if OpenAI is None:
        raise HTTPException(
            status_code=500,
            detail="OpenAI client library is not installed on this server."
        )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Missing OPENAI_API_KEY on server."
        )

    return OpenAI(api_key=api_key)


# ---------------------------
# Routes
# ---------------------------


@router.get("/{group_id}")
def get_group(group_id: int, supabase: Client = Depends(get_supabase)):
    """Get group details."""
    result = supabase.table("groups").select("*").eq("id", group_id).single().execute()

    if result.data is None:
        raise HTTPException(status_code=404, detail="Group not found")

    return result.data


@router.post("/{group_id}/generate-summary", response_model=TripSummaryResponse)
def generate_trip_summary(group_id: int, supabase: Client = Depends(get_supabase)):
    """
    Generates a GenAI trip summary based on the group's description.
    """
    # --- 1. Fetch group ---
    group_result = (
        supabase.table("groups")
        .select("id, name, description")
        .eq("id", group_id)
        .single()
        .execute()
    )

    if group_result.data is None:
        raise HTTPException(status_code=404, detail="Group not found")

    group = group_result.data
    description = group.get("description")

    # --- 2. Handle missing description ---
    if not description or description.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="This group has no trip description to summarize."
        )

    # --- 3. Call GenAI ---
    try:
        client = get_openai_client()

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You summarize group trips clearly and concisely."},
                {"role": "user", "content": f"Summarize this trip: {description}"}
            ],
            max_tokens=150,
        )

        summary = response.choices[0].message["content"]

        return TripSummaryResponse(summary=summary)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"GenAI error occurred: {str(e)}"
        )
