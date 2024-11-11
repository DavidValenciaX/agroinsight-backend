from cloudinary import config, uploader
from fastapi import UploadFile
import os

from dotenv import load_dotenv

load_dotenv(override=True)

class CloudinaryService:
    def __init__(self):
        config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
            secure=True
        )

    async def upload_image(self, file: UploadFile, folder: str) -> dict:
        """
        Sube una imagen a Cloudinary
        
        Args:
            file: Archivo de imagen
            folder: Carpeta donde se guardará la imagen
            
        Returns:
            dict: Información de la imagen subida
        """
        try:
            # Leer el contenido del archivo
            contents = await file.read()
            
            # Subir imagen a Cloudinary
            result = uploader.upload(
                contents,
                folder=folder,
                resource_type="image",
                format="jpg",
                quality="auto:good"
            )
            
            return {
                "url": result["secure_url"],
                "public_id": result["public_id"]
            }
            
        except Exception as e:
            raise Exception(f"Error subiendo imagen a Cloudinary: {str(e)}")

    async def upload_bytes(self, content: bytes, filename: str, folder: str) -> dict:
        """
        Sube contenido de bytes a Cloudinary
        """
        try:
            result = uploader.upload(
                content,
                folder=folder,
                resource_type="image",
                format="jpg",
                quality="auto:good"
            )
            
            return {
                "url": result["secure_url"],
                "public_id": result["public_id"]
            }
            
        except Exception as e:
            raise Exception(f"Error subiendo imagen a Cloudinary: {str(e)}")