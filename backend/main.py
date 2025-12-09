from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import ChatMessage, ChatResponse
from services.gemini_service import GeminiService
from services.qdrant_service import QdrantService
from services.database import DatabaseService
import uvicorn
import traceback

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
    """Handle chat requests"""
    try:
        print(f"📩 Received message: {message.message[:50]}...")
        
        # If user selected text, use it as context
        if message.selected_text:
            print("📝 Using selected text as context")
            context = message.selected_text
            sources = [{"text": message.selected_text, "source": "Selected Text"}]
        else:
            print("🔍 Searching for relevant content...")
            # Generate query embedding
            try:
                query_embedding = gemini_service.generate_query_embedding(message.message)
                print(f"✅ Generated embedding with {len(query_embedding)} dimensions")
            except Exception as e:
                print(f"❌ Error generating embedding: {str(e)}")
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")
            
            # Search for similar content in Qdrant
            try:
                search_results = qdrant_service.search_similar(query_embedding, limit=3)
                print(f"✅ Found {len(search_results)} relevant results")
            except Exception as e:
                print(f"❌ Error searching Qdrant: {str(e)}")
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
            
            # Combine search results as context
            if search_results:
                context = "\n\n".join([result["text"] for result in search_results])
                sources = [
                    {
                        "text": result["text"][:200] + "...",
                        "source": result.get("metadata", {}).get("file_name", "Textbook"),
                        "score": result.get("score", 0.0)
                    }
                    for result in search_results
                ]
            else:
                print("⚠️ No search results found, using general context")
                context = "This is a textbook about Physical AI and Humanoid Robotics covering ROS 2, simulation, NVIDIA Isaac, and Vision-Language-Action systems."
                sources = [{"text": "General knowledge", "source": "Textbook", "score": 0.0}]
        
        # Generate response using Gemini
        try:
            print("🤖 Generating response with Gemini...")
            response = gemini_service.generate_response(message.message, context)
            print(f"✅ Generated response: {response[:50]}...")
        except Exception as e:
            print(f"❌ Error generating response: {str(e)}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"AI response error: {str(e)}")
        
        # Save chat to database
        try:
            await db_service.save_chat(
                user_message=message.message,
                bot_response=response,
                selected_text=message.selected_text
            )
            print("✅ Saved chat to database")
        except Exception as e:
            print(f"⚠️ Warning: Could not save to database: {str(e)}")
            # Don't fail the request if DB save fails
        
        return ChatResponse(response=response, sources=sources)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR in /chat: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

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
        print(f"❌ Error in /signup: {str(e)}")
        traceback.print_exc()
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
        print(f"❌ Error in /signin: {str(e)}")
        traceback.print_exc()
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
        
        # Create personalization prompt
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
        
        response = gemini_service.model.generate_content(prompt)
        
        return {"personalizedContent": response.text}
        
    except Exception as e:
        print(f"❌ Error in /personalize: {str(e)}")
        traceback.print_exc()
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
        
        response = gemini_service.model.generate_content(prompt)
        
        return {"translatedContent": response.text}
        
    except Exception as e:
        print(f"❌ Error in /translate: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Export for Vercel
handler = app

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)