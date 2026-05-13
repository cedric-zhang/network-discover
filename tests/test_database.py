import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import IPAsset, ScanTask
from datetime import datetime


# Create test database
TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


def test_create_asset(db_session):
    """Test creating new IP asset"""
    asset = IPAsset(
        ip="192.168.1.1",
        status="online",
        hostname="test-host",
        os_name="Linux",
        vendor="Test Vendor",
        mac_address="aa:bb:cc:dd:ee:ff",
        open_ports=[22, 80, 443],
        created_at=datetime.utcnow()
    )
    db_session.add(asset)
    db_session.commit()
    
    retrieved = db_session.query(IPAsset).filter(IPAsset.ip == "192.168.1.1").first()
    assert retrieved is not None
    assert retrieved.ip == "192.168.1.1"
    assert retrieved.status == "online"


def test_upsert_asset(db_session):
    """Test updating existing IP (overwrite data)"""
    # First insert
    asset = IPAsset(
        ip="10.0.0.1",
        status="offline",
        hostname="old-host",
        os_name="Windows",
        vendor="Old Vendor",
        mac_address="11:22:33:44:55:66",
        open_ports=[80],
        created_at=datetime.utcnow()
    )
    db_session.add(asset)
    db_session.commit()
    
    # Verify first insert
    retrieved = db_session.query(IPAsset).filter(IPAsset.ip == "10.0.0.1").first()
    assert retrieved.hostname == "old-host"
    assert retrieved.os_name == "Windows"
    assert retrieved.open_ports == [80]
    
    # Update data (simulate second scan)
    db_session.query(IPAsset).filter(IPAsset.ip == "10.0.0.1").update({
        IPAsset.status: "online",
        IPAsset.hostname: "new-host",
        IPAsset.os_name: "Linux",
        IPAsset.vendor: "New Vendor",
        IPAsset.mac_address: "aa:bb:cc:dd:ee:ff",
        IPAsset.open_ports: [22, 80, 443],
        IPAsset.last_scan_at: datetime.utcnow()
    })
    db_session.commit()
    
    # Verify update
    updated = db_session.query(IPAsset).filter(IPAsset.ip == "10.0.0.1").first()
    assert updated.hostname == "new-host"
    assert updated.os_name == "Linux"
    assert updated.open_ports == [22, 80, 443]
    assert updated.status == "online"


def test_query_tasks(db_session):
    """Test querying task list/details"""
    # Create test task
    task = ScanTask(
        task_id="task_test_123",
        target="192.168.1.1",
        status="completed",
        result_summary="Scan completed successfully"
    )
    db_session.add(task)
    db_session.commit()
    
    # Query task
    retrieved = db_session.query(ScanTask).filter(ScanTask.task_id == "task_test_123").first()
    assert retrieved is not None
    assert retrieved.target == "192.168.1.1"
    assert retrieved.status == "completed"
