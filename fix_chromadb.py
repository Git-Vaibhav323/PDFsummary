"""
Script to fix ChromaDB HNSW index issues by rebuilding the collection.
Run this if you're experiencing "Cannot return the results in a contigious 2D array" errors.
"""
import os
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_chromadb():
    """Rebuild ChromaDB collection to fix HNSW index issues."""
    chroma_db_path = "./chroma_db"
    
    if not os.path.exists(chroma_db_path):
        logger.info("ChromaDB directory doesn't exist, nothing to fix")
        return
    
    logger.warning("⚠️  This will delete your current ChromaDB and require re-uploading PDFs")
    response = input("Do you want to continue? (yes/no): ")
    
    if response.lower() != "yes":
        logger.info("Cancelled. ChromaDB not modified.")
        return
    
    try:
        # Backup the directory
        backup_path = f"{chroma_db_path}_backup"
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
        shutil.copytree(chroma_db_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
        
        # Delete the ChromaDB directory
        shutil.rmtree(chroma_db_path)
        logger.info(f"Deleted ChromaDB directory: {chroma_db_path}")
        
        logger.info("✅ ChromaDB has been reset!")
        logger.info("📝 Next steps:")
        logger.info("   1. Restart your backend server")
        logger.info("   2. Re-upload your PDF files")
        logger.info("   3. The new collection will be created with proper settings")
        
    except Exception as e:
        logger.error(f"Error fixing ChromaDB: {e}")
        logger.info("You can manually delete the chroma_db directory and restart the server")

if __name__ == "__main__":
    fix_chromadb()

