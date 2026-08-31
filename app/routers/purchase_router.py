from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas, auth, ledger
from ..database import get_db

router = APIRouter(prefix="/purchases", tags=["purchases"])



@router.post("", response_model=schemas.PurchaseOut)
def buy_voucher(
    purchase_in: schemas.PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_role(models.UserRole.customer)),
):
    crop = db.query(models.Crop).filter(models.Crop.id == purchase_in.crop_id).first()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop not found")

    if crop.status != models.CropStatus.open:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Crop is not open for purchases")

    remaining_kg = crop.expected_yield_kg - crop.qty_sold_kg
    if purchase_in.qty_kg > remaining_kg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {remaining_kg}kg of vouchers remain for this crop",
        )

    amount_due = purchase_in.qty_kg * crop.price_per_kg
    if current_user.wallet_balance < amount_due:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient wallet balance")

    current_user.wallet_balance -= amount_due
    crop.qty_sold_kg += purchase_in.qty_kg
    if crop.qty_sold_kg >= crop.expected_yield_kg:
        crop.status = models.CropStatus.funded

    new_purchase = models.Purchase(
        crop_id=crop.id,
        customer_id=current_user.id,
        qty_kg=purchase_in.qty_kg,
        amount_paid=amount_due,
    )
    db.add(new_purchase)
    db.commit()
    db.refresh(new_purchase)

    ledger.add_entry(
        db=db,
        crop_id=crop.id,
        event_type="voucher_purchased",
        payload={
            "customer_id": current_user.id,
            "qty_kg": purchase_in.qty_kg,
            "amount_paid": amount_due,
            "qty_sold_kg_total": crop.qty_sold_kg,
        },
    )

    return new_purchase