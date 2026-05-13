from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from sqlalchemy import create_engine
from datetime import datetime
import atexit
import logging
from app.services.scanner import scanner_service
from app.models import ScanSubmitRequest, ScanOptions
from app.database import DATABASE_URL


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置作业存储和执行器
jobstores = {
    'default': SQLAlchemyJobStore(url=DATABASE_URL)
}
executors = {
    'default': ThreadPoolExecutor(20)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

# 创建调度器实例
scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)


def run_scan_for_schedule(target: str):
    """
    为定时任务执行扫描的函数
    """
    logger.info(f"开始执行定时扫描任务，目标: {target}")

    try:
        # 创建扫描请求对象
        scan_request = ScanSubmitRequest(
            target=target,
            scan_options=ScanOptions(
                port_scan=True,
                os_detection=True,
                vendor_detection=True
            )
        )

        # 执行扫描
        # 注意：在真实环境中，我们可能需要使用数据库会话或其他上下文管理器
        result = scanner_service.scan_host(target)

        logger.info(f"定时扫描任务完成，目标: {target}")

        # 更新调度任务的最后运行时间
        from app.database import get_db
        from app.models import Schedule
        db = next(get_db())
        schedule = db.query(Schedule).filter(Schedule.target == target).first()
        if schedule:
            schedule.last_run_at = datetime.utcnow()
            db.commit()
        db.close()

        return result
    except Exception as e:
        logger.error(f"定时扫描任务失败，目标: {target}, 错误: {str(e)}")
        raise


def load_schedules_from_db():
    """
    从数据库加载活跃的定时任务
    """
    from app.database import get_db
    from app.models import Schedule

    db = next(get_db())
    try:
        # 获取所有活跃的定时任务
        active_schedules = db.query(Schedule).filter(Schedule.is_active == True).all()

        for schedule in active_schedules:
            try:
                # 解析cron表达式
                cron_parts = schedule.cron_expr.split()
                if len(cron_parts) == 5:
                    minute, hour, day, month, day_of_week = cron_parts
                else:
                    logger.error(f"无效的cron表达式: {schedule.cron_expr}")
                    continue

                # 添加作业到调度器
                scheduler.add_job(
                    func=run_scan_for_schedule,
                    trigger='cron',
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                    id=f"schedule_{schedule.id}",
                    args=[schedule.target],
                    name=f"{schedule.name} - {schedule.target}"
                )

                logger.info(f"已加载定时任务: {schedule.name} (ID: {schedule.id})")
            except Exception as e:
                logger.error(f"加载定时任务失败: {schedule.name}, 错误: {str(e)}")
    finally:
        db.close()


def init_scheduler():
    """
    初始化调度器
    """
    if not scheduler.running:
        # 从数据库加载现有的定时任务
        load_schedules_from_db()

        # 启动调度器
        scheduler.start()
        logger.info("调度器已启动")

        # 注册关闭时的清理函数
        atexit.register(shutdown_scheduler)


def shutdown_scheduler():
    """
    关闭调度器
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("调度器已关闭")