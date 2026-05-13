from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from fastapi import File, UploadFile
import subprocess as sb

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000"],
    allow_methods = ["*"],
    allow_headers = ["*"],
)


def hdf_file_reader1():
    folder_path = "c:\WINDLAB_SUMMER\file_drop"
    folder_files = os.listdir(folder_path)

    for filename in folder_files:
        if filename.endswith(".HDF"):
            full_path = os.path.join(folder_path, filename)
    
    decoder_path = r"C:\WINDLAB_SUMMER\NIST_Download\bin\win32\hdf_read_demo_win.exe"

    command = [decoder_path, full_path]  

    result = sb.run(
        command,
        capture_output = True,
        text = True,
        check = False
    )
    
    return False


def hdf_file_reader(target_path : str):
    decoder_path = r"C:\WINDLAB_SUMMER\NIST_Download\bin\win32\hdf_read_demo_win.exe"
    command = [decoder_path, target_path]  

    result = sb.run(command, capture_output=True, text=True, check=False)
    
    # Log the output to your terminal so you can see what the .exe says
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    
    return result.returncode == 0





@app.post("/files/upload")
async def upload_files(file: UploadFile = File(...)):

    upload_drop = "C:/WINDLAB_SUMMER/file_drop"
    if not os.path.exists(upload_drop):
        os.makedirs(upload_drop)


    
    file_path = os.path.join(upload_drop, file.filename)

    try:
        with open(file_path,"wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        print("Error saving file : {e}")
        return{
            "error" : str(e)
        }
    

    if file.filename.endswith(".HDF"):
        conversion_success = hdf_file_reader(file_path)
        if not conversion_success:
            return {
                "message" : "file saved but not decoded"
            }
    
    return {
        "message" : "Success!!",
        "saved at" : file_path
    }
        


    
