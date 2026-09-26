@echo off
REM Rebuild ffxicrafting.com from LandSandBoat + Phoenix sources
REM Usage: rebuild.bat
REM Prereqs: pip install pyyaml
setlocal

set LSB=C:\Users\MEE87\Documents\lsb-server
set PXI=C:\Users\MEE87\Documents\phoenix-server\modules
set SITE=C:\Users\MEE87\Documents\ffxicrafting
set DB=%SITE%\data\ffxi_crafting.db
set TOOLS=%SITE%\tools

echo === Pulling latest LandSandBoat ===
cd /d %LSB%
git pull --ff-only

echo === Building database ===
python %TOOLS%\build_db.py %LSB% %DB% %PXI%
if errorlevel 1 goto :fail

echo === Generating site pages ===
cd /d %SITE%
python %TOOLS%\build_calculator.py
python %TOOLS%\build_crafts.py
python %TOOLS%\build_craft_detail.py
python %TOOLS%\build_gathering.py
python %TOOLS%\build_bcnm.py
python %TOOLS%\build_items.py
python %TOOLS%\build_profit.py
python %TOOLS%\build_shopping.py
python %TOOLS%\build_zones.py
python %TOOLS%\build_about.py
python %TOOLS%\build_search_index.py

echo.
echo === Done ===
echo Review with: cd %SITE% ^& git diff --stat
echo Then commit and push when ready.
goto :eof

:fail
echo.
echo BUILD FAILED
exit /b 1
