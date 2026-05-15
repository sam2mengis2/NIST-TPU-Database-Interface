import matplotlib.pyplot as plt
import pandas as pd
from itertools import islice
import io
from scipy.interpolate import griddata
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import re
from scipy.io import loadmat
from mpl_toolkits.mplot3d.art3d import Poly3DCollection




class WindDataAnalyzerNIST:
    def __init__(self, asc_path, hed_path: str):
        self.asc_path = asc_path
        self.hed_path = hed_path
        self.df = None

    def get_wind_dataframe(self, header_info:str, header_data):
        """This function parses the hed file to generate a df for a plot"""
        
        start_line = 0
        num_entities = 0

        with open (self.hed_path, 'r') as f:
            for i, line in enumerate(f):
                if header_info in line:
                    match = re.search(r'\[\s*(\d+)', line)
                    if match:
                        num_entities = int(match.group(1))
                        start_line = i + 1
                        break

            new_df = pd.read_csv(
                self.hed_path,
                skiprows=start_line,
                nrows=num_entities,
                sep='\s+',
                header=None,
                names=header_data,
                on_bad_lines='skip', 
                engine='python'
            )

            return new_df
        

    def get_wind_frame_plot_3D(self, tap_df, frame_df, corners_df, output_path: str):
        fig = plt.figure(figsize=(10,8))
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(corners_df['X'], corners_df['Y'], corners_df['Z'], 
           color='darkorange', s=60, label='Corners')
        

        for _, line in frame_df.iterrows():
            start_id = int(line['Start']) - 1
            end_id = int(line['End']) - 1


            start_node = corners_df.iloc[start_id]
            end_node = corners_df.iloc[end_id]

        
            xs = [start_node['X'], end_node['X']]
            ys = [start_node['Y'], end_node['Y']]
            zs = [start_node['Z'], end_node['Z']]

            ax.plot(xs, ys, zs, color='black', linewidth=2)

        for i, row in corners_df.iterrows():
            ax.text(row['X'], row['Y'], row['Z'], str(i), fontsize=12, fontweight='bold')

        scatter = ax.scatter(tap_df['X'], tap_df['Y'], tap_df['Z'], 
                     c=tap_df['Face_No'], 
                     cmap='tab10', 
                     s=15, 
                     label='Pressure Taps')
        
        cbar = plt.colorbar(scatter, ax = ax, pad=0.1)
        cbar.set_label('Face Number')


        ax.set_xlabel('X (Width)')
        ax.set_ylabel('Y (Length)')
        ax.set_zlabel('Z (Height)')
        ax.set_title('Building Wireframe Model with Face-Coded Taps')

        ax.set_box_aspect([80, 125, 20]) 
        ax.legend()

        plt.savefig(output_path)
        plt.close()
        return output_path
    

    def get_pressure_contour_map(self, mean_pressure_df, output_path : str):
        taps = mean_pressure_df["Tap no."].values
        cp = mean_pressure_df["Cp Mean"].values
        
        y = np.array([0, 1])
        X, Y = np.meshgrid(taps, y)

        CP = np.vstack([cp, cp])
        
        plt.figure(figsize=(12, 3))
        
        contour = plt.contourf(X, Y, CP, levels=50, cmap='RdBu_r')
        #Formatting
        plt.colorbar(contour, label='Mean $C_p$', pad=0.05)
        plt.xlabel('Tap Number')
        plt.yticks([]) # Hide the Y-axis since it's just a dummy height
        plt.title('2D Pressure Contour by Tap Sequence')
        
        plt.tight_layout()
        
        plt.savefig(output_path)
        plt.close()
        return output_path
    

#class to get the wind data from the tpu datbase
class WindDataAnalyzerTPU:
    def __init__(self, mat_path):
        self.mat_path = mat_path
        self.df = None


    # function meant to return a dataframe of the users choosing to read the matlab file they put in 
    def get_mat_df(self, var_name):
        data = loadmat(self.mat_path)
        matrix = data[var_name]
        mat_df = pd.DataFrame(matrix)
        return mat_df
    

    #use this function if theres a variable with only ONE value you need to extract
    #good for height, breadth and depth because they are tables of ONE
    def get_one_stat(self, stat_name):
        data = loadmat(self.mat_path)
        stat = data[stat_name].item()
        return stat
    

    def get_building_plot(self, loc_df, H, B, D, output_path : str):
        # We initialize them with zeros first
        loc_df['G_X'] = 0.0
        loc_df['G_Y'] = 0.0
        loc_df['G_Z'] = 0.0

        # 3. Apply the transformation logic face-by-face
        # Surface 1: Windward (X is horizontal, Y is height)
        # Surface 1: Windward (Front)
        # X starts at 0, goes to B
        mask1 = loc_df['Face_No'] == 1
        loc_df.loc[mask1, 'G_X'] = loc_df['X']
        loc_df.loc[mask1, 'G_Y'] = 0

        # Surface 2: Right Side
        # X continues from B, goes to B+D
        mask2 = loc_df['Face_No'] == 2
        loc_df.loc[mask2, 'G_X'] = B
        loc_df.loc[mask2, 'G_Y'] = loc_df['X'] - B 

        # Surface 3: Leeward (Back)
        # X continues from B+D, goes to B+D+B
        mask3 = loc_df['Face_No'] == 3
        loc_df.loc[mask3, 'G_X'] = B - (loc_df['X'] - (B + D))
        loc_df.loc[mask3, 'G_Y'] = D

        # Surface 4: Left Side
        # X continues from B+D+B, goes to B+D+B+D
        mask4 = loc_df['Face_No'] == 4
        loc_df.loc[mask4, 'G_X'] = 0
        loc_df.loc[mask4, 'G_Y'] = D - (loc_df['X'] - (2*B + D))

        # Z is always Y in this dataset
        loc_df['G_Z'] = loc_df['Y']

        print(f"Mapped coordinates for {len(loc_df)} taps using B={B}, D={D}, H={H}")
        loc_df.head(10)
        

        corners = np.array([
            [0, 0, 0], [B, 0, 0], [B, D, 0], [0, D, 0], # Bottom
            [0, 0, H], [B, 0, H], [B, D, H], [0, D, H]  # Top
        ])

        # 2. Define the 6 faces (surfaces)
        faces = [
            [corners[0], corners[1], corners[5], corners[4]], # Windward (Front)
            [corners[1], corners[2], corners[6], corners[5]], # Right Side
            [corners[2], corners[3], corners[7], corners[6]], # Leeward (Back)
            [corners[3], corners[0], corners[4], corners[7]], # Left Side
            [corners[4], corners[5], corners[6], corners[7]]  # Roof
        ]

        # 3. Add to your existing plot
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection='3d')

        # Add the surfaces (semi-transparent gray)
        ax.add_collection3d(Poly3DCollection(faces, facecolors='cyan', linewidths=1, edgecolors='black', alpha=.1))

        # Scatter the taps on top
        scatter = ax.scatter(loc_df['G_X'], loc_df['G_Y'], loc_df['G_Z'], 
                            c=loc_df['Face_No'], cmap='viridis', s=25, alpha=1)

        # Match the box aspect ratio to the building dimensions
        ax.set_box_aspect([B, D, H]) 

        plt.colorbar(scatter, label='Surface Number')

        ax.set_xlabel('Global X (m)')
        ax.set_ylabel('Global Y (m)')
        ax.set_zlabel('Global Z (m)')

        plt.savefig(output_path)
        plt.close()
        return output_path



    
    


        

    
