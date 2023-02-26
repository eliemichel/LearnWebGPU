
ffmpeg ^
    -r 25 -i G:\SourceCode\LearnWebGPU-Code-folded\build\render\frame%%d.png ^
    -i G:\SourceCode\LearnWebGPU\images\empty-window.png ^
    -filter_complex "[0]format=rgba[X],[X]pad=x=1:y=31:w=642:h=512:color=black@0[Y],[1][Y]overlay" ^
    -c:v libx264 -preset veryslow -crf 18 -pix_fmt yuv420p video.mp4

