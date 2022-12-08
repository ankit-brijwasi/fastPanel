# PENDING IS HANDLING CORRECT MESSAGES ON THE CLIENT SIDE

import json

from bson import ObjectId
from fastapi import APIRouter, Request, WebSocket
from fastapi.exceptions import HTTPException
from fastapi_pagination import paginate, add_pagination
from pymongo import ReturnDocument, DESCENDING
import motor.motor_asyncio as motor
import requests

from fastpanel.core.schemas import CustomPage
from fastpanel.core.serializers import FastPanelJSONEncoder
from fastpanel.utils import timezone
from . import models, schemas

router = APIRouter()


@router.post("/users/create", response_model=models.User)
async def create_user(req: Request, user: schemas.UserCreate):
    user_obj = models.User(**user.dict())
    return await user_obj.save(req.app.db)


@router.get("/events/list", response_model=CustomPage)
async def list_event(req: Request):
    collection: motor.core.Collection = req.app.db[models.Event.get_collection_name()]
    cursor: motor.AsyncIOMotorCursor = collection.find().sort([
        ('_id', DESCENDING)
    ])

    entries = [
        await models.Event(**entry).transform_data([
            {
                "field_name": "question_assigned",
                "model": models.Question
            },
            {
                "field_name": "admin_user",
                "model": models.User
            }
        ]) \
        for entry in await cursor.to_list(int(req._query_params.get("size", "50")))
    ]

    return paginate(entries)


@router.get("/events/{id}/retrieve")
async def retrieve_event(id: str, req: Request):
    collection: motor.core.Collection = req.app.db[models.Event.get_collection_name()]

    db_obj = await collection.find_one({"_id": ObjectId(id)})
    if db_obj is None:
        raise HTTPException(404, "Object not found")

    del db_obj["id"]
    return await models.Event(**db_obj).transform_data(
        [
            {
                "field_name": "question_assigned",
                "model": models.Question
            },
            {
                "field_name": "admin_user",
                "model": models.User
            }
        ]
    )


@router.post("/events/create")
async def create_event(req: Request, payload: schemas.EventCreate):
    obj = await models.Event(**payload.dict(), created_on=timezone.now()).save(req.app.db)
    return await models.Event(**obj).transform_data([
        {
            "field_name": "admin_user",
            "model": models.User
        }
    ])


@router.post("/participants/submit-solution")
async def submit_solution(payload: schemas.SubmitSolution, req: Request):
    from dateutil import parser

    collection: motor.core.Collection = req.app.db[models.Participant.get_collection_name()]
    participant = await collection.find_one({"_id": ObjectId(payload.participant_id)})

    if participant.get("solution"):
        raise HTTPException(403, "already submitted your answer")

    evt_coll: motor.core.Collection = req.app.db[models.Event.get_collection_name()]
    evt = await evt_coll.find_one({"_id": participant.get("event")})

    response = requests.post(
        "https://api.jdoodle.com/v1/execute",
        json={
            "clientId": "7fd706b00ad892896ebe3f4e230482b2",
            "clientSecret": "ff94197549b0f12da34a5d521c66ea2bec1dbf90e33c21fa45d21a87202fa587",
            "script": payload.proposed_answer.script,
            "language": evt.get("language"),
            "versionIndex": "0"
        },
        headers={
            'Content-Type': 'application/json'
        }
    )
    response = response.json()

    participant = await collection.find_one_and_update(
        {"_id": participant.get("_id")},
        {
            "$set": {
                "solution": {
                    "code": payload.proposed_answer.script,
                    "output": response["output"],
                    "output_time": response["cpuTime"]
                },
                "time_taken": str(parser.parse(payload.proposed_answer.ended_on) - parser.parse(payload.proposed_answer.started_on))
            }
        },
        return_document=ReturnDocument.AFTER
    )

    return await models.Participant(**participant).transform_data([
        {
            "field_name": "user",
            "model": models.User
        },
        {
            "field_name": "event",
            "model": models.Event
        }
    ])


@router.put("/events/{id}/join")
async def join_event(id: str, user_id: str, req: Request):
    participant_coll: motor.core.Collection = req.app.db[models.Participant.get_collection_name()]
    evt_coll: motor.core.Collection = req.app.db[models.Event.get_collection_name()]
    usr_coll: motor.core.Collection = req.app.db[models.User.get_collection_name()]

    event = await evt_coll.find_one({ "_id": ObjectId(id) })
    user = await usr_coll.find_one({ "_id": ObjectId(user_id) })

    if not event or not user:
        raise HTTPException(404, "event or user not found")
    
    event, user = models.Event(**event), models.User(**user)

    if event.has_started: raise HTTPException(403, "event has already started")

    db_obj = await participant_coll.find_one({"user": user.id, "event": event.id})

    nested_data = [
        {
            "field_name": "user",
            "model": models.User
        },
        {
            "field_name": "event",
            "model": models.Event
        }
    ]
    if db_obj: return await models.Participant(**db_obj).transform_data(nested_data)
    saved_obj = await models.Participant(user=user.id, event=event.id).save(req.app.db)
    return await models.Participant(**saved_obj).transform_data(nested_data)


