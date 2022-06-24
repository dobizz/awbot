$temp = 'False'
$Folder = '.\venv'

Do {
    # checking for venv dir
    if (Test-Path -Path $Folder) {
        .\venv\Scripts\activate
        $temp = 'True'
    } else {
        python -m venv venv     # creating venv
    }
} While($temp -eq 'False')

# to run the bot
python awbot.py;