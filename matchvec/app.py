import os
import cv2
import numpy as np
from flask import Flask, send_from_directory, request, Blueprint
from flask_restplus import Resource, Api, reqparse
from process import predict_class, predict_objects
from werkzeug.datastructures import FileStorage
from urllib.request import urlopen, HTTPError, URLError
from utils import logger

app = Flask(__name__)
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
app.config.SWAGGER_UI_OPERATION_ID = True
app.config.SWAGGER_UI_REQUEST_DURATION = True


##########################
#  Documentation Sphinx  #
##########################

blueprint_doc = Blueprint('documentation', __name__,
                          static_folder='../docs/build/html/_static',
                          url_prefix='/docs')


@blueprint_doc.route('/', defaults={'filename': 'index.html'})
@blueprint_doc.route('/<path:filename>')
def show_pages(filename):
    return send_from_directory('../docs/build/html', filename)


app.register_blueprint(blueprint_doc)

#################
#  API SWAGGER  #
#################

blueprint = Blueprint('api', __name__, url_prefix='/api')
api = Api(blueprint, doc='/doc', version='1.0', title='IA Flash',
          description='Classification marque et modèle')
app.register_blueprint(blueprint)


parser = reqparse.RequestParser()
parser.add_argument('url', type=str, location='form')
parser.add_argument('image', type=FileStorage, location='files')


@api.route('/object_detection')
class ObjectDetection(Resource):
    """Docstring for MyClass. """

    @api.expect(parser)
    def post(self):
        images = request.files.getlist('image', None)
        url = request.form.get('url', None)
        res = list()
        if url:
            try:
                resp = urlopen(url, timeout=3)
                img = np.asarray(bytearray(resp.read()), dtype="uint8")
                img = cv2.imdecode(img, cv2.IMREAD_COLOR)
                res.append(predict_objects(img))
            except Exception as e:
                logger.debug(e)
                logger.debug(url)
        if images:
            for i in range(len(images)):
                nparr = np.frombuffer(images[i].read(), np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                res.append(predict_objects(img))
        return res


@api.route('/predict')
class ClassPrediction(Resource):
    """Predict vehicule class"""

    @api.expect(parser)
    def post(self):
        images = request.files.getlist('image')
        url = request.form.get('url', None)
        res = list()
        if url:
            try:
                resp = urlopen(url)
                img = np.asarray(bytearray(resp.read()), dtype="uint8")
                img = cv2.imdecode(img, cv2.IMREAD_COLOR)
                res.append(predict_class(img))
            except Exception as e:
                logger.debug(e)
                logger.debug(url)
                res.append(list())
        if images:
            for i in range(len(images)):
                nparr = np.frombuffer(images[i].read(), np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                res.append(predict_class(img))
        return res


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=bool(os.getenv('DEBUG')))
