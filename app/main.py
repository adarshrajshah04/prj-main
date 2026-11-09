from fastapi import FastAPI,Depends
from app.database import Base,engine,migrate_payment_schema
from app.routes.users import security
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from app.utils.notification_cleanup import start_notification_cleanup
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.routes.users import router as users_router
from app.routes.category import router as category_routes
from app.routes.properties import router as properties_routes
from app.routes.notification import router as notification_routes
from app.routes.payment import router as payment_routes
from app.routes.booking import router as booking_routes 
from app.routes.reviews import router as review_routes 
from app.routes.wishlist import router as wishlist_routes 


# deleting the notification in 1 day
# app.openapi = custom_openapi

@asynccontextmanager
async def lifespan(app: FastAPI):

    start_notification_cleanup()

    yield


app = FastAPI()


app=FastAPI(
    title="EscapeRentals API",
    lifespan=lifespan
)

Base.metadata.create_all(bind=engine)
migrate_payment_schema()

# Cross-Origin Resource Sharing ( for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(users_router)
app.include_router(category_routes)
app.include_router(properties_routes)
app.include_router(notification_routes)
app.include_router(payment_routes)
app.include_router(booking_routes)
app.include_router(review_routes)
app.include_router(wishlist_routes)


@app.get("/")
def home():
    return {"message": "Welcome to EscapeRentals API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get('/profile/')
def profile(token = Depends(security)):
    return {
        'message':'Welcome! , you are logged in!!!',
        'token':token.credentials

    }

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    def convert_file_schema(schema):
        if isinstance(schema, dict):
            if schema.get("contentMediaType") == "application/octet-stream":
                schema.pop("contentMediaType")
                schema["format"] = "binary"

            for value in schema.values():
                convert_file_schema(value)

        elif isinstance(schema, list):
            for item in schema:
                convert_file_schema(item)

    convert_file_schema(openapi_schema)

    app.openapi_schema = openapi_schema
    return app.openapi_schema
