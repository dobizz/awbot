$temp = 'False'
$Folder = '.\venv'

Do {
    # checking for venv dir
    if (Test-Path -Path $Folder) {
        .\venv\Scripts\activate
        $temp = 'True'
    } else {
        py -m venv venv     # creating venv
    }
} While($temp -eq 'False')

# installing/updating dependencies
pip install -r requirements.txt

# to run the bot
py awbot.py;