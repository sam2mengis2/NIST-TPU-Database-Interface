import pandas as pd

file_path = r"C:\WINDLAB_SUMMER\ee1\ADW100o100D016a1950\ADW100o100D016a1950.asc"

# sep='\s+' tells pandas to look for any amount of whitespace between numbers
# header=None tells pandas the first row is actual data, not labels
df = pd.read_csv(file_path, sep='\s+', header=None)

stats = pd.DataFrame({
    'Mean_Cp': df.mean(),        # Average pressure on each sensor
    'RMS_Cp': df.std(),          # Standard deviation (Fluctuating pressure)
    'Min_Cp': df.min(),          # Peak suction (important for structural failure)
    'Max_Cp': df.max()
})

print(stats)