from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from presentation.dependencies import get_current_user_id
from local_backend.database.code.command.database_command import (
    create_event, list_events_by_user, get_event, update_event, delete_event,
)

router = APIRouter(prefix="/events", tags=["events"])


class EventCreate(BaseModel):
    event_title: str
    event_type: str = "manual"
    event_source: str = "manual"
    event_start_time: Optional[str] = None
    event_end_time: Optional[str] = None
    event_location: Optional[str] = None
    event_description: Optional[str] = None
    event_link_url: Optional[str] = None
    event_show_in_todo: int = 1
    event_priority: int = 2
    event_color_tag: str = "#007aff"
    event_meta_json: Optional[str] = None


class EventUpdate(BaseModel):
    event_title: Optional[str] = None
    event_type: Optional[str] = None
    event_start_time: Optional[str] = None
    event_end_time: Optional[str] = None
    event_location: Optional[str] = None
    event_description: Optional[str] = None
    event_link_url: Optional[str] = None
    event_is_completed: Optional[int] = None
    event_show_in_todo: Optional[int] = None
    event_priority: Optional[int] = None
    event_color_tag: Optional[str] = None
    event_meta_json: Optional[str] = None


def _row_to_dict(row: dict) -> dict:
    return {k: row[k] for k in row.keys() if not k.startswith("_")}


@router.get("/")
async def list_events(
    user_id: str = Depends(get_current_user_id),
    type: Optional[str] = Query(None, alias="type"),
    source: Optional[str] = Query(None),
    show_in_todo: Optional[int] = Query(None),
    completed: Optional[int] = Query(None),
):
    rows = list_events_by_user(
        user_id=user_id, event_type=type, event_source=source,
        show_in_todo=show_in_todo, completed=completed,
    )
    return {"events": [dict(r) for r in rows], "total": len(rows)}


@router.get("/{event_id}")
async def get_single_event(event_id: int, user_id: str = Depends(get_current_user_id)):
    row = get_event(event_id)
    if not row or row.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Event not found")
    return dict(row)


@router.post("/")
async def create_new_event(body: EventCreate, user_id: str = Depends(get_current_user_id)):
    eid = create_event(
        user_id=user_id, event_title=body.event_title,
        event_type=body.event_type, event_source=body.event_source,
        event_start_time=body.event_start_time, event_end_time=body.event_end_time,
        event_location=body.event_location, event_description=body.event_description,
        event_link_url=body.event_link_url,
        event_show_in_todo=body.event_show_in_todo,
        event_priority=body.event_priority, event_color_tag=body.event_color_tag,
        event_meta_json=body.event_meta_json,
    )
    return {"event_id": eid, "message": "Event created"}


@router.put("/{event_id}")
async def update_existing_event(
    event_id: int, body: EventUpdate, user_id: str = Depends(get_current_user_id)
):
    row = get_event(event_id)
    if not row or row.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Event not found")
    update_event(
        event_id=event_id,
        event_title=body.event_title, event_type=body.event_type,
        event_start_time=body.event_start_time, event_end_time=body.event_end_time,
        event_location=body.event_location, event_description=body.event_description,
        event_link_url=body.event_link_url,
        event_is_completed=body.event_is_completed,
        event_show_in_todo=body.event_show_in_todo,
        event_priority=body.event_priority, event_color_tag=body.event_color_tag,
        event_meta_json=body.event_meta_json,
    )
    return {"message": "Event updated"}


@router.delete("/{event_id}")
async def delete_existing_event(event_id: int, user_id: str = Depends(get_current_user_id)):
    row = get_event(event_id)
    if not row or row.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Event not found")
    delete_event(event_id)
    return {"message": "Event deleted"}
