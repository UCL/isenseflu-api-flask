from flask_api import FlaskAPI, status
from flask_sqlalchemy import SQLAlchemy

from instance.config import app_config

db = SQLAlchemy()


def create_app(config_name):

    from app.models import FluModel

    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.ini', silent=True)
    db.init_app(app)

    @app.route('/', methods=['GET'])
    def root_route():
        flu_models = FluModel.get_all_public()
        if flu_models is None:
            return '', status.HTTP_503_SERVICE_UNAVAILABLE
        elif not flu_models:
            return '', status.HTTP_204_NO_CONTENT
        else:
            results = []
            for flu_model in flu_models:
                datapoint = []
                for score in flu_model.model_scores:
                    child = {
                        'score_date': score.score_date,
                        'score_value': score.score_value
                    }
                    datapoint.append(child)
                model_parameters = flu_model.get_model_parameters()
                obj = {
                    'name': flu_model.name,
                    'sourceType': flu_model.source_type,
                    'displayModel': flu_model.is_displayed,
                    'parameters': {'georegion': 'e', 'smoothing': model_parameters['average_window_size']},
                    'datapoints': datapoint
                }
                results.append(obj)
            return results, status.HTTP_200_OK

    @app.route('/models', methods=['GET'])
    def models_route():
        flu_models = FluModel.get_all_public()
        if flu_models is None:
            return '', status.HTTP_503_SERVICE_UNAVAILABLE
        elif not flu_models:
            return '', status.HTTP_204_NO_CONTENT
        else:
            results = []
            for flu_model in flu_models:
                obj = {
                    'id': flu_model.id,
                    'name': flu_model.name
                }
                results.append(obj)
            return results, status.HTTP_200_OK

    from .google import google_blueprint
    app.register_blueprint(google_blueprint)

    return app