@router.get("/events/{id}/start")
async def event_start(id: str, req: Request):
    evt_coll: motor.core.Collection = req.app.db[models.Event.get_collection_name()]
    event_obj = await evt_coll.find_one({"_id": ObjectId(id)})

    if not event_obj: raise HTTPException(404, "event not found")

    event = models.Event(**event_obj)

    if event.has_started: raise HTTPException(403, "event has already started")

    ques_coll: motor.core.Collection = req.app.db[models.Question.get_collection_name()]
    ques_obj = await ques_coll.aggregate([
        {"$match": {
            "$and": [
                    {"language": event.language},
                    {"level": event.level}
                ]
            }
        },
        {"$sample": { "size": 1 }}
    ]).to_list(length=None)

    await evt_coll.update_one(
        {"_id": event.id},
        {"$set": {
            "question_assigned": ques_obj[0]["_id"],
            "has_started": True
        }},
    )

    updated_evt = await evt_coll.find_one({"_id": ObjectId(id)})
    return await models.Event(**updated_evt).transform_data(
        [
            {
                "field_name": "question_assigned",
                "model": models.Question
            },
            {
                "field_name": "admin_user",
                "model": models.User
            }
        ]
    )


@router.put("/participants/{id}/ready")
async def ready(id: str, req: Request):
    collection: motor.core.Collection = req.app.db[models.Participant.get_collection_name()]
    updated_participant = await collection.find_one_and_update(
        {"_id": ObjectId(id)},
        [{"$set": {"is_ready": { "$not": "$is_ready" }}}],
        return_document=ReturnDocument.AFTER
    )
    if not updated_participant:
        raise HTTPException(404, "participant not found")
    return await models.Participant(**updated_participant).transform_data(
        [
            {
                "field_name": "user",
                "model": models.User
            },
            {
                "field_name": "event",
                "model": models.Event
            }
        ]
    )


@router.get("/events/{id}/participants")
async def event_participants(id: str, req: Request):
    collection: motor.core.Collection = req.app.db[models.Participant.get_collection_name()]
    participants = await collection.find({ "event": ObjectId(id) }).sort([
        ('_id', DESCENDING)
    ]).to_list(None)

    participants = [
        await models.Participant(**participant).transform_data(
            [
                {
                    "field_name": "user",
                    "model": models.User
                },
                {
                    "field_name": "event",
                    "model": models.Event
                }
            ]
        ) \
            for participant in participants
    ]
    return participants


@router.websocket("/ws/watch")
async def watch(websocket: WebSocket):
    await websocket.accept()
    db: motor.core.Database = websocket.app.db
    pipeline = [
        {
            "$match": {
                "$or": [
                    {"ns.coll": "participants"},
                    {"ns.coll": "events"},
                ]
            }
        }
    ]
    try:
        async with db.watch(pipeline) as change_stream:
            async for change in change_stream:
                data = {}
                if change["operationType"] == "insert":
                    data["operationType"] = "insert"

                    if change["ns"]["coll"] == "events":
                        data["coll"] = "events"
                        data['document'] = await models.Event(**change["fullDocument"]).transform_data(
                            [
                                {
                                    "field_name": "question_assigned",
                                    "model": models.Question
                                },
                                {
                                    "field_name": "admin_user",
                                    "model": models.User
                                }
                            ]
                        )
                    elif change["ns"]["coll"] == "participants":
                        data["coll"] = "participants"
                        data['document'] = await models.Participant(**change["fullDocument"]).transform_data(
                            [
                                {
                                    "field_name": "user",
                                    "model": models.User
                                },
                                {
                                    "field_name": "event",
                                    "model": models.Event
                                }
                            ]
                        )

                elif change["operationType"] == "update":
                    data["operationType"] = "update"

                    if change["ns"]["coll"] == "events":
                        data["coll"] = "events"
                        data['document'] = {
                            **change["documentKey"],
                            **change["updateDescription"]["updatedFields"]
                        }

                    elif change["ns"]["coll"] == "participants":
                        data["coll"] = "participants"
                        data['document'] = {
                            **change["documentKey"],
                            **change["updateDescription"]["updatedFields"]
                        }

                await websocket.send_text(json.dumps(data, cls=FastPanelJSONEncoder))

    except Exception as e:
        await websocket.close()


add_pagination(router)
