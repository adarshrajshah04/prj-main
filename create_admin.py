# from app.database import sessionLocal
# from app.model.user import UserTable
# from passlib.context import CryptContext

# pwd_context = CryptContext(
#     schemes=["bcrypt"],
#     deprecated="auto"
# )

# db = sessionLocal()

# try:
#     admin = UserTable(
#         first_name="admin",
#         last_name="admin",
#         email="admin@gmail.com",
#         contact_No="9876543210",
#         password=pwd_context.hash("Admin1234"),
#         is_admin=True,
#         is_active=True
#     )

#     db.add(admin)
#     db.commit()

#     print("Admin created successfully!")

# except Exception as e:
#     db.rollback()
#     print("Error:", e)

# finally:
#     db.close()