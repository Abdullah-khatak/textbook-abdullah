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
            sources = [{"text": "AI Knowledge Base", "source": "AI"}]
        
        # Generate response
        response = gemini_service.generate_response(message.message, context)
        
        # Save chat to database
        try:
            await db_service.save_chat(
                user_message=message.message,
                bot_response=response,
                selected_text=message.selected_text
            )
        except Exception as db_error:
            print(f"⚠️ DB save warning: {str(db_error)}")
        
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

@app.post("/personalize")
async def personalize_content(request: dict):
    """Personalize content based on user background"""
    try:
        content = request.get("content", "")
        user_background = request.get("userBackground", {})
        
        experience_level = user_background.get("experienceLevel", "beginner")
        software_bg = user_background.get("softwareBackground", "")
        hardware_bg = user_background.get("hardwareBackground", "")
        
        prompt = f"""You are an educational content personalizer. Adjust the following technical content for a student with this background:

Experience Level: {experience_level}
Software Background: {software_bg}
Hardware Background: {hardware_bg}

Original Content:
{content}

Instructions:
- If beginner: Simplify technical terms, add more explanations, use analogies
- If intermediate: Balance theory and practice, assume basic programming knowledge
- If advanced: Add advanced topics, reduce basic explanations, include optimization tips
- Adjust code examples complexity based on software background
- Reference hardware they know when explaining concepts

Provide the personalized version of the content maintaining the same structure and format."""
        
        response = gemini_service.client.chat.completions.create(
            model="meta-llama/llama-3.2-3b-instruct:free",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return {"personalizedContent": response.choices[0].message.content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate")
async def translate_content(request: dict):
    """Translate content to Urdu or back to English"""
    try:
        content = request.get("content", "")
        target_language = request.get("targetLanguage", "urdu")
        
        if target_language == "urdu":
            prompt = f"""Translate the following technical content to Urdu (اردو). 
Keep technical terms in English but explain them in Urdu.
Maintain markdown formatting.

Content to translate:
{content}

Provide the Urdu translation:"""
        else:
            prompt = f"""Translate the following Urdu technical content back to English.
Maintain markdown formatting.

Content to translate:
{content}

Provide the English translation:"""
        
        response = gemini_service.client.chat.completions.create(
            model="meta-llama/llama-3.2-3b-instruct:free",
            messages=[
                {"role": "system", "content": "You are a helpful translator."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return {"translatedContent": response.choices[0].message.content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Export for Vercel
app = app

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)