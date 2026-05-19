from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from fastapi import File, UploadFile
import subprocess as sb
import glob
from clean_read import WindDataAnalyzerNIST
from clean_read import WindDataAnalyzerTPU
from fastapi.staticfiles import StaticFiles
from supabase import create_client, Client
import supabase

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000"],
    allow_methods = ["*"],
    allow_headers = ["*"],
)

upload_drop = r"C:\WINDLAB_SUMMER\file_drop"

app.mount("/static", StaticFiles(directory=upload_drop), name="static")


#function to read start the hdf decoder to decode the hdf file into readable hed and asc time series data files
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

#Post request to recieve the uploaded file and then to create graphs and charts from them
@app.post("/files/upload")
async def upload_files(file: UploadFile = File(...)):

    #making a place to put the files uploaded
    upload_drop = "C:/WINDLAB_SUMMER/file_drop"
    #if it doesnt exist make it
    if not os.path.exists(upload_drop):
        os.makedirs(upload_drop)
    

    #make a new file path that joins the upload folder dir and the new file name
    file_path = os.path.join(upload_drop, file.filename)

    try:
        #open the file and close it when we are done
        with open(file_path,"wb") as buffer:
            shutil.copyfileobj(file.file, buffer)



        #if the file ends with .HDF run the reader function that opens the decoder
        if file.filename.endswith(".HDF"):
            hed_path, asc_path = hdf_file_reader()

            #if the hed path exists from the decoder, then run the WindDataAnalyzer code
            if os.path.exists(hed_path):
                analyzer = WindDataAnalyzerNIST(asc_path, hed_path)

                #define the tap, building corners and frame df for future plotting
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

                mean_pressure_df = analyzer.get_wind_dataframe(
                    " Tap_Max_Min_Mean_RMS         ",
                    ['Tap no.', 'Cp Max', 'Cp Min', 'Cp Mean', 'Cp RMS']
                )


                flow_field_stats_df = analyzer.get_wind_dataframe(
                    " Wind_Speed_Profile           ",
                    ['Z', 'V', 'Iu', 'Iv', 'Iw']
                )

                reference_velocity = analyzer.get_wind_dataframe(
                    " Reference_Wind_Speed         ",
                    ['Reference Velocity (Feet/Second)']
                )

                pressure_time_df = analyzer.get_pressure_timestep_df()

                # DEBUG PRINTS
                print("--- WINDLAB DEBUG INFO ---")
                print(pressure_time_df.head())

                # Now the code tries to plot

                plot_filename = file.filename.replace(".HDF", "_3d_plt.png")
                plot_path = os.path.join(upload_drop, plot_filename)

                analyzer.get_wind_frame_plot_3D(tap_df, frame_df, corners_df, plot_path)
                

                #if its good we return success with the path of the new plot (for now until we have a ui)
                return {
                    "plot_url": f"http://localhost:8000/static/{plot_filename}"
                }


        #if the file ends with .mat the use the TPU WindDataAnalyzer class
        if file.filename.endswith(".mat"):
            analyzer = WindDataAnalyzerTPU(file_path)

            #get the location of the taps in 2d 
            loc_df_before = analyzer.get_mat_df("Location_of_measured_points")
            loc_df = loc_df_before.T
            loc_df.columns = ['X', 'Y', 'Point_No', 'Face_No']
            #get the dataframe of the pressure
            pressure_df = analyzer.get_mat_df("Wind_pressure_coefficients")

            #get the singluar stat of the height breadth and width
            height = analyzer.get_one_stat('Building_height')
            breadth = analyzer.get_one_stat('Building_breadth')
            depth = analyzer.get_one_stat('Building_depth')


            #make the new plot filename and path
            plot_filename = file.filename.replace('.mat','_3d_plt.png')
            plot_path = os.path.join(upload_drop, plot_filename)

            #plot the new building
            analyzer.get_building_plot(loc_df, height, breadth, depth, plot_path)

            #return a success message with the path of the plot if all goes well
            return {
                "plot_url": plot_path
            }
    except Exception as e:
        return {
            "error" : str(e)
        }
    return {"message": "File uploaded, but could not process metadata."}
        





@app.get("/plot/timeseries")
async def get_custom_timeseries(tap_no, start, end):
    folder_path = r"C:\WINDLAB_SUMMER\file_drop"
    asc_path = None
    hed_path = None # <-- We need to find this too!
    
    # 1. Look for BOTH the active .asc and .hed files in the folder
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            if filename.endswith(".asc"):
                asc_path = os.path.join(folder_path, filename)
            elif filename.endswith(".hed"):
                hed_path = os.path.join(folder_path, filename)
            
    # 2. Safety Check: Make sure BOTH files exist before proceeding
    if not asc_path or not hed_path:
        return {"error": "Missing active wind data (.asc or .hed). Please upload a .HDF file first."}
        
    try:
        # 3. Initialize analyzer with BOTH paths! (No more empty strings)
        analyzer = WindDataAnalyzerNIST(asc_path, hed_path)
        
        # 4. Read the data (This will now safely parse the .hed file for your tap coords)
        df = analyzer.get_pressure_timestep_df()
        
        # 5. Create unique filename
        plot_filename = f"tap_{tap_no}_steps_{start}_to_{end}.png"
        plot_path = os.path.join(folder_path, plot_filename)
        
        # 6. Generate and save the plot
        analyzer.get_pressure_plot(df, tap_no, start, end, plot_path)
        
        # 7. Return the URL
        return {
            "plot_url": f"http://localhost:8000/static/{plot_filename}"
        }
        
    except Exception as e:
        import traceback
        print("--- CRITICAL TIMESERIES ERROR ---")
        print(traceback.format_exc())
        return {
            "error": str(e)
        }