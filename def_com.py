import subprocess
import sys
from flask import Flask, request
import firebase_admin
from firebase_admin import credentials


app = Flask(__name__)
cred = credentials.Certificate('tab-tools-firebase-adminsdk-8ncav-4f5ccee9af.json')
firebase_admin.initialize_app(cred)


@app.route('/launchidentify', methods=['GET'])
def launch_python_file():
    user_uid = request.args.get('uid')
    selected_del = request.args.get('del')

    subprocess.call([sys.executable, "pre_process.py", user_uid, selected_del])


    return 'Success'

@app.route('/launchcombinefiles', methods=['GET'])
def launch_combine_files():
    driver_id = request.args.get('driverId')
    selected = request.args.get('selected')
    loadnumber = request.args.get('loadnumber')
    file_name = request.args.get('fileName')

    subprocess.call([sys.executable, "combine_files.py", driver_id, selected, loadnumber, file_name])
    

    return 'Successful'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)