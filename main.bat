title "Main Screen"
start "main" py -2 universe.py 3 2 2 0
timeout /t 2
start "view" py -2 humanview.py "localhost"
