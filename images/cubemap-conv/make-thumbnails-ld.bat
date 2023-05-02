if not exist "ld\" mkdir ld
for %%i in (*.png) do magick convert "%%i" -resize 256x256 "ld/%%~ni.jpg"
pause
