import gspread
import pandas as pd
from datetime import datetime, timedelta, date
import numpy as np
import h5py
import plotly.graph_objects as go


def round_seconds(obj: datetime) -> datetime:
    if obj.microsecond >= 500_000:
        obj += timedelta(seconds=1)
    return obj.replace(microsecond=0)


gc = gspread.service_account()

rooms = ["TV Room", "Living Room", "Laundry", "Bedroom"]

fig = go.Figure()

for i in range(4):
    print(rooms[i])
    worksheet = gc.open(f"esp32 logging {i + 1}").sheet1
    times = worksheet.col_values(1)
    temperatures = worksheet.col_values(2)
    humidities = worksheet.col_values(3)
    sheets_length = len(times)

    # Find last pulled index
    cell = worksheet.find("Last Pulled")
    if cell:
        print(cell)
    else:
        cell = 0

    # Create dataframe
    data_tv = pd.DataFrame(list(zip(times, temperatures, humidities)))
    data_tv.columns = ["Time", "Temperature (C)", "Humidity (%)"]
    data_tv = data_tv[data_tv["Temperature (C)"] != "0"]
    data_tv.reset_index(inplace=True, drop=True)

    # Calcuate datetimes
    length = len(data_tv["Humidity (%)"])
    dates = data_tv["Time"]
    dates = dates[dates.str.contains(":").fillna(False)]

    for k in range(len(dates)):
        date_split = dates.iat[k].split(" ")
        datet = f"{date_split[1]} {date_split[2]}"
        datet = datetime.strptime(datet, "%Y%m%d %H:%M:%S")
        if k == 0:
            print(datet)
            time0 = datet
            j = dates.index[k]

        elif k == len(dates) - 1:
            print(datet)
            deltat = datet - time0
            delta_idx = dates.index[k] - j

    data_tv["Time"] = pd.date_range(
        start=(datet - (length * deltat / delta_idx)), end=datet, periods=length
    )

    # Convert to data to floats for h5
    time_array = data_tv["Time"].to_numpy()
    time_array = time_array.astype(float)
    time_array.shape
    data_array = data_tv[["Temperature (C)", "Humidity (%)"]].to_numpy()
    data_array = data_array.astype(float)
    data_array.shape
    data_array = np.concatenate((time_array[:, None], data_array), axis=1)

    # Create dataset if it doesn't exist, append if it does
    with h5py.File("data/temperature_data.h5", "w") as f:
        try:
            f.create_dataset(
                rooms[i],
                data=data_array,
                compression="gzip",
                chunks=True,
                maxshape=(None, 4),
            )
        except ValueError:
            # Overwrite data until gsheets data is deleted
            f[rooms[i]] = data_array

            # Append new data to it
            # f[rooms[i]].resize((f[rooms[i]].shape[0] + tv_room.shape[0]),
            #                     axis=0,)
            # f[rooms[i]][-tv_room.shape[0]:] = tv_room

    worksheet.update_acell(
        f"D{sheets_length + cell}", f"Last Pulled on {date.today().isoformat()}"
    )

    with h5py.File("data/temperature_data.h5", "r") as f:
        all_data = pd.DataFrame(np.array(f[rooms[i]]))

    all_data.columns = ["Time", "Temperature (C)", "Humidity (%)"]
    all_data["Time"] = pd.to_datetime(all_data["Time"], unit="ns", utc=True)
    all_data["Time"] = all_data["Time"].dt.tz_convert("US/Pacific")

    fig.add_trace(
        go.Scatter(
            x=all_data["Time"],
            y=all_data["Temperature (C)"],
            mode="lines",
            name=rooms[i],
        )
    )

fig.write_html("index.html", include_plotlyjs=True)
# TODO: create batch script to automate, delete gsheets data after saving to h5
