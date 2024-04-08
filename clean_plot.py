import gspread
import pandas as pd
from datetime import datetime, timedelta, date
import numpy as np
import h5py
from os import path


def round_seconds(obj: datetime) -> datetime:
    if obj.microsecond >= 500_000:
        obj += timedelta(seconds=1)
    return obj.replace(microsecond=0)


gc = gspread.service_account()

rooms = ["TV Room", "Living Room", "Laundry", "Bedroom"]

for i in range(2):  # Change to 4 once logging on all 4 starts.
    print(rooms[i])
    worksheet = gc.open(f"esp32 logging {i + 1}").sheet1
    times = worksheet.col_values(1)
    temperatures = worksheet.col_values(2)
    humidities = worksheet.col_values(3)

    # Find last pulled index
    cell = worksheet.find("Last Pulled")
    if cell:
        print(cell)

    # Create dataframe
    data_tv = pd.DataFrame(list(zip(times, temperatures, humidities)))
    data_tv.columns = ["Time", "Temperature (C)", "Humidity (%)"]
    data_tv = data_tv[data_tv['Temperature (C)'] != "0"]
    data_tv.reset_index(inplace=True, drop=True)
    # print(len(data_tv))
    # print(data_tv.head(25))

    # Calcuate datetimes
    length = len(data_tv["Humidity (%)"])
    dates = data_tv['Time']
    dates = dates[dates.str.contains(":").fillna(False)]

    for i in range(len(dates)):
        date_split = dates.iat[i].split(" ")
        datet = f"{date_split[1]} {date_split[2]}"
        datet = datetime.strptime(datet, "%Y%m%d %H:%M:%S")
        if i == 0:
            print(datet)
            time0 = datet
            j = dates.index[i]

        elif i == len(dates) - 1:
            print(datet)
            deltat = datet - time0
            delta_idx = dates.index[i] - j

    data_tv["Time"] = pd.date_range(
        start=(datet - (length * deltat / delta_idx)),
        end=datet,
        periods=length
    )

    # Convert to floats for h5
    time_array = data_tv["Time"].to_numpy()
    time_array = time_array.astype(float)
    time_array.shape
    data_array = data_tv[['Temperature (C)', 'Humidity (%)']].to_numpy()
    data_array = data_array.astype(float)
    data_array.shape
    tv_room = np.concatenate((time_array[:, None], data_array), axis=1)
    # Convert time back to datetime
    # time_array = pd.to_datetime(time_array, unit='ns')

    # Create dataset if it doesn't exist, append if it does
    with h5py.File('data/temperature_data.h5', 'a') as f:
        try:
            f.create_dataset(f"{rooms[i]}", data=tv_room, compression="gzip", chunks=True, maxshape=(None, 4))
        except ValueError:
            # Append new data to it
            f[f"{rooms[i]}"].resize((f[f"{rooms[i]}"].shape[0] + tv_room.shape[0]), axis=0)
            f[f"{rooms[i]}"][-tv_room.shape[0]:] = tv_room
    # f = h5py.File('data/temperature_data.h5', 'a')
    # f.close()

    worksheet.update_acell(f'D{length + cell}', f"Last Pulled on {date.today().isoformat()}")

    # TODO: Plotly html plots, create batch script, Correct for TZ+DLS