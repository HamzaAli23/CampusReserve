from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from .database import get_session
from .models import Booking, BookingCreate, BookingRead, BookingStatus, Resource, ResourceCreate

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/resources", response_model=list[Resource])
def list_resources(session: Session = Depends(get_session)) -> list[Resource]:
    return list(session.exec(select(Resource).order_by(Resource.name)))


@router.post("/resources", response_model=Resource, status_code=status.HTTP_201_CREATED)
def create_resource(payload: ResourceCreate, session: Session = Depends(get_session)) -> Resource:
    resource = Resource.model_validate(payload)
    session.add(resource)
    session.commit()
    session.refresh(resource)
    return resource


@router.get("/bookings", response_model=list[BookingRead])
def list_bookings(session: Session = Depends(get_session)) -> list[Booking]:
    return list(session.exec(select(Booking).order_by(Booking.starts_at)))


@router.post("/bookings", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(payload: BookingCreate, session: Session = Depends(get_session)) -> Booking:
    if payload.starts_at.tzinfo is None or payload.ends_at.tzinfo is None:
        raise HTTPException(422, "starts_at and ends_at must include a timezone")
    if payload.starts_at >= payload.ends_at:
        raise HTTPException(422, "ends_at must be after starts_at")
    if session.get(Resource, payload.resource_id) is None:
        raise HTTPException(404, "resource not found")

    overlap = session.exec(
        select(Booking).where(
            Booking.resource_id == payload.resource_id,
            Booking.status == BookingStatus.ACTIVE,
            Booking.starts_at < payload.ends_at,
            Booking.ends_at > payload.starts_at,
        )
    ).first()
    if overlap:
        raise HTTPException(409, "resource is already booked for this time")

    booking = Booking.model_validate(payload)
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


@router.post("/bookings/{booking_id}/cancel", response_model=BookingRead)
def cancel_booking(booking_id: int, session: Session = Depends(get_session)) -> Booking:
    booking = session.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(404, "booking not found")
    booking.status = BookingStatus.CANCELLED
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking
