# FILE: app/routers/groups.py
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from postgrest.exceptions import APIError

from ..core.supabase_client import supabase
from .auth import get_current_user

# NEW: OpenAI client import
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

router = APIRouter(prefix="/api/groups", tags=["groups"])


class CreateGroup(BaseModel):
    """Payload for creating a group from the add group form."""
    name: str
    description: Optional[str] = None
    member_ids: List[str] = []


@router.post("/", summary="Create a new group")
def create_group(payload: CreateGroup, user=Depends(get_current_user)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Group name cannot be empty")

    friend_uuids: List[str] = []
    for row_id in payload.member_ids:
        try:
            res = (
                supabase.table("friend_links")
                .select("friend_id")
                .eq("id", row_id)
                .single()
                .execute()
            )
        except APIError:
            raise HTTPException(
                status_code=400, detail=f"Friend id {row_id} not found"
            )

        data = res.data or {}
        friend_id = data.get("friend_id")
        if not friend_id:
            raise HTTPException(
                status_code=400, detail=f"Friend id {row_id} not found"
            )
        friend_uuids.append(friend_id)

    all_members = [user["id"], *friend_uuids]
    members_unique = list({m for m in all_members if m})

    insert_data = {
        "name": name,
        "description": payload.description,
        "members": members_unique,
    }

    try:
        res = supabase.table("groups").insert(insert_data).execute()
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e))

    data = res.data
    if isinstance(data, list):
        if not data:
            raise HTTPException(status_code=500, detail="Group insert returned no data")
        group_row = data[0]
    else:
        group_row = data

    return {"ok": True, "group": group_row}


@router.get("/", summary="List groups for current user")
def get_groups_for_current_user(user=Depends(get_current_user)):
    try:
        res = (
            supabase.table("groups")
            .select("*")
            .contains("members", [user["id"]])
            .order("created_at", desc=True)
            .execute()
        )
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return res.data or []


@router.get("/user/{user_id}", summary="Get groups for a given user id")
def get_user_groups(user_id: str):
    try:
        res = (
            supabase.table("groups")
            .select("*")
            .contains("members", [user_id])
            .order("created_at", desc=True)
            .execute()
        )
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"ok": True, "groups": res.data or []}


@router.get("/{group_id}", summary="Get group details")
def get_group(group_id: str):
    try:
        res = (
            supabase.table("groups")
            .select("*")
            .eq("id", group_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Group not found")

    if not res.data:
        raise HTTPException(status_code=404, detail="Group not found")

    return res.data


@router.get("/{group_id}/members", summary="Get members of a group")
def get_group_members(group_id: str):
    try:
        group_res = (
            supabase.table("groups")
            .select("members")
            .eq("id", group_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Group not found")

    group_data = group_res.data or {}
    member_ids = group_data.get("members") or []
    if not member_ids:
        return {"ok": True, "members": []}

    try:
        res = (
            supabase.table("users")
            .select("id, name, full_name, username, email")
            .in_("id", member_ids)
            .execute()
        )
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"ok": True, "members": res.data or []}


# =========================================================
# NEW ROUTE: Generate Trip Summary
# =========================================================

@router.post("/{group_id}/generate_summary", summary="Generate AI trip summary")
def generate_trip_summary(group_id: str):
    """Generate a concise trip summary using the group's description."""

    # Load group description
    try:
        res = (
            supabase.table("groups")
            .select("name, description")
            .eq("id", group_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Group not found")

    group = res.data or {}
    description = (group.get("description") or "").strip()

    if not description:
        raise HTTPException(
            status_code=400,
            detail="This group has no description to summarize."
        )

    # Construct AI prompt
    prompt = (
        "Write a concise and friendly trip summary (3–5 sentences) based on the "
        "following description:\n\n"
        f"{description}"
    )

    # Call OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        summary = response.choices[0].message.content.strip()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="AI service error: unable to generate summary."
        )

    return {"summary": summary}
