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
    """Handle chat requests"""
    try:
        # If user selected text, use it as context
        if message.selected_text:
            context = message.selected_text
            sources = [{"text": message.selected_text, "source": "Selected Text"}]
        else:
            # Generate query embedding
            query_embedding = gemini_service.generate_query_embedding(message.message)
            
            # Search for similar content in Qdrant
            search_results = qdrant_service.search_similar(query_embedding, limit=3)
            
            # Combine search results as context
            context = "\n\n".join([result["text"] for result in search_results])
            sources = [
                {
                    "text": result["text"][:200] + "...",
                    "source": result["metadata"].get("file_name", "Unknown"),
                    "score": result["score"]
                }
                for result in search_results
            ]
        
        # Generate response using Gemini
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Export for Vercel
handler = app

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)