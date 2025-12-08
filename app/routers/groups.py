import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.supabase_client import supabase

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
# Helper: OpenAI client
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
def get_group(group_id: str):
    """Get group details."""
    result = supabase.table("groups").select("*").eq("id", group_id).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Group not found")

    return result.data


@router.get("/{group_id}/members")
def get_group_members(group_id: str):
    """Return user records for all members in a group."""
    group_result = supabase.table("groups").select("members").eq("id", group_id).single().execute()

    if not group_result.data:
        raise HTTPException(status_code=404, detail="Group not found")

    member_ids = group_result.data.get("members") or []

    if not member_ids:
        return {"ok": True, "members": []}

    users_result = supabase.table("users").select("id, name, full_name, username, email").in_("id", member_ids).execute()

    if not users_result.data:
        return {"ok": True, "members": []}

    return {"ok": True, "members": users_result.data}


@router.post("/{group_id}/generate-summary", response_model=TripSummaryResponse)
def generate_trip_summary(group_id: str):
    """Generate a trip summary using OpenAI based on the group's description."""

    group_result = supabase.table("groups").select("id, name, description").eq("id", group_id).single().execute()

    if not group_result.data:
        raise HTTPException(status_code=404, detail="Group not found")

    group = group_result.data
    description = group.get("description")

    if not description or description.strip() == "":
        raise HTTPException(status_code=400, detail="This group has no trip description to summarize.")

    try:
        client = get_openai_client()

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Summarize group trips clearly and concisely."},
                {"role": "user", "content": f"Summarize this trip: {description}"}
            ],
            max_tokens=150,
        )

        summary = response.choices[0].message["content"]

        return TripSummaryResponse(summary=summary)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GenAI error occurred: {str(e)}")
