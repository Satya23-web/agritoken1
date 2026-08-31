from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas, auth, ledger
from ..database import get_db

router = APIRouter(prefix="/crops", tags=["crops"])


@router.post("", response_model=schemas.CropOut)
def create_crop(
    crop_in: schemas.CropCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.farmer)),
):
    price_per_kg = crop_in.cost_needed / crop_in.expected_yield_kg

    new_crop = models.Crop(
        farmer_id=current_user.id,
        crop_name=crop_in.crop_name,
        expected_yield_kg=crop_in.expected_yield_kg,
        cost_needed=crop_in.cost_needed,
        price_per_kg=price_per_kg,
    )
    db.add(new_crop)
    db.commit()
    db.refresh(new_crop)

    ledger.add_entry(
        db=db,
        crop_id=new_crop.id,
        event_type="crop_listed",
        payload={
            "farmer_id": current_user.id,
            "crop_name": new_crop.crop_name,
            "expected_yield_kg": new_crop.expected_yield_kg,
            "cost_needed": new_crop.cost_needed,
            "price_per_kg": new_crop.price_per_kg,
        },
    )

    return new_crop



@router.get("", response_model=list[schemas.CropOut])
def list_crops(db: Session = Depends(get_db)):
    return db.query(models.Crop).all()


@router.get("/{crop_id}", response_model=schemas.CropOut)
def get_crop(crop_id: int, db: Session = Depends(get_db)):
    crop = db.query(models.Crop).filter(models.Crop.id == crop_id).first()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop not found")
    return crop




@router.post("/{crop_id}/harvest", response_model=schemas.CropOut)
def record_harvest(
    crop_id: int,
    harvest_in: schemas.HarvestRecord,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.farmer)),
):
    crop = db.query(models.Crop).filter(models.Crop.id == crop_id).first()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop not found")

    if crop.farmer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your crop")

    if crop.status == models.CropStatus.harvested:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Harvest already recorded")

    fulfillment_ratio = harvest_in.actual_yield_kg / crop.expected_yield_kg

    crop.actual_yield_kg = harvest_in.actual_yield_kg
    crop.quality_grade = harvest_in.quality_grade
    crop.fulfillment_ratio = fulfillment_ratio
    crop.status = models.CropStatus.harvested

    purchases = db.query(models.Purchase).filter(models.Purchase.crop_id == crop.id).all()
    for purchase in purchases:
        purchase.redeemed_qty_kg = purchase.qty_kg * fulfillment_ratio

    db.commit()
    db.refresh(crop)

    ledger.add_entry(
        db=db,
        crop_id=crop.id,
        event_type="harvest_recorded",
        payload={
            "actual_yield_kg": harvest_in.actual_yield_kg,
            "quality_grade": harvest_in.quality_grade,
            "fulfillment_ratio": fulfillment_ratio,
            "purchases_updated": len(purchases),
        },
    )

    return crop