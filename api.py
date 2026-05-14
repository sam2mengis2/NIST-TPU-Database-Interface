from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from fastapi import File, UploadFile
import subprocess as sb
import glob
from clean_read import WindDataAnalyzer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000"],
    allow_methods = ["*"],
    allow_headers = ["*"],
)


def hdf_file_reader():
    decoder_path = r"C:\WINDLAB_SUMMER\NIST_Download\bin\win32\hdf_read_demo_win.exe"

    # We are simulating (after all entires enter needs to be submitted to get to the next line): 
    # Pressing 'a' for ALL taps
    # Pressing 'c' for the time series data
    # Pressing 'a' again for the data to be in asc format
    input_sequence = "a\nc\na"

    result = sb.run(
        [decoder_path],
        input=input_sequence,
        capture_output=True,
        text=True,
        check=False
    )

    folder_path = r"C:\WINDLAB_SUMMER\file_drop"

    hed_path = None
    asc_path = None

    for filename in os.listdir(folder_path):
        if filename.endswith(".hed"):
            hed_path = os.path.join(folder_path, filename)
        elif filename.endswith(".asc"):
            asc_path = os.path.join(folder_path, filename)
    
    return hed_path, asc_path





@app.post("/files/upload")
async def upload_files(file: UploadFile = File(...)):

    upload_drop = "C:/WINDLAB_SUMMER/file_drop"
    if not os.path.exists(upload_drop):
        os.makedirs(upload_drop)


    
    file_path = os.path.join(upload_drop, file.filename)

    try:
        with open(file_path,"wb") as buffer:
            shutil.copyfileobj(file.file, buffer)



        if file.filename.endswith(".HDF"):
            hed_path, asc_path = hdf_file_reader()

        if os.path.exists(hed_path):
            analyzer = WindDataAnalyzer(asc_path, hed_path)

            tap_df = analyzer.get_wind_dataframe(
                " Tap_Coordinates_3D           ",
                ['Tap_No', 'Face_No', 'X', 'Y', 'Z']
            )

            corners_df = analyzer.get_wind_dataframe(
                " Building_Corners_3D          ",
                ['X', 'Y', 'Z']
            )

            frame_df = analyzer.get_wind_dataframe(
                " Wire_Frame_Lines_3D          ",
                ['Start', 'End']
            )

            # ... after you define tap_df, corners_df, and frame_df ...

            # DEBUG PRINTS - Watch your terminal for these!
            print("--- WINDLAB DEBUG INFO ---")
            print(f"Tap Rows: {len(tap_df)}")
            print(f"Corner Rows: {len(corners_df)}")
            print(f"Frame Rows: {len(frame_df)}")

            if not corners_df.empty:
                print("First few corners found:")
                print(corners_df.head())
            else:
                print("ERROR: corners_df is EMPTY. Check your header_info string!")

            # Now the code tries to plot
            analyzer.get_wind_frame_plot_3D(tap_df, frame_df, corners_df, plot_path)

            plot_filename = file.filename.replace(".HDF", "_3d_plt.png")
            plot_path = os.path.join(upload_drop, plot_filename)

            analyzer.get_wind_frame_plot_3D(tap_df, frame_df, corners_df, plot_path)

            return {
                "message": "Success!!",
                "plot_url": plot_path,
                "taps_found": len(tap_df)
            }



    except Exception as e:
        return {
            "error" : str(e)
        }
    

    return {"message": "File uploaded, but could not process metadata."}
        


    
