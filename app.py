import os
import shutil
import subprocess
import tempfile
import zipfile
import datetime

from flask_cors import CORS

MIN_BITS = 2
MAX_BITS = 16
MIN_NUM_PROBLEMS = 1
MAX_NUM_PROBLEMS = 99

from flask import Flask, request, send_file

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
# TODO: disable this when not using localhost
CORS(app)


def make_answers_path(path):
    path, filename = os.path.split(path)
    new_filename = f"{filename.split('.pdf')[0]}-answers.pdf"
    return os.path.join(path, new_filename)


def make_zip_path():
    return f"/tmp/problems_and_answers_{str(datetime.datetime.now().timestamp()).replace('.', '_')}.zip"


def make_zip_archive(*filepaths):
    zip_path = make_zip_path()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zfd:
        for filepath in filepaths:
            zfd.write(filepath, os.path.basename(filepath))
    return zip_path


def clear_tempdir():
    temp_files = os.listdir("/tmp")
    for f in temp_files:
        if f.endswith(".zip"):
            os.unlink(os.path.join("/tmp", f))


def validate_bits_and_num_probs(bits, num_problems):
    if bits > MAX_BITS:
        return f"max bits is {MAX_BITS}", 400
    elif bits < MIN_BITS:
        return f"min bits is {MIN_BITS}", 400
    elif num_problems > MAX_NUM_PROBLEMS:
        return f"max num_problems is {MAX_NUM_PROBLEMS}", 400
    elif num_problems < MIN_NUM_PROBLEMS:
        return f"max num_problems is {MIN_NUM_PROBLEMS}", 400


@app.route("/")
def everything():
    if not request.args:
        return "Hello World!"
    try:
        bits, num_problems = request.args["bits"], request.args["num_problems"]
    except KeyError:
        return "please provide both bits and num_problems", 400

    bits, num_problems = int(bits), int(num_problems)

    not_valid = validate_bits_and_num_probs(bits, num_problems)
    if not_valid:
        return not_valid

    include_answers = True
    if "make_answers" in request.args and request.args["make_answers"] == "false":
        include_answers = False
    make_zip = include_answers

    with tempfile.NamedTemporaryFile(mode="w", suffix=".pdf") as fout:
        subprocess.call(
            f"binary {bits} {num_problems} --pdf --output-filepath={fout.name} ",
            shell=True,
        )
        if make_zip:
            clear_tempdir()
            filepath = make_zip_archive(fout.name, make_answers_path(fout.name))
            mimetype = "application/zip"
        else:
            filepath = fout.name
            mimetype = "application/pdf"
        print(filepath)

        return send_file(
            filepath,
            as_attachment=True,
            attachment_filename=os.path.basename(filepath),
            mimetype=mimetype,
            cache_timeout=0,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4444, debug=True)
