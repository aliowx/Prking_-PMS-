import math
import random
import logging
from app.core.celery_app import celery_app
from app import schemas, crud, models
from sqlalchemy import text
from app.core.celery_app import DatabaseTask, celery_app
from app.schemas import RecordUpdate, PlateUpdate
from datetime import timedelta, datetime
from app.jobs.celery.celeryworker_pre_start import redis_client
from app.core.config import settings


namespace = "parking"
logger = logging.getLogger(__name__)


@celery_app.task
def test_celery(word: str) -> str:
    return f"test task return {word}"


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    acks_late=True,
    max_retries=4,
    soft_time_limit=240,
    time_limit=360,
    name="add_plates",
)
def add_plates(self, plate: dict) -> str:

    try:
        plate = crud.plate.create(db=self.session, obj_in=plate)

        celery_app.send_task(
            "update_record",
            args=[plate.id],
        )

    except Exception as exc:
        countdown = int(random.uniform(1, 2) ** self.request.retries)
        logger.info(f"Error adding plate:{exc} ,retrying in {countdown}s.")
        logger.exception(exc)
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    acks_late=True,
    max_retries=3,
    soft_time_limit=240,
    time_limit=360,
    name="update_record",
)
def update_record(self, plate_id) -> str:
    logger.info(f"******** update_record: {plate_id}")

    if plate_id == {}:
        logger.warning(f"Invalid Plate id found: {plate_id}")
        return None

    if isinstance(plate_id, dict) and "id" in plate_id:
        plate_id = plate_id["id"]

    try:
        # lock plates table to prevent multiple record insertion
        self.session.execute(text("LOCK TABLE plate IN EXCLUSIVE MODE"))
        plate = crud.plate.get(self.session, plate_id)
        record = crud.record.get_by_plate(
            db=self.session, plate=plate, for_update=True
        )

        if record is None:
            record = schemas.RecordCreate(
                ocr=plate.ocr,
                record_number=0,
                start_time=plate.record_time,
                end_time=plate.record_time,
                score=0.01,
                best_lpr_id=plate.lpr_id,
                best_big_image_id=plate.big_image_id,
            )
            record = crud.record.create(db=self.session, obj_in=record)

        else:
            if record.start_time > plate.record_time:
                record_update = RecordUpdate(
                    score=math.sqrt(record.score),
                    start_time=plate.record_time,
                )
            elif record.end_time < plate.record_time:
                record_update = RecordUpdate(
                    score=math.sqrt(record.score),
                    end_time=plate.record_time,
                    best_lpr_id=plate.lpr_id,
                    best_big_image_id=plate.big_image_id,
                )
            else:
                record_update = RecordUpdate(
                    score=math.sqrt(record.score),
                )

            record = crud.record.update(
                self.session, db_obj=record, obj_in=record_update
            )

        update_plate = PlateUpdate(record_id=record.id)
        # this refresh for update plate with out this not working ==> solution 1
        self.session.refresh(plate)
        # or solution 2
        # logger.info(f"latest value plate.record_id ===> {plate.record_id}")
        # or solution 3
        # plate.record_id = record.id
        # plate_update = crud.plate.update(
        #     self.session, db_obj=plate
        # )

        plate_update = crud.plate.update(
            self.session, db_obj=plate, obj_in=update_plate
        )
        if plate_update:
            logger.info(
                f"new value plate.record_id ===> {plate_update.record_id}"
            )

    except Exception as exc:
        countdown = int(random.uniform(2, 4) ** self.request.retries)
        logger.info(f"Error adding record:{exc} ,retring in {countdown}s.")
        logger.exception(exc)
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    logger.info(
        f"cleanup {settings.CLEANUP_COUNT} images every {settings.CLEANUP_PERIOD} seconds "
        f"which are older than {settings.CLEANUP_AGE} days"
    )
    if settings.CLEANUP_AGE > 0:
        sender.add_periodic_task(
            settings.CLEANUP_PERIOD,
            cleanup.s("image"),
            name="cleanup image task",
        )
        sender.add_periodic_task(
            settings.CLEANUP_PERIOD,
            cleanup.s("plate"),
            name="cleanup plate task",
        )
        sender.add_periodic_task(
            settings.CLEANUP_PERIOD,
            cleanup.s("record"),
            name="cleanup record task",
        )


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    acks_late=True,
    max_retries=1,
    soft_time_limit=240,
    time_limit=360,
    name="cleanup",
)
def cleanup(self, table_name: str = "image"):
    """cleans db up and wait at least CLEANUP_PERIOD seconds between each operation"""
    # lock = RedisLock("cleanup_task_lock")
    lock_name = f"cleanup_{table_name}_task_lock"
    if redis_client.get(lock_name):
        return f"Cleanup {table_name} canceled for performance"
    redis_client.setex(
        lock_name, timedelta(seconds=60 * settings.CLEANUP_PERIOD), 1
    )
    try:
        if table_name == "image":
            limit = datetime.now() - timedelta(days=settings.CLEANUP_AGE)
            filter = models.Image.modified
            model = models.Image
        elif table_name == "plate":
            limit = datetime.now() - timedelta(
                days=settings.CLEANUP_PLATES_AGE
            )
            filter = models.Plate.record_time
            model = models.Plate
        elif table_name == "record":
            limit = datetime.now() - timedelta(
                days=settings.CLEANUP_RECORDS_AGE
            )
            filter = models.Record.end_time
            model = models.Record
        else:
            return f"Cleanup Unknown Table ({table_name})!"
        logger.info(
            f"running cleanup {table_name} ({settings.CLEANUP_COUNT}, {settings.CLEANUP_AGE})"
        )
        subquery = (
            self.session.query(model.id)
            .filter(filter < limit)
            .limit(settings.CLEANUP_COUNT)
            .subquery()
        )
        result = (
            self.session.query(model)
            .filter(model.id.in_(subquery))
            .delete(synchronize_session="fetch")
        )
        self.session.commit()
        redis_client.setex(
            lock_name, timedelta(seconds=settings.CLEANUP_PERIOD), 1
        )
        return f"Cleanup {table_name} done, result: {result}"
    finally:
        redis_client.setex(
            lock_name, timedelta(seconds=settings.CLEANUP_PERIOD), 1
        )
