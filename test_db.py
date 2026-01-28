from app.database import engine
from app.database.models import Base

# Create tables
Base.metadata.create_all(bind=engine)
print("✅ Database tables created successfully!")

# List tables
from sqlalchemy import inspect
inspector = inspect(engine)
print("\nTables created:")
for table in inspector.get_table_names():
    print(f"  - {table}")
