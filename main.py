from flask import Flask, request, flash, redirect, send_file, render_template

import cv2 as cv

import os
import time
import shutil

from cropper import Cropper

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER, mode=0o777)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.environ.get('SECRET_KEY')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def landing_page():
    return render_template('index.html')


@app.route('/process-image', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return 'No images part'

    file = request.files['image']
    image_count = int(request.form.get('image_count'))

    if file.filename == '':
        return 'No selected image'

    if file and allowed_file(file.filename):
        folder_name = str(int(time.time()))
        os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'], folder_name))

        filename = 'original.' + file.filename.rsplit('.')[1]
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], folder_name, filename))

        image = cv.imread(os.path.join(app.config['UPLOAD_FOLDER'], folder_name, filename))

        cropper = Cropper(image)
        cropped_images = cropper.crop(image_count)

        # cv.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], folder_name, 'boundaries.png'),
        #            cropper.image_visualizer, [cv.IMWRITE_PNG_COMPRESSION, 9])
        # cv.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], folder_name, 'filter.png'),
        #            cropper.thresh, [cv.IMWRITE_PNG_COMPRESSION, 9])

        for i, image in enumerate(cropped_images):
            straight_rectangle_image = image[0]
            rotated_rectangle_image = image[1]

            # cv.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], folder_name, str(i+1) + '-straight.png'),
            #            straight_rectangle_image)
            cv.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], folder_name, str(i + 1) + '-rotated.png'),
                       rotated_rectangle_image)

        archive_name = folder_name + '-output'
        archive_extension = 'zip'
        archive_path = os.path.join(app.config['UPLOAD_FOLDER'], archive_name)

        shutil.make_archive(archive_path, archive_extension, os.path.join(app.config['UPLOAD_FOLDER'], folder_name))

        shutil.rmtree(os.path.join(app.config['UPLOAD_FOLDER'], folder_name))

        return send_file(archive_path + '.' + archive_extension, as_attachment=True)


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)