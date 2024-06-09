from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ServiceFailure
from app.parking.repo import parking_repo
from app.parking.schemas import SetZonePriceInput
from app.parking.services import parkingzone as parkingzone_services
from app.pricing import schemas as price_schemas
from app.pricing.repo import price_repo
from app.utils import MessageCodes


async def create_price(
    db: AsyncSession, price_data: price_schemas.PriceCreate
) -> price_schemas.Price:
    if price_data.parking_id:
        parking = await parking_repo.get(db, id=price_data.parking_id)
    else:
        parking = await parking_repo.get_main_parking(db)
    if not parking:
        raise ServiceFailure(
            detail="Parking not found",
            msg_code=MessageCodes.not_found,
        )
    price_data_create = price_data.model_copy(
        update={"zone_ids": None, "priority": None}
    )
    price = await price_repo.create(
        db,
        obj_in=price_data_create.model_dump(exclude_none=True),
        commit=False,
    )
    for zone_id in price_data.zone_ids:
        zoneprice_data = SetZonePriceInput(
            price_id=price.id, priority=price_data.priority
        )
        await parkingzone_services.set_price(
            db,
            parkingzone_id=zone_id,
            zoneprice_data=zoneprice_data,
            commit=False,
        )
    await db.commit()
    return price
