from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import ChatMessage, ChatResponse
from services.gemini_service import GeminiService
from services.qdrant_service import QdrantService
from services.database import DatabaseService
import uvicorn

app = FastAPI(title="Physical AI Chatbot API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
gemini_service = GeminiService()
qdrant_service = QdrantService()
db_service = DatabaseService()

@app.on_event("startup")
async def startup_event():
    """Initialize database and Qdrant on startup"""
    print("🚀 Starting up...")
    await db_service.initialize_tables()
    qdrant_service.initialize_collection(vector_size=768)
    print("✅ Server ready!")

@app.get("/")
async def root():
    return {"message": "Physical AI Chatbot API is running!"}

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Handle chat requests - WITHOUT embeddings to avoid rate limits"""
    try:
        # If user selected text, use it as context
        if message.selected_text:
            context = message.selected_text
            sources = [{"text": message.selected_text[:200] + "...", "source": "Selected Text"}]
        else:
            # No embeddings - just use the question directly
            context = """You are a helpful assistant for a Physical AI & Humanoid Robotics textbook. 
            Answer questions about ROS 2, Gazebo, NVIDIA Isaac, humanoid robots, and robotics in general.
            Be clear, technical but accessible, and provide practical examples when possible."""
            sources = [{"text": "AI Knowledge Base", "source": "Gemini"}]
        
        # Generate response using Gemini (text generation only, no embeddings)
        response = gemini_service.generate_response(message.message, context)
        
        # Save chat to database
        await db_service.save_chat(
            user_message=message.message,
            bot_response=response,
            selected_text=message.selected_text
        )
        
        return ChatResponse(response=response, sources=sources)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/signup")
async def signup(request: dict):
    """Handle user signup"""
    try:
        name = request.get("name")
        email = request.get("email")
        password = request.get("password")
        experience_level = request.get("experienceLevel", "beginner")
        software_background = request.get("softwareBackground", "")
        hardware_background = request.get("hardwareBackground", "")
        
        result = await db_service.create_user(
            name=name,
            email=email,
            password=password,
            experience_level=experience_level,
            software_background=software_background,
            hardware_background=hardware_background
        )
        
        if result["success"]:
            # Get user data to return
            auth_result = await db_service.authenticate_user(email, password)
            return {
                "success": True,
                "user": auth_result["user"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/signin")
async def signin(request: dict):
    """Handle user signin"""
    try:
        email = request.get("email")
        password = request.get("password")
        
        result = await db_service.authenticate_user(email, password)
        
        if result["success"]:
            return {
                "success": True,
                "user": result["user"]
            }
        else:
            raise HTTPException(status_code=401, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Handle chat requests - WITHOUT embeddings to avoid rate limits"""
    try:
        print(f"📩 Received: {message.message}")
        
        # If user selected text, use it as context
        if message.selected_text:
            print("📝 Using selected text")
            context = message.selected_text
            sources = [{"text": message.selected_text[:200] + "...", "source": "Selected Text"}]
        else:
            print("💭 Using general context")
            # No embeddings - just use the question directly
            context = """You are a helpful assistant for a Physical AI & Humanoid Robotics textbook. 
            Answer questions about ROS 2, Gazebo, NVIDIA Isaac, humanoid robots, and robotics in general.
            Be clear, technical but accessible, and provide practical examples when possible."""
            sources = [{"text": "AI Knowledge Base", "source": "Gemini"}]
        
        print("🤖 Calling Gemini...")
        # Generate response using Gemini (text generation only, no embeddings)
        response = gemini_service.generate_response(message.message, context)
        print(f"✅ Got response: {response[:50]}")
        
        print("💾 Saving to database...")
        # Save chat to database
        await db_service.save_chat(
            user_message=message.message,
            bot_response=response,
            selected_text=message.selected_text
        )
        print("✅ Saved!")
        
        return ChatResponse(response=response, sources=sources)
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Handle chat requests - WITHOUT embeddings to avoid rate limits"""
    
    # Step 1: Log incoming request
    print("=" * 50)
    print(f"📩 CHAT REQUEST RECEIVED")
    print(f"Message: {message.message}")
    print(f"Selected text: {message.selected_text}")
    print("=" * 50)
    
    try:
        # Step 2: Determine context
        if message.selected_text:
            print("✅ Using selected text as context")
            context = message.selected_text
            sources = [{"text": message.selected_text[:200] + "...", "source": "Selected Text"}]
        else:
            print("✅ Using general knowledge context")
            context = """You are a helpful assistant for a Physical AI & Humanoid Robotics textbook. 
            Answer questions about ROS 2, Gazebo, NVIDIA Isaac, humanoid robots, and robotics in general.
            Be clear, technical but accessible, and provide practical examples when possible."""
            sources = [{"text": "AI Knowledge Base", "source": "AI"}]
        
        # Step 3: Call AI service
        print("🤖 Calling AI service...")
        try:
            response = gemini_service.generate_response(message.message, context)
            print(f"✅ AI Response received: {len(response)} characters")
        except Exception as ai_error:
            print(f"❌ AI SERVICE ERROR: {type(ai_error).__name__}: {str(ai_error)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"AI service error: {str(ai_error)}")
        
        # Step 4: Save to database
        print("💾 Saving to database...")
        try:
            await db_service.save_chat(
                user_message=message.message,
                bot_response=response,
                selected_text=message.selected_text
            )
            print("✅ Saved to database")
        except Exception as db_error:
            print(f"⚠️ DATABASE SAVE WARNING: {str(db_error)}")
            # Don't fail the request if DB save fails
        
        # Step 5: Return response
        print("✅ Returning response to client")
        return ChatResponse(response=response, sources=sources)
        
    except HTTPException as he:
        print(f"❌ HTTP EXCEPTION: {he.status_code} - {he.detail}")
        raise
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Export for Vercel
handler = app

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)