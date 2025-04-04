from fastapi import APIRouter, UploadFile, File, HTTPException
import supabase
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

supabase_client = supabase.create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


@router.post("/")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # Generate a unique filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")  
        file_ext = file.filename.split(".")[-1]
        file_name = f"{timestamp}_{file.filename}"
        file_path = f"uploads/{file_name}"  # Path inside Supabase Storage
        
        # Read file content
        file_content = await file.read()
        
        # Upload to Supabase Storage
        response = supabase_client.storage.from_(os.getenv("SUPABASE_BUCKET")).upload(file_path, file_content, {"content-type": file.content_type})
        
        if not response:
            raise HTTPException(status_code=500, detail="Failed to upload PDF to Supabase")

        # Get public URL
        public_url = f"{os.getenv("SUPABASE_URL")}/storage/v1/object/public/{os.getenv("SUPABASE_BUCKET")}/{file_path}"
        
        return {"message": "File uploaded successfully", "pdf_url": public_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))