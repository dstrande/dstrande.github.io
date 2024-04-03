import gspread
import pandas as pd

gc = gspread.service_account()

worksheet = gc.open("esp32 logging 1").sheet1

times_1 = worksheet.row_values(1)
temperatures_1 = worksheet.row_values(2)
humidities_1 = worksheet.row_values(3)

# # Uncomments once loggers are active
# worksheet = gc.open("esp32 logging 2").sheet1
# times_2 = worksheet.row_values(1)
# temperatures_2 = worksheet.row_values(2)
# humidities_2 = worksheet.row_values(3)

# worksheet = gc.open("esp32 logging 3").sheet1
# times_3 = worksheet.row_values(1)
# temperatures_3 = worksheet.row_values(2)
# humidities_3 = worksheet.row_values(3)

# worksheet = gc.open("esp32 logging 4").sheet1
# times_4 = worksheet.row_values(1)
# temperatures_4 = worksheet.row_values(2)
# humidities_4 = worksheet.row_values(3)

print(times_1)