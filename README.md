This is a small UI Based Program (1 to 1 Scale to Picture below) that displays the current live chart and price of Bitcoin.


Download Libraries:
Open Powershell, paste:
pip install tkinter matplotlib numpy requests pillow

Success!
->
Open Powershell in folder, paste:

Python "(Version).py"

Enter
-> BTC Pracker opens up.

-------------------------------
you'll need to create the exe yourself because of 25mb limitation on github:

Open Powershell, paste:
pip install pyinstaller
Success!
->
Open Powershell in folder

pyinstaller --onefile --windowed --icon=btc.ico --name="BTC Pracker" (Version).py

>> wait a min

>> succes

You can now find the .exe in the newly created "dist" folder.



-----------------------------------------
Original BTC Pracker 100k:

![Pracker](https://github.com/user-attachments/assets/9b5b7b4c-9bb3-4b2c-9c01-70da3409342d)

New Versions:

<img width="640" height="966" alt="BTC-Pracker" src="https://github.com/user-attachments/assets/1434909a-c298-453f-a7a9-63e0b2715a52" />

-----------------------------------------
-----------------------------------------

known bugs:
-Theme applies not correctly automatically. Restart is needed.
-Big Dumps/Pumps will freeze Converter Value till restarted.
-Some temporary freezing while Dragging/Interacting with Window, Optimized Version will follow.
_________________________________________
Changelog:
[BTC-Pracker-HeikinAshi/Baseline] :
-> Cleaner Graph/Baseline
-> 2New added Converters.
-> 2New Realtime Trackers (USD/EUR, BTC/USD).
->12h AVG completly removed, no Text over F/G Index, no AVG-Line, only Graph is shown.

[BTC-Pracker-HeikinAshi/Baseline-AVG] :
-> Heikin Ashi Graph Added.
-> Cleaner Graph/Baseline.
-> 2New added Converters.
-> 2New Realtime Trackers (USD/EUR, BTC/USD).
-> 12h AVG got fixed, now showing correct AVG.
->AVG Price got moved besides Line
_________________________________________
Next Versions:
-New Realtime Trackers besides the newly added, ETH, LTC, PEP, XMR .
-Optimization
-BTC-Pracker shows in Toolbar
